"""
词典管理模块 - 负责管理永久词典和临时词典，以及专有名词识别
"""
import os
import json
import re
import jieba
from typing import Dict, List, Set, Tuple


class DictionaryManager:
    def __init__(self, permanent_dict_path: str, temp_dict_path: str):
        """
        初始化词典管理器
        
        Args:
            permanent_dict_path: 永久词典文件路径
            temp_dict_path: 临时词典文件路径
        """
        self.permanent_dict_path = permanent_dict_path
        self.temp_dict_path = temp_dict_path
        self.permanent_dict = self._load_dict(permanent_dict_path)
        self.temp_dict = self._load_dict(temp_dict_path)
        
        # 日语停用词集合
        self.stopwords = self._load_stopwords()
        
        # 加载jieba分词器
        jieba.initialize()

    def _load_dict(self, dict_path: str) -> Dict[str, str]:
        """
        加载词典文件
        
        Args:
            dict_path: 词典文件路径
            
        Returns:
            词典字典，键为原文，值为翻译
        """
        if not os.path.exists(dict_path):
            # 如果文件不存在，创建空词典文件
            with open(dict_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return {}
            
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # 如果文件为空
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回空词典
            return {}

    def _load_stopwords(self) -> Set[str]:
        """
        加载日语停用词
        
        Returns:
            停用词集合
        """
        # 常见日语助词、助动词和代词等
        stopwords = {
            'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'も', 'な', 'ない', 'から', 'まで',
            'より', 'など', 'これ', 'それ', 'あれ', 'この', 'その', 'あの', 'ここ', 'そこ', 'あそこ',
            'わたし', 'あなた', 'かれ', 'かのじょ', 'です', 'ます', 'でした', 'ました', 'である',
            'だ', 'だった', 'です', 'ます', 'ください', 'ございます', 'ありがとう', 'すみません',
            'おはよう', 'こんにちは', 'こんばんは', 'さようなら', 'いいえ', 'はい', 'ええ',
            'そう', 'そうです', 'そうですか', 'どう', 'どうぞ', 'どうも', 'もう', 'まだ', 'また',
            'いつ', 'どこ', 'だれ', 'なに', 'なぜ', 'どんな', 'どの', 'いくつ', 'いくら',
            'ひとつ', 'ふたつ', 'みっつ', 'よっつ', 'いつつ', 'むっつ', 'ななつ', 'やっつ', 'ここのつ', 'とお'
        }
        return stopwords

    def save_permanent_dict(self) -> None:
        """保存永久词典到文件"""
        with open(self.permanent_dict_path, 'w', encoding='utf-8') as f:
            json.dump(self.permanent_dict, f, ensure_ascii=False, indent=2)

    def save_temp_dict(self) -> None:
        """保存临时词典到文件"""
        with open(self.temp_dict_path, 'w', encoding='utf-8') as f:
            json.dump(self.temp_dict, f, ensure_ascii=False, indent=2)

    def add_to_permanent_dict(self, original: str, translation: str) -> None:
        """
        添加词条到永久词典
        
        Args:
            original: 原文
            translation: 翻译
        """
        self.permanent_dict[original] = translation
        self.save_permanent_dict()

    def add_to_temp_dict(self, original: str, translation: str) -> None:
        """
        添加词条到临时词典
        
        Args:
            original: 原文
            translation: 翻译
        """
        self.temp_dict[original] = translation
        self.save_temp_dict()

    def remove_from_permanent_dict(self, original: str) -> None:
        """
        从永久词典中删除词条
        
        Args:
            original: 原文
        """
        if original in self.permanent_dict:
            del self.permanent_dict[original]
            self.save_permanent_dict()

    def remove_from_temp_dict(self, original: str) -> None:
        """
        从临时词典中删除词条
        
        Args:
            original: 原文
        """
        if original in self.temp_dict:
            del self.temp_dict[original]
            self.save_temp_dict()

    def clear_temp_dict(self) -> None:
        """清空临时词典"""
        self.temp_dict = {}
        self.save_temp_dict()

    def extract_proper_nouns(self, text: str) -> List[str]:
        """
        从文本中提取可能的专有名词
        
        Args:
            text: 输入文本
            
        Returns:
            可能的专有名词列表
        """
        # 使用正则表达式匹配可能的日语专有名词特征
        # 1. 片假名词语（通常用于外来语和专有名词）
        katakana_pattern = r'[ァ-ヶー]{2,}'
        katakana_words = re.findall(katakana_pattern, text)
        
        # 2. 带有特定后缀的词语（如さん、君、様等）
        suffix_pattern = r'[一-龯ぁ-んァ-ヶー]{2,}(さん|くん|君|様|先生|氏)'
        suffix_words = re.findall(suffix_pattern, text)
        
        # 3. 使用jieba分词，提取可能的专有名词
        words = jieba.cut(text)
        
        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) >= 2 and word not in self.stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 提取高频词（出现次数大于1的词）
        frequent_words = [word for word, freq in word_freq.items() if freq > 1]
        
        # 合并结果并去重
        proper_nouns = list(set(katakana_words + [w.replace(s, '') for w, s in zip(suffix_words, ['さん', 'くん', '君', '様', '先生', '氏'])]))
        proper_nouns.extend([w for w in frequent_words if w not in proper_nouns])
        
        # 过滤掉已经在永久词典中的词
        proper_nouns = [w for w in proper_nouns if w not in self.permanent_dict]
        
        return proper_nouns

    def scan_document_for_terms(self, content: str) -> List[Tuple[str, str]]:
        """
        扫描文档，提取可能的专有名词并生成临时词典
        
        Args:
            content: 文档内容
            
        Returns:
            专有名词列表，每项为(原文, 建议翻译)元组
        """
        proper_nouns = self.extract_proper_nouns(content)
        
        # 为每个专有名词生成一个空的建议翻译
        terms = [(noun, "") for noun in proper_nouns]
        
        return terms

    def apply_dictionaries(self, text: str) -> Tuple[str, List[Tuple[int, int, str]]]:
        """
        应用词典替换文本中的词语，并标记替换的部分
        
        Args:
            text: 输入文本
            
        Returns:
            替换后的文本和替换位置列表，每项为(开始位置, 结束位置, 替换后的文本)
        """
        # 合并永久词典和临时词典
        combined_dict = {**self.permanent_dict, **self.temp_dict}
        
        # 如果词典为空，直接返回原文
        if not combined_dict:
            return text, []
        
        # 按照词语长度降序排序，优先替换长词
        sorted_terms = sorted(combined_dict.keys(), key=len, reverse=True)
        
        # 记录替换位置
        replacements = []
        
        # 替换文本
        result = text
        offset = 0  # 用于调整位置偏移
        
        for term in sorted_terms:
            if term in result:
                # 查找所有匹配位置
                start = 0
                while True:
                    pos = result.find(term, start)
                    if pos == -1:
                        break
                        
                    # 替换文本
                    replacement = combined_dict[term]
                    marked_replacement = f"***{replacement}***"
                    
                    # 记录替换位置
                    replacements.append((pos + offset, pos + len(term) + offset, replacement))
                    
                    # 更新文本
                    result = result[:pos] + marked_replacement + result[pos + len(term):]
                    
                    # 更新下一次查找的起始位置和偏移量
                    start = pos + len(marked_replacement)
                    offset += len(marked_replacement) - len(term)
        
        return result, replacements

    def remove_markers(self, text: str) -> str:
        """
        移除文本中的标记符号
        
        Args:
            text: 带标记的文本
            
        Returns:
            移除标记后的文本
        """
        # 移除 *** 标记
        return re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)


