"""配置管理模块"""
import json
import os
from typing import Any, Optional, Dict, List
from pathlib import Path


class Config:
    """配置管理类"""

    DEFAULT_CONFIG = {
        "config_name": "Default",
        "ai_provider": "aihubmix",
        "model": "gpt-4o-mini",
        "user_language": "English",
        "text_language": "auto",
        "background": "",
        "article_requirements": "Professional and objective",
        "seo_keywords": [],
        "default_word_count": 800,
        "output_folder": "output_text",
        "image_source": "pexels",
        "image_count": 2,
        "image_model": "gemini-3.1-flash-image-preview",
        "template_name": "default"
    }

    @staticmethod
    def get_config_folder() -> Path:
        """获取配置文件夹路径"""
        possible_paths = [
            Path(__file__).parent.parent / "config",
            Path(__file__).parent / "config",
        ]
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path
        # 默认返回 config 目录
        return possible_paths[0]

    @staticmethod
    def list_configs() -> List[Dict[str, str]]:
        """列出所有可用的配置文件"""
        config_folder = Config.get_config_folder()
        configs = []

        if config_folder.exists():
            for file_path in config_folder.glob("*.json"):
                if file_path.name.startswith("__"):
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        configs.append({
                            "name": data.get("config_name", file_path.stem),
                            "file": file_path.name,
                            "path": str(file_path)
                        })
                except Exception:
                    pass

        # 如果没有配置文件，创建默认配置
        if not configs:
            config_folder.mkdir(parents=True, exist_ok=True)
            default_path = config_folder / "default.json"
            default_config = Config.DEFAULT_CONFIG.copy()
            with open(default_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            configs.append({
                "name": "Default",
                "file": "default.json",
                "path": str(default_path)
            })

        return configs

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为 None 则从 config 文件夹加载
        """
        if config_path is None:
            # 默认使用 config/default.json
            config_folder = self.get_config_folder()
            config_folder.mkdir(parents=True, exist_ok=True)
            default_config_path = config_folder / "default.json"

            # 如果 default.json 不存在，先创建
            if not default_config_path.exists():
                with open(default_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULT_CONFIG.copy(), f, indent=2, ensure_ascii=False)

            config_path = str(default_config_path)

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # 合并默认配置
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            # 文件不存在，使用默认配置
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    # 便捷方法
    @property
    def ai_provider(self) -> str:
        return self.get("ai_provider", "aihubmix")

    @property
    def model(self) -> str:
        return self.get("model", "gpt-4o-mini")

    @property
    def user_language(self) -> str:
        return self.get("user_language", "English")

    @property
    def text_language(self) -> str:
        return self.get("text_language", "auto")

    @property
    def background(self) -> str:
        return self.get("background", "")

    @property
    def article_requirements(self) -> str:
        return self.get("article_requirements", "Professional")

    @property
    def seo_keywords(self) -> List[str]:
        return self.get("seo_keywords", [])

    @property
    def default_word_count(self) -> int:
        return self.get("default_word_count", 800)

    @property
    def output_folder(self) -> str:
        return self.get("output_folder", "output_text")

    @property
    def image_source(self) -> str:
        """图片来源: pexels / unsplash / ai"""
        return self.get("image_source", "pexels")

    @property
    def image_count(self) -> int:
        """每篇文章图片数量"""
        return self.get("image_count", 2)

    @property
    def image_model(self) -> str:
        """AI 生成图片的模型"""
        return self.get("image_model", "gemini-3.1-flash-image-preview")

    @property
    def publish_to_wp(self) -> bool:
        """是否发布到 WordPress"""
        return self.get("publish_to_wp", True)

    @property
    def save_html_locally(self) -> bool:
        """是否保存 HTML 到本地"""
        return self.get("save_html_locally", True)

    @property
    def wp_site_url(self) -> str:
        """WordPress 站点 URL"""
        return self.get("wp_site_url", "")

    @property
    def wp_username(self) -> str:
        """WordPress 用户名"""
        return self.get("wp_username", "")

    @property
    def wp_password(self) -> str:
        """WordPress 应用密码"""
        return self.get("wp_password", "")

    @property
    def config_name(self) -> str:
        """配置名称"""
        return self.get("config_name", "Default")

    @property
    def template_name(self) -> str:
        """模板名称"""
        return self.get("template_name", "default")

    @staticmethod
    def list_templates() -> Dict[str, List[str]]:
        """列出所有可用的模板分类和组件"""
        template_dirs = [
            Path(__file__).parent.parent / "templates",
            Path(__file__).parent / "templates",
        ]

        templates = {}  # {category: [component1, component2, ...]}
        for template_dir in template_dirs:
            if template_dir.exists():
                # 遍历模板目录下的子目录（分类）
                for subdir in template_dir.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith("__"):
                        # 获取该分类下的所有组件（html文件）
                        components = []
                        for file in subdir.glob("*.html"):
                            if not file.name.startswith("__"):
                                components.append(file.stem)  # 文件名不含扩展名

                        if components:
                            templates[subdir.name] = components
                        else:
                            templates[subdir.name] = []
                break

        # 如果没有模板，添加默认选项
        if not templates:
            templates["default"] = []

        return templates

        return templates

    @property
    def output_path(self) -> Path:
        """获取输出目录的绝对路径"""
        base_dir = Path(__file__).parent
        output = base_dir / self.output_folder
        output.mkdir(parents=True, exist_ok=True)
        return output

    def display_config(self) -> None:
        """显示当前配置"""
        print("\n=== 当前配置 ===")
        print(f"Config Name: {self.config_name}")
        print(f"Template: {self.template_name}")
        print(f"AI Provider: {self.ai_provider}")
        print(f"Model: {self.model}")
        print(f"User Language: {self.user_language}")
        print(f"Text Language: {self.text_language}")
        print(f"Background: {self.background or '(未设置)'}")
        print(f"Article Requirements: {self.article_requirements}")
        print(f"SEO Keywords: {', '.join(self.seo_keywords) or '(未设置)'}")
        print(f"Default Word Count: {self.default_word_count}")
        print(f"Output Folder: {self.output_folder}")
        print(f"Image Source: {self.image_source}")
        print(f"Image Count: {self.image_count}")
        print(f"Image Model: {self.image_model}")
        print(f"Publish to WP: {self.publish_to_wp}")
        print(f"Save HTML Locally: {self.save_html_locally}")
        # 显示模板设置
        template_settings = self.get("template_settings", {})
        if template_settings.get("enabled"):
            components = template_settings.get("components", {})
            if components:
                for comp, pos in components.items():
                    print(f"  - {comp} (位置: {pos})")
        print(f"WP Site URL: {self.wp_site_url or '(未设置)'}")
        print(f"WP Username: {self.wp_username or '(未设置)'}")
        print("================\n")


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_path: str = None) -> Config:
    """
    获取配置实例（单例）

    Args:
        config_path: 配置文件路径，如果为 None 则从 config/default.json 加载

    Returns:
        Config 实例
    """
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = Config(config_path)
    return _config_instance


def reset_config() -> None:
    """重置配置实例，强制重新加载"""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # 测试
    config = Config()
    config.display_config()
