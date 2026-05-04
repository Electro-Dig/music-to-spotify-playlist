# music-to-spotify-playlist

<p align="right">
  <a href="./README.md"><img alt="中文" src="https://img.shields.io/badge/中文-当前-blue"></a>
  <a href="./README.en.md"><img alt="English" src="https://img.shields.io/badge/English-switch-lightgrey"></a>
</p>

把截图、公众号文章、YouTube DJ set、歌单截图、榜单、书摘和文字 tracklist 转成 Spotify 可匹配数据，并在确认后创建 Spotify 歌单的 Codex Skill。

## 这个 Skill 做什么

- 从音乐截图、文章、链接或文本里提取候选曲目。
- 保留原始顺序、时间戳、榜单名次、来源和低置信度项。
- 生成 Spotify 匹配用 JSONL。
- 匹配 Spotify 曲目并先 dry-run。
- 确认后创建新歌单或追加到已有歌单。
- 可选保存 Obsidian/Markdown 笔记或生成分享海报。

默认不整理 Obsidian 文档、不归档全文、不生成海报。多数场景直接走“识别音乐 -> 匹配 Spotify -> 创建歌单”的轻量流程。

## 适合的场景

- 截一张音乐推荐图，让 AI 生成 Spotify 歌单。
- 发一篇公众号/网页文章，让 AI 抽取提到的音乐。
- 发 YouTube DJ set 或 radio show 链接，提取 description 里的 tracklist。
- 发 Spotify、Apple Music、网易云、QQ 音乐、Shazam 截图，迁移到 Spotify。
- 发榜单、书摘、研究材料，先整理候选音乐，再决定是否做成歌单。

## 使用前提

- 一个能运行 skills、读写文件并执行 Python 的 agent 环境，例如 Codex Desktop、Codex CLI、Claude Code 或类似工具。
- Python 3.10+。
- Python 依赖：`requests`。
- Spotify 账号和 Spotify Developer App。
- `SPOTIFY_CLIENT_ID` 和 `SPOTIFY_CLIENT_SECRET`。
- 浏览器 OAuth 授权。创建/修改歌单不是只靠 Client ID/Secret 就能完成。

Spotify 官方 Web API 文档当前写明 Web API 使用需要 Premium；Development Mode 还限制 app owner 需要 Premium、最多 5 个 allowlisted authenticated users。免费账号可能无法顺利完成开发者 app、授权或 API 调用。详见 `references/SPOTIFY_SETUP.md`、[Spotify Web API](https://developer.spotify.com/documentation/web-api) 和 [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)。

## 安装

把本目录放到 Codex 可发现的 skill 根目录：

```text
~/.codex/skills/music-to-spotify-playlist
```

或：

```text
~/.agents/skills/music-to-spotify-playlist
```

然后在对话里调用：

```text
$music-to-spotify-playlist
```

## 快速开始

1. 设置 Spotify 凭据：

```powershell
$env:SPOTIFY_CLIENT_ID="your_client_id"
$env:SPOTIFY_CLIENT_SECRET="your_client_secret"
```

2. 对 agent 说：

```text
$music-to-spotify-playlist 帮我把这张截图里的歌做成 Spotify 歌单
```

3. agent 会先提取候选曲目，列出低置信度项，然后询问是否继续 Spotify 匹配。

4. 匹配后先 dry-run：

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --dry-run
```

5. 确认无误后再创建私密歌单：

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>"
```

公开歌单需要明确指定：

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --public
```

## 默认流程

1. **Collect & transcribe**：识别来源，提取候选音乐项目。
2. **Prepare & match**：写入 JSONL，匹配 Spotify，标记不确定项。
3. **Publish & share**：先 dry-run，再按确认创建或追加歌单。

Obsidian/Markdown 整理是可选分支。只有明确需要“保存笔记、归档、整理成文档、放进 Obsidian”时才做。

## 文件结构

```text
music-to-spotify-playlist/
  SKILL.md
  README.md
  README.en.md
  references/
    DEPENDENCIES.md
    INPUT_SOURCES.md
    SPOTIFY_SETUP.md
    WORKFLOW.md
  scripts/
    create_spotify_playlist.py
```

## 隐私说明

Spotify 凭据和 OAuth token 只需要保存在本地环境中。脚本默认读取环境变量、`.env`，或显式传入的 `--credentials-note`；不会自动扫描私人 Obsidian 笔记。

匹配和创建歌单时，脚本只会把曲目查询和歌单写入请求发送给 Spotify API。截图、公众号原文、私人聊天内容是否保存为 Markdown/Obsidian 笔记，始终是可选步骤。

## 云端和手机使用说明

本 skill 最适合本地电脑运行，因为 Spotify OAuth 默认使用：

```text
http://127.0.0.1:8888/callback
```

如果 agent 跑在云服务器，手机只是聊天入口，OAuth 回调可能回不到运行脚本的机器。云端使用需要额外处理端口转发、远程浏览器或公开 HTTPS callback。

## License

MIT