# 测试代码
if __name__ == "__main__":
    # 创建临时词典文件
    with open("test_permanent_dict.json", "w", encoding="utf-8") as f:
        json.dump({"田中": "Tanaka", "山田": "Yamada"}, f, ensure_ascii=False, indent=2)
    
    with open("test_temp_dict.json", "w", encoding="utf-8") as f:
        json.dump({"東京": "Tokyo", "大阪": "Osaka"}, f, ensure_ascii=False, indent=2)
    
    # 初始化词典管理器
    dict_manager = DictionaryManager("test_permanent_dict.json", "test_temp_dict.json")
    
    # 测试专有名词提取
    test_text = """
    田中さんは東京に住んでいます。
    山田先生は大阪から来ました。
    鈴木くんはアメリカへ行きました。
    私はラーメンが好きです。
    """
    
    proper_nouns = dict_manager.extract_proper_nouns(test_text)
    print("提取的专有名词:")
    for noun in proper_nouns:
        print(f"- {noun}")
    
    # 测试词典应用
    replaced_text, replacements = dict_manager.apply_dictionaries(test_text)
    print("\n替换后的文本:")
    print(replaced_text)
    
    print("\n替换位置:")
    for start, end, replacement in replacements:
        print(f"位置 {start}-{end}: {replacement}")
    
    # 测试移除标记
    clean_text = dict_manager.remove_markers(replaced_text)
    print("\n移除标记后的文本:")
    print(clean_text)
