"""AI 服务客户端模块 - 支持多语言和自定义模型"""
import os
import json
from typing import Optional, List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIClient:
    """AI 服务统一封装类"""

    # 支持的提供商配置
    PROVIDERS = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'env_key': 'OPENAI_API_KEY',
        },
        'aihubmix': {
            'base_url': 'https://aihubmix.com/v1',
            'env_key': 'AIHUBMIX_API_KEY',
        }
    }

    # 默认模型映射
    DEFAULT_MODELS = {
        'openai': 'gpt-4o',
        'aihubmix': 'gpt-4o',
    }

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        user_language: Optional[str] = None,
        text_language: Optional[str] = None
    ):
        """
        初始化 AI 客户端

        Args:
            provider: AI 提供商 ('openai' 或 'aihubmix')
            model: 模型名称，默认使用提供商的默认模型
            user_language: 用户语言/AI 响应语言 (如 'zh-CN', 'en')
            text_language: 输入文本的语言 (如 'zh-CN', 'en', 'auto')
        """
        self.provider = provider or os.getenv('AI_PROVIDER', 'aihubmix')
        self.model = model or os.getenv('AI_MODEL', self.DEFAULT_MODELS.get(self.provider, 'gpt-4o'))

        # 语言设置
        self.user_language = user_language or os.getenv('USER_LANGUAGE', 'zh-CN')
        self.text_language = text_language or os.getenv('TEXT_LANGUAGE', 'auto')

        if self.provider not in self.PROVIDERS:
            raise ValueError(f"不支持的 AI provider: {self.provider}")

        provider_config = self.PROVIDERS[self.provider]
        api_key = os.getenv(provider_config['env_key'])

        if not api_key:
            raise ValueError(f"未设置 API key: {provider_config['env_key']}")

        self.client = OpenAI(
            api_key=api_key,
            base_url=provider_config['base_url']
        )

    def _uses_max_completion_tokens(self) -> bool:
        """
        检测模型是否使用 max_completion_tokens 参数

        某些模型（如 gemini、gpt-5 系列）不支持 max_tokens，需要使用 max_completion_tokens
        """
        model_lower = self.model.lower()
        # 需要使用 max_completion_tokens 的模型
        return any([
            'gemini' in model_lower,
            'gpt-5' in model_lower,
            'o1' in model_lower,
            'o3' in model_lower,
        ])

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        发送聊天请求

        Args:
            prompt: 用户提示
            system_prompt: 系统提示，默认根据语言设置
            temperature: 温度参数 (0-2)
            max_tokens: 最大 token 数

        Returns:
            AI 响应文本
        """
        # 构建系统提示
        if system_prompt is None:
            system_prompt = self._build_system_prompt()

        # 根据模型类型选择正确的 token 参数
        if self._uses_max_completion_tokens():
            kwargs = {"max_completion_tokens": max_tokens}
        else:
            kwargs = {"max_tokens": max_tokens}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            **kwargs
        )

        return response.choices[0].message.content

    def _build_system_prompt(self) -> str:
        """根据语言设置构建系统提示"""
        # 用户语言指导
        language_instruction = ""
        if self.user_language:
            language_map = {
                'zh-CN': '中文（简体）',
                'zh-TW': '中文（繁体）',
                'cn': 'Chinese',
                'en': 'English',
                'ja': '日本語',
                'ko': '한국어',
            }
            lang_name = language_map.get(self.user_language, self.user_language)
            language_instruction = f"请使用 {lang_name} 语言回复。"

        # 文本语言指导
        text_instruction = ""
        if self.text_language and self.text_language != 'auto':
            language_map = {
                'zh-CN': '中文（简体）',
                'zh-TW': '中文（繁体）',
                'cn': 'Chinese',
                'en': 'English',
                'ja': '日本語',
                'ko': '한국어',
            }
            lang_name = language_map.get(self.text_language, self.text_language)
            text_instruction = f"用户输入的文本语言是 {lang_name}。"

        base_prompt = "你是一个专业的 AI 助手。"
        return f"{base_prompt} {language_instruction} {text_instruction}".strip()

    def generate_topics(
        self,
        topic: str,
        count: int = 10,
        language: Optional[str] = None,
        background: str = ""
    ) -> List[str]:
        """
        生成主题列表

        Args:
            topic: 用户输入的模糊主题
            count: 生成主题数量
            language: 主题语言，默认使用 user_language
            background: 用户背景信息

        Returns:
            主题列表
        """
        lang = language or self.user_language

        prompt = f"""你是一个内容策划助手。用户想要写一篇关于「{topic}」的文章。

