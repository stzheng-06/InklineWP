# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WordPress AI Article Publishing Tool - generates articles using AI, adds images, and publishes to WordPress. Supports multiple configurations and templates.

## Commands

```bash
# Run main program (interactive menu)
python main.py
```

## Project Structure

```
wp text/
├── main.py                 # Main entry point with menu
├── .env                   # Environment variables (API keys)
├── config/                # Configuration folder
│   ├── default.json       # Default configuration
│   └── *.json            # Custom configurations
├── scripts/               # Core modules
│   ├── ai_client.py       # AI client (OpenAI/AIHubMix)
│   ├── config.py          # Configuration manager
│   ├── file_manager.py    # File operations
│   ├── wp_publisher.py    # WordPress publishing
│   ├── image_service.py   # Image service (Pexels/Unsplash/AI)
│   ├── markdown_converter.py # Markdown to HTML
│   └── template_loader.py # Template components loader
├── templates/             # HTML template components
│   └── cta/              # Call-to-action components
├── tests/                 # Test files
└── output_text/           # Generated articles
    └── {date} {title}/
        ├── article.md
        ├── article.html
        ├── article_info.json
        └── assets/
            └── {images}.jpg
```

## Main Program Flow (main.py)

When running `python main.py`:
1. Select configuration file (or create new)
2. Display current config - user can modify
3. Choose operation:
   - 1. Full flow: generate article + images + publish
   - 2. Image flow: select existing article to add images
   - 3. Publish flow: select existing article to publish (checks HTML, converts if needed)
   - 4. Test WordPress connection

## Configuration System

**Location**: `config/*.json`

Each config file contains:
- `config_name`: Display name
- `ai_provider`: "aihubmix" or "openai"
- `model`: Model name (e.g., "gemini-3.1-flash-lite-preview")
- `user_language`: AI response language
- `text_language`: Article output language
- `background`: Author background for content generation
- `article_requirements`: Article requirements/guidelines
- `seo_keywords`: Default SEO keywords
- `default_word_count`: Default article length
- `image_source`: "pexels", "unsplash", or "ai"
- `image_count`: Number of images per article
- `template_name`: Template category (e.g., "cta")
- `template_settings`: Components to insert (enabled, components with position)
- `wp_site_url`, `wp_username`, `wp_password`: WordPress credentials

## Architecture

### AI Client (scripts/ai_client.py)
- Supports: OpenAI, AIHubMix
- Auto-detects model compatibility
- Key methods:
  - `generate_topics(topic, count)` - Generate subtopics
  - `generate_markdown_article(...)` - Generate full article
  - `get_image_insert_points(article, images)` - AI determines image positions

### Image Service (scripts/image_service.py)
- **PexelsService**: Search/download from Pexels
- **UnsplashService**: Search/download from Unsplash
- **ImageGenerator**: AI-generated images
- **ImageService**: Auto-switches (Pexels → Unsplash → AI)

### WordPress Publisher (scripts/wp_publisher.py)
- WordPress REST API (wp/v2) with Basic Auth
- Methods: `test_connection()`, `publish_post()`, `upload_media()`

### Template System
- Templates stored in `templates/{category}/`
- Components in `templates/{category}/*.html`
- Configured via `template_settings` in config.json

## Key Patterns

- All imports: `from scripts.ai_client import ...`
- Config loading: `get_config()` returns singleton Config instance
- Output folder: `{date} {title}/article.md` with date prefix (DD-MM-YY HH)
- Image insertion: AI returns `insert_after` text snippets
- HTML conversion: Uses markdown2 + BeautifulSoup for post-processing
- Template components: Inserted at start/end of article HTML

## Environment Variables (.env)

```
AI_PROVIDER=aihubmix
AIHUBMIX_API_KEY=your_key
OPENAI_API_KEY=your_key
PEXELS_API_KEY=your_key
UNSPLASH_ACCESS_KEY=your_key
WP_SITE_URL=https://yoursite.com
WP_USERNAME=your_username
WP_PASSWORD=your_password
```
