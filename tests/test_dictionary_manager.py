"""
日语到中文翻译程序 - 词典管理模块测试

此模块用于测试DictionaryManager类的功能
"""

import os
import sys
import json
import unittest
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from modules.dictionary_manager import DictionaryManager

class TestDictionaryManager(unittest.TestCase):
    """测试词典管理器类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时文件作为测试词典
        self.temp_dir = tempfile.TemporaryDirectory()
        self.perm_dict_path = os.path.join(self.temp_dir.name, "permanent_dict.json")
        self.temp_dict_path = os.path.join(self.temp_dir.name, "temp_dict.json")
        
        # 初始化永久词典
        with open(self.perm_dict_path, 'w', encoding='utf-8') as f:
            json.dump({"permanent_dict": {
                "翻訳": "翻译",
                "辞書": "词典",
                "日本語": "日语"
            }}, f, ensure_ascii=False)
        
        # 初始化临时词典
        with open(self.temp_dict_path, 'w', encoding='utf-8') as f:
            json.dump({"temp_dict": {
                "テスト": "测试",
                "プログラム": "程序"
            }}, f, ensure_ascii=False)
    
    def tearDown(self):
        """测试后清理"""
        self.temp_dir.cleanup()
    
    def test_load_dictionaries(self):
        """测试加载词典"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path,
            temp_dict_path=self.temp_dict_path
        )
        
        # 验证永久词典
        self.assertEqual(len(dict_manager.permanent_dict), 3)
        self.assertEqual(dict_manager.permanent_dict["翻訳"], "翻译")
        self.assertEqual(dict_manager.permanent_dict["辞書"], "词典")
        self.assertEqual(dict_manager.permanent_dict["日本語"], "日语")
        
        # 验证临时词典
        self.assertEqual(len(dict_manager.temp_dict), 2)
        self.assertEqual(dict_manager.temp_dict["テスト"], "测试")
        self.assertEqual(dict_manager.temp_dict["プログラム"], "程序")
        
        print("\n词典加载测试结果:")
        print(f"永久词典: {dict_manager.permanent_dict}")
        print(f"临时词典: {dict_manager.temp_dict}")
    
    def test_add_to_dictionaries(self):
        """测试添加词条到词典"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path,
            temp_dict_path=self.temp_dict_path
        )
        
        # 添加词条到永久词典
        dict_manager.add_to_permanent_dict("新しい", "新的")
        
        # 添加词条到临时词典
        dict_manager.add_to_temp_dict("古い", "旧的")
        
        # 验证添加结果
        self.assertEqual(dict_manager.permanent_dict["新しい"], "新的")
        self.assertEqual(dict_manager.temp_dict["古い"], "旧的")
        
        # 验证文件保存
        with open(self.perm_dict_path, 'r', encoding='utf-8') as f:
            perm_data = json.load(f)
            self.assertEqual(perm_data["permanent_dict"]["新しい"], "新的")
        
        with open(self.temp_dict_path, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
            self.assertEqual(temp_data["temp_dict"]["古い"], "旧的")
        
        print("\n词典添加测试结果:")
        print(f"添加后永久词典: {dict_manager.permanent_dict}")
        print(f"添加后临时词典: {dict_manager.temp_dict}")
    
    def test_remove_from_dictionaries(self):
        """测试从词典中删除词条"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path,
            temp_dict_path=self.temp_dict_path
        )
        
        # 从永久词典中删除词条
        dict_manager.remove_from_permanent_dict("翻訳")
        
        # 从临时词典中删除词条
        dict_manager.remove_from_temp_dict("テスト")
        
        # 验证删除结果
        self.assertNotIn("翻訳", dict_manager.permanent_dict)
        self.assertNotIn("テスト", dict_manager.temp_dict)
        
        # 验证文件保存
        with open(self.perm_dict_path, 'r', encoding='utf-8') as f:
            perm_data = json.load(f)
            self.assertNotIn("翻訳", perm_data["permanent_dict"])
        
        with open(self.temp_dict_path, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
            self.assertNotIn("テスト", temp_data["temp_dict"])
        
        print("\n词典删除测试结果:")
        print(f"删除后永久词典: {dict_manager.permanent_dict}")
        print(f"删除后临时词典: {dict_manager.temp_dict}")
    
    def test_merged_dictionary(self):
        """测试合并词典"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path,
            temp_dict_path=self.temp_dict_path
        )
        
        # 添加重复词条（临时词典优先）
        dict_manager.add_to_permanent_dict("重複", "重复(永久)")
        dict_manager.add_to_temp_dict("重複", "重复(临时)")
        
        # 获取合并词典
        merged_dict = dict_manager.get_merged_dict()
        
        # 验证合并结果
        self.assertEqual(len(merged_dict), 6)  # 3+2+1(重复项)
        self.assertEqual(merged_dict["重複"], "重复(临时)")  # 临时词典优先
        
        print("\n词典合并测试结果:")
        print(f"合并词典: {merged_dict}")
    
    def test_extract_terms(self):
        """测试从文本中提取术语"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path,
            temp_dict_path=self.temp_dict_path
        )
        
        # 测试文本
        test_text = "これは日本語から中国語への翻訳プログラムをテストするためのサンプル文です。"
        
        # 提取术语
        terms = dict_manager.extract_terms_from_text(test_text)
        
        # 验证提取结果
        self.assertGreater(len(terms), 0)
        self.assertIn("日本語", terms)
        self.assertIn("翻訳", terms)
        
        print("\n术语提取测试结果:")
        print(f"提取的术语: {terms}")
    
    def test_create_temp_dict(self):
        """测试创建新的临时词典"""
        # 创建词典管理器
        dict_manager = DictionaryManager(
            permanent_dict_path=self.perm_dict_path
        )
        
        # 创建新的临时词典
        new_temp_dict_path = os.path.join(self.temp_dir.name, "new_temp_dict.json")
        dict_manager.create_temp_dict(new_temp_dict_path)
        
        # 添加词条
        dict_manager.add_to_temp_dict("新規", "新建")
        
        # 验证文件创建
        self.assertTrue(os.path.exists(new_temp_dict_path))
        
        # 验证文件内容
        with open(new_temp_dict_path, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
            self.assertEqual(temp_data["temp_dict"]["新規"], "新建")
        
        print("\n临时词典创建测试结果:")
        print(f"新建临时词典路径: {new_temp_dict_path}")
        print(f"新建临时词典内容: {dict_manager.temp_dict}")

if __name__ == "__main__":
    unittest.main()
