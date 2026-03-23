"""文件管理模块"""
import re
from pathlib import Path
from typing import List, Dict


# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class FileManager:
    """文件管理类"""

    def __init__(self, output_folder: str = "output_text"):
        """
        初始化文件管理器

        Args:
            output_folder: 输出文件夹名称
        """
        self.base_dir = PROJECT_ROOT
        self.output_folder = self.base_dir / output_folder
        self._ensure_output_folder()

    def _ensure_output_folder(self) -> None:
        """确保输出文件夹存在"""
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, name: str) -> str:
        """
        清理文件名，移除非法字符

        Args:
            name: 原始名称

        Returns:
            清理后的名称
        """
        # 替换非法文件名字符
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        return name.strip()

    def create_article_folder(self, title: str) -> Path:
        """
        创建文章文件夹

        Args:
            title: 文章标题

        Returns:
            文件夹路径
        """
        from datetime import datetime
        # 创建日期前缀
        now = datetime.now()
        date_prefix = now.strftime("%d-%m-%y %H")
        folder_name = f"{date_prefix} {self.sanitize_filename(title)}"
        article_folder = self.output_folder / folder_name
        article_folder.mkdir(parents=True, exist_ok=True)
        return article_folder

    def save_markdown(
        self,
        folder: Path,
        filename: str,
        content: str
    ) -> Path:
        """
        保存 Markdown 文件

        Args:
            folder: 文件夹路径
            filename: 文件名（不含扩展名）
            content: Markdown 内容

        Returns:
            保存的文件路径
        """
        # 确保有 .md 扩展名
        if not filename.endswith('.md'):
            filename = filename + '.md'

        file_path = folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

    def save_article_info(
        self,
        folder: Path,
        title: str,
        h1_title: str = None,
        content: str = None,
        status: str = None,
        wp_post_id: int = None,
        wp_url: str = None,
        featured_image: str = None,
        seo_keywords: list = None
    ) -> Path:
        """保存文章信息为 JSON"""
        import json
        from datetime import datetime

        info = {
            "title": title,
            "h1_title": h1_title,
            "content_preview": content[:500] if content else None,
            "created_at": datetime.now().isoformat(),
            "status": status,
            "wp_post_id": wp_post_id,
            "wp_url": wp_url,
            "featured_image": featured_image,
            "seo_keywords": seo_keywords or []
        }

        info_path = folder / "article_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        return info_path

    def save_article(self, title: str, content: str, filename: str = "article.md") -> Path:
        """
        保存文章到文件夹

        Args:
            title: 文章标题（用于创建文件夹）
            content: 文章内容
            filename: 文件名，默认 article.md

        Returns:
            保存的文件路径
        """
        folder = self.create_article_folder(title)
        return self.save_markdown(folder, filename, content)

    def get_output_path(self) -> Path:
        """获取输出路径"""
        return self.output_folder

    def list_articles(self) -> list:
        """
        列出所有已生成的文章

        Returns:
            文章文件夹列表
        """
        if not self.output_folder.exists():
            return []

        articles = []
        for item in self.output_folder.iterdir():
            if item.is_dir():
                # 查找 article.md 文件
                article_file = item / "article.md"
                if article_file.exists():
                    articles.append({
                        "title": item.name,
                        "path": str(article_file)
                    })
        return articles

    def update_article_with_images(
        self,
        article_path: Path,
        insert_points: List[Dict]
    ) -> str:
        """
        更新文章，插入图片

        Args:
            article_path: 文章文件路径
            insert_points: 插入点列表 [{"image": "xxx.jpg", "insert_after": "原文片段"}, ...]

        Returns:
            更新后的文章内容
        """
        # 读取文章内容
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 按插入点位置排序（从后往前插入，避免位置偏移）
        insert_points = sorted(insert_points, key=lambda x: x.get('insert_after', ''), reverse=True)

        # 执行插入
        for point in insert_points:
            image_file = point.get('image', '')
            anchor = point.get('insert_after', '')

            if not anchor:
                continue

            # 构建 Markdown 图片语法
            relative_path = f"./assets/{image_file}"
            image_markdown = f"\n![{image_file}]({relative_path})\n"

            # 查找锚点位置
            pos = content.find(anchor)
            if pos != -1:
                # 在锚点后插入图片
                insert_pos = pos + len(anchor)
                content = content[:insert_pos] + image_markdown + content[insert_pos:]
            else:
                # 锚点未找到，打印警告
                print(f"警告: 未找到插入点锚点: {anchor[:30]}...")

        # 保存更新后的文章
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content


def get_file_manager(output_folder: str = "output_text") -> FileManager:
    """
    获取 FileManager 实例

    Args:
        output_folder: 输出文件夹名称

    Returns:
        FileManager 实例
    """
    return FileManager(output_folder)


if __name__ == "__main__":
    # 测试
    fm = FileManager()
    print(f"输出路径: {fm.get_output_path()}")

    # 测试保存文章
    test_content = """# 测试文章

这是测试内容。

## 第一章
内容...
"""
    path = fm.save_article("测试文章标题", test_content)
    print(f"保存路径: {path}")
