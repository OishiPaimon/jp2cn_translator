"""
日语到中文翻译程序 - 文本处理工具

此模块提供文本处理相关的工具函数
"""

import re
from typing import List, Dict, Any, Tuple

def split_text_into_sentences(text: str) -> List[str]:
    """
    将文本分割为句子
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 句子列表
    """
    # 日语句子分隔符
    separators = r'[。！？\n]+'
    sentences = re.split(separators, text)
    
    # 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def split_text_into_chunks(text: str, max_length: int = 4000) -> List[str]:
    """
    将长文本分割为适合API处理的小块
    
    Args:
        text: 输入文本
        max_length: 每块的最大长度
        
    Returns:
        List[str]: 文本块列表
    """
    if len(text) <= max_length:
        return [text]
    
    # 先按句子分割
    sentences = split_text_into_sentences(text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # 如果单个句子超过最大长度，需要进一步分割
        if len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # 按字符分割长句子
            for i in range(0, len(sentence), max_length):
                chunks.append(sentence[i:i+max_length])
        
        # 如果添加当前句子会超过最大长度，先保存当前块
        elif len(current_chunk) + len(sentence) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = sentence
        
        # 否则添加到当前块
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def detect_language(text: str) -> str:
    """
    检测文本语言
    
    Args:
        text: 输入文本
        
    Returns:
        str: 语言代码，'ja'表示日语，'zh'表示中文，'other'表示其他语言
    """
    # 简单实现：根据字符集判断语言
    # 实际应用中可以使用更复杂的语言检测库
    
    # 日语特有字符（平假名和片假名）
    japanese_chars = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    
    # 中文特有字符
    chinese_chars = re.compile(r'[\u4E00-\u9FFF]')
    
    # 统计字符数量
    ja_count = len(japanese_chars.findall(text))
    zh_count = len(chinese_chars.findall(text))
    
    # 根据字符数量判断语言
    if ja_count > zh_count:
        return 'ja'
    elif zh_count > 0:
        return 'zh'
    else:
        return 'other'

def find_potential_terms(text: str, min_length: int = 2, max_length: int = 10) -> List[str]:
    """
    从文本中查找潜在的术语
    
    Args:
        text: 输入文本
        min_length: 最小术语长度
        max_length: 最大术语长度
        
    Returns:
        List[str]: 潜在术语列表
    """
    # 简单实现：查找连续的汉字、平假名或片假名
    # 实际应用中可以使用更复杂的术语提取算法
    
    # 匹配日语术语的正则表达式
    pattern = r'[一-龥ぁ-んァ-ヶ]{' + str(min_length) + r',' + str(max_length) + r'}'
    
    # 查找所有匹配项
    terms = re.findall(pattern, text)
    
    # 去重
    unique_terms = list(set(terms))
    
    return unique_terms
