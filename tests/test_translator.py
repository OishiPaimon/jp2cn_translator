"""
日语到中文翻译程序 - 翻译模块测试

此模块用于测试Translator类的功能
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from modules.translator import TranslatorFactory, OpenAITranslator, OllamaTranslator

class TestTranslator(unittest.TestCase):
    """测试翻译器类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_text = "これは日本語から中国語への翻訳プログラムをテストするためのサンプル文です。"
        self.test_dictionary = {
            "翻訳プログラム": "翻译程序",
            "サンプル": "样本"
        }
    
    @patch('openai.ChatCompletion.create')
    def test_openai_translator(self, mock_create):
        """测试OpenAI翻译器"""
        # 模拟OpenAI API响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "这是用于测试从日语到中文的翻译程序的样本句子。"
        mock_create.return_value = mock_response
        
        # 创建OpenAI翻译器
        translator = TranslatorFactory.create_translator('openai', api_key='test_key')
        
        # 测试翻译
        translated = translator.translate(self.test_text, self.test_dictionary)
        
        # 验证结果
        self.assertIsNotNone(translated)
        self.assertTrue(len(translated) > 0)
        print(f"\nOpenAI翻译测试结果:")
        print(f"原文: {self.test_text}")
        print(f"译文: {translated}")
        
        # 验证API调用
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs['model'], 'gpt-4')
        self.assertEqual(len(kwargs['messages']), 2)
    
    @patch('requests.post')
    def test_ollama_translator(self, mock_post):
        """测试Ollama翻译器"""
        # 模拟Ollama API响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "这是用于测试从日语到中文的翻译程序的样本句子。"
        }
        mock_post.return_value = mock_response
        
        # 创建Ollama翻译器
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            translator = TranslatorFactory.create_translator('ollama')
        
        # 测试翻译
        translated = translator.translate(self.test_text, self.test_dictionary)
        
        # 验证结果
        self.assertIsNotNone(translated)
        self.assertTrue(len(translated) > 0)
        print(f"\nOllama翻译测试结果:")
        print(f"原文: {self.test_text}")
        print(f"译文: {translated}")
        
        # 验证API调用
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/api/generate', args[0])
        self.assertEqual(kwargs['json']['model'], 'llama3')
    
    def test_translator_factory(self):
        """测试翻译器工厂"""
        # 测试创建OpenAI翻译器
        with patch('openai.ChatCompletion.create'):
            translator = TranslatorFactory.create_translator('openai', api_key='test_key')
            self.assertIsInstance(translator, OpenAITranslator)
        
        # 测试创建Ollama翻译器
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            translator = TranslatorFactory.create_translator('ollama')
            self.assertIsInstance(translator, OllamaTranslator)
        
        # 测试无效的翻译器类型
        with self.assertRaises(ValueError):
            TranslatorFactory.create_translator('invalid')

if __name__ == "__main__":
    unittest.main()
