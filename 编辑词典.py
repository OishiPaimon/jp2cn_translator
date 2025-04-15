"""
词典编辑器 - 独立的词典编辑工具，支持Excel格式词典的创建、编辑和管理
"""
import sys
import os
import re
import jieba
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QComboBox, QMenu, QInputDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

# 导入文件处理模块
sys.path.append(str(Path(__file__).parent))
from core.file_processor import FileProcessor


def is_kana_or_kanji(text: str) -> bool:
    """
    判断字符串是否全为假名或汉字（可混合）。
    """
    return bool(re.fullmatch(r"[ぁ-んァ-ン一-龯々ー]+", text))

class AddCategoryDialog(QDialog):
    """添加分类对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加分类")
        self.setMinimumWidth(300)
        
        layout = QFormLayout()
        
        self.category_name = QLineEdit()
        layout.addRow("分类名称:", self.category_name)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class AddEntryDialog(QDialog):
    """添加词条对话框"""
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加词条")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.original = QLineEdit()
        self.translation = QLineEdit()
        self.category = QComboBox()
        
        # 添加分类选项
        self.category.addItems(categories)
        
        layout.addRow("原文:", self.original)
        layout.addRow("翻译:", self.translation)
        layout.addRow("分类:", self.category)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class ScanTermsDialog(QDialog):
    """扫描专有名词对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫描文档")
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        # 文件选择
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self.browse_file)
        
        file_layout.addWidget(QLabel("文档文件:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.btn_browse)
        
        layout.addLayout(file_layout)
        
        # 扫描按钮
        self.btn_scan = QPushButton("开始扫描")
        self.btn_scan.clicked.connect(self.scan_document)
        layout.addWidget(self.btn_scan)
        
        # 结果表格
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["原文", "出现次数"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(QLabel("扫描结果:"))
        layout.addWidget(self.table)
        
        # 对话框按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # 初始化变量
        self.file_processor = FileProcessor()
        self.current_content = None
        self.terms = []
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> Set[str]:
        """加载日语停用词"""
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
    
    def browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文档文件", "./", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path.setText(file_path)
    
    def extract_proper_nouns(self, text: str) -> List[Tuple[str, int]]:
        """
        从文本中提取可能的专有名词
        
        Args:
            text: 输入文本
            
        Returns:
            可能的专有名词列表，每项为(词语, 出现次数)元组
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
        frequent_words = [(word, freq) for word, freq in word_freq.items() if freq > 1]
        
        # 合并结果并去重
        proper_nouns = []
        
        # 添加片假名词语
        for word in katakana_words:
            count = text.count(word)
            if count > 0:
                proper_nouns.append((word, count))
        
        # 添加带有特定后缀的词语
        for match in suffix_words:
            word = match.replace('さん', '').replace('くん', '').replace('君', '').replace('様', '').replace('先生', '').replace('氏', '')
            count = text.count(word)
            if count > 0:
                proper_nouns.append((word, count))
        
        # 添加高频词
        for word, freq in frequent_words:
            # 检查是否已经添加
            if not any(word == w for w, _ in proper_nouns):
                proper_nouns.append((word, freq))
        
        # 按出现次数降序排序
        proper_nouns.sort(key=lambda x: x[1], reverse=True)
        
        return proper_nouns



    def scan_document(self):
        """扫描文档"""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(self, "无法扫描", "请先选择文档文件")
            return
        
        try:
            # 读取文件
            self.current_content = self.file_processor.read_file(file_path)
            
            # 提取专有名词
            raw_terms = self.extract_proper_nouns(self.current_content)

            # 过滤 + 去重
            seen = set()
            self.terms = []
            for term, count in raw_terms:
                term = term.strip()
                if term in seen:
                    continue
                if is_kana_or_kanji(term):
                    self.terms.append((term, count))
                    seen.add(term)

            # 更新表格
            self.table.setRowCount(0)
            for i, (term, count) in enumerate(self.terms):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(term))
                self.table.setItem(i, 1, QTableWidgetItem(str(count)))
            
            QMessageBox.information(self, "扫描完成", f"成功扫描文档，共提取 {len(self.terms)} 个可能的专有名词")
            
        except Exception as e:
            QMessageBox.critical(self, "扫描失败", f"扫描文档时发生错误: {str(e)}")
    
    def get_selected_terms(self) -> List[str]:
        """获取选中的词条"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return []
        
        terms = []
        for row in selected_rows:
            term = self.table.item(row.row(), 0).text()
            terms.append(term)
        
        return terms


class DictionaryEditor(QMainWindow):
    """词典编辑器主窗口"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("日语词典编辑器")
        self.setMinimumSize(800, 600)
        
        # 初始化变量
        self.current_file = None
        self.is_modified = False
        self.df = pd.DataFrame(columns=["原文", "翻译", "分类"])
        
        # 初始化界面
        self.init_ui()
        
        # 更新界面状态
        self.update_ui_state()
    
    def init_ui(self):
        """初始化界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 文件操作按钮
        self.btn_new = QPushButton("新建")
        self.btn_open = QPushButton("打开")
        self.btn_save = QPushButton("保存")
        self.btn_save_as = QPushButton("另存为")
        
        self.btn_new.clicked.connect(self.new_dictionary)
        self.btn_open.clicked.connect(self.open_dictionary)
        self.btn_save.clicked.connect(self.save_dictionary)
        self.btn_save_as.clicked.connect(self.save_dictionary_as)
        
        toolbar_layout.addWidget(self.btn_new)
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addWidget(self.btn_save)
        toolbar_layout.addWidget(self.btn_save_as)
        
        # 词条操作按钮
        self.btn_add = QPushButton("添加词条")
        self.btn_edit = QPushButton("编辑词条")
        self.btn_delete = QPushButton("删除词条")
        self.btn_scan = QPushButton("扫描文档")
        self.btn_add_category = QPushButton("添加分类")
        
        self.btn_add.clicked.connect(self.add_entry)
        self.btn_edit.clicked.connect(self.edit_entry)
        self.btn_delete.clicked.connect(self.delete_entry)
        self.btn_scan.clicked.connect(self.scan_document)
        self.btn_add_category.clicked.connect(self.add_category)
        
        toolbar_layout.addWidget(self.btn_add)
        toolbar_layout.addWidget(self.btn_edit)
        toolbar_layout.addWidget(self.btn_delete)
        toolbar_layout.addWidget(self.btn_scan)
        toolbar_layout.addWidget(self.btn_add_category)
        
        main_layout.addLayout(toolbar_layout)
        
        # 状态标签
        self.status_label = QLabel("未打开任何词典")
        main_layout.addWidget(self.status_label)
        
        # 表格
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["原文", "翻译", "分类"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # 禁止直接编辑
        self.table.doubleClicked.connect(self.edit_entry)  # 双击编辑
        
        main_layout.addWidget(self.table)
    
    def update_ui_state(self):
        """更新界面状态"""
        has_file = self.current_file is not None
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        
        # self.btn_save.setEnabled(has_file and self.is_modified)
        # self.btn_save_as.setEnabled(has_file)
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        
        # 更新状态标签
        if has_file:
            status = f"当前词典: {os.path.basename(self.current_file)}"
            if self.is_modified:
                status += " (已修改)"
            self.status_label.setText(status)
        else:
            self.status_label.setText("未打开任何词典")
    
    def update_table(self):
        """更新表格"""
        self.table.setRowCount(0)
        
        for i, row in self.df.iterrows():
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(row["原文"]))
            self.table.setItem(i, 1, QTableWidgetItem(row["翻译"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["分类"]))
    
    def new_dictionary(self):
        """新建词典"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "确认新建", "当前词典已修改，是否保存更改？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if not self.save_dictionary():
                    return  # 保存失败，取消新建
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # 取消新建
        
        # 创建新词典
        self.current_file = None
        self.is_modified = False
        self.df = pd.DataFrame(columns=["原文", "翻译", "分类"])
        
        # 更新界面
        self.update_table()
        self.update_ui_state()
    
    def open_dictionary(self):
        """打开词典"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "确认打开", "当前词典已修改，是否保存更改？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if not self.save_dictionary():
                    return  # 保存失败，取消打开
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # 取消打开
        
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开词典", "./", "Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 读取Excel文件
                self.df = pd.read_excel(file_path)
                
                # 检查必要的列
                required_columns = ["原文", "翻译", "分类"]
                for col in required_columns:
                    if col not in self.df.columns:
                        self.df[col] = ""  # 添加缺失的列
                
                # 更新界面
                self.current_file = file_path
                self.is_modified = False
                self.update_table()
                self.update_ui_state()
                
                QMessageBox.information(self, "打开成功", f"成功打开词典，共 {len(self.df)} 个词条")
                
            except Exception as e:
                QMessageBox.critical(self, "打开失败", f"打开词典时发生错误: {str(e)}")
    
    def save_dictionary(self):
        """保存词典"""
        if not self.current_file:
            return self.save_dictionary_as()
        
        try:
            # 保存为Excel文件
            self.df.to_excel(self.current_file, index=False)
            self.is_modified = False
            self.update_ui_state()
            
            QMessageBox.information(self, "保存成功", f"词典已保存到 {self.current_file}")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存词典时发生错误: {str(e)}")
            return False
    
    def save_dictionary_as(self):
        """另存为词典"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存词典", "./", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            # 确保有.xlsx扩展名
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"
            
            self.current_file = file_path
            return self.save_dictionary()
        
        return False
    
    def add_entry(self):
        """添加词条"""
        # 获取所有分类
        categories = self.df["分类"].unique().tolist()
        if not categories:
            categories = ["默认"]
        
        dialog = AddEntryDialog(categories, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            original = dialog.original.text()
            translation = dialog.translation.text()
            category = dialog.category.currentText()
            
            if original and translation:
                # 检查是否已存在
                if original in self.df["原文"].values:
                    reply = QMessageBox.question(
                        self, "词条已存在", f"词条 '{original}' 已存在，是否覆盖？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # 更新已有词条
                        idx = self.df[self.df["原文"] == original].index[0]
                        self.df.at[idx, "翻译"] = translation
                        self.df.at[idx, "分类"] = category
                    else:
                        return
                else:
                    # 添加新词条
                    new_row = pd.DataFrame({
                        "原文": [original],
                        "翻译": [translation],
                        "分类": [category]
                    })
                    self.df = pd.concat([self.df, new_row], ignore_index=True)
                
                # 更新界面
                self.is_modified = True
                self.update_table()
                self.update_ui_state()
    
    def edit_entry(self):
        """编辑词条"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        original = self.table.item(row, 0).text()
        translation = self.table.item(row, 1).text()
        category = self.table.item(row, 2).text()
        
        # 获取所有分类
        categories = self.df["分类"].unique().tolist()
        if not categories:
            categories = ["默认"]
        
        dialog = AddEntryDialog(categories, self)
        dialog.original.setText(original)
        dialog.translation.setText(translation)
        dialog.category.setCurrentText(category)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_original = dialog.original.text()
            new_translation = dialog.translation.text()
            new_category = dialog.category.currentText()
            
            if new_original and new_translation:
                # 更新词条
                idx = self.df[self.df["原文"] == original].index[0]
                self.df.at[idx, "原文"] = new_original
                self.df.at[idx, "翻译"] = new_translation
                self.df.at[idx, "分类"] = new_category
                
                # 更新界面
                self.is_modified = True
                self.update_table()
                self.update_ui_state()
    
    def delete_entry(self):
        """删除词条"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 个词条吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 获取要删除的索引
            rows_to_delete = []
            for row in selected_rows:
                original = self.table.item(row.row(), 0).text()
                idx = self.df[self.df["原文"] == original].index
                rows_to_delete.extend(idx.tolist())
            
            # 删除词条
            self.df = self.df.drop(rows_to_delete).reset_index(drop=True)
            
            # 更新界面
            self.is_modified = True
            self.update_table()
            self.update_ui_state()
    
    def scan_document(self):
        """扫描文档"""
        dialog = ScanTermsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_terms = dialog.get_selected_terms()
            
            if selected_terms:
                # 获取所有分类
                categories = self.df["分类"].unique().tolist()
                if not categories:
                    categories = ["默认"]
                
                # 添加选中的词条
                existing_set = set(self.df["原文"].astype(str).str.strip())

                for term in selected_terms:
                    clean_term = term.strip()
                    if clean_term in existing_set:
                        continue

                    new_row = pd.DataFrame({
                        "原文": [clean_term],
                        "翻译": [""],
                        "分类": [categories[0]]
                    })
                    self.df = pd.concat([self.df, new_row], ignore_index=True)
                    existing_set.add(clean_term)  # 实时更新已有词
                
                # 更新界面
                self.is_modified = True
                self.update_table()
                self.update_ui_state()
                
                QMessageBox.information(self, "添加成功", f"已添加 {len(selected_terms)} 个词条到词典")
    
    def add_category(self):
        """添加分类"""
        dialog = AddCategoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category = dialog.category_name.text()
            
            if category:
                # 检查是否已存在
                if category in self.df["分类"].unique():
                    QMessageBox.warning(self, "分类已存在", f"分类 '{category}' 已存在")
                    return
                
                # 添加新分类
                QMessageBox.information(self, "添加成功", f"分类 '{category}' 已添加")
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "确认退出", "当前词典已修改，是否保存更改？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if not self.save_dictionary():
                    event.ignore()  # 保存失败，取消关闭
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()  # 取消关闭


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = DictionaryEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
