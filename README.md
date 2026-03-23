# WordPress AI 文章发布工具

使用 AI 生成文章并发布到 WordPress 的工具。支持多配置管理和模板系统。

## 快速开始

```bash
python main.py
```

按提示选择配置和操作即可。

## 环境配置

在 `.env` 文件中配置 API 密钥：

```env
# AI 服务
AI_PROVIDER=aihubmix
AIHUBMIX_API_KEY=your_key
OPENAI_API_KEY=your_key

# 图片服务
PEXELS_API_KEY=your_key
UNSPLASH_ACCESS_KEY=your_key

# WordPress
WP_SITE_URL=https://your-site.com
WP_USERNAME=your_username
WP_PASSWORD=your_app_password
```

## 配置系统

配置文件位于 `config/` 文件夹下，每个 JSON 文件是一个独立配置。

### 创建新配置

运行 `python main.py` 后选择"创建新配置"，需要提供：
- 配置名称
- WordPress 站点 URL
- WordPress 用户名
- WordPress 应用密码

### 配置字段说明

| 字段 | 说明 |
|------|------|
| `config_name` | 配置显示名称 |
| `ai_provider` | AI 服务商 (aihubmix/openai) |
| `model` | 模型名称 |
| `text_language` | 文章输出语言 |
| `background` | 作者背景（用于生成内容） |
| `seo_keywords` | SEO 关键词 |
| `template_name` | 模板分类 |
| `template_settings` | 模板组件设置 |

## 主程序功能

运行 `python main.py` 后：

1. **选择配置文件** - 选择已有配置或创建新配置
2. **查看/修改配置** - 可修改 AI、语言、模板等设置
3. **选择操作**：
   - 完整流程：生成文章 + 配图 + 发布
   - 配图流程：选择已有文章重新配图
   - 发布流程：选择已有文章直接发布（自动检查/转换 HTML）
   - 测试 WordPress 连接

## 模板系统

模板组件位于 `templates/` 目录下：

```
templates/
└── cta/
    ├── whatsapp_cta.html
    ├── contact_cta.html
    └── ...
```

在配置中启用模板后，组件会自动插入到文章 HTML 中（开头或结尾）。

## 输出结构

生成的文章保存在 `output_text/` 文件夹：

```
output_text/
└── {日期} {标题}/
    ├── article.md          # Markdown 源文件
    ├── article.html        # 转换后的 HTML
    ├── article_info.json   # 发布信息
    └── assets/
        └── *.jpg          # 文章图片
```

## 项目结构

```
wp text/
├── main.py              # 主程序入口
├── .env                 # 环境变量
├── config/              # 配置文件
├── scripts/             # 核心模块
│   ├── ai_client.py    # AI 客户端
│   ├── config.py        # 配置管理
│   ├── file_manager.py  # 文件操作
│   ├── image_service.py # 图片服务
│   ├── markdown_converter.py # Markdown 转 HTML
│   ├── template_loader.py   # 模板加载
│   └── wp_publisher.py # WordPress 发布
├── templates/           # HTML 模板组件
└── output_text/         # 生成的 文章
```

## 依赖

```
openai
requests
python-dotenv
markdown2
beautifulsoup4
```
