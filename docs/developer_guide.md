# 日语到中文翻译程序 - 开发文档

## 项目架构

本项目采用模块化设计，主要包含以下几个核心模块：

1. **文档读取模块**：负责读取Word和PDF文档，提取文本内容和格式信息
2. **翻译模块**：负责调用翻译API或本地模型进行翻译
3. **词典管理模块**：负责管理永久词典和临时词典
4. **格式保存模块**：负责保持原文档格式
5. **用户界面模块**：提供命令行界面和参数处理

### 目录结构

```
jp2cn_translator/
├── config.py                 # 配置文件
├── main.py                   # 主程序入口
├── dictionaries/             # 词典目录
│   ├── permanent_dict.json   # 永久词典
│   └── temp_dict_template.json # 临时词典模板
├── modules/                  # 核心模块
│   ├── __init__.py
│   ├── document_reader.py    # 文档读取模块
│   ├── translator.py         # 翻译模块
│   ├── dictionary_manager.py # 词典管理模块
│   └── format_preserver.py   # 格式保存模块
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── text_processor.py     # 文本处理工具
│   └── progress_bar.py       # 进度显示工具
├── tests/                    # 测试文件
│   ├── __init__.py
│   ├── samples/              # 测试样例
│   ├── test_document_reader.py
│   ├── test_translator.py
│   ├── test_dictionary_manager.py
│   ├── test_format_preserver.py
│   ├── test_user_interface.py
│   └── test_integration.py
└── docs/                     # 文档
    ├── user_manual.md        # 用户手册
    └── developer_guide.md    # 开发指南
```

## 核心模块详解

### 文档读取模块 (document_reader.py)

该模块负责读取Word和PDF文档，提取文本内容和格式信息。

#### 主要类和方法

- `DocumentReader`：文档读取器类
  - `__init__(self, file_path)`：初始化文档读取器
  - `read(self)`：读取文档，返回段落列表和格式信息
  - `_read_docx(self)`：读取Word文档
  - `_read_pdf(self)`：读取PDF文档

#### 技术细节

- 使用`python-docx`库读取Word文档
- 使用`PyPDF2`和`pdfplumber`库读取PDF文档
- 对于Word文档，保存段落样式、字体、颜色等格式信息
- 对于PDF文档，保存文本位置、字体大小等信息

### 翻译模块 (translator.py)

该模块负责调用翻译API或本地模型进行翻译。

#### 主要类和方法

- `TranslatorBase`：翻译器基类
  - `translate(self, text, dictionary)`：翻译文本
  - `batch_translate(self, texts, dictionary)`：批量翻译文本
- `OpenAITranslator`：OpenAI翻译器
  - `translate(self, text, dictionary)`：使用OpenAI API翻译文本
  - `_build_prompt(self, text, dictionary)`：构建提示词
- `DeepSeekTranslator`：DeepSeek翻译器
  - `translate(self, text, dictionary)`：使用DeepSeek API翻译文本
  - `_build_prompt(self, text, dictionary)`：构建提示词
- `OllamaTranslator`：Ollama翻译器
  - `translate(self, text, dictionary)`：使用Ollama模型翻译文本
  - `_build_prompt(self, text, dictionary)`：构建提示词
- `TranslatorFactory`：翻译器工厂
  - `create_translator(translator_type, **kwargs)`：创建翻译器实例

#### 技术细节

- 使用工厂模式创建不同类型的翻译器
- 使用策略模式实现不同的翻译策略
- 支持OpenAI API、DeepSeek API和Ollama本地模型
- 提供模拟模式用于测试
- 使用提示工程技术确保逐字逐句翻译
- DeepSeek API使用与OpenAI兼容的接口，但需要指定不同的API基础URL

### 词典管理模块 (dictionary_manager.py)

该模块负责管理永久词典和临时词典。

#### 主要类和方法

