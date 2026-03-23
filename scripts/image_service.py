"""图片服务模块 - 支持 Pexels、Unsplash 和 AI 生成"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO
import base64
from dotenv import load_dotenv

load_dotenv()


class PexelsService:
    """Pexels 图片搜索服务"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('PEXELS_API_KEY', '')
        self.base_url = "https://api.pexels.com/v1"

    def search_images(self, query: str, per_page: int = 2) -> List[Dict]:
        """搜索图片"""
        if not self.api_key:
            return []

        try:
            headers = {"Authorization": self.api_key}
            params = {"query": query, "per_page": per_page}
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "url": photo["src"]["original"],
                        "thumbnail": photo["src"]["medium"],
                        "alt": photo.get("alt", ""),
                        "photographer": photo.get("photographer", "")
                    }
                    for photo in data.get("photos", [])
                ]
            return []
        except Exception as e:
            print(f"Pexels 搜索失败: {e}")
            return []

    def download_image(self, url: str, save_path: Path) -> bool:
        """下载图片"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Pexels 下载失败: {e}")
            return False


class UnsplashService:
    """Unsplash 图片搜索服务"""

    def __init__(self, access_key: str = None):
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY', '')
        self.base_url = "https://api.unsplash.com"

    def search_images(self, query: str, per_page: int = 2) -> List[Dict]:
        """搜索图片"""
        if not self.access_key:
            return []

        try:
            headers = {"Authorization": f"Client-ID {self.access_key}"}
            params = {"query": query, "per_page": per_page}
            response = requests.get(
                f"{self.base_url}/search/photos",
                headers=headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "url": photo["urls"]["raw"],
                        "thumbnail": photo["urls"]["small"],
                        "alt": photo.get("alt_description", ""),
                        "photographer": photo.get("user", {}).get("name", "")
                    }
                    for photo in data.get("results", [])
                ]
            return []
        except Exception as e:
            print(f"Unsplash 搜索失败: {e}")
            return []

    def download_image(self, url: str, save_path: Path) -> bool:
        """下载图片"""
        try:
            # Unsplash 需要添加请求头
            headers = {"Authorization": f"Client-ID {self.access_key}"}
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            print(f"Unsplash 下载失败: {e}")
            return False


class ImageGenerator:
    """AI 图片生成服务"""

    def __init__(self, api_key: str = None, base_url: str = "https://aihubmix.com/v1"):
        self.api_key = api_key or os.getenv('AIHUBMIX_API_KEY', '')
        self.base_url = base_url

    def generate_image(
        self,
        prompt: str,
        save_path: Path,
        aspect_ratio: str = "16:9"
    ) -> bool:
        """使用 AI 生成图片"""
        if not self.api_key:
            print("AI 图片生成失败: 未配置 API Key")
            return False

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

            # 尝试使用 images.generate API (适用于 DALL-E 等模型)
            try:
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024" if aspect_ratio == "1:1" else "1792x1024",
                    quality="standard",
                    n=1,
                )

                # 获取图片 URL 或 base64
                image_data = response.data[0]

                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    b64_data = image_data.b64_json
                    image_bytes = base64.b64decode(b64_data)
                elif hasattr(image_data, 'url') and image_data.url:
                    # 需要下载图片
                    import requests
                    resp = requests.get(image_data.url, timeout=30)
                    image_bytes = resp.content
                else:
                    raise Exception("No image data in response")

                # 保存图片
                save_path.parent.mkdir(parents=True, exist_ok=True)
                image = Image.open(BytesIO(image_bytes))
                image.save(save_path)
                return True

            except Exception as img_err:
                print(f"images.generate 失败: {img_err}")

            # 回退：尝试使用 chat.completions (适用于 Gemini 等模型)
            print("尝试使用 multimodal 模型生成图片...")

            response = client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Generate an image with this prompt: {prompt}. Output the image directly."}
                    ]}
                ],
                modalities=["image"],
                max_tokens=4096,
            )

            # 解析响应并保存图片
            message = response.choices[0].message

            # 尝试多种方式获取图片数据
            parts = []
            if hasattr(message, 'multi_mod_content'):
                parts = message.multi_mod_content or []
            elif hasattr(message, 'multi_modal_content'):
                parts = message.multi_modal_content or []
            elif hasattr(message, 'content') and isinstance(message.content, list):
                parts = message.content

            # 调试输出
            print(f"Debug: parts = {parts}")

            for part in parts:
                if isinstance(part, dict):
                    # 处理两种格式：{"inline_data": {"data": "base64..."}} 或 {"inline_data": "base64..."}
                    inline_data = part.get("inline_data")
                    if inline_data:
                        if isinstance(inline_data, dict):
                            b64_data = inline_data.get("data")
                        else:
                            b64_data = inline_data

                        if b64_data:
                            image_data = base64.b64decode(b64_data)
                            image = Image.open(BytesIO(image_data))
                            save_path.parent.mkdir(parents=True, exist_ok=True)
                            image.save(save_path)
                            return True

            print("AI 图片生成失败: 未收到有效图片数据")
            return False

        except Exception as e:
            print(f"AI 图片生成失败: {e}")
            return False


class ImageService:
    """图片服务主类 - 自动切换图片来源"""

    def __init__(
        self,
        image_source: str = "pexels",
        image_count: int = 2,
        image_model: str = "gemini-3.1-flash-image-preview"
    ):
        self.image_source = image_source
        self.image_count = image_count
        self.image_model = image_model

        # 初始化各服务
        self.pexels = PexelsService()
        self.unsplash = UnsplashService()
        self.generator = ImageGenerator()

    def search_and_download(
        self,
        query: str,
        save_folder: Path
    ) -> List[Dict]:
        """
        搜索并下载图片

        Args:
            query: 搜索关键词
            save_folder: 保存文件夹

        Returns:
            下载成功的图片列表
        """
        results = []

        # 根据配置选择图片来源
        sources = []
        if self.image_source == "pexels":
            sources = ["pexels"]
        elif self.image_source == "unsplash":
            sources = ["unsplash"]
        elif self.image_source == "ai":
            sources = ["ai"]
        else:
            # 自动切换模式
            sources = ["pexels", "unsplash", "ai"]

        for source in sources:
            images = []
            download_source = source

            if source == "pexels":
                images = self.pexels.search_images(query, self.image_count)
            elif source == "unsplash":
                images = self.unsplash.search_images(query, self.image_count)
            else:
                # AI 生成模式
                images = self._generate_by_ai(query, save_folder, self.image_count)
                # 如果 AI 失败，回退到 Pexels
                if not images:
                    print("AI 图片生成失败，尝试使用 Pexels...")
                    images = self.pexels.search_images(query, self.image_count)
                    download_source = "pexels"

            if not images:
                continue

            # 下载图片 - 使用简短文件名避免中文长路径问题
            for i, img_info in enumerate(images):
                filename = f"image{i+1}.jpg"
                save_path = save_folder / filename

                # 检查图片数据是否有 url
                img_url = img_info.get("url")
                if not img_url:
                    print(f"Warning: 图片信息中没有 url 字段: {img_info}")
                    continue

                if download_source == "pexels":
                    success = self.pexels.download_image(img_url, save_path)
                else:
                    success = self.unsplash.download_image(img_url, save_path)

                if success:
                    results.append({
                        "filename": filename,
                        "path": str(save_path),
                        "source": download_source,
                        "alt": img_info.get("alt", ""),
                        "thumbnail": img_info.get("thumbnail", "")
                    })

            if results:
                break  # 成功获取图片后退出

        return results

    def _generate_by_ai(
        self,
        prompt: str,
        save_folder: Path,
        count: int
    ) -> List[Dict]:
        """使用 AI 生成多张图片"""
        results = []
        aspect_ratios = ["16:9", "4:3", "1:1"]

        for i in range(count):
            filename = f"image{i+1}.jpg"
            save_path = save_folder / filename
            aspect_ratio = aspect_ratios[i % len(aspect_ratios)]

            success = self.generator.generate_image(
                prompt=prompt,
                save_path=save_path,
                aspect_ratio=aspect_ratio
            )

            if success:
                results.append({
                    "filename": filename,
                    "path": str(save_path),
                    "source": "ai",
                    "alt": prompt,
                    "prompt": prompt
                })

        return results

    def generate_image_from_prompt(
        self,
        prompt: str,
        save_folder: Path,
        filename: str = None
    ) -> Optional[Dict]:
        """
        根据提示词生成单张图片（用于用户重新生成）

        Args:
            prompt: 图片提示词
            save_folder: 保存文件夹
            filename: 文件名（可选）

        Returns:
            生成结果
        """
        if filename is None:
            filename = "image1.jpg"

        save_path = save_folder / filename

        success = self.generator.generate_image(
            prompt=prompt,
            save_path=save_path
        )

        if success:
            return {
                "filename": filename,
                "path": str(save_path),
                "source": "ai",
                "alt": prompt,
                "prompt": prompt
            }
        return None

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        import re
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        if len(name) > 30:
            name = name[:30]
        return name


def get_image_service(
    image_source: str = "pexels",
    image_count: int = 2,
    image_model: str = "gemini-3.1-flash-image-preview"
) -> ImageService:
    """获取 ImageService 实例"""
    return ImageService(image_source, image_count, image_model)
