"""测试图片服务 - 交互式测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from scripts.image_service import PexelsService, UnsplashService, ImageGenerator, get_image_service
from scripts.file_manager import FileManager

# 测试资源目录
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_FOLDER = PROJECT_ROOT / "assets"
ASSETS_FOLDER.mkdir(exist_ok=True)

# 测试输出目录
TEST_OUTPUT_FOLDER = PROJECT_ROOT / "test_tests"
TEST_OUTPUT_FOLDER.mkdir(exist_ok=True)


def test_pexels():
    """测试 Pexels API"""
    print("\n=== 测试 Pexels API ===")
    service = PexelsService()

    # 搜索图片
    query = "business meeting"
    print(f"搜索关键词: {query}")
    images = service.search_images(query, 2)
    print(f"找到 {len(images)} 张图片")

    if images:
        # 下载第一张到 assets 文件夹
        save_path = ASSETS_FOLDER / "test_pexels.jpg"
        success = service.download_image(images[0]["url"], save_path)
        if success:
            print(f"下载成功: {save_path}")
            return save_path
        else:
            print("下载失败")

    return None


def test_unsplash():
    """测试 Unsplash API"""
    print("\n=== 测试 Unsplash API ===")
    service = UnsplashService()

    # 搜索图片
    query = "office work"
    print(f"搜索关键词: {query}")
    images = service.search_images(query, 2)
    print(f"找到 {len(images)} 张图片")

    if images:
        # 下载第一张到 assets 文件夹
        save_path = ASSETS_FOLDER / "test_unsplash.jpg"
        success = service.download_image(images[0]["url"], save_path)
        if success:
            print(f"下载成功: {save_path}")
            return save_path
        else:
            print("下载失败")

    return None


def test_ai_generation():
    """测试 AI 图片生成"""
    print("\n=== 测试 AI 图片生成 ===")

    generator = ImageGenerator()

    prompt = "A modern office workspace with laptop and coffee"
    save_path = ASSETS_FOLDER / "ai_test.jpg"

    print(f"生成提示词: {prompt}")
    success = generator.generate_image(prompt, save_path)

    if success:
        print(f"AI 图片生成成功: {save_path}")
        return save_path
    else:
        print("AI 图片生成失败")
        return None


def test_auto_switch():
    """测试自动切换功能"""
    print("\n=== 测试自动切换功能 ===")

    # 创建测试文件夹 (test_tests/test_auto/)
    test_folder = TEST_OUTPUT_FOLDER / "test_auto"
    test_folder.mkdir(exist_ok=True)

    # 创建 assets 文件夹
    assets_folder = test_folder / "assets"
    assets_folder.mkdir(exist_ok=True)

    # 测试自动切换 (先 pexels -> 失败则 unsplash -> 失败则 ai)
    service = get_image_service(image_source="pexels", image_count=2)

    query = "technology"
    print(f"搜索关键词: {query}")

    images = service.search_and_download(query, assets_folder)
    print(f"获取到 {len(images)} 张图片")

    for img in images:
        print(f"  - {img['filename']} (来源: {img['source']})")

    return images


def test_image_insert():
    """测试图片插入功能"""
    print("\n=== 测试图片插入功能 ===")

    # 创建测试文章文件夹 (test_tests/test_insert/)
    test_folder = TEST_OUTPUT_FOLDER / "test_insert"
    test_folder.mkdir(exist_ok=True)

    # 创建 assets 文件夹
    assets_folder = test_folder / "assets"
    assets_folder.mkdir(exist_ok=True)

    # 下载测试图片到 assets 文件夹
    pexels = PexelsService()
    print("下载测试图片到 assets 文件夹...")

    # 下载 image1.jpg
    images1 = pexels.search_images("business", 1)
    if images1:
        pexels.download_image(images1[0]["url"], assets_folder / "image1.jpg")
        print(f"  下载 image1.jpg 成功")

    # 下载 image2.jpg
    images2 = pexels.search_images("office", 1)
    if images2:
        pexels.download_image(images2[0]["url"], assets_folder / "image2.jpg")
        print(f"  下载 image2.jpg 成功")

    article_content = """# 测试文章

这是第一段内容，介绍了一些基本信息。

