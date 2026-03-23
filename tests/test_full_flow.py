"""完整流程测试 - 生成文章并配图，转换 HTML 并发布到 WordPress"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ai_client import AIClient
from scripts.config import get_config
from scripts.file_manager import FileManager
from scripts.image_service import get_image_service
from scripts.markdown_converter import get_markdown_converter
from scripts.wp_publisher import WPPublisher


def run_full_flow(topic: str = None, title: str = None, word_count: int = 300):
    """运行完整流程"""
    # 1. 生成文章
    print("\n[1/4] 生成文章...")

    if not topic:
        topic = input("请输入主题: ").strip()
    if not topic:
        topic = "Python 编程入门"

    if not title:
        title = topic

    ai = AIClient(provider='aihubmix', model='gpt-4o-mini')

    # 先生成细分主题
    print(f"正在生成关于「{topic}」的细分主题...")
    topics = ai.generate_topics(topic, count=5)

    print("\n请选择要生成的主题：")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t}")

    while True:
        try:
            choice = input("\n请输入数字 (1-5): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(topics):
                selected_title = topics[idx]
                break
        except:
            pass
        print("请输入 1-5 之间的数字")

    # 获取文章参数
    print("\n文章生成参数（直接回车使用默认值）：")

    default_background = "我们是一家教育科技公司"
    background = input(f"背景信息 [{default_background}]: ").strip() or default_background

    default_keywords = "Python, 编程, 入门"
    keywords_input = input(f"SEO 关键词（逗号分隔） [{default_keywords}]: ").strip() or default_keywords
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

    default_requirements = "简洁易懂，适合初学者"
    requirements = input(f"文章要求 [{default_requirements}]: ").strip() or default_requirements

    wc_input = input(f"文章长度（词数） [{word_count}]: ").strip()
    try:
        word_count = int(wc_input) if wc_input else word_count
    except:
        pass

    print(f"\n正在生成文章，请稍候...")
    article = ai.generate_markdown_article(
        title=selected_title,
        background=background,
        keywords=keywords,
        requirements=requirements,
        word_count=word_count
    )
    print(f"文章长度: {len(article)} 字符")

    # 2. 显示文章让用户审核
    print("\n" + "=" * 60)
    print("生成的文章内容：")
    print("=" * 60)
    print(article)

    while True:
        print("\n请选择操作：")
        print("  1. 确认完成 - 文章没问题了")
        print("  2. 修改文章 - 输入修改意见重新生成")

        choice = input("\n请输入数字 (1/2): ").strip()

        if choice == "1":
            break
        elif choice == "2":
            feedback = input("请输入修改意见：").strip()
            if feedback:
                print("\n正在根据修改意见重新生成...")
                article = ai.chat(f"请根据以下修改意见重新生成文章：\n{feedback}\n\n原始标题：{selected_title}\n目标字数：约 {word_count} 词\n\n请直接返回修改后的完整 Markdown 文章：")
                print("\n" + "=" * 60)
                print("重新生成的文章内容：")
                print("=" * 60)
                print(article)

    # 3. 保存文章
    print("\n[2/4] 保存文章...")
    file_manager = FileManager()
    article_path = file_manager.save_article(selected_title, article)
    print(f"文章保存到: {article_path}")

    # 4. 获取图片
    print("\n[3/4] 获取图片...")
    article_folder = article_path.parent
    assets_folder = article_folder / "assets"
    assets_folder.mkdir(exist_ok=True)

    # 选择图片来源
    print("\n请选择图片来源：")
    print("  1. Pexels (推荐)")
    print("  2. Unsplash")
    print("  3. AI 生成图片")

    while True:
        choice = input("\n请输入数字 (1-3): ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("请输入 1-3 之间的数字")

    source_map = {"1": "pexels", "2": "unsplash", "3": "ai"}
    image_source = source_map.get(choice, "pexels")

    image_service = get_image_service(
        image_source=image_source,
        image_count=2
    )

    # 使用文章标题作为搜索关键词
    images = image_service.search_and_download(selected_title, assets_folder)
    print(f"获取到 {len(images)} 张图片")

    if not images:
        print("未能获取图片")
        return

    # 5. 审查图片
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
            if image_source == "ai":
                prompt = input("请输入图片提示词: ").strip()
                if prompt:
                    new_img = image_service.generate_image_from_prompt(prompt, assets_folder)
                    if new_img:
                        images = [new_img]
            else:
                print("只有 AI 生成的图片支持重新生成")

    # 6. 插入图片
    print("\n[4/4] 插入图片...")
    insert_points = ai.get_image_insert_points(article, images)
    print(f"插入点: {insert_points}")

    file_manager.update_article_with_images(article_path, insert_points)

    # 7. WordPress 发布流程
    print("\n" + "=" * 60)
    print("开始 WordPress 发布流程")
    print("=" * 60)

    # 收集图片列表
    image_files = []
    for img_path in assets_folder.glob("*"):
        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            image_files.append({
                "filename": img_path.name,
                "path": str(img_path)
            })

    if image_files:
        print(f"\n找到 {len(image_files)} 张图片")

        # 获取 WordPress 配置
        config = get_config("scripts/config.json")
        wp_site_url = config.wp_site_url or os.getenv('WP_SITE_URL', '')
        wp_username = config.wp_username or os.getenv('WP_USERNAME', '')
        wp_password = config.wp_password or os.getenv('WP_PASSWORD', '')

        if wp_site_url and wp_username and wp_password:
            # 7.1 上传图片到 WordPress
            print("\n[5/6] 上传图片到 WordPress...")
            wp = WPPublisher(wp_site_url, wp_username, wp_password)
            image_url_map = wp.upload_images_batch(image_files)

            if image_url_map:
                # 7.2 转换 Markdown 为 HTML
                print("\n[6/6] 转换 Markdown 为 HTML...")

                # 读取原始 markdown 文件
                with open(article_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # 转换 HTML - 提取 URL 映射
                simple_url_map = {k: v.get("url", "") for k, v in image_url_map.items()}
                converter = get_markdown_converter()
                html_content = converter.convert_to_html(markdown_content, simple_url_map)

                # 保存 HTML 文件
                html_path = article_folder / "article.html"
                converter.save_html(html_content, html_path)
                print(f"✅ HTML 已保存到: {html_path}")

                # 7.3 发布到 WordPress
                print("\n发布文章到 WordPress...")

                # 获取第一张图片作为封面图
                first_image = list(image_url_map.values())[0]
                featured_media = first_image.get("media_id", 0) if first_image else 0
                print(f"设置封面图 ID: {featured_media}")

                # 询问用户发布状态
                print("\n请选择发布状态:")
                print("1. 草稿 (draft)")
                print("2. 发布 (publish)")

                status_choice = input("请输入数字 (1-2): ").strip()
                status = "draft" if status_choice == "1" else "publish"

                post_result = wp.publish_post(
                    title=selected_title,
                    content=html_content,
                    status=status,
                    featured_media=featured_media
                )

                if post_result.get("success"):
                    print(f"✅ 文章已发布到 WordPress (ID: {post_result.get('post_id')})")
                else:
                    print(f"❌ 发布失败: {post_result.get('error')}")
            else:
                print("图片上传失败，跳过发布")
        else:
            print("WordPress 配置未完整，跳过发布")
            print(f"  WP_SITE_URL: {'已设置' if wp_site_url else '未设置'}")
            print(f"  WP_USERNAME: {'已设置' if wp_username else '未设置'}")
            print(f"  WP_PASSWORD: {'已设置' if wp_password else '未设置'}")
    else:
        print("没有找到图片，跳过发布流程")

    print("\n" + "=" * 60)
    print("完整流程测试完成!")
    print(f"输出目录: {article_folder}")
    print("=" * 60)


def main():
    print("=" * 60)
    print("完整流程测试：生成文章 + 配图")
    print("=" * 60)

    print("\n请选择测试模式：")
    print("  1. 手动输入 - 交互式完整流程")
    print("  2. 默认测试 - 自动运行")

    choice = None
    while choice not in ["1", "2"]:
        try:
            choice = input("\n请输入数字 (1/2): ").strip()
        except EOFError:
            choice = "1"
            print("1 (默认)")

    if choice == "1":
        run_full_flow()
    else:
        # 默认测试
        run_full_flow(
            topic="Python 编程入门",
            title="Python 零基础入门指南",
            word_count=300
        )


if __name__ == "__main__":
    main()
