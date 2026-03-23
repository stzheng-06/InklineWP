"""WordPress AI 文章生成与发布工具"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.ai_client import AIClient
from scripts.config import get_config, Config
from scripts.file_manager import FileManager
from scripts.image_service import get_image_service
from scripts.markdown_converter import get_markdown_converter
from scripts.wp_publisher import WPPublisher


def create_new_config(existing_configs):
    """创建新配置文件"""
    print("\n=== 创建新配置 ===")

    # 获取配置名称
    while True:
        config_name = input("请输入新配置名称: ").strip()
        if config_name:
            # 检查名称是否已存在
            if any(c['name'].lower() == config_name.lower() for c in existing_configs):
                print("该名称已存在，请使用其他名称")
            else:
                break
        else:
            print("名称不能为空")

    # 获取 WordPress 配置
    print("\n--- WordPress 配置 ---")
    while True:
        wp_site_url = input("WordPress 站点 URL (例如 https://example.com): ").strip()
        if wp_site_url:
            # 验证 URL 格式
            if wp_site_url.startswith("http://") or wp_site_url.startswith("https://"):
                break
            else:
                print("URL 必须以 http:// 或 https:// 开头")
        else:
            print("URL 不能为空")

    wp_username = input("WordPress 用户名: ").strip()
    while not wp_username:
        print("用户名不能为空")
        wp_username = input("WordPress 用户名: ").strip()

    wp_password = input("WordPress 应用密码: ").strip()
    while not wp_password:
        print("应用密码不能为空")
        wp_password = input("WordPress 应用密码: ").strip()

    # 创建新配置
    config_folder = Config.get_config_folder()
    config_folder.mkdir(parents=True, exist_ok=True)

    # 基于默认配置创建
    new_config = Config.DEFAULT_CONFIG.copy()
    new_config['config_name'] = config_name
    new_config['wp_site_url'] = wp_site_url
    new_config['wp_username'] = wp_username
    new_config['wp_password'] = wp_password

    # 生成文件名
    filename = f"{config_name.lower().replace(' ', '_')}.json"
    config_path = config_folder / filename

    # 保存配置
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)

    print(f"\n配置已创建: {config_path}")
    return get_config(str(config_path))


def manage_configs(configs):
    """管理配置文件 - 删除或重命名"""
    print("\n=== 管理配置 ===")

    if not configs:
        print("没有可管理的配置")
        return

    print("请选择要管理的配置:")
    for i, cfg in enumerate(configs, 1):
        print(f"  {i}. {cfg['name']}")
    print("  0. 返回")

    while True:
        try:
            choice = input("\n请输入数字: ").strip()
            idx = int(choice)
            if idx == 0:
                break
            elif 1 <= idx <= len(configs):
                selected = configs[idx - 1]
                print(f"\n已选择: {selected['name']}")
                print("  1. 重命名")
                print("  2. 删除")
                print("  0. 返回")

                action = input("请输入数字: ").strip()
                if action == '1':
                    # 重命名
                    new_name = input("请输入新名称: ").strip()
                    if new_name:
                        import json
                        with open(selected['path'], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        data['config_name'] = new_name
                        with open(selected['path'], 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"已重命名为: {new_name}")
                elif action == '2':
                    # 删除
                    confirm = input(f"确定要删除配置 '{selected['name']}' 吗? (y/n): ").strip().lower()
                    if confirm == 'y':
                        os.remove(selected['path'])
                        print("配置已删除")
                break
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效的数字")


def edit_config(config):
    """允许用户修改配置"""
    # 获取模板设置
    template_settings = config.get("template_settings", {"enabled": False, "components": {}})

    # 获取可用模板
    templates = Config.list_templates()

    print("\n=== 当前配置 ===")
    print(f"0. Template: {config.template_name}")
    if template_settings.get("enabled"):
        components = template_settings.get("components", {})
        if components:
            for comp, pos in components.items():
                print(f"   - {comp} ({pos})")
    print(f"1. AI Provider: {config.ai_provider}")
    print(f"2. Model: {config.model}")
    print(f"3. Text Language: {config.text_language}")
    print(f"4. Background: {config.background[:50]}..." if len(config.background) > 50 else f"4. Background: {config.background}")
    print(f"5. Article Requirements: {config.article_requirements}")
    print(f"6. SEO Keywords: {', '.join(config.seo_keywords)}")
    print(f"7. Word Count: {config.default_word_count}")
    print(f"8. Image Source: {config.image_source}")
    print(f"9. Image Count: {config.image_count}")
    print(f"10. Publish to WP: {config.publish_to_wp}")
    print("================")

    print("\n请输入要修改的配置编号（直接回车跳过）:")

    while True:
        choice = input("编号: ").strip()
        if not choice:
            break

        if choice == "0":
            # 选择模板 - 先选分类，再选组件
            print("\n=== 选择模板 ===")
            categories = list(templates.keys())
            print(f"可用分类 ({len(categories)}个):")
            for i, cat in enumerate(categories, 1):
                comps = templates.get(cat, [])
                print(f"  {i}. {cat} ({len(comps)}个组件)")

            cat_choice = input("\n选择分类编号: ").strip()
            if not cat_choice:
                continue

            try:
                idx = int(cat_choice) - 1
                if 0 <= idx < len(categories):
                    selected_category = categories[idx]
                    config.set("template_name", selected_category)
                    print(f"已选择分类: {selected_category}")

                    # 选择该分类下的组件
                    components = templates.get(selected_category, [])
                    if components:
                        print(f"\n{selected_category} 分类下的可用组件:")
                        for i, comp in enumerate(components, 1):
                            print(f"  {i}. {comp}")

                        # 询问是否启用模板组件
                        enable = input("\n是否启用模板组件? (y/n): ").strip().lower()
                        if enable == 'y':
                            comp_choice = input("选择组件编号 (直接回车不添加组件): ").strip()
                            if comp_choice:
                                try:
                                    comp_idx = int(comp_choice) - 1
                                    if 0 <= comp_idx < len(components):
                                        selected_comp = components[comp_idx]
                                        pos = input("位置 (start/end，直接回车放末尾): ").strip() or "end"
                                        config.set("template_settings", {
                                            "enabled": True,
                                            "components": {selected_comp: pos}
                                        })
                                        print(f"✅ 已选择组件: {selected_comp} (位置: {pos})")
                                except ValueError:
                                    print("❌ 输入无效")
                        else:
                            config.set("template_settings", {"enabled": False, "components": {}})
                    else:
                        print(f"分类 {selected_category} 下没有可用组件")
                else:
                    print("❌ 无效的选择")
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "1":
            config.set("ai_provider", input("AI Provider (aihubmix/openai): ").strip() or "aihubmix")
        elif choice == "2":
            config.set("model", input("Model: ").strip() or "gpt-4o-mini")
        elif choice == "3":
            config.set("text_language", input("Text Language (Spanish/English/cn): ").strip() or "Spanish")
        elif choice == "4":
            config.set("background", input("Background: ").strip())
        elif choice == "5":
            config.set("article_requirements", input("Article Requirements: ").strip())
        elif choice == "6":
            keywords = input("SEO Keywords (逗号分隔): ").strip()
            config.set("seo_keywords", [k.strip() for k in keywords.split(",") if k.strip()])
        elif choice == "7":
            try:
                wc = int(input("Word Count: ").strip())
                config.set("default_word_count", wc)
            except:
                pass
        elif choice == "8":
            config.set("image_source", input("Image Source (pexels/unsplash/ai): ").strip() or "pexels")
        elif choice == "9":
            try:
                ic = int(input("Image Count: ").strip())
                config.set("image_count", ic)
            except:
                pass
        elif choice == "10":
            pub = input("Publish to WP (true/false): ").strip().lower()
            config.set("publish_to_wp", pub == "true")

        more = input("继续修改? (y/n): ").strip().lower()
        if more != 'y':
            break

    config.save()
    print("配置已保存")


def run_full_flow(topic: str = None, title: str = None, word_count: int = 800):
    """运行完整流程"""
    # 加载配置
    config = get_config()

    # 1. 生成文章
    print("\n[1/6] 生成文章...")

    if not topic:
        topic = input("请输入主题: ").strip()
    if not topic:
        topic = "Python 编程入门"

    if not title:
        title = topic

    ai = AIClient(provider=config.ai_provider, model=config.model, text_language=config.text_language)

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

    # 询问是否需要重新生成更详细的标题
    print(f"\n当前标题: {selected_title}")
    print("是否需要生成更详细/具体的标题?")
    print("  1. 使用当前标题")
    print("  2. 重新生成详细标题")
    print("  3. 手动输入标题")
    regen_choice = input("请输入数字 (1/2/3，直接回车选1): ").strip()
    if regen_choice == '2':
        print(f"\n正在为「{topic}」生成更详细的标题...")
        # 使用 generate_topics 获取更详细的标题选项
        detailed_titles = ai.generate_topics(topic, count=3)
        if detailed_titles:
            print("\n请选择详细标题：")
            for i, t in enumerate(detailed_titles, 1):
                print(f"  {i}. {t}")
            while True:
                try:
                    choice = input("\n请输入数字 (1-3，直接回车使用原标题): ").strip()
                    if not choice:
                        break
                    idx = int(choice) - 1
                    if 0 <= idx < len(detailed_titles):
                        selected_title = detailed_titles[idx]
                        break
                except:
                    pass
                print("请输入 1-3 之间的数字")
    elif regen_choice == '3':
        custom_title = input("请输入自定义标题: ").strip()
        if custom_title:
            selected_title = custom_title
    print(f"\n最终标题: {selected_title}")

    # 获取文章参数
    print("\n文章生成参数（直接回车使用默认值）：")

    default_background = config.background or "我们是一家教育科技公司"
    background = input(f"背景信息 [{default_background}]: ").strip() or default_background

    keywords = config.seo_keywords
    if keywords:
        keywords_str = ", ".join(keywords)
    else:
        keywords_str = "Python, 编程, 入门"
    keywords_input = input(f"SEO 关键词（逗号分隔） [{keywords_str}]: ").strip()
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    else:
        keywords = keywords

    default_requirements = config.article_requirements or "简洁易懂"
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
    print("\n[2/6] 保存文章...")

    # 提取 H1 标题
    import re
    h1_match = re.search(r'^#\s+(.+)$', article, re.MULTILINE)
    h1_title = h1_match.group(1).strip() if h1_match else selected_title
    print(f"H1 标题: {h1_title}")

    file_manager = FileManager()
    article_path = file_manager.save_article(selected_title, article)
    print(f"文章保存到: {article_path}")

    # 保存文章信息
    article_folder = article_path.parent
    file_manager.save_article_info(
        folder=article_folder,
        title=selected_title,
        h1_title=h1_title,
        content=article,
        seo_keywords=keywords
    )

    # 4. 获取图片
    print("\n[3/6] 获取图片...")
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
        image_count=config.image_count
    )

    # 使用文章标题作为搜索关键词
    images = image_service.search_and_download(selected_title, assets_folder)
    print(f"获取到 {len(images)} 张图片")

    if not images:
        print("未能获取图片")
        continue_choice = input("是否继续（无图片）? (y/n): ").strip().lower()
        if continue_choice != 'y':
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
    print("\n[4/6] 插入图片...")
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
        wp_site_url = config.wp_site_url
        wp_username = config.wp_username
        wp_password = config.wp_password

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
                converter = get_markdown_converter(template_name=config.template_name)
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

                # 读取 markdown 获取 H1 标题作为 WP 文章标题
                with open(article_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                h1_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
                wp_title = h1_match.group(1).strip() if h1_match else selected_title
                print(f"WordPress 文章标题: {wp_title}")

                post_result = wp.publish_post(
                    title=wp_title,
                    content=html_content,
                    status=status,
                    featured_media=featured_media
                )

                if post_result.get("success"):
                    print(f"✅ 文章已发布到 WordPress (ID: {post_result.get('post_id')})")
                    # 更新文章信息
                    file_manager.save_article_info(
                        folder=article_folder,
                        title=selected_title,
                        h1_title=wp_title,
                        content=md_content,
                        status=status,
                        wp_post_id=post_result.get("post_id"),
                        wp_url=f"{config.wp_site_url}/?p={post_result.get('post_id')}",
                        featured_image=first_image.get("url", "") if first_image else None,
                        seo_keywords=config.seo_keywords
                    )
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
    print("完整流程完成!")
    print(f"输出目录: {article_folder}")
    print("=" * 60)


def get_existing_articles(output_folder: str = "output_text"):
    """获取已存在的文章列表"""
    from pathlib import Path
    output_path = Path(output_folder)
    if not output_path.exists():
        return []

    articles = []
    for folder in output_path.iterdir():
        if folder.is_dir():
            article_file = folder / "article.md"
            if article_file.exists():
                articles.append({
                    "title": folder.name,
                    "path": folder,
                    "article_path": article_file
                })

    # 按修改时间排序
    articles.sort(key=lambda x: x["path"].stat().st_mtime, reverse=True)
    return articles


def run_publish_flow():
    """仅发布流程 - 选择已有文章发布到 WordPress"""
    config = get_config()

    # 检查 WordPress 配置
    if not config.wp_site_url or not config.wp_username or not config.wp_password:
        print("\n❌ WordPress 配置不完整，请先在配置中设置 WP Site URL、用户名和密码")
        return

    # 获取已存在的文章
    articles = get_existing_articles(config.output_folder)

    if not articles:
        print("\n没有找到已生成的文章，请先创建新文章")
        return

    print("\n=== 请选择要发布的文章 ===")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['title']}")

    while True:
        try:
            choice = input("\n请输入数字: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(articles):
                selected = articles[idx]
                break
        except:
            pass
        print("无效输入")

    article_folder = selected["path"]
    article_path = selected["article_path"]
    selected_title = selected["title"]

    print(f"\n已选择文章: {selected_title}")
    print(f"文章路径: {article_path}")

    # 1. 检查/转换 HTML
    html_path = article_folder / "article.html"
    markdown_content = None
    image_url_map = {}  # 初始化为空

    if html_path.exists():
        print(f"\n✅ HTML 文件已存在: {html_path}")
        # 读取 HTML 内容用于发布
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        print(f"\n⚠️ HTML 文件不存在，正在从 Markdown 转换...")
        # 读取 Markdown
        with open(article_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 获取图片信息
        assets_folder = article_folder / "assets"
        image_files = []
        if assets_folder.exists():
            for img_path in assets_folder.glob("*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    image_files.append({
                        "filename": img_path.name,
                        "path": str(img_path)
                    })

        # 如果有图片，先上传获取 URL（只需要上传一次）
        if image_files:
            print(f"\n找到 {len(image_files)} 张图片，正在上传到 WordPress...")
            wp = WPPublisher(config.wp_site_url, config.wp_username, config.wp_password)
            image_url_map = wp.upload_images_batch(image_files)
            print(f"✅ 图片上传完成")

        # 转换 HTML
        simple_url_map = {k: v.get("url", "") for k, v in image_url_map.items()}
        converter = get_markdown_converter(template_name=config.template_name)
        html_content = converter.convert_to_html(markdown_content, simple_url_map)

        # 保存 HTML
        converter.save_html(html_content, html_path)
        print(f"✅ HTML 已保存到: {html_path}")

    # 3. 提取 H1 标题
    with open(article_path, 'r', encoding='utf-8') as f:
        markdown_for_title = f.read()
    h1_match = re.search(r'^#\s+(.+)$', markdown_for_title, re.MULTILINE)
    wp_title = h1_match.group(1).strip() if h1_match else selected_title
    print(f"\nWordPress 文章标题: {wp_title}")

    # 4. 选择发布状态
    print("\n请选择发布状态:")
    print("  1. 草稿 (draft)")
    print("  2. 发布 (publish)")

    status_choice = input("请输入数字 (1-2): ").strip()
    status = "draft" if status_choice == "1" else "publish"

    # 5. 发布文章
    first_image = list(image_url_map.values())[0] if image_url_map else {}
    featured_media = first_image.get("media_id", 0) if first_image else 0

    print(f"\n正在发布文章...")
    wp = WPPublisher(config.wp_site_url, config.wp_username, config.wp_password)
    post_result = wp.publish_post(
        title=wp_title,
        content=html_content,
        status=status,
        featured_media=featured_media
    )

    if post_result:
        print(f"\n{'='*60}")
        print(f"✅ 文章发布成功!")
        print(f"{'='*60}")
        if isinstance(post_result, dict):
            print(f"文章 ID: {post_result.get('id', 'N/A')}")
            print(f"文章链接: {post_result.get('link', 'N/A')}")

            # 保存发布信息到 article_info.json
            file_manager = FileManager()
            file_manager.save_article_info(
                folder=article_folder,
                title=selected_title,
                h1_title=wp_title,
                status=status,
                wp_post_id=post_result.get('id'),
                wp_url=post_result.get('link')
            )
    else:
        print("\n❌ 文章发布失败")


def run_image_only_flow():
    """仅配图流程 - 使用已有文章"""
    config = get_config()

    # 获取已存在的文章
    articles = get_existing_articles(config.output_folder)

    if not articles:
        print("\n没有找到已生成的文章，请先创建新文章")
        return

    print("\n=== 请选择文章 ===")
    for i, article in enumerate(articles, 1):
        print(f"  {i}. {article['title']}")

    while True:
        try:
            choice = input("\n请输入数字: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(articles):
                selected = articles[idx]
                break
        except:
            pass
        print("无效输入")

    article_path = selected["article_path"]
    selected_title = selected["title"]
    article_folder = selected["path"]

    print(f"\n已选择文章: {selected_title}")

    # 继续配图流程
    run_image_flow(config, selected_title, article_path, article_folder)


def run_image_flow(config, selected_title, article_path, article_folder):
    """图片流程 - 配图和发布"""
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
        image_count=config.image_count
    )

    # 使用文章标题作为搜索关键词
    images = image_service.search_and_download(selected_title, assets_folder)
    print(f"获取到 {len(images)} 张图片")

    if not images:
        print("未能获取图片")
        continue_choice = input("是否继续（无图片）? (y/n): ").strip().lower()
        if continue_choice != 'y':
            return

    # 审查图片
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

    # 插入图片
    print("\n[4/6] 插入图片...")

    # 读取文章
    with open(article_path, 'r', encoding='utf-8') as f:
        article_content = f.read()

    ai = AIClient(provider=config.ai_provider, model=config.model, text_language=config.text_language)
    insert_points = ai.get_image_insert_points(article_content, images)
    print(f"插入点: {insert_points}")

    file_manager = FileManager()
    file_manager.update_article_with_images(article_path, insert_points)

    # WordPress 发布流程
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

        wp_site_url = config.wp_site_url
        wp_username = config.wp_username
        wp_password = config.wp_password

        if wp_site_url and wp_username and wp_password:
            print("\n[5/6] 上传图片到 WordPress...")
            wp = WPPublisher(wp_site_url, wp_username, wp_password)
            image_url_map = wp.upload_images_batch(image_files)

            if image_url_map:
                print("\n[6/6] 转换 Markdown 为 HTML...")

                with open(article_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                simple_url_map = {k: v.get("url", "") for k, v in image_url_map.items()}
                converter = get_markdown_converter(template_name=config.template_name)
                html_content = converter.convert_to_html(markdown_content, simple_url_map)

                html_path = article_folder / "article.html"
                converter.save_html(html_content, html_path)
                print(f"✅ HTML 已保存到: {html_path}")

                print("\n发布文章到 WordPress...")

                first_image = list(image_url_map.values())[0]
                featured_media = first_image.get("media_id", 0) if first_image else 0
                print(f"设置封面图 ID: {featured_media}")

                print("\n请选择发布状态:")
                print("1. 草稿 (draft)")
                print("2. 发布 (publish)")

                status_choice = input("请输入数字 (1-2): ").strip()
                status = "draft" if status_choice == "1" else "publish"

                # 提取 H1 标题作为 WP 文章标题
                h1_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
                wp_title = h1_match.group(1).strip() if h1_match else selected_title
                print(f"WordPress 文章标题: {wp_title}")

                post_result = wp.publish_post(
                    title=wp_title,
                    content=html_content,
                    status=status,
                    featured_media=featured_media
                )

                if post_result.get("success"):
                    print(f"✅ 文章已发布到 WordPress (ID: {post_result.get('post_id')})")
                    # 更新文章信息
                    file_manager.save_article_info(
                        folder=article_folder,
                        title=selected_title,
                        h1_title=wp_title,
                        content=markdown_content,
                        status=status,
                        wp_post_id=post_result.get("post_id"),
                        wp_url=f"{config.wp_site_url}/?p={post_result.get('post_id')}",
                        featured_image=first_image.get("url", "") if first_image else None,
                        seo_keywords=config.seo_keywords
                    )
                else:
                    print(f"❌ 发布失败: {post_result.get('error')}")
            else:
                print("图片上传失败，跳过发布")
        else:
            print("WordPress 配置未完整，跳过发布")
    else:
        print("没有找到图片，跳过发布流程")

    print("\n" + "=" * 60)
    print("配图流程完成!")
    print(f"输出目录: {article_folder}")
    print("=" * 60)


def main():
    from scripts.config import Config, reset_config

    print("=" * 60)
    print("WordPress AI 文章生成与发布工具")
    print("=" * 60)

    # 1. 显示可用的配置文件
    print("\n请选择配置文件:")
    configs = Config.list_configs()

    # 显示默认配置选项
    for i, cfg in enumerate(configs, 1):
        print(f"  {i}. {cfg['name']}")
    print(f"  {len(configs) + 1}. 创建新配置")
    print(f"  {len(configs) + 2}. 管理配置 (删除/重命名)")

    while True:
        try:
            choice = input("\n请输入数字: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(configs):
                # 选择现有配置
                selected_config = configs[idx]
                config = get_config(selected_config['path'])
                break
            elif idx == len(configs):
                # 创建新配置
                config = create_new_config(configs)
                break
            elif idx == len(configs) + 1:
                # 管理配置
                manage_configs(configs)
                configs = Config.list_configs()
                print("\n请重新选择配置文件:")
                for i, cfg in enumerate(configs, 1):
                    print(f"  {i}. {cfg['name']}")
                print(f"  {len(configs) + 1}. 创建新配置")
                print(f"  {len(configs) + 2}. 管理配置")
            else:
                print("无效选择，请重新输入")
        except ValueError:
            print("请输入有效的数字")

    # 2. 显示当前配置详情
    print("\n" + "=" * 60)
    print(f"当前配置: {config.get('config_name', '未命名')}")
    print("=" * 60)
    config.display_config()

    # 3. 询问是否修改配置
    print("\n是否需要修改配置? (直接回车使用当前配置)")
    modify = input("输入 y 修改配置: ").strip().lower()
    if modify == 'y':
        edit_config(config)
        # 重新加载配置
        reset_config()
        config = get_config(config.config_path)

    # 显示已存在的文章
    existing_articles = get_existing_articles(config.output_folder)
    if existing_articles:
        print(f"\n发现 {len(existing_articles)} 篇已生成的文章")

    print("\n请选择操作：")
    print("  1. 完整流程 - 生成新文章 + 配图 + 发布")
    if existing_articles:
        print("  2. 配图流程 - 选择已有文章重新配图")
        print("  3. 发布流程 - 选择已有文章直接发布 (检查/转换HTML)")
        print("  4. 测试 WordPress 连接")
    else:
        print("  2. 测试 WordPress 连接")

    choice = input("\n请输入数字: ").strip()

    if choice == "1":
        run_full_flow()
    elif choice == "2" and existing_articles:
        run_image_only_flow()
    elif choice == "3" and existing_articles:
        run_publish_flow()
    elif (choice == "2" and not existing_articles) or choice == "4":
        # 测试 WordPress 连接
        wp = WPPublisher(
            site_url=config.wp_site_url,
            username=config.wp_username,
            password=config.wp_password
        )
        result = wp.test_connection()
        print(result)
    elif choice == "3" and not existing_articles:
        # 测试 WordPress 连接
        wp = WPPublisher(
            site_url=config.wp_site_url,
            username=config.wp_username,
            password=config.wp_password
        )
        result = wp.test_connection()
        print(result)
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
