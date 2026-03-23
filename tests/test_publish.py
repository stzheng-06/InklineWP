"""测试发布文章 - 使用 WordPress REST API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.wp_publisher import WPPublisher

# 初始化发布器
wp = WPPublisher(
    site_url="https://jktrade.org",
    username="wp text poster",
    password="abc.123456"
)

# 测试连接
print("=== 测试连接 ===")
conn_result = wp.test_connection()
print(conn_result)

if conn_result.get('connected'):
    print("\n=== 发布文章 ===")
    result = wp.publish_post(
        title="测试文章 - 使用 REST API",
        content="<h2>简介</h2><p>这是一篇测试文章，使用 WordPress REST API 发布。</p>",
        status="draft"
    )
    print(result)

    # 测试上传图片（需要本地文件路径）
    # print("\n=== 上传图片 ===")
    # media_result = wp.upload_media("test.jpg", "测试图片")
    # print(media_result)
else:
    print("连接失败")