- `DictionaryManager`：词典管理器类
  - `__init__(self, permanent_dict_path, temp_dict_path)`：初始化词典管理器
  - `load_permanent_dict(self)`：加载永久词典
  - `load_temp_dict(self)`：加载临时词典
  - `save_permanent_dict(self)`：保存永久词典
  - `save_temp_dict(self)`：保存临时词典
  - `add_to_permanent_dict(self, term, translation)`：添加术语到永久词典
  - `add_to_temp_dict(self, term, translation)`：添加术语到临时词典
  - `remove_from_permanent_dict(self, term)`：从永久词典中删除术语
  - `remove_from_temp_dict(self, term)`：从临时词典中删除术语
  - `get_merged_dict(self)`：获取合并的词典
  - `extract_terms_from_text(self, text)`：从文本中提取术语
  - `create_temp_dict(self, path)`：创建新的临时词典

#### 技术细节

- 使用JSON格式存储词典
- 支持术语提取和建议翻译
- 临时词典优先于永久词典
- 使用正则表达式提取潜在术语

### 格式保存模块 (format_preserver.py)

该模块负责保持原文档格式。

#### 主要类和方法

- `FormatPreserver`：格式保存器类
  - `__init__(self, preserve_format)`：初始化格式保存器
  - `create_document(self, original_paragraphs, translated_paragraphs, format_info, output_path, file_type)`：创建格式一致的文档
  - `_create_docx_document(self, original_paragraphs, translated_paragraphs, format_info, output_path)`：创建Word文档
  - `_create_pdf_document(self, original_paragraphs, translated_paragraphs, format_info, output_path)`：创建PDF文档
  - `_create_plain_document(self, translated_paragraphs, output_path, file_type)`：创建纯文本文档

#### 技术细节

- 使用`python-docx`库创建Word文档
- 使用`reportlab`库创建PDF文档
- 支持保持段落样式、字体、颜色等格式
- 提供格式保存开关选项

## 工具函数

### 文本处理工具 (text_processor.py)

- `split_text_into_chunks(text, max_length)`：将文本分割成适合翻译的块
- `detect_language(text)`：检测文本语言
- `find_potential_terms(text)`：查找潜在术语

### 进度显示工具 (progress_bar.py)

- `ProgressBar`：进度条类
- `ConsoleLogger`：控制台日志类
- `TranslationStats`：翻译统计信息类

## 主程序入口 (main.py)

主程序入口实现了命令行界面和参数处理，并协调各个模块的工作。

### 主要类和方法

- `JP2CNTranslator`：主程序类
  - `__init__(self, args)`：初始化翻译程序
  - `run(self)`：运行翻译程序
- `parse_args(args)`：解析命令行参数
- `main()`：主函数

### 技术细节

- 使用`argparse`库处理命令行参数
- 提供多种配置选项
- 实现进度显示和日志功能
- 处理错误和异常情况

## 配置文件 (config.py)

配置文件定义了程序的默认配置，包括：

- 默认词典路径
- API密钥和模型设置
- 格式保存选项
- 批处理大小等

## 测试

项目包含多个测试文件，用于测试各个模块的功能：

- `test_document_reader.py`：测试文档读取模块
- `test_translator.py`：测试翻译模块
- `test_dictionary_manager.py`：测试词典管理模块
- `test_format_preserver.py`：测试格式保存模块
- `test_user_interface.py`：测试用户界面
- `test_integration.py`：集成测试

## 扩展指南

### 添加新的翻译器

1. 在`translator.py`中创建新的翻译器类，继承`TranslatorBase`
2. 实现`translate`方法
3. 在`TranslatorFactory`中添加对新翻译器的支持

### 支持新的文档格式

1. 在`document_reader.py`中添加新的读取方法
2. 在`format_preserver.py`中添加新的格式保存方法
3. 更新文件类型检测逻辑

### 改进词典功能

1. 在`dictionary_manager.py`中添加新的词典功能
2. 更新术语提取和建议翻译的逻辑

## 性能优化

- 使用批处理减少API调用次数
- 缓存翻译结果避免重复翻译
- 使用多线程处理大型文档

## 已知问题和限制

- 不支持处理图片和表格
- PDF格式保存可能不完美
- 对于非常长的文档，可能需要分批处理
- 翻译质量依赖于所使用的模型

## 未来计划

- 添加图形用户界面
- 支持更多文档格式
- 改进术语提取算法
- 实现翻译记忆功能