## 第二章

这是第二段内容，详细说明了某些内容。

## 第三章

最后一段是总结部分。
"""

    article_path = test_folder / "article.md"
    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(article_content)

    # 模拟插入点
    insert_points = [
        {"image": "image1.jpg", "insert_after": "这是第一段内容，介绍了一些基本信息。"},
        {"image": "image2.jpg", "insert_after": "## 第三章"}
    ]

    # 执行插入
    file_manager = FileManager()
    updated = file_manager.update_article_with_images(article_path, insert_points)

    print("文章更新后的内容：")
    print(updated)

    return article_path


def interactive_mode():
    """交互式测试模式"""
    print("\n=== 交互式图片测试 ===")
    print("请在提示时输入你的选择...")

    # 创建测试文件夹 (test_tests/test_interactive/)
    test_folder = TEST_OUTPUT_FOLDER / "test_interactive"
    test_folder.mkdir(exist_ok=True)

    # 创建 assets 文件夹
    assets_folder = test_folder / "assets"
    assets_folder.mkdir(exist_ok=True)

    # 选择图片来源
    print("\n请选择图片来源：")
    print("  1. Pexels")
    print("  2. Unsplash")
    print("  3. AI 生成")
    print("  4. 自动选择")

    while True:
        choice = input("\n请输入数字 (1-4): ").strip()
        if choice in ["1", "2", "3", "4"]:
            break
        print("请输入 1-4 之间的数字")

    source_map = {
        "1": ("Pexels", "pexels"),
        "2": ("Unsplash", "unsplash"),
        "3": ("AI", "ai"),
        "4": ("自动", "pexels")
    }

    source_name, source = source_map[choice]
    print(f"\n已选择: {source_name}")

    # 输入搜索关键词
    query = input("请输入图片搜索关键词: ").strip()
    if not query:
        query = "business"

    # 获取图片
    service = get_image_service(image_source=source, image_count=2)
    print(f"\n正在搜索图片: {query}")

    images = service.search_and_download(query, assets_folder)
    print(f"获取到 {len(images)} 张图片")

    if not images:
        print("未能获取图片")
        return

    # 显示图片
    print("\n获取的图片：")
    for i, img in enumerate(images, 1):
        print(f"  {i}. {img['filename']} (来源: {img['source']})")

    # 如果是 AI，询问是否重新生成
    if source == "ai":
        print("\n是否重新生成？(输入新提示词，或直接回车确认当前图片)")
        new_prompt = input("> ").strip()
        if new_prompt:
            new_img = service.generate_image_from_prompt(new_prompt, assets_folder)
            if new_img:
                images = [new_img]
                print(f"✅ 重新生成: {new_img['filename']}")

    print("\n✅ 测试完成")


def main():
    """主测试函数"""
    print("=" * 60)
    print("图片服务测试")
    print("=" * 60)

    print("\n请选择测试模式：")
    print("  1. 默认测试 - 自动运行预设测试")
    print("  2. 手动输入 - 交互式完整流程")

    choice = None
    while choice not in ["1", "2"]:
        try:
            choice = input("\n请输入数字 (1/2): ").strip()
        except EOFError:
            # 非交互环境，默认使用手动模式
            choice = "2"
            print("2 (默认)")

    if choice == "1":
        run_default_tests()
    else:
        interactive_mode()


def run_default_tests():
    """运行默认测试"""
    print("\n运行默认测试...")

    # 测试 Pexels
    try:
        test_pexels()
    except Exception as e:
        print(f"Pexels 测试跳过: {e}")

    # 测试 Unsplash
    try:
        test_unsplash()
    except Exception as e:
        print(f"Unsplash 测试跳过: {e}")

    # 测试 AI 生成
    try:
        test_ai_generation()
    except Exception as e:
        print(f"AI 生成测试跳过: {e}")

    # 测试自动切换
    try:
        test_auto_switch()
    except Exception as e:
        print(f"自动切换测试跳过: {e}")

    # 测试图片插入
    try:
        test_image_insert()
    except Exception as e:
        print(f"图片插入测试跳过: {e}")

    print("\n[OK] 默认测试完成!")


if __name__ == "__main__":
    main()
