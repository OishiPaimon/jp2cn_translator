"""
日语到中文翻译程序 - 集成测试

此模块用于测试整个程序的集成功能
"""

import os
import sys
import unittest
import tempfile
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

class TestIntegration(unittest.TestCase):
    """测试程序的整体功能"""
    
    def setUp(self):
        """测试前准备"""
        self.samples_dir = Path(__file__).parent / "samples"
        self.docx_sample = self.samples_dir / "sample_ja.docx"
        self.pdf_sample = self.samples_dir / "sample_ja.pdf"
        
        # 创建临时目录用于保存输出文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_docx = Path(self.temp_dir.name) / "output_ja.docx"
        self.output_pdf = Path(self.temp_dir.name) / "output_ja.pdf"
        
        # 创建临时词典
        self.temp_dict_path = Path(self.temp_dir.name) / "temp_dict.json"
        with open(self.temp_dict_path, 'w', encoding='utf-8') as f:
            f.write('{"temp_dict": {"日本語": "日语", "翻訳": "翻译", "プログラム": "程序", "テスト": "测试"}}')
        
        # 主程序路径
        self.main_script = Path(__file__).parent.parent / "main.py"
    
    def tearDown(self):
        """测试后清理"""
        self.temp_dir.cleanup()
    
    def test_full_translation_workflow_docx(self):
        """测试完整的Word文档翻译流程"""
        # 检查样例文件是否存在
        if not self.docx_sample.exists():
            self.skipTest(f"样例Word文档不存在: {self.docx_sample}")
        
        # 运行翻译命令（使用模拟模式，不实际调用API）
        result = subprocess.run(
            [
                sys.executable, 
                str(self.main_script),
                str(self.docx_sample),
                "-o", str(self.output_docx),
                "-t", str(self.temp_dict_path),
                "--skip-term-extraction",
                "--skip-dict-edit",
                "--force",
                "-q"  # 安静模式，减少输出
            ],
            capture_output=True,
            text=True
        )
        
        # 验证结果
        self.assertEqual(result.returncode, 0, f"翻译失败: {result.stderr}")
        self.assertTrue(self.output_docx.exists(), "输出文件不存在")
        
        # 检查文件大小
        self.assertGreater(self.output_docx.stat().st_size, 0, "输出文件为空")
        
        print("\nWord文档翻译集成测试结果:")
        print(f"返回码: {result.returncode}")
        print(f"输入文件: {self.docx_sample}")
        print(f"输出文件: {self.output_docx}")
        print(f"输出文件大小: {self.output_docx.stat().st_size} 字节")
    
    def test_full_translation_workflow_pdf(self):
        """测试完整的PDF文档翻译流程"""
        # 检查样例文件是否存在
        if not self.pdf_sample.exists():
            self.skipTest(f"样例PDF文档不存在: {self.pdf_sample}")
        
        # 运行翻译命令（使用模拟模式，不实际调用API）
        result = subprocess.run(
            [
                sys.executable, 
                str(self.main_script),
                str(self.pdf_sample),
                "-o", str(self.output_pdf),
                "-t", str(self.temp_dict_path),
                "--skip-term-extraction",
                "--skip-dict-edit",
                "--force",
                "-q"  # 安静模式，减少输出
            ],
            capture_output=True,
            text=True
        )
        
        # 验证结果
        self.assertEqual(result.returncode, 0, f"翻译失败: {result.stderr}")
        self.assertTrue(self.output_pdf.exists(), "输出文件不存在")
        
        # 检查文件大小
        self.assertGreater(self.output_pdf.stat().st_size, 0, "输出文件为空")
        
        print("\nPDF文档翻译集成测试结果:")
        print(f"返回码: {result.returncode}")
        print(f"输入文件: {self.pdf_sample}")
        print(f"输出文件: {self.output_pdf}")
        print(f"输出文件大小: {self.output_pdf.stat().st_size} 字节")
    
    def test_dictionary_application(self):
        """测试词典应用功能"""
        # 检查样例文件是否存在
        if not self.docx_sample.exists():
            self.skipTest(f"样例Word文档不存在: {self.docx_sample}")
        
        # 创建包含特定术语的临时词典
        special_dict_path = Path(self.temp_dir.name) / "special_dict.json"
        with open(special_dict_path, 'w', encoding='utf-8') as f:
            f.write('{"temp_dict": {"テスト": "特殊测试", "サンプル": "特殊样本"}}')
        
        # 运行翻译命令
        result = subprocess.run(
            [
                sys.executable, 
                str(self.main_script),
                str(self.docx_sample),
                "-o", str(self.output_docx),
                "-t", str(special_dict_path),
                "--skip-term-extraction",
                "--skip-dict-edit",
                "--force",
                "-q"  # 安静模式，减少输出
            ],
            capture_output=True,
            text=True
        )
        
        # 验证结果
        self.assertEqual(result.returncode, 0, f"翻译失败: {result.stderr}")
        
        # 检查是否使用了词典中的术语
        # 注意：由于我们使用的是模拟翻译，无法直接验证翻译内容
        # 在实际应用中，可以通过读取输出文件并检查内容来验证
        
        print("\n词典应用测试结果:")
        print(f"返回码: {result.returncode}")
        print(f"特殊词典: {special_dict_path}")
        print(f"输出文件: {self.output_docx}")
    
    def test_format_preservation(self):
        """测试格式保存功能"""
        # 检查样例文件是否存在
        if not self.docx_sample.exists():
            self.skipTest(f"样例Word文档不存在: {self.docx_sample}")
        
        # 创建两个输出文件，一个保持格式，一个不保持
        format_on_output = Path(self.temp_dir.name) / "format_on.docx"
        format_off_output = Path(self.temp_dir.name) / "format_off.docx"
        
        # 运行保持格式的翻译命令
        result_on = subprocess.run(
            [
                sys.executable, 
                str(self.main_script),
                str(self.docx_sample),
                "-o", str(format_on_output),
                "--preserve-format",
                "--skip-term-extraction",
                "--skip-dict-edit",
                "--force",
                "-q"
            ],
            capture_output=True,
            text=True
        )
        
        # 运行不保持格式的翻译命令
        result_off = subprocess.run(
            [
                sys.executable, 
                str(self.main_script),
                str(self.docx_sample),
                "-o", str(format_off_output),
                "--no-preserve-format",
                "--skip-term-extraction",
                "--skip-dict-edit",
                "--force",
                "-q"
            ],
            capture_output=True,
            text=True
        )
        
        # 验证结果
        self.assertEqual(result_on.returncode, 0, f"保持格式翻译失败: {result_on.stderr}")
        self.assertEqual(result_off.returncode, 0, f"不保持格式翻译失败: {result_off.stderr}")
        
        # 检查两个文件是否都存在
        self.assertTrue(format_on_output.exists(), "保持格式输出文件不存在")
        self.assertTrue(format_off_output.exists(), "不保持格式输出文件不存在")
        
        # 检查文件大小是否不同
        # 通常保持格式的文件会更大，因为包含了更多的格式信息
        self.assertNotEqual(
            format_on_output.stat().st_size,
            format_off_output.stat().st_size,
            "保持格式和不保持格式的输出文件大小相同，可能格式保存功能未生效"
        )
        
        print("\n格式保存测试结果:")
        print(f"保持格式输出文件: {format_on_output}")
        print(f"保持格式文件大小: {format_on_output.stat().st_size} 字节")
        print(f"不保持格式输出文件: {format_off_output}")
        print(f"不保持格式文件大小: {format_off_output.stat().st_size} 字节")

if __name__ == "__main__":
    unittest.main()
