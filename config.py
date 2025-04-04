"""
日语到中文翻译程序 - 配置文件

此文件包含程序的全局配置参数
"""

import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# 词典目录
DICT_DIR = ROOT_DIR / "dictionaries"
PERMANENT_DICT_PATH = DICT_DIR / "permanent_dict.json"
TEMP_DICT_TEMPLATE_PATH = DICT_DIR / "temp_dict_template.json"

# 翻译API配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4"  # 默认使用的OpenAI模型
# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-23c4c481fcd54273a724dc0793f225cb"
DEEPSEEK_MODEL = "deepseek-r1"
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
# Ollama配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "qwen2.5"  # 默认使用的Ollama模型

# 翻译配置
MAX_TOKENS_PER_REQUEST = 4000  # 每次请求的最大token数
TRANSLATION_BATCH_SIZE = 10  # 每批处理的段落数
TRANSLATION_TIMEOUT = 60  # 翻译请求超时时间(秒)

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 临时文件目录
TEMP_DIR = ROOT_DIR / "temp"

# 格式保存配置
PRESERVE_FORMAT = True  # 默认保存格式
