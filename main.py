#!/usr/bin/env python3
"""
日语到中文翻译程序 - 主程序

此程序用于将日语文档翻译成中文，支持Word和PDF格式，
并保持原文档格式，支持永久词典和临时词典。
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# 导入配置
from config import (
    PERMANENT_DICT_PATH,
    TEMP_DICT_TEMPLATE_PATH,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    PRESERVE_FORMAT
)

# 导入模块
from modules.document_reader import DocumentReader
from modules.translator import TranslatorFactory
from modules.dictionary_manager import DictionaryManager
from modules.format_preserver import FormatPreserver

# 导入工具
from utils.text_processor import split_text_into_chunks, detect_language, find_potential_terms
from utils.progress_bar import ProgressBar, ConsoleLogger, TranslationStats


class JP2CNTranslator:
    """日语到中文翻译程序主类"""
    
    def __init__(self, args):
        """
        初始化翻译程序
        
        Args:
            args: 命令行参数
        """
        self.args = args
        self.logger = ConsoleLogger(verbose=not args.quiet)
        self.stats = TranslationStats()
        
        # 初始化词典管理器
        self.dict_manager = DictionaryManager(
            permanent_dict_path=args.permanent_dict or PERMANENT_DICT_PATH,
            temp_dict_path=args.temp_dict
        )
        
        # 初始化翻译器
        translator_type = args.translator_type or 'openai'
        translator_params = {}
        
        if translator_type == 'openai':
            translator_params['api_key'] = args.api_key or OPENAI_API_KEY
            translator_params['model'] = args.model or OPENAI_MODEL
        elif translator_type == 'ollama':
            translator_params['host'] = args.ollama_host or OLLAMA_HOST
            translator_params['model'] = args.ollama_model or OLLAMA_MODEL
        
        self.translator = TranslatorFactory.create_translator(translator_type, **translator_params)
        
        # 初始化格式保存器
        self.format_preserver = FormatPreserver(preserve_format=args.preserve_format)
    
    def run(self):
        """运行翻译程序"""
        # 检查输入文件
        if not os.path.exists(self.args.input_file):
            self.logger.error(f"输入文件不存在: {self.args.input_file}")
            return False
        
        # 确定输出文件
        if not self.args.output_file:
            input_path = Path(self.args.input_file)
            output_path = input_path.with_stem(f"{input_path.stem}_translated")
            self.args.output_file = str(output_path)
        
        # 确定临时词典路径
        if not self.args.temp_dict and not self.args.no_temp_dict:
            input_path = Path(self.args.input_file)
            temp_dict_path = input_path.with_stem(f"{input_path.stem}_temp_dict").with_suffix('.json')
            self.args.temp_dict = str(temp_dict_path)
            self.dict_manager.temp_dict_path = self.args.temp_dict
        
        # 读取文档
        self.logger.info(f"正在读取文档: {self.args.input_file}")
        try:
            reader = DocumentReader(self.args.input_file)
            paragraphs, format_info = reader.read()
            
            # 检查文档语言
            if paragraphs:
                sample_text = " ".join(paragraphs[:5])
                lang = detect_language(sample_text)
                if lang != 'ja':
                    self.logger.warning(f"文档可能不是日语 (检测到: {lang})，是否继续？(y/n)")
                    if not self.args.force and input().lower() != 'y':
                        self.logger.info("已取消翻译")
                        return False
            
            self.logger.info(f"文档读取成功，共 {len(paragraphs)} 段落")
        except Exception as e:
            self.logger.error(f"读取文档失败: {e}")
            return False
        
        # 提取潜在术语并创建临时词典
        if not self.args.no_temp_dict and not self.args.skip_term_extraction:
            self.logger.info("正在提取潜在术语...")
            try:
                # 合并所有段落文本
                full_text = " ".join(paragraphs)
                
                # 提取潜在术语
                terms = find_potential_terms(full_text)
                
                # 创建临时词典
                if not os.path.exists(self.args.temp_dict):
                    self.dict_manager.create_temp_dict(self.args.temp_dict)
                
                # 检查术语是否已在词典中
                term_dict = {}
                merged_dict = self.dict_manager.get_merged_dict()
                for term in terms:
                    if term in merged_dict:
                        term_dict[term] = merged_dict[term]
                    else:
                        term_dict[term] = ""
                
                # 保存临时词典
                if term_dict:
                    self.dict_manager.temp_dict = term_dict
                    self.dict_manager.save_temp_dict()
                    self.logger.info(f"已提取 {len(term_dict)} 个潜在术语并保存到临时词典: {self.args.temp_dict}")
                
                # 提示用户编辑临时词典
                if not self.args.skip_dict_edit:
                    self.logger.info(f"请编辑临时词典文件: {self.args.temp_dict}")
                    self.logger.info("编辑完成后按回车键继续...")
                    input()
                    
                    # 重新加载临时词典
                    self.dict_manager = DictionaryManager(
                        permanent_dict_path=self.args.permanent_dict or PERMANENT_DICT_PATH,
                        temp_dict_path=self.args.temp_dict
                    )
            except Exception as e:
                self.logger.error(f"提取术语失败: {e}")
        
        # 开始翻译
        self.logger.info("开始翻译...")
        self.stats.start(len(paragraphs), sum(len(p) for p in paragraphs))
        
        try:
            # 创建进度条
            progress_bar = ProgressBar(total=len(paragraphs), desc="翻译进度")
            
            # 获取合并的词典
            dictionary = self.dict_manager.get_merged_dict()
            self.stats.dictionary_terms = len(dictionary)
            
            # 批量翻译
            translated_paragraphs = []
            batch_size = self.args.batch_size or 10
            
            for i in range(0, len(paragraphs), batch_size):
                batch = paragraphs[i:i+batch_size]
                
                # 翻译批次
                batch_translated = self.translator.batch_translate(batch, dictionary)
                translated_paragraphs.extend(batch_translated)
                
                # 更新进度和统计
                progress_bar.update(len(batch))
                self.stats.update(
                    paragraphs=len(batch),
                    characters=sum(len(p) for p in batch),
                    api_calls=len(batch)
                )
            
            progress_bar.close()
            self.stats.finish()
            
            # 打印统计信息
            self.stats.print_summary()
            
        except Exception as e:
            self.logger.error(f"翻译失败: {e}")
            return False
        
        # 保存翻译结果
        self.logger.info(f"正在保存翻译结果: {self.args.output_file}")
        try:
            # 获取文件类型
            file_extension = os.path.splitext(self.args.input_file)[1].lower()
            file_type = 'docx' if file_extension == '.docx' else 'pdf' if file_extension == '.pdf' else 'txt'
            
            # 创建输出文件
            success = self.format_preserver.create_document(
                paragraphs,
                translated_paragraphs,
                format_info,
                self.args.output_file,
                file_type
            )
            
            if success:
                self.logger.success(f"翻译完成，结果已保存到: {self.args.output_file}")
                return True
            else:
                self.logger.error("保存翻译结果失败")
                return False
                
        except Exception as e:
            self.logger.error(f"保存翻译结果失败: {e}")
            return False


def parse_args(args=None):
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="日语到中文翻译程序")
    
    # 必需参数
    parser.add_argument("input_file", help="输入文件路径", nargs="?")
    
    # 可选参数
    parser.add_argument("-o", "--output-file", help="输出文件路径")
    parser.add_argument("-p", "--permanent-dict", help="永久词典路径")
    parser.add_argument("-t", "--temp-dict", help="临时词典路径")
    parser.add_argument("--no-temp-dict", action="store_true", help="不使用临时词典")
    parser.add_argument("--skip-term-extraction", action="store_true", help="跳过术语提取")
    parser.add_argument("--skip-dict-edit", action="store_true", help="跳过词典编辑")
    
    # 翻译器选项
    parser.add_argument("--translator-type", choices=["openai", "deepseek", "ollama"], help="翻译器类型")
    parser.add_argument("--api-key", help="OpenAI或DeepSeek API密钥")
    parser.add_argument("--model", help="OpenAI或DeepSeek模型名称")
    parser.add_argument("--api-base", help="DeepSeek API基础URL")
    parser.add_argument("--ollama-host", help="Ollama服务器地址")
    parser.add_argument("--ollama-model", help="Ollama模型名称")
    
    # 格式选项
    parser.add_argument("--preserve-format", action="store_true", help="保持原文档格式")
    parser.add_argument("--no-preserve-format", action="store_false", dest="preserve_format", help="不保持原文档格式")
    parser.set_defaults(preserve_format=PRESERVE_FORMAT)
    
    # 其他选项
    parser.add_argument("--batch-size", type=int, help="批处理大小")
    parser.add_argument("--force", action="store_true", help="强制执行，不询问确认")
    parser.add_argument("-q", "--quiet", action="store_true", help="安静模式，减少输出")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    
    return parser.parse_args(args)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 显示版本信息
    if args.version:
        print("日语到中文翻译程序 v1.0.0")
        return 0

    # 创建并运行翻译程序
    translator = JP2CNTranslator(args)
    success = translator.run()
    
    # 返回状态码
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