背景信息：{background or '无特定背景'}

请生成 {count} 个详细、具体、有吸引力的文章主题。
要求：
1. 主题要具体且有吸引力
2. 每个主题字数在 10-30 字之间
3. 涵盖不同角度（入门、进阶、技巧、案例等）
4. 返回格式：每行一个主题，不要编号

直接返回 {count} 个主题，不要有任何解释或其他内容。"""

        # 根据模型类型选择正确的 token 参数
        if self._uses_max_completion_tokens():
            token_kwargs = {"max_completion_tokens": 500}
        else:
            token_kwargs = {"max_tokens": 500}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"你是一个专业的内容策划助手。请使用 {lang} 语言输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            **token_kwargs
        )

        content = response.choices[0].message.content
        themes = [t.strip() for t in content.split('\n') if t.strip()]
        return themes[:count]

    def generate_article(
        self,
        title: str,
        keywords: Optional[List[str]] = None,
        outline: Optional[List[str]] = None,
        word_count: int = 1000,
        style: str = "professional"
    ) -> str:
        """
        生成文章内容

        Args:
            title: 文章标题
            keywords: 关键词列表
            outline: 文章大纲
            word_count: 目标字数
            style: 文章风格 (professional/friendly/technical)

        Returns:
            生成的 HTML 文章内容
        """
        style_map = {
            'professional': '专业、正式、客观',
            'friendly': '亲切、友好、易懂',
            'technical': '技术性强、详细、深入'
        }

        prompt = f"""请根据以下信息生成一篇文章：

标题：{title}
目标字数：约 {word_count} 字
风格：{style_map.get(style, style)}

{f"关键词：{', '.join(keywords)}" if keywords else ""}
{f"大纲：\n" + "\n".join(f"- {o}" for o in outline) if outline else ""}

请生成完整的文章内容，使用 HTML 标签格式化（h2、p、ul/li 等）。
请使用 {self.user_language} 语言输出。"""

        return self.chat(prompt, temperature=0.7, max_tokens=word_count * 2)

    def generate_markdown_article(
        self,
        title: str,
        background: str = "",
        keywords: Optional[List[str]] = None,
        requirements: str = "Professional and well-structured",
        word_count: int = 800
    ) -> str:
        """
        生成 Markdown 格式的文章

        Args:
            title: 文章标题
            background: 用户背景信息
            keywords: SEO 关键词列表
            requirements: 文章要求/风格
            word_count: 目标字数

        Returns:
            Markdown 格式的文章内容
        """
        # 使用实例的默认语言设置
        # 文章以 text_language 输出
        output_lang = self.text_language
        input_lang = self.text_language

        # 语言名称映射
        language_map = {
            'zh-CN': 'Chinese',
            'zh-TW': 'Chinese (Traditional)',
            'cn': 'Chinese',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
            'Spanish': 'Spanish',
            'Portuguese': 'Portuguese',
            'French': 'French',
            'German': 'German',
            'Italian': 'Italian',
            'Russian': 'Russian',
            'Arabic': 'Arabic',
        }
        output_lang_name = language_map.get(output_lang, output_lang)
        input_lang_name = language_map.get(input_lang, input_lang) if input_lang != 'auto' else 'auto-detect'

        prompt = f"""Write a complete article in {output_lang_name} based on the following information:

## Basic Information
Title: {title}
Target word count: approximately {word_count} words
Article output language: {output_lang_name}
Input text language: {input_lang_name}

## Author Background
{background or 'Not specified'}

## SEO Keywords
{', '.join(keywords) if keywords else 'Not specified'}

## Article Requirements
{requirements}

