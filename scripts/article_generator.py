"""文章生成器 - 主逻辑模块"""
import os
from typing import Optional, List
from pathlib import Path
from .config import Config, get_config
from .ai_client import AIClient, get_ai_client
from .file_manager import FileManager, get_file_manager
from .image_service import ImageService, get_image_service
from .markdown_converter import MarkdownConverter, get_markdown_converter
from .wp_publisher import WPPublisher


class ArticleGenerator:
    """文章生成器类"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化文章生成器

        Args:
            config: 配置对象，如果为 None 则从默认配置加载
        """
        self.config = config or get_config()
        self.ai_client = get_ai_client(
            provider=self.config.ai_provider,
            model=self.config.model,
            user_language=self.config.user_language,
            text_language=self.config.text_language
        )
        self.file_manager = get_file_manager(self.config.output_folder)

    def generate_topics(self, topic: str) -> List[str]:
        """
        生成细分主题列表

        Args:
            topic: 用户输入的主题

        Returns:
            10 个细分主题列表
        """
        print(f"\n正在生成关于「{topic}」的细分主题...")
        topics = self.ai_client.generate_topics(
            topic,
            count=10,
            background=self.config.background
        )
        return topics

    def display_topics(self, topics: List[str]) -> int:
        """
        显示主题列表并获取用户选择

        Args:
            topics: 主题列表

        Returns:
            用户选择的主题索引（0-9）
        """
        print("\n" + "=" * 50)
        print("请选择你要生成的主题：")
        print("=" * 50)
        for i, topic in enumerate(topics, 1):
            print(f"  {i}. {topic}")
        print("=" * 50)

        while True:
            try:
                choice = input("\n请输入数字 (1-10): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(topics):
                    return idx
                else:
                    print("请输入 1-10 之间的数字")
            except ValueError:
                print("请输入有效的数字")

    def get_article_params(self, selected_topic: str) -> dict:
        """
        获取文章生成参数（可让用户修改）

        Args:
            selected_topic: 用户选择的主题

        Returns:
            包含所有生成参数的字典
        """
        print("\n" + "=" * 50)
        print("文章生成参数（直接回车使用默认值）")
        print("=" * 50)

        # 背景信息
        default_background = self.config.background
        background_input = input(f"背景信息 [{default_background}]: ").strip()
        background = background_input if background_input else default_background

        # SEO 关键词
        default_keywords = ", ".join(self.config.seo_keywords)
        keywords_input = input(f"SEO 关键词（逗号分隔） [{default_keywords}]: ").strip()
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        else:
            keywords = self.config.seo_keywords

        # 文章要求
        default_requirements = self.config.article_requirements
        requirements_input = input(f"文章要求 [{default_requirements}]: ").strip()
        requirements = requirements_input if requirements_input else default_requirements

        # 字数
        default_word_count = self.config.default_word_count
        word_count_input = input(f"文章长度（词数） [{default_word_count}]: ").strip()
        try:
            word_count = int(word_count_input) if word_count_input else default_word_count
        except ValueError:
            word_count = default_word_count

        print("=" * 50)

        return {
            "title": selected_topic,
            "background": background,
            "keywords": keywords,
            "requirements": requirements,
            "word_count": word_count,
            "user_language": self.config.user_language,
            "text_language": self.config.text_language
        }

    def generate_article(self, params: dict) -> str:
        """
        生成文章

        Args:
            params: 包含标题、背景、关键词等参数的字典

        Returns:
            Markdown 格式的文章内容
        """
        print("\n正在生成文章，请稍候...")

        article = self.ai_client.generate_markdown_article(
            title=params["title"],
            background=params["background"],
            keywords=params["keywords"],
            requirements=params["requirements"],
            word_count=params["word_count"]
        )

        return article

    def save_article(self, title: str, content: str) -> str:
        """
        保存文章到文件

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            保存的文件路径
        """
        file_path = self.file_manager.save_article(title, content)
        return str(file_path)

    def display_article(self, article: str) -> None:
        """
        显示文章内容

        Args:
            article: 文章内容
        """
        print("\n" + "=" * 60)
        print("生成的文章内容：")
        print("=" * 60)
        print(article)
        print("=" * 60)

    def review_and_regenerate(self, article: str, params: dict) -> tuple:
        """
        让用户审核文章，可选择修改或确认

        Args:
            article: 当前文章内容
            params: 当前使用的参数

        Returns:
            (确认完成标志, 新的文章内容或修改意见)
        """
        while True:
            print("\n请选择操作：")
            print("  1. 确认完成 - 文章没问题了")
            print("  2. 修改文章 - 输入修改意见重新生成")

            choice = input("\n请输入数字 (1/2): ").strip()

            if choice == "1":
                return True, None
            elif choice == "2":
                feedback = input("\n请输入修改意见：").strip()
                if feedback:
                    # 根据反馈更新参数或直接修改文章
                    params["feedback"] = feedback
                    return False, params
                else:
                    print("请输入有效的修改意见")
            else:
                print("请输入 1 或 2")

    def regenerate_article(self, params: dict) -> str:
        """
        根据修改意见重新生成文章

        Args:
            params: 包含修改意见的参数字典

        Returns:
            重新生成的文章内容
        """
        feedback = params.get("feedback", "")

        # 在提示中加入修改意见
        prompt = f"""请根据以下修改意见重新生成文章：

原始标题：{params["title"]}
修改意见：{feedback}
背景信息：{params["background"]}
SEO 关键词：{', '.join(params["keywords"])}
文章要求：{params["requirements"]}
目标字数：约 {params["word_count"]} 词
文章语言：{params.get("user_language", self.config.user_language)}

请直接返回修改后的完整 Markdown 文章："""

        print("\n正在根据修改意见重新生成文章...")

        article = self.ai_client.chat(
            prompt=prompt,
            temperature=0.7,
            max_tokens=params["word_count"] * 3
        )

        return article

    def run(self) -> None:
        """运行文章生成流程"""
        print("\n" + "=" * 60)
        print("欢迎使用 AI 文章生成器")
        print("=" * 60)

        # 显示当前配置
        self.config.display_config()

        # 1. 输入主题
        topic = input("请输入你想要写的主题：").strip()
        if not topic:
            print("主题不能为空")
            return

        # 2. 生成细分主题
        topics = self.generate_topics(topic)

        # 3. 选择主题
        selected_idx = self.display_topics(topics)
        selected_topic = topics[selected_idx]

        # 4. 获取/修改参数
        params = self.get_article_params(selected_topic)

        # 5. 生成第一版文章
        article = self.generate_article(params)

        # 6. 循环审核
        while True:
            # 显示文章
            self.display_article(article)

            # 审核
            is_confirmed, result = self.review_and_regenerate(article, params)

            if is_confirmed:
                break

            # 重新生成
            params = result
            article = self.regenerate_article(params)

        # 7. 保存文章
        file_path = self.save_article(selected_topic, article)
        print(f"\n✅ 文章已保存到: {file_path}")

        # 8. 图片处理流程
        self.handle_images(selected_topic, article, file_path)

    def handle_images(self, title: str, article_content: str, article_path: Path) -> None:
        """处理文章图片"""
        print("\n" + "=" * 50)
        print("开始处理图片")
        print("=" * 50)

        # 获取文章文件夹
        article_folder = article_path.parent
        assets_folder = article_folder / "assets"
        assets_folder.mkdir(exist_ok=True)

        # 询问图片来源
        print("\n请选择图片来源：")
        print("  1. Pexels (推荐)")
        print("  2. Unsplash")
        print("  3. AI 生成图片")
        print("  4. 自动选择 (先 Pexels → 失败则 Unsplash → 失败则 AI)")

        while True:
            choice = input("\n请输入数字 (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                break
            print("请输入 1-4 之间的数字")

        # 设置图片来源
        source_map = {"1": "pexels", "2": "unsplash", "3": "ai", "4": "auto"}
        image_source = source_map.get(choice, "pexels")

        # 初始化图片服务
        image_service = get_image_service(
            image_source=image_source if image_source != "auto" else "pexels",
            image_count=self.config.image_count,
            image_model=self.config.image_model
        )

        # 使用文章标题作为搜索关键词
        search_query = title

        # 搜索并下载图片
        print(f"\n正在搜索图片: {search_query}")
        images = image_service.search_and_download(search_query, assets_folder)

        if not images:
            print("未能获取图片")
            return

        print(f"\n获取到 {len(images)} 张图片")

        # 循环审查图片
        while True:
            print("\n已下载的图片：")
            for i, img in enumerate(images, 1):
                print(f"  {i}. {img['filename']} (来源: {img['source']})")

            print("\n请选择操作：")
            print("  1. 图片确认 - 继续插入图片")
            print("  2. 重新生成 - 输入新提示词重新生成图片")

            choice = input("\n请输入数字 (1/2): ").strip()

            if choice == "1":
                break
            elif choice == "2":
                if image_source == "ai" or image_source == "auto":
                    prompt = input("请输入图片提示词: ").strip()
                    if prompt:
                        # 重新生成图片
                        new_img = image_service.generate_image_from_prompt(prompt, assets_folder)
                        if new_img:
                            images = [new_img]
                else:
                    print("只有 AI 生成的图片支持重新生成")
            else:
                print("请输入 1 或 2")

        # 获取插入点
        print("\n正在分析文章，确定图片插入位置...")
        insert_points = self.ai_client.get_image_insert_points(article_content, images)
        print(f"插入点: {insert_points}")

        # 更新文章
        print("\n正在更新文章...")
        self.file_manager.update_article_with_images(article_path, insert_points)
        print("✅ 图片已插入文章")

        # WordPress 发布流程
        self.handle_wordpress_publishing(article_path, title)

    def handle_wordpress_publishing(self, article_path: Path, title: str) -> None:
        """处理 WordPress 发布流程"""
        print("\n" + "=" * 50)
        print("开始 WordPress 发布流程")
        print("=" * 50)

        # 获取文章文件夹
        article_folder = article_path.parent

        # 1. 获取 assets 文件夹中的图片
        assets_folder = article_folder / "assets"
        if not assets_folder.exists():
            print("没有找到图片，跳过发布流程")
            return

        # 收集图片列表
        image_files = []
        for img_path in assets_folder.glob("*"):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                image_files.append({
                    "filename": img_path.name,
                    "path": str(img_path)
                })

        if not image_files:
            print("没有找到图片，跳过发布流程")
            return

        print(f"\n找到 {len(image_files)} 张图片")

        # 2. 上传图片到 WordPress
        print("\n[1/3] 上传图片到 WordPress...")

        # 获取 WordPress 配置
        wp_site_url = os.getenv('WP_SITE_URL', '')
        wp_username = os.getenv('WP_USERNAME', '')
        wp_password = os.getenv('WP_PASSWORD', '')

        if not wp_site_url or not wp_username or not wp_password:
            print("警告: WordPress 配置未完整，跳过上传")
            print(f"  WP_SITE_URL: {'已设置' if wp_site_url else '未设置'}")
            print(f"  WP_USERNAME: {'已设置' if wp_username else '未设置'}")
            print(f"  WP_PASSWORD: {'已设置' if wp_password else '未设置'}")
            return

        # 创建 WordPress 发布器
        wp = WPPublisher(wp_site_url, wp_username, wp_password)

        # 批量上传图片
        image_url_map = wp.upload_images_batch(image_files)

        if not image_url_map:
            print("图片上传失败，跳过发布流程")
            return

        # 3. 读取 Markdown 并转换
        print("\n[2/3] 转换 Markdown 为 HTML...")

        # 读取原始 markdown 文件
        with open(article_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 转换 HTML
        converter = get_markdown_converter()
        html_content = converter.convert_to_html(markdown_content, image_url_map)

        # 4. 保存 HTML 文件
        print("\n[3/3] 保存 HTML 文件...")

        html_path = article_folder / "article.html"
        converter.save_html(html_content, html_path)
        print(f"✅ HTML 已保存到: {html_path}")

        # 5. 发布到 WordPress（如果配置允许）
        if self.config.publish_to_wp:
            print("\n发布文章到 WordPress...")

            # 询问用户发布状态
            print("\n请选择发布状态:")
            print("1. 草稿 (draft)")
            print("2. 发布 (publish)")

            status_choice = input("请输入数字 (1-2): ").strip()
            status = "draft" if status_choice == "1" else "publish"

            # 读取 HTML 内容作为文章内容
            post_result = wp.publish_post(
                title=title,
                content=html_content,
                status=status
            )

            if post_result.get("success"):
                print(f"✅ 文章已发布到 WordPress (ID: {post_result.get('post_id')})")
            else:
                print(f"❌ 发布失败: {post_result.get('error')}")
        else:
            print("\n跳过 WordPress 发布（配置已禁用）")

        print("\n✅ WordPress 发布流程完成")


def main():
    """主函数"""
    generator = ArticleGenerator()
    generator.run()


if __name__ == "__main__":
    main()
