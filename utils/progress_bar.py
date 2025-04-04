"""
日语到中文翻译程序 - 进度显示工具

此模块提供进度显示相关的工具函数
"""

import sys
import time
from typing import List, Dict, Any, Optional, Union
from tqdm import tqdm

class ProgressBar:
    """进度条管理器，用于显示翻译进度"""
    
    def __init__(self, total: int, desc: str = "进度"):
        """
        初始化进度条
        
        Args:
            total: 总任务数
            desc: 进度条描述
        """
        self.total = total
        self.desc = desc
        self.progress_bar = tqdm(total=total, desc=desc)
        self.current = 0
    
    def update(self, n: int = 1):
        """
        更新进度
        
        Args:
            n: 完成的任务数
        """
        self.progress_bar.update(n)
        self.current += n
    
    def set_description(self, desc: str):
        """
        设置进度条描述
        
        Args:
            desc: 新的描述
        """
        self.desc = desc
        self.progress_bar.set_description(desc)
    
    def close(self):
        """关闭进度条"""
        self.progress_bar.close()


class ConsoleLogger:
    """控制台日志记录器"""
    
    def __init__(self, verbose: bool = True):
        """
        初始化日志记录器
        
        Args:
            verbose: 是否显示详细信息
        """
        self.verbose = verbose
    
    def info(self, message: str):
        """
        记录信息
        
        Args:
            message: 信息内容
        """
        if self.verbose:
            print(f"[INFO] {message}")
    
    def warning(self, message: str):
        """
        记录警告
        
        Args:
            message: 警告内容
        """
        print(f"[WARNING] {message}")
    
    def error(self, message: str):
        """
        记录错误
        
        Args:
            message: 错误内容
        """
        print(f"[ERROR] {message}", file=sys.stderr)
    
    def success(self, message: str):
        """
        记录成功信息
        
        Args:
            message: 成功信息内容
        """
        print(f"[SUCCESS] {message}")


class TranslationStats:
    """翻译统计信息"""
    
    def __init__(self):
        """初始化统计信息"""
        self.start_time = time.time()
        self.end_time = None
        self.total_paragraphs = 0
        self.translated_paragraphs = 0
        self.total_characters = 0
        self.translated_characters = 0
        self.dictionary_terms = 0
        self.api_calls = 0
        self.errors = 0
    
    def start(self, total_paragraphs: int, total_characters: int):
        """
        开始统计
        
        Args:
            total_paragraphs: 总段落数
            total_characters: 总字符数
        """
        self.start_time = time.time()
        self.total_paragraphs = total_paragraphs
        self.total_characters = total_characters
    
    def update(self, paragraphs: int = 0, characters: int = 0, api_calls: int = 0, errors: int = 0):
        """
        更新统计信息
        
        Args:
            paragraphs: 新翻译的段落数
            characters: 新翻译的字符数
            api_calls: 新的API调用次数
            errors: 新的错误次数
        """
        self.translated_paragraphs += paragraphs
        self.translated_characters += characters
        self.api_calls += api_calls
        self.errors += errors
    
    def finish(self):
        """完成统计"""
        self.end_time = time.time()
    
    def get_elapsed_time(self) -> float:
        """
        获取已用时间（秒）
        
        Returns:
            float: 已用时间
        """
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_progress(self) -> float:
        """
        获取进度百分比
        
        Returns:
            float: 进度百分比
        """
        if self.total_paragraphs == 0:
            return 0.0
        return (self.translated_paragraphs / self.total_paragraphs) * 100
    
    def get_speed(self) -> float:
        """
        获取翻译速度（字符/秒）
        
        Returns:
            float: 翻译速度
        """
        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0
        return self.translated_characters / elapsed
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要
        
        Returns:
            Dict[str, Any]: 统计摘要
        """
        elapsed = self.get_elapsed_time()
        return {
            "total_paragraphs": self.total_paragraphs,
            "translated_paragraphs": self.translated_paragraphs,
            "total_characters": self.total_characters,
            "translated_characters": self.translated_characters,
            "progress": self.get_progress(),
            "elapsed_time": elapsed,
            "speed": self.get_speed(),
            "api_calls": self.api_calls,
            "errors": self.errors,
            "dictionary_terms": self.dictionary_terms
        }
    
    def print_summary(self):
        """打印统计摘要"""
        summary = self.get_summary()
        print("\n翻译统计信息:")
        print(f"总段落数: {summary['total_paragraphs']}")
        print(f"已翻译段落: {summary['translated_paragraphs']}")
        print(f"总字符数: {summary['total_characters']}")
        print(f"已翻译字符: {summary['translated_characters']}")
        print(f"进度: {summary['progress']:.2f}%")
        print(f"用时: {summary['elapsed_time']:.2f}秒")
        print(f"速度: {summary['speed']:.2f}字符/秒")
        print(f"API调用次数: {summary['api_calls']}")
        print(f"词典术语数: {summary['dictionary_terms']}")
        print(f"错误次数: {summary['errors']}")
