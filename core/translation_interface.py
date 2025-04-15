"""
翻译接口模块 - 负责与DeepSeek API和Ollama本地接口交互，处理翻译请求
"""
import os
import json
import requests
import configparser
from typing import Dict, List, Tuple, Optional, Any


class TranslationInterface:
    def __init__(self, config_path: str):
        """
        初始化翻译接口
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.translation_method = self.config.get('Translation', 'translation_method')
        self.max_prompt_length = int(self.config.get('Translation', 'max_prompt_length'))
        
        # DeepSeek API配置
        self.deepseek_api_key = self.config.get('API', 'deepseek_api_key')
        self.deepseek_model = self.config.get('API', 'deepseek_model')
        
        # Ollama配置
        self.ollama_url = self.config.get('API', 'ollama_url')
        self.ollama_model = self.config.get('API', 'ollama_model')

    def _load_config(self, config_path: str) -> configparser.ConfigParser:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置对象
        """
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        return config

    def save_config(self, config_path: str) -> None:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        with open(config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def update_config(self, section: str, key: str, value: str, config_path: str) -> None:
        """
        更新配置
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
            config_path: 配置文件路径
        """
        self.config.set(section, key, value)
        self.save_config(config_path)
        
        # 更新实例变量
        if section == 'Translation' and key == 'translation_method':
            self.translation_method = value
        elif section == 'Translation' and key == 'max_prompt_length':
            self.max_prompt_length = int(value)
        elif section == 'API' and key == 'deepseek_api_key':
            self.deepseek_api_key = value
        elif section == 'API' and key == 'deepseek_model':
            self.deepseek_model = value
        elif section == 'API' and key == 'ollama_url':
            self.ollama_url = value
        elif section == 'API' and key == 'ollama_model':
            self.ollama_model = value

    def build_prompt(self, content_blocks: List[str]) -> str:
        """
        构建翻译提示词
        
        Args:
            content_blocks: 内容块列表
            
        Returns:
            构建的提示词
        """
        prompt = """请将以下日语文本翻译成中文。请严格遵守以下要求：
1. 保留所有原文的换行符，不要改变文本格式
2. 不要添加任何额外内容，如总结、解释或问题
3. 不要修改被标记为 ***内容*** 的部分，直接保留其中的内容
4. 只需提供翻译结果，不需要原文或其他说明
5. 保留所有符号

以下是需要翻译的文本：

"""
        
        # 添加内容块
        for block in content_blocks:
            prompt += block
            
        return prompt

    def translate_with_deepseek(self, prompt: str) -> Optional[str]:
        """
        使用DeepSeek API进行翻译
        
        Args:
            prompt: 提示词
            
        Returns:
            翻译结果，如果失败则返回None
        """
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API密钥未设置")
            
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.deepseek_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # 低温度以获得更确定性的输出
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return None
        except Exception as e:
            print(f"DeepSeek API调用失败: {str(e)}")
            return None

    def translate_with_ollama(self, prompt: str) -> Optional[str]:
        """
        使用 Ollama 本地的 /api/chat 接口进行翻译

        Args:
            prompt: 要翻译的原始文本

        Returns:
            翻译结果字符串，如果失败返回 None
        """
        if not self.ollama_url or not self.ollama_model:
            raise ValueError("Ollama URL或模型未设置")

        data = {
            "model": self.ollama_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
        }

        # print(prompt)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=data,
                stream=True  # 使用流式返回
            )
            response.raise_for_status()

            result_text = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        obj = json.loads(line)
                        if "message" in obj and "content" in obj["message"]:
                            result_text += obj["message"]["content"]
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")

            return result_text.strip() if result_text else None

        except Exception as e:
            print(f"Ollama API调用失败: {str(e)}")
            return None

    def translate(self, content_blocks: List[str]) -> Optional[str]:
        """
        根据配置的翻译方法进行翻译
        
        Args:
            content_blocks: 内容块列表
            
        Returns:
            翻译结果，如果失败则返回None
        """
        prompt = self.build_prompt(content_blocks)
        
        if self.translation_method == "deepseek":
            return self.translate_with_deepseek(prompt)
        elif self.translation_method == "ollama":
            print(self.translate_with_ollama(prompt))
            return self.translate_with_ollama(prompt)
        else:
            raise ValueError(f"不支持的翻译方法: {self.translation_method}")


# 测试代码
if __name__ == "__main__":
    # 创建临时配置文件
    config_content = """[API]
# DeepSeek API配置
deepseek_api_key = test_key
deepseek_model = deepseek-chat

# Ollama配置
ollama_url = http://localhost:11434
ollama_model = llama3

[Translation]
# 翻译设置
max_prompt_length = 4000
translation_method = deepseek
"""
    
    with open("test_config.ini", "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # 初始化翻译接口
    translator = TranslationInterface("test_config.ini")
    
    # 测试提示词构建
    test_blocks = [
        "こんにちは、私の名前は田中です。\n",
        "私は東京に住んでいます。\n\n",
        "よろしくお願いします。"
    ]
    
    prompt = translator.build_prompt(test_blocks)
    print("构建的提示词:")
    print(prompt)
    
    # 注意：实际的API调用需要有效的API密钥
    print("\n由于没有实际的API密钥，跳过实际翻译测试")
    
    # 测试配置更新
    translator.update_config("Translation", "translation_method", "ollama", "test_config.ini")
    print("\n更新后的翻译方法:", translator.translation_method)
