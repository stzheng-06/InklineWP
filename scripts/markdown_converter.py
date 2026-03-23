"""Markdown 转 HTML 模块"""
import json
import re
from pathlib import Path
from typing import Dict, Optional
import markdown2


class MarkdownConverter:
    """Markdown 转换为带样式的 HTML"""

    def __init__(self, config_path: str = "element_mapping.json", template_name: str = "default"):
        """
        初始化转换器

        Args:
            config_path: element_mapping.json 配置文件路径
            template_name: 模板名称，用于加载对应的模板
        """
        self.template_name = template_name
        self.config = self._load_config(config_path)
        self.elements = self.config.get("elements", {})
        self.container_class = self.config.get("container", {}).get("class", "prose")
        self.div_config = self.config.get("div", {})

        # 加载模板配置
        self.template_config = self._load_template_config()
        self.template_loader = None
        if self.template_config.get("enabled", False):
            try:
                from .template_loader import get_template_loader
                # 使用模板名称加载对应的模板目录
                # template_name 是分类名，直接用它查找 templates/{category}/
                self.template_loader = get_template_loader(self.template_name)
            except ImportError:
                pass

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        # 尝试多个可能的路径
        possible_paths = [
            Path(config_path),
            Path(__file__).parent / config_path,
            Path(__file__).parent.parent / config_path,
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # 如果找不到，返回默认配置
        return {"elements": {}, "div": {"class": ""}}

    def _load_template_config(self) -> Dict:
        """加载模板配置"""
        try:
            # 尝试从 config.json 加载
            config_path = Path(__file__).parent / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("template_settings", {"enabled": False})
        except Exception:
            pass
        return {"enabled": False}

    def convert_to_html(
        self,
        markdown_content: str,
        image_url_map: Optional[Dict[str, str]] = None
    ) -> str:
        """
        将 Markdown 转换为 HTML

        Args:
            markdown_content: Markdown 内容
            image_url_map: 图片本地路径到 HTTP 链接的映射

        Returns:
            HTML 字符串
        """
        # 先替换图片路径为 HTTP 链接
        if image_url_map:
            content = self._replace_image_urls(markdown_content, image_url_map)
        else:
            content = markdown_content

        # 使用 markdown2 转换
        html = markdown2.markdown(
            content,
            extras=[
                'fenced-code-blocks',
                'tables',
                'strikethrough',
                'task_list',
                'code-friendly'
            ]
        )

        # 后处理：添加 class 和 attributes
        html = self._post_process_html(html)

        # 用 div 包裹
        div_class = self.div_config.get("class", "")
        if div_class:
            html = f'<div class="{div_class}">\n{html}\n</div>'
        else:
            html = f'<div>\n{html}\n</div>'

        # 插入 CTA 组件
        html = self._insert_cta_components(html)

        return html

    def _insert_cta_components(self, html: str) -> str:
        """插入 CTA 组件"""
        if not self.template_config.get("enabled", False):
            return html

        if self.template_loader is None:
            return html

        # 获取要插入的组件
        components_config = self.template_config.get("components", {})
        if not components_config:
            return html

        # 加载组件内容
        components = {}
        positions = {}
        for name, position in components_config.items():
            content = self.template_loader.get_component(name)
            if content:
                components[name] = content
                positions[name] = position

        if not components:
            return html

        # 插入组件
        return self.template_loader.insert_components(html, components, positions)

    def _replace_image_urls(
        self,
        content: str,
        image_url_map: Dict[str, str]
    ) -> str:
        """替换 Markdown 中的图片路径为 HTTP 链接"""
        for local_path, http_url in image_url_map.items():
            # 使用文件名进行匹配
            filename = Path(local_path).name

            # 匹配模式：./assets/image1.jpg 或 assets/image1.jpg 或直接文件名
            patterns = [
                rf'\(\./assets/{re.escape(filename)}\)',
                r'\(assets/' + re.escape(filename) + r'\)',
                r'\(./' + re.escape(filename) + r'\)',
                r'\(' + re.escape(filename) + r'\)',
            ]

            for pattern in patterns:
                try:
                    content = re.sub(pattern, f'({http_url})', content)
                except re.error:
                    continue

        return content

    def _post_process_html(self, html: str) -> str:
        """后处理 HTML，添加 class 和 attributes"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 处理各个元素
        element_mappings = {
            'h1': 'h1', 'h2': 'h2', 'h3': 'h3',
            'h4': 'h4', 'h5': 'h5', 'h6': 'h6',
            'p': 'p', 'img': 'img', 'code': 'code',
            'blockquote': 'blockquote', 'ul': 'ul',
            'ol': 'ol', 'li': 'li', 'table': 'table',
            'pre': 'pre', 'a': 'a'
        }

        for key, tag in element_mappings.items():
            config = self.elements.get(key, {})
            tag_class = config.get("class", "")
            attributes = config.get("attributes", {})

            if not tag_class and not attributes:
                continue

            for element in soup.find_all(tag):
                # 添加 class
                if tag_class:
                    existing_class = element.get("class", [])
                    if isinstance(existing_class, str):
                        existing_class = existing_class.split()
                    if tag_class not in existing_class:
                        element["class"] = " ".join(existing_class + [tag_class])

                # 添加其他 attributes
                for attr, value in attributes.items():
                    element[attr] = value

        return str(soup)

    def save_html(
        self,
        html_content: str,
        output_path: Path
    ) -> bool:
        """
        保存 HTML 文件

        Args:
            html_content: HTML 内容
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"保存 HTML 失败: {e}")
            return False


def get_markdown_converter(config_path: str = "element_mapping.json", template_name: str = "default") -> MarkdownConverter:
    """获取 MarkdownConverter 实例"""
    return MarkdownConverter(config_path, template_name)


if __name__ == "__main__":
    # 测试
    converter = MarkdownConverter()

    test_md = """# 测试标题

这是一个段落。

## 二级标题

![image1](./assets/image1.jpg)

```python
print("hello")
```
"""

    # 模拟图片映射
    image_map = {
        "image1.jpg": "https://example.com/wp-content/uploads/2024/01/image1.jpg"
    }

    html = converter.convert_to_html(test_md, image_map)
    print(html)
