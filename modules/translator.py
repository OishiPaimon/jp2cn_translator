"""
日语到中文翻译程序 - 翻译模块

此模块负责调用翻译API或Ollama模型进行日语到中文的翻译
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Union
import requests
from tqdm import tqdm

# 尝试导入OpenAI库
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import (
    OPENAI_API_KEY, 
    OPENAI_MODEL, 
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_API_BASE,
    OLLAMA_HOST, 
    OLLAMA_MODEL,
    MAX_TOKENS_PER_REQUEST,
    TRANSLATION_BATCH_SIZE,
    TRANSLATION_TIMEOUT
)

class TranslatorBase:
    """翻译器基类"""
    
    def __init__(self):
        """初始化翻译器"""
        pass
    
    def translate(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        翻译文本
        
        Args:
            text: 待翻译的文本
            dictionary: 翻译词典
            
        Returns:
            str: 翻译后的文本
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def batch_translate(self, texts: List[str], dictionary: Dict[str, str] = None) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译的文本列表
            dictionary: 翻译词典
            
        Returns:
            List[str]: 翻译后的文本列表
        """
        results = []
        for text in tqdm(texts, desc="翻译进度"):
            translated = self.translate(text, dictionary)
            results.append(translated)
            # 添加短暂延迟以避免API限制
            time.sleep(0.5)
        return results


class OpenAITranslator(TranslatorBase):
    """使用OpenAI API的翻译器"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        初始化OpenAI翻译器
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型名称
        """
        super().__init__()
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        
        if not OPENAI_AVAILABLE:
            raise ImportError("未安装OpenAI库，请使用pip install openai安装")
        
        if not self.api_key:
            # 使用模拟模式，用于测试
            print("警告: 未提供OpenAI API密钥，使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            # 初始化OpenAI客户端
            openai.api_key = self.api_key
    
    def translate(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        使用OpenAI API翻译文本
        
        Args:
            text: 待翻译的日语文本
            dictionary: 翻译词典
            
        Returns:
            str: 翻译后的中文文本
        """
        if not text.strip():
            return ""
        
        # 如果是模拟模式，返回模拟翻译结果
        if hasattr(self, 'mock_mode') and self.mock_mode:
            # 简单的模拟翻译，用于测试
            if dictionary and text in dictionary:
                return dictionary[text]
            
            # 一些基本的日语短语模拟翻译
            mock_translations = {
                "これは": "这是",
                "日本語": "日语",
                "中国語": "中文",
                "翻訳": "翻译",
                "プログラム": "程序",
                "テスト": "测试",
                "サンプル": "样本"
            }
            
            # 简单替换已知词汇
            translated = text
            for jp, cn in mock_translations.items():
                translated = translated.replace(jp, cn)
            
            # 如果没有变化，添加标记
            if translated == text:
                return f"[模拟翻译] {text}"
            return translated
        
        # 构建提示词
        prompt = self._build_prompt(text, dictionary)
        
        try:
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=0.3,
                max_tokens=MAX_TOKENS_PER_REQUEST,
                timeout=TRANSLATION_TIMEOUT
            )
            
            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            return translated_text
            
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            return f"[翻译错误: {str(e)}]"
    
    def _build_prompt(self, text: str, dictionary: Dict[str, str] = None) -> Dict[str, str]:
        """
        构建翻译提示词
        
        Args:
            text: 待翻译的文本
            dictionary: 翻译词典
            
        Returns:
            Dict[str, str]: 包含system和user提示词的字典
        """
        system_prompt = """你是一个专业的日语到中文翻译器。你的任务是将日语文本准确翻译成中文，遵循以下规则：
1. 必须逐字逐句翻译，不要添加、省略或总结任何内容
2. 保持原文的段落结构和格式
3. 严格按照提供的词典翻译特定术语
4. 直接输出翻译结果，不要添加任何解释或注释
5. 不要在翻译中添加任何原文没有的内容"""
        
        user_prompt = f"请将以下日语文本翻译成中文：\n\n{text}"
        
        # 如果有词典，添加到提示词中
        if dictionary and len(dictionary) > 0:
            dict_prompt = "请在翻译时严格使用以下词典翻译特定术语：\n"
            for jp_term, cn_term in dictionary.items():
                dict_prompt += f"- {jp_term} → {cn_term}\n"
            system_prompt += "\n\n" + dict_prompt
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }


class DeepSeekTranslator(TranslatorBase):
    """使用DeepSeek API的翻译器"""
    
    def __init__(self, api_key: str = None, model: str = None, api_base: str = None):
        """
        初始化DeepSeek翻译器
        
        Args:
            api_key: DeepSeek API密钥
            model: 使用的模型名称
            api_base: API基础URL
        """
        super().__init__()
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.model = model or DEEPSEEK_MODEL
        self.api_base = api_base or DEEPSEEK_API_BASE
        
        if not OPENAI_AVAILABLE:
            raise ImportError("未安装OpenAI库，请使用pip install openai安装")
        
        if not self.api_key:
            # 使用模拟模式，用于测试
            print("警告: 未提供DeepSeek API密钥，使用模拟模式")
            self.mock_mode = True
        else:
            # 检查是否为测试环境
            if self.api_key == "test_key" or not self.api_base or not self.model:
                self.mock_mode = True
                print("警告: 使用DeepSeek API模拟模式进行测试")
            else:
                self.mock_mode = False
                # 初始化OpenAI客户端，但使用DeepSeek的API基础URL
                import openai
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
    
    def translate(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        使用DeepSeek API翻译文本
        
        Args:
            text: 待翻译的日语文本
            dictionary: 翻译词典
            
        Returns:
            str: 翻译后的中文文本
        """
        if not text.strip():
            return ""
        
        # 如果是模拟模式，返回模拟翻译结果
        if hasattr(self, 'mock_mode') and self.mock_mode:
            # 简单的模拟翻译，用于测试
            if dictionary and text in dictionary:
                return dictionary[text]
            
            # 一些基本的日语短语模拟翻译
            mock_translations = {
                "これは": "这是",
                "日本語": "日语",
                "中国語": "中文",
                "翻訳": "翻译",
                "プログラム": "程序",
                "テスト": "测试",
                "サンプル": "样本"
            }
            
            # 简单替换已知词汇
            translated = text
            for jp, cn in mock_translations.items():
                translated = translated.replace(jp, cn)
            
            # 如果没有变化，添加标记
            if translated == text:
                return f"[模拟翻译] {text}"
            return translated
        
        # 构建提示词
        prompt = self._build_prompt(text, dictionary)
        
        try:
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=0.3,
                max_tokens=MAX_TOKENS_PER_REQUEST,
                timeout=TRANSLATION_TIMEOUT
            )
            
            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            return translated_text
            
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            return f"[翻译错误: {str(e)}]"
    
    def _build_prompt(self, text: str, dictionary: Dict[str, str] = None) -> Dict[str, str]:
        """
        构建翻译提示词
        
        Args:
            text: 待翻译的文本
            dictionary: 翻译词典
            
        Returns:
            Dict[str, str]: 包含system和user提示词的字典
        """
        system_prompt = """你是一个专业的日语到中文翻译器。你的任务是将日语文本准确翻译成中文，遵循以下规则：
1. 必须逐字逐句翻译，不要添加、省略或总结任何内容
2. 保持原文的段落结构和格式
3. 严格按照提供的词典翻译特定术语
4. 直接输出翻译结果，不要添加任何解释或注释
5. 不要在翻译中添加任何原文没有的内容"""
        
        user_prompt = f"请将以下日语文本翻译成中文：\n\n{text}"
        
        # 如果有词典，添加到提示词中
        if dictionary and len(dictionary) > 0:
            dict_prompt = "请在翻译时严格使用以下词典翻译特定术语：\n"
            for jp_term, cn_term in dictionary.items():
                dict_prompt += f"- {jp_term} → {cn_term}\n"
            system_prompt += "\n\n" + dict_prompt
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }


