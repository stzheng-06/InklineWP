"""文章生成器测试代码 - 自动测试模式"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.article_generator import ArticleGenerator
from scripts.config import Config


def test_generate_topics():
    """测试生成主题功能"""
    print("\n=== 测试 1: 生成主题 ===")

    config = Config()
    generator = ArticleGenerator(config)

    # 测试生成主题
    topics = generator.generate_topics("Python programming")
    print(f"生成了 {len(topics)} 个主题:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")

    return topics


def test_generate_article(topic: str):
    """测试生成文章功能"""
    print(f"\n=== 测试 2: 生成文章 ===")

    config = Config()
    generator = ArticleGenerator(config)

    params = {
        "title": topic,
        "background": config.background,
        "keywords": config.seo_keywords,
        "requirements": config.article_requirements,
        "word_count": 300,  # 用较小的字数测试
        "user_language": config.user_language
    }

    article = generator.generate_article(params)
    print(f"生成的文章 ({len(article)} 字符):")
    print("-" * 40)
    print(article[:1000] + "..." if len(article) > 1000 else article)
    print("-" * 40)

    return article


def test_save_article(topic: str, article: str):
    """测试保存文章功能"""
    print(f"\n=== 测试 3: 保存文章 ===")

    config = Config()
    generator = ArticleGenerator(config)

    file_path = generator.save_article(topic, article)
    print(f"文章已保存到: {file_path}")


def interactive_mode():
    """交互模式 - 完整流程测试"""
    print("\n=== 交互模式测试 ===")
    print("请在提示时输入你的选择...")

    # 重定向输入来模拟用户
    # 这里不做自动输入，让用户手动体验完整流程
    from scripts.article_generator import main as run_generator
    run_generator()


def run_default_test():
    """运行默认测试"""
    # 显示配置
    config = Config()
    config.display_config()

    # 测试 1: 生成主题
    topics = test_generate_topics()

    if topics:
        # 选择第一个主题测试
        selected_topic = topics[0]
        print(f"\n选择主题: {selected_topic}")

        # 测试 2: 生成文章
        article = test_generate_article(selected_topic)

        # 测试 3: 保存文章
        test_save_article(selected_topic, article)

        print("\n[OK] 基础测试通过!")


def main():
    """主测试函数"""
    print("=" * 60)
    print("AI 文章生成器 - 测试模式")
    print("=" * 60)

    print("\n请选择测试模式：")
    print("  1. 默认测试 - 自动运行预设测试")
    print("  2. 手动输入 - 交互式完整流程")

    while True:
        choice = input("\n请输入数字 (1/2): ").strip()
        if choice == "1":
            run_default_test()
            break
        elif choice == "2":
            interactive_mode()
            break
        else:
            print("请输入 1 或 2")


if __name__ == "__main__":
    main()
