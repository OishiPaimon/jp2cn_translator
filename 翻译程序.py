"""
翻译程序 - 支持多词典的日语翻译工具
"""
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar,
    QTabWidget, QMessageBox, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

import configparser

# 导入核心模块
sys.path.append(str(Path(__file__).parent))
from core.file_processor import FileProcessor
from core.translation_interface import TranslationInterface
from core.document_generator import DocumentGenerator


class DictionaryConflictDialog(QDialog):
    """词典冲突对话框"""
    def __init__(self, conflicts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("词典冲突")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("以下词条在不同词典中有不同的翻译，请选择要使用的翻译：")
        layout.addWidget(label)
        
        # 冲突表格
        self.table = QTableWidget(len(conflicts), 3)
        self.table.setHorizontalHeaderLabels(["原文", "词典1翻译", "词典2翻译"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 填充表格
        for i, (term, trans1, trans2) in enumerate(conflicts):
            self.table.setItem(i, 0, QTableWidgetItem(term))
            self.table.setItem(i, 1, QTableWidgetItem(trans1))
            self.table.setItem(i, 2, QTableWidgetItem(trans2))
        
        layout.addWidget(self.table)
        
        # 选择按钮
        btn_layout = QHBoxLayout()
        
        self.btn_use_1 = QPushButton("使用词典1翻译")
        self.btn_use_2 = QPushButton("使用词典2翻译")
        
        self.btn_use_1.clicked.connect(self.use_dict1)
        self.btn_use_2.clicked.connect(self.use_dict2)
        
        btn_layout.addWidget(self.btn_use_1)
        btn_layout.addWidget(self.btn_use_2)
        
        layout.addLayout(btn_layout)
        
        # 对话框按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # 初始化变量
        self.selected_dict = None
    
    def use_dict1(self):
        """使用词典1的翻译"""
        self.selected_dict = 1
        self.accept()
    
    def use_dict2(self):
        """使用词典2的翻译"""
        self.selected_dict = 2
        self.accept()


class ConfigDialog(QDialog):
    """配置对话框"""
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        
        self.setWindowTitle("翻译设置")
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # API设置组
        api_group = QGroupBox("API设置")
        api_layout = QFormLayout()
        
        # DeepSeek设置
        self.deepseek_api_key = QLineEdit(self.config.get('API', 'deepseek_api_key', fallback=''))
        self.deepseek_model = QLineEdit(self.config.get('API', 'deepseek_model', fallback='deepseek-chat'))
        api_layout.addRow("DeepSeek API密钥:", self.deepseek_api_key)
        api_layout.addRow("DeepSeek 模型:", self.deepseek_model)
        
        # Ollama设置
        self.ollama_url = QLineEdit(self.config.get('API', 'ollama_url', fallback='http://localhost:11434'))
        self.ollama_model = QLineEdit(self.config.get('API', 'ollama_model', fallback='llama3'))
        api_layout.addRow("Ollama URL:", self.ollama_url)
        api_layout.addRow("Ollama 模型:", self.ollama_model)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 翻译设置组
        trans_group = QGroupBox("翻译设置")
        trans_layout = QFormLayout()
        
        # 翻译方法
        self.trans_method = QComboBox()
        self.trans_method.addItems(["deepseek", "ollama"])
        current_method = self.config.get('Translation', 'translation_method', fallback='deepseek')
        self.trans_method.setCurrentText(current_method)
        
        # 最大提示词长度
        self.max_prompt_length = QSpinBox()
        self.max_prompt_length.setRange(1000, 10000)
        self.max_prompt_length.setSingleStep(500)
        self.max_prompt_length.setValue(int(self.config.get('Translation', 'max_prompt_length', fallback='4000')))
        
        trans_layout.addRow("翻译方法:", self.trans_method)
        trans_layout.addRow("最大提示词长度:", self.max_prompt_length)
        
        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)
        
        # 文件路径设置组
        path_group = QGroupBox("文件路径设置")
        path_layout = QFormLayout()
        
        # 默认输入目录
        self.default_input_dir = QLineEdit(self.config.get('Files', 'default_input_dir', fallback='./'))
        self.btn_input_dir = QPushButton("浏览...")
        self.btn_input_dir.clicked.connect(self.browse_input_dir)
        input_dir_layout = QHBoxLayout()
        input_dir_layout.addWidget(self.default_input_dir)
        input_dir_layout.addWidget(self.btn_input_dir)
        
        # 默认输出目录
        self.default_output_dir = QLineEdit(self.config.get('Files', 'default_output_dir', fallback='./output'))
        self.btn_output_dir = QPushButton("浏览...")
        self.btn_output_dir.clicked.connect(self.browse_output_dir)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.default_output_dir)
        output_dir_layout.addWidget(self.btn_output_dir)
        
        path_layout.addRow("默认输入目录:", QWidget())
        path_layout.itemAt(1).widget().setLayout(input_dir_layout)
        path_layout.addRow("默认输出目录:", QWidget())
        path_layout.itemAt(3).widget().setLayout(output_dir_layout)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def browse_input_dir(self):
        """浏览输入目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择默认输入目录", self.default_input_dir.text())
        if dir_path:
            self.default_input_dir.setText(dir_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择默认输出目录", self.default_output_dir.text())
        if dir_path:
            self.default_output_dir.setText(dir_path)
    
    def accept(self):
        """保存配置"""
        # 更新配置
        self.config.set('API', 'deepseek_api_key', self.deepseek_api_key.text())
        self.config.set('API', 'deepseek_model', self.deepseek_model.text())
        self.config.set('API', 'ollama_url', self.ollama_url.text())
        self.config.set('API', 'ollama_model', self.ollama_model.text())
        
        self.config.set('Translation', 'translation_method', self.trans_method.currentText())
        self.config.set('Translation', 'max_prompt_length', str(self.max_prompt_length.value()))
        
        self.config.set('Files', 'default_input_dir', self.default_input_dir.text())
        self.config.set('Files', 'default_output_dir', self.default_output_dir.text())
        
        # 保存到文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
        
        super().accept()


class TranslationThread(QThread):
    """翻译线程"""
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, translator, content_groups, combined_dict):
        super().__init__()
        self.translator = translator
        self.content_groups = content_groups
        self.combined_dict = combined_dict
        self.results = []
    
    def run(self):
        """运行翻译任务"""
        try:
            total_groups = len(self.content_groups)
            
            for i, group in enumerate(self.content_groups):
                # 应用词典
                marked_blocks = []
                for block in group:
                    marked_block = self.apply_dictionary(block)
                    marked_blocks.append(marked_block)
                
                # 翻译
                translation = self.translator.translate(marked_blocks)
                
                if translation:
                    # 移除标记
                    clean_translation = self.remove_markers(translation)
                    self.results.append(clean_translation)
                else:
                    self.error_signal.emit(f"翻译第 {i+1} 组内容失败")
                    return
                
                # 更新进度
                progress = int((i + 1) / total_groups * 100)
                self.progress_signal.emit(progress)
            
            # 合并结果
            final_result = "".join(self.results)
            self.result_signal.emit(final_result)
            
        except Exception as e:
            self.error_signal.emit(f"翻译过程中发生错误: {str(e)}")
    
    def apply_dictionary(self, text: str) -> str:
        """
        应用词典替换文本中的词语，并标记替换的部分
        
        Args:
            text: 输入文本
            
        Returns:
            替换后的文本
        """
        # 如果词典为空，直接返回原文
        if not self.combined_dict:
            return text
        
        # 按照词语长度降序排序，优先替换长词
        sorted_terms = sorted(self.combined_dict.keys(), key=len, reverse=True)
        
        # 替换文本
        result = text
        
        for term in sorted_terms:
            if term in result:
                # 替换所有匹配
                replacement = self.combined_dict[term]
                marked_replacement = f"***{replacement}***"
                result = result.replace(term, marked_replacement)
        
        return result
    
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


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("日语剧本翻译程序")
        self.setMinimumSize(800, 600)
        
        # 初始化变量
        self.config_path = os.path.join(os.path.dirname(__file__), "config", "config.ini")
        self.file_processor = FileProcessor()
        self.document_generator = DocumentGenerator()
        self.dictionaries = []

        # 加载配置
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
        else:
            # 创建默认配置
            self.create_default_config()
        
        # 初始化翻译接口
        self.translator = TranslationInterface(self.config_path)
        
        # 初始化界面
        self.init_ui()
        
        # 翻译线程
        self.translation_thread = None
        
        # 当前文件和内容
        self.current_file = None
        self.current_content = None
        self.content_groups = None
        self.translation_result = None
        
        # 词典列表
        self.dictionaries = []
        self.combined_dict = {}
    
    def create_default_config(self):
        """创建默认配置"""
        self.config['API'] = {
            'deepseek_api_key': '',
            'deepseek_model': 'deepseek-chat',
            'ollama_url': 'http://localhost:11434',
            'ollama_model': 'llama3'
        }
        
        self.config['Translation'] = {
            'max_prompt_length': '4000',
            'translation_method': 'deepseek'
        }
        
        self.config['Files'] = {
            'default_input_dir': './',
            'default_output_dir': './output'
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # 保存配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def init_ui(self):
        """初始化界面"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self.browse_file)
        
        file_layout.addWidget(QLabel("日语文件:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.btn_browse)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 词典管理区域
        dict_group = QGroupBox("词典管理")
        dict_layout = QVBoxLayout()
        
        # 词典列表
        self.dict_list = QListWidget()
        dict_layout.addWidget(QLabel("已添加的词典:"))
        dict_layout.addWidget(self.dict_list)
        
        # 词典操作按钮
        dict_btn_layout = QHBoxLayout()
        
        self.btn_add_dict = QPushButton("添加词典")
        self.btn_remove_dict = QPushButton("移除词典")
        self.btn_clear_dicts = QPushButton("清空词典")
        
        self.btn_add_dict.clicked.connect(self.add_dictionary)
        self.btn_remove_dict.clicked.connect(self.remove_dictionary)
        self.btn_clear_dicts.clicked.connect(self.clear_dictionaries)
        
        dict_btn_layout.addWidget(self.btn_add_dict)
        dict_btn_layout.addWidget(self.btn_remove_dict)
        dict_btn_layout.addWidget(self.btn_clear_dicts)
        
        dict_layout.addLayout(dict_btn_layout)
        dict_group.setLayout(dict_layout)
        main_layout.addWidget(dict_group)
        
        # 选项卡区域
        self.tabs = QTabWidget()
        
        # 原文选项卡
        self.tab_original = QWidget()
        tab_original_layout = QVBoxLayout()
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        tab_original_layout.addWidget(self.original_text)
        self.tab_original.setLayout(tab_original_layout)
        
        # 翻译选项卡
        self.tab_translation = QWidget()
        tab_translation_layout = QVBoxLayout()
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        tab_translation_layout.addWidget(self.translation_text)
        self.tab_translation.setLayout(tab_translation_layout)
        
        # 添加选项卡
        self.tabs.addTab(self.tab_original, "原文")
        self.tabs.addTab(self.tab_translation, "翻译")
        
        main_layout.addWidget(self.tabs)
        
        # 操作区域
        operation_layout = QHBoxLayout()
        
        # 翻译操作
        trans_group = QGroupBox("翻译操作")
        trans_layout = QVBoxLayout()
        
        self.btn_translate = QPushButton("开始翻译")
        self.btn_save = QPushButton("保存结果")
        self.btn_settings = QPushButton("翻译设置")
        
        self.btn_translate.clicked.connect(self.start_translation)
        self.btn_save.clicked.connect(self.save_result)
        self.btn_settings.clicked.connect(self.open_settings)
        
        trans_layout.addWidget(self.btn_translate)
        trans_layout.addWidget(self.btn_save)
        trans_layout.addWidget(self.btn_settings)
        
        trans_group.setLayout(trans_layout)
        operation_layout.addWidget(trans_group)
        
        main_layout.addLayout(operation_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("翻译进度:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        
        # 初始状态
        self.update_ui_state(False, False)
    
    def update_ui_state(self, file_loaded=False, translation_done=False):
        """更新界面状态"""
        self.btn_translate.setEnabled(file_loaded and len(self.dictionaries) > 0)
        self.btn_save.setEnabled(translation_done)
        self.btn_remove_dict.setEnabled(len(self.dictionaries) > 0)
        self.btn_clear_dicts.setEnabled(len(self.dictionaries) > 0)
    
    def browse_file(self):
        """浏览文件"""
        default_dir = self.config.get('Files', 'default_input_dir', fallback='./')
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择日语文件", default_dir, "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_path.setText(file_path)
            
            try:
                # 读取文件
                self.current_content = self.file_processor.read_file(file_path)
                self.original_text.setText(self.current_content)
                
                # 分割内容块
                blocks = self.file_processor.split_into_blocks(self.current_content)
                
                # 计算提示词长度
                max_length = int(self.config.get('Translation', 'max_prompt_length', fallback='4000'))
                self.content_groups = self.file_processor.calculate_prompt_length(blocks, max_length)
                
                # 更新界面状态
                self.update_ui_state(True, False)
                self.translation_text.clear()
                self.progress_bar.setValue(0)
                self.translation_result = None
                
                # 切换到原文选项卡
                self.tabs.setCurrentIndex(0)
                
                QMessageBox.information(
                    self, "文件加载成功", 
                    f"成功加载文件，共 {len(blocks)} 个内容块，{len(self.content_groups)} 个翻译组。"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "文件加载失败", f"加载文件时发生错误: {str(e)}")
    
    def add_dictionary(self):
        """添加词典"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择词典文件", "./", "Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path)
                
                # 检查必要的列
                if "原文" not in df.columns or "翻译" not in df.columns:
                    QMessageBox.warning(self, "词典格式错误", "词典文件必须包含'原文'和'翻译'列")
                    return
                
                # 创建词典
                new_dict = {}
                for _, row in df.iterrows():
                    if pd.notna(row["原文"]) and pd.notna(row["翻译"]) and row["原文"] and row["翻译"]:
                        new_dict[row["原文"]] = row["翻译"]
                
                # 检查冲突
                conflicts = []
                for term, trans in new_dict.items():
                    if term in self.combined_dict and self.combined_dict[term] != trans:
                        conflicts.append((term, self.combined_dict[term], trans))
                
                if conflicts:
                    # 显示冲突对话框
                    dialog = DictionaryConflictDialog(conflicts, self)
                    result = dialog.exec()
                    
                    if result == QDialog.DialogCode.Accepted:
                        # 根据用户选择解决冲突
                        if dialog.selected_dict == 1:
                            # 保留原有词典的翻译
                            for term, _, _ in conflicts:
                                new_dict[term] = self.combined_dict[term]
                        # 如果选择2，则使用新词典的翻译，不需要修改
                    else:
                        # 用户取消，不添加词典
                        return
                
                # 添加词典
                self.dictionaries.append((os.path.basename(file_path), new_dict))
                self.dict_list.addItem(os.path.basename(file_path))
                
                # 更新合并词典
                self.combined_dict.update(new_dict)
                
                # 更新界面状态
                self.update_ui_state(self.current_file is not None, False)
                
                QMessageBox.information(
                    self, "词典添加成功", 
                    f"成功添加词典 '{os.path.basename(file_path)}'，包含 {len(new_dict)} 个词条"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "词典添加失败", f"添加词典时发生错误: {str(e)}")
    
    def remove_dictionary(self):
        """移除词典"""
        selected_items = self.dict_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "未选择词典", "请先选择要移除的词典")
            return
        
        # 获取选中的词典
        selected_item = selected_items[0]
        selected_index = self.dict_list.row(selected_item)
        
        # 移除词典
        removed_name, removed_dict = self.dictionaries.pop(selected_index)
        self.dict_list.takeItem(selected_index)
        
        # 重建合并词典
        self.combined_dict = {}
        for _, dict_data in self.dictionaries:
            self.combined_dict.update(dict_data)
        
        # 更新界面状态
        self.update_ui_state(self.current_file is not None, False)
        
        QMessageBox.information(self, "词典移除成功", f"成功移除词典 '{removed_name}'")
    
    def clear_dictionaries(self):
        """清空词典"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有词典吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 清空词典
            self.dictionaries = []
            self.combined_dict = {}
            self.dict_list.clear()
            
            # 更新界面状态
            self.update_ui_state(self.current_file is not None, False)
            
            QMessageBox.information(self, "词典清空成功", "已清空所有词典")
    
    def start_translation(self):
        """开始翻译"""
        if not self.content_groups:
            QMessageBox.warning(self, "无法翻译", "请先加载文件")
            return
        
        if not self.dictionaries:
            QMessageBox.warning(self, "无法翻译", "请先添加词典")
            return
        
        # 检查翻译方法
        method = self.config.get('Translation', 'translation_method')
        if method == "deepseek" and not self.config.get('API', 'deepseek_api_key'):
            QMessageBox.warning(self, "API密钥缺失", "请在设置中配置DeepSeek API密钥")
            self.open_settings()
            return
        
        # 禁用按钮
        self.btn_translate.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.btn_add_dict.setEnabled(False)
        self.btn_remove_dict.setEnabled(False)
        self.btn_clear_dicts.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # 创建并启动翻译线程
        self.translation_thread = TranslationThread(
            self.translator, self.content_groups, self.combined_dict
        )
        self.translation_thread.progress_signal.connect(self.update_progress)
        self.translation_thread.result_signal.connect(self.handle_translation_result)
        self.translation_thread.error_signal.connect(self.handle_translation_error)
        self.translation_thread.start()
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def handle_translation_result(self, result):
        """处理翻译结果"""
        self.translation_result = result
        self.translation_text.setText(result)
        
        # 更新界面状态
        self.update_ui_state(True, True)
        self.btn_browse.setEnabled(True)
        self.btn_add_dict.setEnabled(True)
        self.btn_remove_dict.setEnabled(True)
        self.btn_clear_dicts.setEnabled(True)
        
        # 切换到翻译选项卡
        self.tabs.setCurrentIndex(1)
        
        QMessageBox.information(self, "翻译完成", "文档翻译已完成")
    
    def handle_translation_error(self, error_msg):
        """处理翻译错误"""
        QMessageBox.critical(self, "翻译失败", error_msg)
        
        # 恢复界面状态
        self.update_ui_state(True, False)
        self.btn_browse.setEnabled(True)
        self.btn_add_dict.setEnabled(True)
        self.btn_remove_dict.setEnabled(True)
        self.btn_clear_dicts.setEnabled(True)
    
    def save_result(self):
        """保存翻译结果"""
        if not self.translation_result:
            QMessageBox.warning(self, "无法保存", "没有可保存的翻译结果")
            return
        
        # 获取默认输出目录
        default_dir = self.config.get('Files', 'default_output_dir', fallback='./output')
        os.makedirs(default_dir, exist_ok=True)
        
        # 获取默认文件名
        if self.current_file:
            base_name = os.path.splitext(os.path.basename(self.current_file))[0] + "_translated"
        else:
            base_name = "translated"
        
        # 保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存翻译结果", os.path.join(default_dir, base_name),
            "Word文档 (*.docx);;文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                # 确定文件类型
                if file_path.endswith(".docx"):
                    # 保存为Word文档
                    self.document_generator.save_as_word(self.translation_result, file_path)
                    
                    # 同时保存文本文件
                    txt_path = os.path.splitext(file_path)[0] + ".txt"
                    self.document_generator.save_as_text(self.translation_result, txt_path)
                    
                    QMessageBox.information(
                        self, "保存成功", 
                        f"翻译结果已保存为Word文档: {file_path}\n同时保存为文本文件: {txt_path}"
                    )
                else:
                    # 保存为文本文件
                    self.document_generator.save_as_text(self.translation_result, file_path)
                    QMessageBox.information(self, "保存成功", f"翻译结果已保存为文本文件: {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时发生错误: {str(e)}")
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = ConfigDialog(self.config_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 重新加载配置
            self.config.read(self.config_path, encoding='utf-8')
            
            # 更新翻译接口
            self.translator = TranslationInterface(self.config_path)
            
            QMessageBox.information(self, "设置已更新", "翻译设置已成功更新")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
