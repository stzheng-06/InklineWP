"""WordPress 发布模块 - 使用原生 REST API"""
import base64
import os
import requests
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class WPPublisher:
    """WordPress 发布类"""

    def __init__(self, site_url: str, username: str, password: str, use_basic_auth: bool = True):
        """
        初始化 WordPress 发布器

        Args:
            site_url: WordPress 站点 URL
            username: 用户名/邮箱
            password: 密码
            use_basic_auth: 是否使用 Basic Auth (默认 True)
        """
        site_url = site_url.rstrip('/')
        self.site_url = site_url
        self.username = username
        self.password = password
        self.use_basic_auth = use_basic_auth

        # WordPress REST API
        self.api_url = f"{site_url}/wp-json/wp/v2"

    def _get_auth_header(self) -> Dict:
        """获取认证头"""
        if self.use_basic_auth:
            # Basic Auth
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json"
            }
        else:
            # Application Passwords 或 Bearer Token
            return {
                "Authorization": f"Bearer {self.password}",
                "Content-Type": "application/json"
            }

    def test_connection(self) -> Dict:
        """测试连接"""
        try:
            response = requests.get(
                f"{self.api_url}/users/me",
                headers=self._get_auth_header(),
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'connected': True,
                    'site_url': self.site_url,
                    'user': response.json().get('name')
                }
            else:
                return {
                    'connected': False,
                    'error': f"HTTP {response.status_code}: {response.text[:100]}"
                }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    def publish_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        featured_media: Optional[int] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None
    ) -> Dict:
        """
        发布文章

        Args:
            title: 文章标题
            content: 文章内容 (HTML)
            status: 发布状态 (draft/publish)
            featured_media: 封面图 media_id
            categories: 分类 ID 列表
            tags: 标签 ID 列表

        Returns:
            发布结果
        """
        try:
            post_data = {
                "title": title,
                "content": content,
                "status": status
            }

            if featured_media:
                post_data["featured_media"] = featured_media
            if categories:
                post_data["categories"] = categories
            if tags:
                post_data["tags"] = tags

            response = requests.post(
                f"{self.api_url}/posts",
                headers=self._get_auth_header(),
                json=post_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'post_id': data.get('id'),
                    'post_url': data.get('link')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def upload_media(self, file_path: str, alt_text: str = "") -> Dict:
        """
        上传媒体文件

        Args:
            file_path: 本地文件路径
            alt_text: 图片 alt 文本

        Returns:
            媒体信息
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {'success': False, 'error': '文件不存在'}

            # 读取文件
            with open(file_path, 'rb') as f:
                file_data = f.read()

            filename = file_path.name
            mime_type = self._get_mime_type(filename)

            # 构建请求
            files = {
                'file': (filename, file_data, mime_type)
            }
            data = {
                'title': alt_text or filename,
                'alt_text': alt_text or filename
            }

            response = requests.post(
                f"{self.api_url}/media",
                headers={
                    "Authorization": self._get_auth_header()["Authorization"]
                },
                files=files,
                data=data,
                timeout=60
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'media_id': data.get('id'),
                    'source_url': data.get('source_url')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def upload_images_batch(self, local_images: List[Dict]) -> Dict[str, Dict]:
        """
        批量上传图片到 WordPress

        Args:
            local_images: 图片列表 [{"filename": "image1.jpg", "path": "/path/to/image1.jpg"}, ...]

        Returns:
            {文件名: {"url": HTTP链接, "media_id": 媒体ID}} 的映射
        """
        url_map = {}

        print(f"\n开始批量上传 {len(local_images)} 张图片...")

        for i, img in enumerate(local_images, 1):
            filename = img.get("filename", "")
            file_path = img.get("path", "")

            if not file_path:
                print(f"  [{i}/{len(local_images)}] 跳过: 无文件路径")
                continue

            print(f"  [{i}/{len(local_images)}] 上传: {filename}")

            result = self.upload_media(file_path, alt_text=filename)

            if result.get("success"):
                http_url = result.get("source_url", "")
                media_id = result.get("media_id", 0)
                url_map[filename] = {
                    "url": http_url,
                    "media_id": media_id
                }
                print(f"    -> 成功: {http_url} (ID: {media_id})")
            else:
                error = result.get("error", "未知错误")
                print(f"    -> 失败: {error}")

        print(f"\n批量上传完成: 成功 {len(url_map)}/{len(local_images)} 张")
        return url_map

    def _get_mime_type(self, filename: str) -> str:
        """根据文件扩展名获取 MIME 类型"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.pdf': 'application/pdf',
        }
        return mime_types.get(ext, 'application/octet-stream')

    def get_categories(self) -> List[Dict]:
        """获取分类列表"""
        try:
            response = requests.get(
                f"{self.api_url}/categories",
                headers=self._get_auth_header(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_tags(self) -> List[Dict]:
        """获取标签列表"""
        try:
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self._get_auth_header(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def replace_images_with_wp_urls(
        self,
        html_content: str,
        media_results: List[Dict]
    ) -> str:
        """替换 HTML 中的本地图片路径为 WordPress URL"""
        import re

        url_map = {}
        for result in media_results:
            if result.get('success'):
                file_path = Path(result['file_path'])
                filename = file_path.name
                url_map[filename] = result['source_url']

        def replace_src(match):
            full_attr = match.group(1)
            src_match = re.search(r'src=["\']([^"\']+)["\']', full_attr)
            if src_match:
                src = src_match.group(1)
                filename = self._extract_filename_from_path(src)
                if filename in url_map:
                    new_src = url_map[filename]
                    new_full_attr = full_attr.replace(src, new_src)
                    return f"<img {new_full_attr}>"
            return match.group(0)

        return re.sub(r'<img\s+([^>]+)>', replace_src, html_content)

    def _extract_filename_from_path(self, path: str) -> str:
        """从路径提取文件名"""
        path = path.split('?')[0]
        return path.split('/')[-1]


def get_wp_publisher() -> Optional[WPPublisher]:
    """获取 WordPress 发布器实例"""
    site_url = os.getenv('WP_SITE_URL', '')
    username = os.getenv('WP_USERNAME', '')
    password = os.getenv('WP_PASSWORD', '')

    if not all([site_url, username, password]):
        return None

    return WPPublisher(site_url, username, password)
