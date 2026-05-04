---
name: music-to-spotify-playlist
description: Use when the user provides music screenshots, articles, YouTube DJ sets, Xiaohongshu cards, chart or playlist screenshots, books, text tracklists, or music links and wants extracted music items, Spotify matching, or a Spotify playlist.
---

# music-to-spotify-playlist

Turn music evidence from links, screenshots, articles, charts, books, or tracklists into candidate music items, Spotify-ready data, optional Spotify playlists, and optional notes/posters.

## Invocation

- After installing this folder into a supported skill root, invoke this skill as `$music-to-spotify-playlist`.
- `$` is the Codex skill prefix. `/` is for commands/built-ins; do not expect `/music-to-spotify-playlist` unless a separate wrapper command exists.
- For Codex, install or symlink this folder under `~/.codex/skills/` or `~/.agents/skills/` so the app can discover it.

## Core rule

Default to Chinese for all user-facing replies, status updates, questions, and summaries. Use another language only when the user explicitly asks for it or the user's input is clearly in another language.

Use source triage plus three stage gates. The default path is Spotify playlist creation; Obsidian or document cleanup is optional and opt-in.

1. **Collect & transcribe** — identify the source and extract candidate music items.
2. **Prepare & match** — create JSONL, validate it, and match Spotify only after confirmation.
3. **Publish & share** — create/update playlist and optionally generate a poster only after confirmation.

If the user asks for a playlist from an image/article/link, do not require Obsidian. Ask whether they want a saved note only if they mention archiving, Obsidian, documents, or "整理成文章/笔记".

If the user only says “整理一下”, ask the intended output: chat-only, Spotify playlist, JSONL, optional note, or poster.

## Security and consent

- Never print, store in docs, or include in examples: Spotify Client Secret, access tokens, refresh tokens, token caches, or private `.env` contents.
- If Spotify credentials are missing, guide setup using `references/SPOTIFY_SETUP.md`; do not pressure users to paste secrets into chat.
- Remind new users they normally need their own Spotify Developer App, Client ID, Client Secret, and browser OAuth authorization.
- Ask before saving private chat screenshots into Obsidian.
- Do not fetch YouTube comments/transcripts by default; start with title/channel/description unless the user asks otherwise.

## Source triage

Supported inputs include:

- YouTube DJ set/radio show descriptions with timestamps or tracklists.
- Xiaohongshu/Instagram-style music cards and screenshots.
- Music chart/ranking screenshots.
- Spotify/Apple Music/NetEase/QQ Music/Shazam playlist screenshots.
- WeChat music posts and image-heavy articles.
- Electronic music history books, PDFs, exhibition material, or page photos.
- Text tracklists, chat screenshots, comments, and multi-link batches.

For non-obvious inputs, load `references/INPUT_SOURCES.md`.

## Stage 1 — Collect & transcribe

Goal: candidate items, not a final playlist.

Capture: source type/ref, order/rank/timestamp, raw text, item type, artist/track when available, confidence, and ambiguities.

Candidate JSONL shape:

```json
{"source_type":"youtube_description","source_ref":"https://youtube.com/...","position":"00:05:42","rank":null,"item_type":"track","artist":"Drexciya","track":"Andreaen Sand Dunes","raw_text":"05:42 Drexciya - Andreaen Sand Dunes","confidence":"high","notes":""}
```

End Stage 1 with a short status: source type, count, item-type summary, low-confidence items, and:

```text
Continue to Spotify matching? This requires a Spotify Developer App, Client ID, Client Secret, and usually Spotify Premium. Do you already have these configured locally?
```

Do not save an Obsidian note by default. If a note would be useful, ask: “Do you also want me to save a整理/Obsidian note? Default is no.”

## Stage 2 — Prepare & match Spotify

Use only after Stage 1 confirmation or when the user already provides tracks/JSONL.

Credential gate:

- Before any Spotify matching, ask whether the user already has a Spotify Developer App and local `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`.
- Tell the user Spotify Web API access currently requires Premium and playlist writes also require browser OAuth.
- Check environment variables, `.env`, or an explicitly user-provided local credentials note only after the user confirms credentials should be available.
- If credentials are missing, stop Stage 2 and load `references/SPOTIFY_SETUP.md`. Do not search the web or use non-Spotify sources as a fallback.
- If the user has not created a Spotify Developer App, stop and guide setup. Resume Spotify matching only after credentials are configured.
- Do not ask users to paste Client Secret into chat unless they explicitly choose that tradeoff; prefer environment variables or a local `.env`.

Hard rule:

- No Spotify credentials means no Spotify matching. Do not use Google, public webpages, lyrics sites, music databases, or general web search to guess Spotify URIs.

Tasks:

1. Write UTF-8 `spotify-query-items.jsonl`.
2. Validate JSONL parses and item count matches Stage 1.
3. Search the Spotify API and add `spotify_uri` plus metadata where possible; do not use uncertain first results without flagging them.
4. Flag ambiguous/missing matches.
5. Run dry-run before any playlist write.

Minimum Spotify JSONL shape:

```json
{"no":1,"artist":"Drexciya","track":"Andreaen Sand Dunes","query":"Drexciya Andreaen Sand Dunes","spotify_uri":"spotify:track:...","confidence":"high","notes":""}
```

End Stage 2 with match count and “Create or update a Spotify playlist?”

## Stage 3 — Publish & share

Before writing to Spotify, confirm:

- new playlist or append to existing playlist
- private or public
- final item order

Dry-run:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --dry-run
```

Create private playlist:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>"
```

Use `--public` only after explicit user request. If JSONL lacks `spotify_uri`, finish Stage 2 matching first or pass `--resolve-missing` during a reviewed dry-run.

Optional poster branch: ask first, use public/non-secret metadata only, save under `posters/`, and embed with `![[posters/example.png]]` only if requested.

## References

- `references/WORKFLOW.md` — fuller workflow from the original long skill.
- `references/INPUT_SOURCES.md` — source-specific triage.
- `references/SPOTIFY_SETUP.md` — developer app, Client ID/Secret, redirect URI, OAuth errors.
- `references/DEPENDENCIES.md` — companion skills and tools.
- `scripts/create_spotify_playlist.py` — Spotify playlist script.

## Completion checks

- Stage 1: source identified, candidates counted, item type clear, uncertainty reported.
- Stage 2: JSONL parses, counts match, Spotify matches/ambiguities reported, dry-run reviewed.
- Stage 3: playlist URL exists if requested; note/poster updated only if requested.

## Common mistakes

- Treating every source as WeChat or every item as a Spotify track.
- Running all stages without confirmation.
- Fetching YouTube comments by default.
- Saving private screenshots without consent.
- Creating playlists before dry-run confirmation.
- Printing secrets or token-cache content.
- Falling back to web search when Spotify credentials are missing.