## Requirements
1. Use Markdown format (# for main title, ## for subsections, paragraphs, lists, etc.)
2. Clear structure with introduction, body, and conclusion
3. Naturally integrate SEO keywords at the beginning or end
4. Professional, valuable, and in-depth content
5. Return ONLY the article content, no explanations

Please generate the complete article:"""

        return self.chat(prompt, temperature=0.7, max_tokens=word_count * 3)

    def get_image_insert_points(self, article: str, images: List[Dict]) -> List[Dict]:
        """
        获取图片插入位置

        Args:
            article: 文章内容
            images: 图片列表，每个包含 filename 和 alt/prompt

        Returns:
            插入点列表 [{"image": "xxx.jpg", "insert_after": "原文片段"}, ...]
        """
        # 构建图片列表描述
        image_list = "\n".join([
            f"- {img.get('filename', f'image_{i+1}.jpg')}: {img.get('alt', img.get('prompt', ''))}"
            for i, img in enumerate(images)
        ])

        prompt = f"""请分析以下文章和图片，为每张图片确定最佳插入位置。

文章内容：
{article}

图片列表：
{image_list}

请返回 JSON 格式的插入点信息：
```json
[
  {{"image": "图片1文件名.jpg", "insert_after": "这里是文章中的某段文字"}},
  {{"image": "图片2文件名.jpg", "insert_after": "这里是另一段文字"}}
]
```

要求：
1. insert_after 必须是文章中的原文片段（不要改写）
2. 选择能够自然衔接的位置
3. 选择足够独特的句子，避免全文重复
4. 每张图片都要有唯一的位置
5. 返回纯 JSON，不要其他内容"""

        response = self.chat(prompt, temperature=0.3, max_tokens=1000)

        # 解析 JSON
        try:
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                insert_points = json.loads(json_match.group())
                return insert_points
        except (json.JSONDecodeError, AttributeError):
            print(f"解析插入点失败: {response[:200]}")

        # 解析失败时返回默认位置（均匀分布）
        return self._get_default_insert_points(article, images)

    def _get_default_insert_points(self, article: str, images: List[Dict]) -> List[Dict]:
        """获取默认插入点（均匀分布）"""
        # 按段落分割
        paragraphs = [p.strip() for p in article.split('\n') if p.strip()]
        if not paragraphs:
            return []

        # 计算每个插入点
        step = max(1, len(paragraphs) // (len(images) + 1))
        insert_points = []

        for i, img in enumerate(images):
            idx = (i + 1) * step
            if idx < len(paragraphs):
                anchor = paragraphs[idx]
                # 截取前50字符作为锚点
                anchor = anchor[:50] + "..." if len(anchor) > 50 else anchor
            else:
                anchor = paragraphs[-1][:50] if len(paragraphs[-1]) > 50 else paragraphs[-1]

            insert_points.append({
                "image": img.get('filename', f'image_{i+1}.jpg'),
                "insert_after": anchor
            })

        return insert_points

    @staticmethod
    def list_available_models(provider: str = 'aihubmix') -> List[str]:
        """
        获取可用模型列表（静态方法）

        Args:
            provider: 提供商名称

        Returns:
            模型列表
        """
        # 常用模型列表（实际应从 API 获取）
        models = {
            'aihubmix': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-3.5-turbo',
                'gpt-4o-search-preview',
                'gpt-4o-mini-search-preview',
            ],
            'openai': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo',
            ]
        }
        return models.get(provider, [])


# 便捷函数
def get_ai_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    user_language: Optional[str] = None,
    text_language: Optional[str] = None
) -> AIClient:
    """
    获取 AI 客户端实例的便捷函数

    Args:
        provider: AI 提供商
        model: 模型名称
        user_language: 用户语言
        text_language: 文本语言

    Returns:
        AIClient 实例
    """
    return AIClient(provider, model, user_language, text_language)


# 测试代码
if __name__ == "__main__":
    # 示例 1: 使用默认配置（从环境变量）
    # ai = AIClient()

    # 示例 2: 指定提供商和模型
    ai = AIClient(
        provider='aihubmix',
        model='gpt-4o-mini',
        user_language='zh-CN',
        text_language='auto'
    )

    # 测试生成主题
    print("=== 测试生成主题 ===")
    topics = ai.generate_topics("Python 编程", 5)
    for t in topics:
        print(f"- {t}")

    # 测试普通对话
    print("\n=== 测试对话 ===")
    response = ai.chat("用一句话介绍 Python")
    print(response)

    # 测试生成文章
    print("\n=== 测试生成文章 ===")
    article = ai.generate_article(
        title="Python 入门指南",
        keywords=["Python", "编程", "入门"],
        word_count=500
    )
    print(article[:500] + "..." if len(article) > 500 else article)
