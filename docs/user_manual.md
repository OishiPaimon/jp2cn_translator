# 日语到中文翻译程序 - 用户手册

## 简介

日语到中文翻译程序是一个专门设计用于将日语文档翻译成中文的工具。它支持Word和PDF格式的文档，能够保持原文档的格式，并提供词典功能以确保术语翻译的一致性。

本程序的主要特点：

- 支持Word和PDF文档的读取和翻译
- 逐字逐句翻译，确保内容完整性
- 支持永久词典和临时词典，保证术语翻译一致
- 可以保持原文档格式
- 支持OpenAI API和Ollama本地模型两种翻译引擎
- 提供命令行界面，支持多种配置选项

## 安装

### 系统要求

- Python 3.8或更高版本
- 操作系统：Windows、macOS或Linux

### 安装步骤

1. 克隆或下载程序代码
2. 安装依赖库：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

最简单的用法是直接指定要翻译的文件：

```bash
python main.py input_file.docx
```

程序会自动生成一个名为`input_file_translated.docx`的翻译后文件。

### 常用选项

- `-o, --output-file`：指定输出文件路径
- `-p, --permanent-dict`：指定永久词典路径
- `-t, --temp-dict`：指定临时词典路径
- `--translator-type`：选择翻译器类型（openai或ollama）
- `--api-key`：设置OpenAI API密钥
- `--preserve-format`：保持原文档格式（默认开启）
- `--no-preserve-format`：不保持原文档格式
- `--force`：强制执行，不询问确认
- `-q, --quiet`：安静模式，减少输出
- `--version`：显示版本信息

完整的命令行选项可以通过`--help`参数查看：

```bash
python main.py --help
```

### 示例

1. 翻译Word文档并指定输出文件：

```bash
python main.py document.docx -o translated.docx
```

2. 翻译PDF文档并使用自定义词典：

```bash
python main.py document.pdf -o translated.pdf -p my_dict.json
```

3. 使用Ollama模型进行翻译：

```bash
python main.py document.docx --translator-type ollama --ollama-host http://localhost:11434
```

4. 不保持原文档格式：

```bash
python main.py document.docx --no-preserve-format
```

## 词典功能

### 词典格式

词典文件使用JSON格式，结构如下：

```json
{
    "permanent_dict": {
        "日本語": "日语",
        "翻訳": "翻译",
        "辞書": "词典"
    }
}
```

或者临时词典：

```json
{
    "temp_dict": {
        "テスト": "测试",
        "プログラム": "程序"
    }
}
```

### 永久词典

永久词典用于存储常用术语的翻译，适用于所有文档。默认路径为`dictionaries/permanent_dict.json`。

### 临时词典

临时词典用于特定文档的术语翻译。程序会自动从文档中提取潜在术语并创建临时词典，用户可以在翻译前编辑这个词典。

### 术语提取

程序会自动从文档中提取潜在的术语，并提示用户编辑临时词典。可以使用`--skip-term-extraction`选项跳过这一步。

## 翻译引擎

### OpenAI API

使用OpenAI的API进行翻译。需要设置API密钥，可以通过`--api-key`参数或在配置文件中设置。

### DeepSeek API

支持使用DeepSeek的API进行翻译。DeepSeek提供了类似OpenAI的接口，但有自己的模型和定价策略。

使用DeepSeek API的方法：
```bash
python main.py document.docx --translator-type deepseek --api-key "your-deepseek-api-key" --model "deepseek-r1" --api-base "https://api.deepseek.com/v1"
```

默认配置中已包含DeepSeek API密钥和模型设置，您也可以在配置文件中修改这些设置。

### Ollama

也支持使用Ollama本地模型进行翻译，适合对隐私有要求或无法访问商业API的情况。需要先安装并运行Ollama服务。

## 格式保存

程序默认会尝试保持原文档的格式，包括字体、颜色、段落样式等。对于Word文档，会保持原始格式；对于PDF文档，会尽量模拟原始格式。

注意：程序不会处理图片，遇到图片时会留出空白。

## 常见问题

### 翻译质量问题

- 如果发现翻译质量不佳，可以尝试使用不同的翻译模型或调整提示词
- 对于专业术语，建议使用词典功能确保翻译准确性

### 格式问题

- 如果格式保存不理想，可以尝试使用`--no-preserve-format`选项，然后手动调整格式
- 对于复杂的PDF文档，格式保存可能不完美

### 性能问题

- 对于大型文档，可以使用`--batch-size`参数调整批处理大小
- 如果使用Ollama，确保您的计算机有足够的资源运行模型

## 配置文件

程序的默认配置存储在`config.py`文件中，包括：

- 默认词典路径
- API密钥和模型设置
- 格式保存选项
- 批处理大小等

您可以直接编辑这个文件来更改默认配置。

## 许可证

本程序采用MIT许可证。详情请参阅LICENSE文件。
