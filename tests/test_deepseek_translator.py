"""
日语到中文翻译程序 - DeepSeek翻译器测试

此模块用于测试DeepSeek翻译器功能
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from modules.translator import DeepSeekTranslator, TranslatorFactory
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_API_BASE

class TestDeepSeekTranslator(unittest.TestCase):
    """测试DeepSeek翻译器功能"""
    
    def setUp(self):
        """测试前准备"""
        self.api_key = DEEPSEEK_API_KEY
        self.model = DEEPSEEK_MODEL
        self.api_base = DEEPSEEK_API_BASE
        
        # 创建翻译器实例
        self.translator = DeepSeekTranslator(
            api_key=self.api_key,
            model=self.model,
            api_base=self.api_base
        )
        
        # 测试用日语文本
        self.test_text = "これは日本語のテストです。翻訳プログラムをテストしています。"
        
        # 测试用词典
        self.test_dict = {
            "テスト": "测试",
            "プログラム": "程序"
        }
    
    def test_translator_initialization(self):
        """测试翻译器初始化"""
        self.assertEqual(self.translator.api_key, self.api_key)
        self.assertEqual(self.translator.model, self.model)
        self.assertEqual(self.translator.api_base, self.api_base)
        
        # 测试模拟模式
        mock_translator = DeepSeekTranslator(api_key="test_key", model="test_model")
        self.assertTrue(hasattr(mock_translator, 'mock_mode'))
        self.assertTrue(mock_translator.mock_mode)
    
    def test_mock_translation(self):
        """测试模拟翻译功能"""
        # 创建模拟模式的翻译器
        mock_translator = DeepSeekTranslator(api_key="test_key", model="test_model")
        
        # 测试简单翻译
        result = mock_translator.translate("これは日本語です")
        self.assertIn("这是日语", result)
        
        # 测试词典应用
        result = mock_translator.translate("テスト", {"テスト": "特殊测试"})
        self.assertEqual(result, "特殊测试")
    
    def test_build_prompt(self):
        """测试提示词构建"""
        # 不带词典的提示词
        prompt = self.translator._build_prompt(self.test_text)
        self.assertIn("system", prompt)
        self.assertIn("user", prompt)
        self.assertIn(self.test_text, prompt["user"])
        
        # 带词典的提示词
        prompt = self.translator._build_prompt(self.test_text, self.test_dict)
        self.assertIn("词典", prompt["system"])
        self.assertIn("テスト → 测试", prompt["system"])
    
    def test_factory_creation(self):
        """测试工厂创建翻译器"""
        # 使用工厂创建DeepSeek翻译器
        translator = TranslatorFactory.create_translator(
            "deepseek",
            api_key=self.api_key,
            model=self.model,
            api_base=self.api_base
        )
        
        self.assertIsInstance(translator, DeepSeekTranslator)
        self.assertEqual(translator.api_key, self.api_key)
        self.assertEqual(translator.model, self.model)
        self.assertEqual(translator.api_base, self.api_base)

if __name__ == "__main__":
    unittest.main()
