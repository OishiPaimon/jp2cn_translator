"""
日语到中文翻译程序 - 文档读取模块测试

此模块用于测试DocumentReader类的功能
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from modules.document_reader import DocumentReader

class TestDocumentReader(unittest.TestCase):
    """测试DocumentReader类"""
    
    def setUp(self):
        """测试前准备"""
        self.samples_dir = Path(__file__).parent / "samples"
        self.docx_sample = self.samples_dir / "sample_ja.docx"
        self.pdf_sample = self.samples_dir / "sample_ja.pdf"
    
    def test_docx_reader(self):
        """测试Word文档读取功能"""
        # 检查样例文件是否存在
        if not self.docx_sample.exists():
            self.skipTest(f"样例Word文档不存在: {self.docx_sample}")
        
        # 创建DocumentReader实例
        reader = DocumentReader(str(self.docx_sample))
        
        # 读取文档
        paragraphs, format_info = reader.read()
        
        # 验证结果
        self.assertIsNotNone(paragraphs)
        self.assertIsNotNone(format_info)
        self.assertGreater(len(paragraphs), 0)
        self.assertIn('styles', format_info)
        
        # 打印结果
        print(f"\nWord文档读取测试结果:")
        print(f"段落数量: {len(paragraphs)}")
        print(f"格式信息: {list(format_info.keys())}")
        if paragraphs:
            print(f"第一段内容: {paragraphs[0][:100]}...")
    
    def test_pdf_reader(self):
        """测试PDF文档读取功能"""
        # 检查样例文件是否存在
        if not self.pdf_sample.exists():
            self.skipTest(f"样例PDF文档不存在: {self.pdf_sample}")
        
        # 创建DocumentReader实例
        reader = DocumentReader(str(self.pdf_sample))
        
        # 读取文档
        paragraphs, format_info = reader.read()
        
        # 验证结果
        self.assertIsNotNone(paragraphs)
        self.assertIsNotNone(format_info)
        self.assertGreater(len(paragraphs), 0)
        self.assertIn('pages', format_info)
        
        # 打印结果
        print(f"\nPDF文档读取测试结果:")
        print(f"段落数量: {len(paragraphs)}")
        print(f"格式信息: {list(format_info.keys())}")
        if paragraphs:
            print(f"第一段内容: {paragraphs[0][:100]}...")

if __name__ == "__main__":
    unittest.main()
