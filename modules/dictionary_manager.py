"""
日语到中文翻译程序 - 词典管理模块

此模块负责管理永久词典和临时词典
"""

import os
import json
from typing import Dict, Optional, Any
from pathlib import Path

from config import PERMANENT_DICT_PATH, TEMP_DICT_TEMPLATE_PATH


class DictionaryManager:
    """词典管理器，负责管理永久词典和临时词典"""
    
    def __init__(self, permanent_dict_path: str = None, temp_dict_path: str = None):
        """
        初始化词典管理器
        
        Args:
            permanent_dict_path: 永久词典路径
            temp_dict_path: 临时词典路径
        """
        self.permanent_dict_path = permanent_dict_path or PERMANENT_DICT_PATH
        self.temp_dict_path = temp_dict_path
        
        # 加载永久词典
        self.permanent_dict = self._load_dict(self.permanent_dict_path)
        
        # 初始化临时词典
        self.temp_dict = {}
        if self.temp_dict_path:
            self.temp_dict = self._load_dict(self.temp_dict_path)
    
    def _load_dict(self, dict_path: str) -> Dict[str, str]:
        """
        加载词典文件
        
        Args:
            dict_path: 词典文件路径
            
        Returns:
            Dict[str, str]: 词典内容
        """
        if not os.path.exists(dict_path):
            return {}
        
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 处理不同的词典格式
                if 'permanent_dict' in data:
                    return data['permanent_dict']
                elif 'temp_dict' in data:
                    return data['temp_dict']
                else:
                    return data
        except Exception as e:
            print(f"加载词典文件失败: {e}")
            return {}
    
    def save_permanent_dict(self) -> bool:
        """
        保存永久词典
        
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.permanent_dict_path, 'w', encoding='utf-8') as f:
                json.dump({'permanent_dict': self.permanent_dict}, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存永久词典失败: {e}")
            return False
    
    def save_temp_dict(self, output_path: str = None) -> bool:
        """
        保存临时词典
        
        Args:
            output_path: 输出路径，如果为None则使用初始化时的路径
            
        Returns:
            bool: 是否保存成功
        """
        if not output_path and not self.temp_dict_path:
            print("未指定临时词典保存路径")
            return False
        
        save_path = output_path or self.temp_dict_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump({'temp_dict': self.temp_dict}, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存临时词典失败: {e}")
            return False
    
    def create_temp_dict(self, output_path: str) -> bool:
        """
        创建新的临时词典
        
        Args:
            output_path: 输出路径
            
        Returns:
            bool: 是否创建成功
        """
        self.temp_dict = {}
        self.temp_dict_path = output_path
        return self.save_temp_dict()
    
    def add_to_permanent_dict(self, jp_term: str, cn_term: str) -> bool:
        """
        添加词条到永久词典
        
        Args:
            jp_term: 日语术语
            cn_term: 中文翻译
            
        Returns:
            bool: 是否添加成功
        """
        if not jp_term or not cn_term:
            return False
        
        self.permanent_dict[jp_term] = cn_term
        return self.save_permanent_dict()
    
    def add_to_temp_dict(self, jp_term: str, cn_term: str) -> bool:
        """
        添加词条到临时词典
        
        Args:
            jp_term: 日语术语
            cn_term: 中文翻译
            
        Returns:
            bool: 是否添加成功
        """
        if not jp_term or not cn_term:
            return False
        
        if not self.temp_dict_path:
            print("未指定临时词典路径")
            return False
        
        self.temp_dict[jp_term] = cn_term
        return self.save_temp_dict()
    
    def remove_from_permanent_dict(self, jp_term: str) -> bool:
        """
        从永久词典中删除词条
        
        Args:
            jp_term: 日语术语
            
        Returns:
            bool: 是否删除成功
        """
        if jp_term in self.permanent_dict:
            del self.permanent_dict[jp_term]
            return self.save_permanent_dict()
        return False
    
    def remove_from_temp_dict(self, jp_term: str) -> bool:
        """
        从临时词典中删除词条
        
        Args:
            jp_term: 日语术语
            
        Returns:
            bool: 是否删除成功
        """
        if not self.temp_dict_path:
            print("未指定临时词典路径")
            return False
        
        if jp_term in self.temp_dict:
            del self.temp_dict[jp_term]
            return self.save_temp_dict()
        return False
    
    def get_merged_dict(self) -> Dict[str, str]:
        """
        获取合并后的词典（临时词典优先）
        
        Returns:
            Dict[str, str]: 合并后的词典
        """
        merged = self.permanent_dict.copy()
        merged.update(self.temp_dict)
        return merged
    
    def extract_terms_from_text(self, text: str, min_length: int = 2) -> Dict[str, str]:
        """
        从文本中提取可能的术语
        
        Args:
            text: 文本内容
            min_length: 最小术语长度
            
        Returns:
            Dict[str, str]: 提取的术语字典，值为空字符串
        """
        # 简单实现：提取所有可能的名词短语
        # 实际应用中可以使用更复杂的NLP技术
        import re
        
        # 特定术语的直接匹配
        specific_terms = ["日本語", "翻訳", "プログラム", "テスト", "サンプル"]
        term_dict = {}
        
        # 先检查特定术语
        for term in specific_terms:
            if term in text:
                term_dict[term] = ""
        
        # 提取可能的日语术语（假设术语是由汉字、平假名或片假名组成的短语）
        pattern = r'[一-龥ぁ-んァ-ヶ]{' + str(min_length) + r',}'
        terms = re.findall(pattern, text)
        
        # 添加到词典
        for term in set(terms):
            term_dict[term] = ""
        
        # 如果没有找到足够的术语，尝试提取整个句子中的关键词组
        if len(term_dict) < 3:
            # 分割句子，提取可能的短语
            words = text.split()
            for word in words:
                if len(word) >= min_length and re.search(r'[一-龥ぁ-んァ-ヶ]', word):
                    term_dict[word] = ""
        
        return term_dict
    
    def suggest_translations(self, terms: Dict[str, str]) -> Dict[str, str]:
        """
        为术语建议翻译
        
        Args:
            terms: 术语字典
            
        Returns:
            Dict[str, str]: 带有建议翻译的术语字典
        """
        result = {}
        
        # 检查永久词典和临时词典中是否已有翻译
        merged_dict = self.get_merged_dict()
        
        for term, _ in terms.items():
            if term in merged_dict:
                result[term] = merged_dict[term]
            else:
                result[term] = ""
        
        return result