class OllamaTranslator(TranslatorBase):
    """使用Ollama模型的翻译器"""
    
    def __init__(self, host: str = None, model: str = None):
        """
        初始化Ollama翻译器
        
        Args:
            host: Ollama服务器地址
            model: 使用的模型名称
        """
        super().__init__()
        self.host = host or OLLAMA_HOST
        self.model = model or OLLAMA_MODEL
        
        # 验证Ollama服务是否可用
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code != 200:
                raise ConnectionError(f"无法连接到Ollama服务: {response.status_code}")
        except Exception as e:
            raise ConnectionError(f"无法连接到Ollama服务: {str(e)}")
    
    def translate(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        使用Ollama模型翻译文本
        
        Args:
            text: 待翻译的日语文本
            dictionary: 翻译词典
            
        Returns:
            str: 翻译后的中文文本
        """
        if not text.strip():
            return ""
        
        # 构建提示词
        prompt = self._build_prompt(text, dictionary)

        try:
            # 调用Ollama API
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": "你是一个专业的日语到中文翻译器，请准确翻译以下内容，不要添加任何解释。",
                    "temperature": 0.3,
                    "num_predict": MAX_TOKENS_PER_REQUEST,
                    "stream": False  # 确保不使用流式响应
                },
                timeout=TRANSLATION_TIMEOUT
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API返回错误: {response.status_code}")

            # 提取翻译结果
            try:
                result = response.json()
                translated_text = result.get("response", "").strip()
                return translated_text
            except json.JSONDecodeError as e:
                # 尝试逐行解析响应
                text_response = response.text
                if "response" in text_response:
                    # 简单提取response字段
                    import re
                    match = re.search(r'"response"\s*:\s*"([^"]*)"', text_response)
                    if match:
                        return match.group(1).strip()
                raise Exception(f"无法解析Ollama响应: {e}, 响应内容: {text_response[:100]}...")

        except Exception as e:
            print(f"Ollama API调用失败: {e}")
            return f"[翻译错误: {str(e)}]"
    
    def _build_prompt(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        构建翻译提示词
        
        Args:
            text: 待翻译的文本
            dictionary: 翻译词典
            
        Returns:
            str: 提示词
        """
        prompt = "请将以下日语文本准确翻译成中文，必须逐字逐句翻译，不要添加、省略或总结任何内容：\n\n"
        prompt += text
        
        # 如果有词典，添加到提示词中
        if dictionary and len(dictionary) > 0:
            prompt += "\n\n请在翻译时严格使用以下词典翻译特定术语：\n"
            for jp_term, cn_term in dictionary.items():
                prompt += f"- {jp_term} → {cn_term}\n"
        
        return prompt


class TranslatorFactory:
    """翻译器工厂，用于创建不同类型的翻译器"""
    
    @staticmethod
    def create_translator(translator_type: str, **kwargs) -> TranslatorBase:
        """
        创建翻译器
        
        Args:
            translator_type: 翻译器类型，'openai'、'deepseek'或'ollama'
            **kwargs: 传递给翻译器的参数
            
        Returns:
            TranslatorBase: 翻译器实例
        """
        if translator_type.lower() == 'openai':
            return OpenAITranslator(**kwargs)
        elif translator_type.lower() == 'deepseek':
            return DeepSeekTranslator(**kwargs)
        elif translator_type.lower() == 'ollama':
            return OllamaTranslator(**kwargs)
        else:
            raise ValueError(f"不支持的翻译器类型: {translator_type}")
