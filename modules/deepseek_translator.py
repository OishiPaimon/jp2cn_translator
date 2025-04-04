class DeepSeekTranslator(TranslatorBase):
    """使用DeepSeek API的翻译器"""
    
    def __init__(self, api_key: str = None, model: str = None, api_base: str = None):
        """
        初始化DeepSeek翻译器
        
        Args:
            api_key: DeepSeek API密钥
            model: 使用的模型名称
            api_base: API基础URL
        """
        super().__init__()
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.model = model or DEEPSEEK_MODEL
        self.api_base = api_base or DEEPSEEK_API_BASE
        
        if not OPENAI_AVAILABLE:
            raise ImportError("未安装OpenAI库，请使用pip install openai安装")
        
        if not self.api_key:
            # 使用模拟模式，用于测试
            print("警告: 未提供DeepSeek API密钥，使用模拟模式")
            self.mock_mode = True
        else:
            self.mock_mode = False
            # 初始化OpenAI客户端，但使用DeepSeek的API基础URL
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
    
    def translate(self, text: str, dictionary: Dict[str, str] = None) -> str:
        """
        使用DeepSeek API翻译文本
        
        Args:
            text: 待翻译的日语文本
            dictionary: 翻译词典
            
        Returns:
            str: 翻译后的中文文本
        """
        if not text.strip():
            return ""
        
        # 如果是模拟模式，返回模拟翻译结果
        if hasattr(self, 'mock_mode') and self.mock_mode:
            # 简单的模拟翻译，用于测试
            if dictionary and text in dictionary:
                return dictionary[text]
            
            # 一些基本的日语短语模拟翻译
            mock_translations = {
                "これは": "这是",
                "日本語": "日语",
                "中国語": "中文",
                "翻訳": "翻译",
                "プログラム": "程序",
                "テスト": "测试",
                "サンプル": "样本"
            }
            
            # 简单替换已知词汇
            translated = text
            for jp, cn in mock_translations.items():
                translated = translated.replace(jp, cn)
            
            # 如果没有变化，添加标记
            if translated == text:
                return f"[模拟翻译] {text}"
            return translated
        
        # 构建提示词
        prompt = self._build_prompt(text, dictionary)
        
        try:
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                temperature=0.3,
                max_tokens=MAX_TOKENS_PER_REQUEST,
                timeout=TRANSLATION_TIMEOUT
            )
            
            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            return translated_text
            
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            return f"[翻译错误: {str(e)}]"
    
    def _build_prompt(self, text: str, dictionary: Dict[str, str] = None) -> Dict[str, str]:
        """
        构建翻译提示词
        
        Args:
            text: 待翻译的文本
            dictionary: 翻译词典
            
        Returns:
            Dict[str, str]: 包含system和user提示词的字典
        """
        system_prompt = """你是一个专业的日语到中文翻译器。你的任务是将日语文本准确翻译成中文，遵循以下规则：
1. 必须逐字逐句翻译，不要添加、省略或总结任何内容
2. 保持原文的段落结构和格式
3. 严格按照提供的词典翻译特定术语
4. 直接输出翻译结果，不要添加任何解释或注释
5. 不要在翻译中添加任何原文没有的内容"""
        
        user_prompt = f"请将以下日语文本翻译成中文：\n\n{text}"
        
        # 如果有词典，添加到提示词中
        if dictionary and len(dictionary) > 0:
            dict_prompt = "请在翻译时严格使用以下词典翻译特定术语：\n"
            for jp_term, cn_term in dictionary.items():
                dict_prompt += f"- {jp_term} → {cn_term}\n"
            system_prompt += "\n\n" + dict_prompt
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
