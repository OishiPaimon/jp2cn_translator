"""
日语到中文翻译程序 - 格式保存模块测试

此模块用于测试FormatPreserver类的功能
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from modules.document_reader import DocumentReader
from modules.format_preserver import FormatPreserver

class TestFormatPreserver(unittest.TestCase):
    """测试格式保存器类"""
    
    def setUp(self):
        """测试前准备"""
        self.samples_dir = Path(__file__).parent / "samples"
        self.docx_sample = self.samples_dir / "sample_ja.docx"
        self.pdf_sample = self.samples_dir / "sample_ja.pdf"
        
        # 创建临时目录用于保存输出文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_docx = Path(self.temp_dir.name) / "output_ja.docx"
        self.output_pdf = Path(self.temp_dir.name) / "output_ja.pdf"
        
        # 准备测试数据
        self.original_paragraphs = [
            "これは日本語のテスト文書です。",
            "翻訳プログラムのテストに使用します。",
            "書式を保持する機能をテストします。"
        ]
        
        self.translated_paragraphs = [
            "这是日语测试文档。",
            "用于测试翻译程序。",
            "测试保持格式的功能。"
        ]
    
    def tearDown(self):
        """测试后清理"""
        self.temp_dir.cleanup()
    
    def test_create_plain_document(self):
        """测试创建纯文本文档"""
        # 创建格式保存器
        format_preserver = FormatPreserver(preserve_format=False)
        
        # 创建纯文本文档
        output_path = Path(self.temp_dir.name) / "plain_output.txt"
        result = format_preserver._create_plain_document(
            self.translated_paragraphs, 
            str(output_path), 
            'txt'
        )
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(output_path.exists())
        
        # 验证文件内容
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for para in self.translated_paragraphs:
                self.assertIn(para, content)
        
        print("\n纯文本文档创建测试结果:")
        print(f"输出文件: {output_path}")
        print(f"文件大小: {output_path.stat().st_size} 字节")
    
    def test_docx_format_preservation(self):
        """测试Word文档格式保存"""
        # 检查样例文件是否存在
        if not self.docx_sample.exists():
            self.skipTest(f"样例Word文档不存在: {self.docx_sample}")
        
        # 读取样例文档
        reader = DocumentReader(str(self.docx_sample))
        original_paragraphs, format_info = reader.read()
        
        # 创建格式保存器
        format_preserver = FormatPreserver(preserve_format=True)
        
        # 创建格式一致的Word文档
        result = format_preserver.create_document(
            original_paragraphs,
            self.translated_paragraphs[:len(original_paragraphs)] if len(original_paragraphs) > 0 else self.translated_paragraphs,
            format_info,
            str(self.output_docx),
            'docx'
        )
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.output_docx.exists())
        
        print("\nWord文档格式保存测试结果:")
        print(f"输入文件: {self.docx_sample}")
        print(f"输出文件: {self.output_docx}")
        print(f"输入文件大小: {self.docx_sample.stat().st_size} 字节")
        print(f"输出文件大小: {self.output_docx.stat().st_size} 字节")
    
    def test_pdf_format_preservation(self):
        """测试PDF文档格式保存"""
        # 检查样例文件是否存在
        if not self.pdf_sample.exists():
            self.skipTest(f"样例PDF文档不存在: {self.pdf_sample}")
        
        # 读取样例文档
        reader = DocumentReader(str(self.pdf_sample))
        original_paragraphs, format_info = reader.read()
        
        # 创建格式保存器
        format_preserver = FormatPreserver(preserve_format=True)
        
        # 创建格式一致的PDF文档
        result = format_preserver.create_document(
            original_paragraphs,
            self.translated_paragraphs[:len(original_paragraphs)] if len(original_paragraphs) > 0 else self.translated_paragraphs,
            format_info,
            str(self.output_pdf),
            'pdf'
        )
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.output_pdf.exists())
        
        print("\nPDF文档格式保存测试结果:")
        print(f"输入文件: {self.pdf_sample}")
        print(f"输出文件: {self.output_pdf}")
        print(f"输入文件大小: {self.pdf_sample.stat().st_size} 字节")
        print(f"输出文件大小: {self.output_pdf.stat().st_size} 字节")
    
    def test_format_toggle(self):
        """测试格式保存开关"""
        # 创建格式保存器（关闭格式保存）
        format_preserver_off = FormatPreserver(preserve_format=False)
        
        # 创建纯文本Word文档
        output_path_off = Path(self.temp_dir.name) / "format_off.docx"
        result_off = format_preserver_off.create_document(
            self.original_paragraphs,
            self.translated_paragraphs,
            {},  # 空格式信息
            str(output_path_off),
            'docx'
        )
        
        # 创建格式保存器（开启格式保存）
        format_preserver_on = FormatPreserver(preserve_format=True)
        
        # 创建带格式Word文档
        output_path_on = Path(self.temp_dir.name) / "format_on.docx"
        result_on = format_preserver_on.create_document(
            self.original_paragraphs,
            self.translated_paragraphs,
            {'styles': []},  # 最小格式信息
            str(output_path_on),
            'docx'
        )
        
        # 验证结果
        self.assertTrue(result_off)
        self.assertTrue(result_on)
        self.assertTrue(output_path_off.exists())
        self.assertTrue(output_path_on.exists())
        
        print("\n格式保存开关测试结果:")
        print(f"关闭格式保存输出: {output_path_off}")
        print(f"开启格式保存输出: {output_path_on}")

if __name__ == "__main__":
    unittest.main()
