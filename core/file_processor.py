"""
文件处理模块 - 负责读取日语文本文件并按照双换行符分割内容块
"""
import os
import re
from typing import List, Tuple


class FileProcessor:
    def __init__(self):
        """初始化文件处理器"""
        pass

    def read_file(self, file_path: str) -> str:
        """
        读取文本文件，保留所有换行符
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串，保留所有换行符
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except UnicodeDecodeError:
            # 尝试使用其他编码
            encodings = ['shift-jis', 'euc-jp', 'iso-2022-jp']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    return content
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，抛出异常
            raise UnicodeDecodeError("无法解码文件，请确保文件编码为UTF-8、Shift-JIS、EUC-JP或ISO-2022-JP")

    def split_into_blocks(self, content: str) -> List[str]:
        """
        将文本内容按照双换行符分割成内容块
        
        Args:
            content: 文本内容
            
        Returns:
            内容块列表
        """
        # 使用正则表达式匹配双换行符
        # 保留换行符在分割后的内容中
        blocks = re.split(r'(\n\n)', content)
        
        # 重新组合内容块和分隔符
        result_blocks = []
        i = 0
        while i < len(blocks):
            if i + 1 < len(blocks) and blocks[i+1] == '\n\n':
                # 将内容块和后面的双换行符合并
                result_blocks.append(blocks[i] + blocks[i+1])
                i += 2
            else:
                # 处理最后一个块或没有双换行符的情况
                result_blocks.append(blocks[i])
                i += 1
                
        # 过滤掉空块
        result_blocks = [block for block in result_blocks if block.strip()]
        
        return result_blocks

    def calculate_prompt_length(self, blocks: List[str], max_length: int) -> List[List[str]]:
        """
        计算提示词总长度，并将内容块分组，确保每组不超过最大长度限制
        
        Args:
            blocks: 内容块列表
            max_length: 最大长度限制
            
        Returns:
            分组后的内容块列表的列表
        """
        groups = []
        current_group = []
        current_length = 0
        
        for block in blocks:
            block_length = len(block)
            
            # 如果单个块超过最大长度，需要进一步分割
            if block_length > max_length:
                # 如果当前组不为空，先添加到结果中
                if current_group:
                    groups.append(current_group)
                
                # 将大块分割成更小的部分
                parts = self._split_large_block(block, max_length)
                for part in parts:
                    groups.append([part])
                
                # 重置当前组
                current_group = []
                current_length = 0
                continue
            
            # 检查添加当前块是否会超过最大长度
            if current_length + block_length > max_length and current_group:
                # 如果会超过，将当前组添加到结果中，并开始新的组
                groups.append(current_group)
                current_group = [block]
                current_length = block_length
            else:
                # 否则，将块添加到当前组
                current_group.append(block)
                current_length += block_length
        
        # 添加最后一个组（如果不为空）
        if current_group:
            groups.append(current_group)
        
        return groups

    def _split_large_block(self, block: str, max_length: int) -> List[str]:
        """
        将大块分割成更小的部分，尽量在句子边界处分割
        
        Args:
            block: 大内容块
            max_length: 最大长度限制
            
        Returns:
            分割后的小块列表
        """
        parts = []
        remaining = block
        
        while len(remaining) > max_length:
            # 尝试在句子边界处分割
            # 日语句子通常以句号、问号或感叹号结束
            split_pos = max_length
            
            # 向前查找最近的句子结束标记
            for end_mark in ['。', '？', '！', '?', '!', '.']:
                pos = remaining[:max_length].rfind(end_mark)
                if pos > 0 and pos < split_pos:
                    split_pos = pos + 1  # 包含句子结束标记
            
            # 如果找不到句子边界，则在最大长度处分割
            if split_pos == max_length:
                # 尝试在换行符处分割
                pos = remaining[:max_length].rfind('\n')
                if pos > 0:
                    split_pos = pos + 1  # 包含换行符
            
            # 分割文本
            parts.append(remaining[:split_pos])
            remaining = remaining[split_pos:]
        
        # 添加剩余部分
        if remaining:
            parts.append(remaining)
        
        return parts


# 测试代码
if __name__ == "__main__":
    processor = FileProcessor()
    
    # 测试文件读取
    test_content = """这是第一段内容。
这是第一段的第二行。

这是第二段内容。
这包含了一些日语文本。

这是最后一段。"""
    
    # 将测试内容写入临时文件
    with open("test_file.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # 读取文件
    content = processor.read_file("test_file.txt")
    print("读取的文件内容:")
    print(content)
    print("-" * 50)
    
    # 分割内容块
    blocks = processor.split_into_blocks(content)
    print(f"分割后的内容块数量: {len(blocks)}")
    for i, block in enumerate(blocks):
        print(f"块 {i+1}:")
        print(repr(block))
        print("-" * 30)
    
    # 测试提示词长度计算和分组
    groups = processor.calculate_prompt_length(blocks, 50)
    print(f"分组后的组数: {len(groups)}")
    for i, group in enumerate(groups):
        group_length = sum(len(block) for block in group)
        print(f"组 {i+1} (长度: {group_length}):")
        for j, block in enumerate(group):
            print(f"  块 {j+1}: {repr(block[:20])}...")
