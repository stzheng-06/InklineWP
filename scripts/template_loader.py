"""模板加载器 - 加载和管理 HTML 组件"""
from pathlib import Path
from typing import Dict, Optional


class TemplateLoader:
    """HTML 组件加载器"""

    def __init__(self, template_dir: str = "templates"):
        """
        初始化模板加载器

        Args:
            template_dir: 模板目录路径，可以是 "templates" 或 "templates/default"
        """
        # 尝试多个可能的路径
        base_paths = [
            Path(__file__).parent.parent,
            Path(__file__).parent,
        ]

        self.template_dir = None
        self.cta_dir = None

        # template_dir 可能是 "cta", "default", "templates", "templates/cta" 等
        # 需要找到正确的 cta 目录

        for base in base_paths:
            # 情况1: template_dir = "cta" -> 找 templates/cta/
            category_cta = base / "templates" / template_dir
            if category_cta.exists():
                self.template_dir = category_cta.parent
                self.cta_dir = category_cta
                break

            # 情况2: template_dir = "templates/cta" -> 找 templates/cta/
            direct_cta = base / template_dir
            if direct_cta.exists():
                self.template_dir = direct_cta.parent
                self.cta_dir = direct_cta
                break

            # 情况3: template_dir = "default" -> 找 templates/default/cta/
            default_cta = base / "templates" / template_dir / "cta"
            if default_cta.exists():
                self.template_dir = default_cta.parent
                self.cta_dir = default_cta
                break

        # 回退: 尝试 templates/cta/
        if self.cta_dir is None or not self.cta_dir.exists():
            for base in base_paths:
                root_cta = base / "templates" / "cta"
                if root_cta.exists():
                    self.template_dir = root_cta.parent
                    self.cta_dir = root_cta
                    break

        # 确保有默认值
        if self.template_dir is None:
            self.template_dir = base_paths[0] / "templates"
        if self.cta_dir is None or not self.cta_dir.exists():
            self.cta_dir = self.template_dir / "cta"

        self.components: Dict[str, str] = {}
        self._load_components()

    def _load_components(self) -> None:
        """加载所有组件"""
        if not self.cta_dir.exists():
            return

        for file_path in self.cta_dir.glob("*.html"):
            if file_path.name.startswith("__"):
                continue

            component_name = file_path.stem  # 文件名不含扩展名
            with open(file_path, 'r', encoding='utf-8') as f:
                self.components[component_name] = f.read()

    def get_cta_components(self) -> Dict[str, str]:
        """获取所有 CTA 组件"""
        return self.components.copy()

    def get_component(self, name: str) -> Optional[str]:
        """获取指定名称的组件"""
        return self.components.get(name)

    def get_all_component_names(self) -> list:
        """获取所有组件名称"""
        return list(self.components.keys())

    def insert_components(
        self,
        html_content: str,
        components: Dict[str, str],
        positions: Dict[str, str] = None
    ) -> str:
        """
        在固定位置插入组件

        Args:
            html_content: 原始 HTML 内容
            components: 要插入的组件 {名称: HTML}
            positions: 位置配置 {名称: "start"|"end"}

        Returns:
            插入组件后的 HTML
        """
        if not positions:
            # 默认全部放在结尾
            positions = {name: "end" for name in components.keys()}

        # 分离开头和结尾的组件
        start_components = []
        end_components = []

        for name, html in components.items():
            position = positions.get(name, "end")
            if position == "start":
                start_components.append(html)
            else:
                end_components.append(html)

        # 插入开头组件
        if start_components:
            start_html = "\n".join(start_components)
            # 找到 </div> 结束标签（最外层 div）
            html_content = html_content.replace("</div>", f"{start_html}\n</div>", 1)

        # 插入结尾组件
        if end_components:
            end_html = "\n".join(end_components)
            html_content = html_content.replace("</div>", f"{end_html}\n</div>", 1)

        return html_content


def get_template_loader(template_dir: str = "templates") -> TemplateLoader:
    """获取 TemplateLoader 实例"""
    return TemplateLoader(template_dir)


if __name__ == "__main__":
    # 测试
    loader = TemplateLoader()
    print("可用组件:", loader.get_all_component_names())

    if loader.get_component("whatsapp_cta"):
        print("\nWhatsApp CTA:")
        print(loader.get_component("whatsapp_cta")[:100])
