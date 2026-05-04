# Dependencies and companion capabilities

This skill can be shared independently, but the full workflow expects these capabilities.

## Optional for Obsidian capture

- A WeChat/webpage-to-Obsidian archiver such as the `web-to-obsidian` skill.
- If `web-to-obsidian` is unavailable, use any tool that produces the same artifact shape when the user asks for saved notes:
  - one article folder
  - one Markdown note
  - one `imgs/` folder with localized images
  - frontmatter or visible source URL metadata

Do not require these tools for the normal screenshot/article-to-Spotify flow.

## Required for playlist creation

- Python 3.10+
- `requests`

Install:

```powershell
python -m pip install requests
```

## Recommended for image-heavy posts

- Local OCR such as `rapidocr_onnxruntime`, Tesseract, PaddleOCR, or a vision-capable model/tool.
- Manual visual inspection for low-confidence OCR fields.

## Optional for share-poster generation

- An image generation tool such as Codex/Image2 or another environment-provided image model.
- Do not generate a poster automatically. Ask the user first and let them choose style/dimensions.
