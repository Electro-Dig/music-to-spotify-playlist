---
name: music-to-spotify-playlist
description: Use when the user provides a YouTube DJ set, Xiaohongshu card, chart screenshot, playlist screenshot, WeChat post, book/photo, text tracklist, or music links and wants music extraction, Spotify matching, or playlist creation.
---

# music-to-spotify-playlist

Convert music evidence from links, screenshots, articles, cards, charts, books, or tracklists into candidate items, Spotify-ready data, Spotify playlists, and optional notes/share posters.

## Core rule: source triage + stage gates

Do **not** assume the input is a WeChat article or a Spotify-ready tracklist. First classify the source, then work in three stages. Stop after each stage for confirmation.

1. **Collect & transcribe** → classify input, extract candidate music items, then stop.
2. **Prepare data & Spotify match** → structure JSONL, match Spotify, dry-run, then stop.
3. **Publish & share** → create/update playlist and optional poster only after confirmation.

This avoids long token-heavy runs and prevents continuing in the wrong direction after OCR, source-type, or matching errors.

## Security and consent rules

- Never print Spotify Client Secret, access tokens, refresh tokens, or token-cache contents.
- Never put personal credentials in `SKILL.md`, scripts, examples, tests, screenshots, or poster prompts.
- Prefer environment variables or a local `.env` ignored by git.
- If credentials are missing, guide setup; do not pressure the user to paste secrets into chat.
- If the user provides private chat screenshots, ask before saving them into Obsidian.
- If the user asks for a playlist from an image/article/link, default to extraction → Spotify matching → dry-run → playlist confirmation. Ask about Obsidian/Markdown notes only when the user requests archiving or documentation.
- If the user only says “整理一下” and has not specified destination, ask whether the output should be Spotify playlist, chat-only, JSONL, optional note, or poster.

## Supported input sources

Common inputs include:

- YouTube video links, especially DJ set/radio show descriptions with tracklists.
- Xiaohongshu/Instagram-style music recommendation cards or screenshots.
- Music chart/ranking screenshots, often album/track/year-end lists.
- Spotify/Apple Music/NetEase/QQ Music/Shazam playlist screenshots.
- WeChat music posts and image-heavy event/label articles.
- Electronic music history books, PDFs, exhibition material, or page photos.
- Text tracklists, chat screenshots, comments, or batches of music links.

For detailed triage rules, load `references/INPUT_SOURCES.md` only when Stage 1 input is not obvious.

## Stage 1 — Collect & transcribe

Goal: turn raw source material into candidate music items, not a final playlist.

Tasks:

1. Classify source type: URL, image/screenshot, chart, platform screenshot, book/photo, text, multi-link, or mixed.
2. If source is a URL, capture or read only the useful public metadata/content.
   - For YouTube, start with title/channel/description; do not fetch comments by default.
   - For WeChat or generic articles, prefer `web-to-obsidian` only when archiving is requested.
3. If source is image-heavy, OCR and visually inspect low-confidence fields.
4. Preserve order, rank, timestamps, raw text, and source context.
5. Determine item type: track, album, artist, label, work, or mixed.
6. Ask before forcing album/history/research material into a track-level Spotify playlist.

Candidate item model:

```json
{"source_type":"youtube_description","source_ref":"https://youtube.com/...","position":"00:05:42","rank":null,"item_type":"track","artist":"Drexciya","track":"Andreaen Sand Dunes","raw_text":"05:42 Drexciya - Andreaen Sand Dunes","confidence":"high","notes":""}
```

Minimum Stage 1 outputs:

- source type and source reference
- candidate item count
- item type summary: tracks/albums/mixed/etc.
- low-confidence or ambiguous items
- optional Obsidian/Markdown note only if requested or context clearly implies it

End-of-stage response should be short:

```text
Stage 1 complete. Source: YouTube DJ set description. Found 23 candidate tracks; 5 are Unknown ID.
Continue to Stage 2: Spotify matching? This requires Spotify API credentials.
```

Do not call Spotify or create playlists in Stage 1.

## Stage 2 — Prepare data & Spotify match

Use only after Stage 1 is confirmed or when the user already provides a track list/JSONL.

Preflight:

1. Check for Spotify credentials:
   - `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
   - optional `.env`
   - optional local credentials note passed by user
2. If credentials are missing, stop and guide the user using `references/SPOTIFY_SETUP.md`.
3. Explain that users normally need their own Spotify Developer App.
4. If the user asks about free accounts, explain the current Spotify docs require Premium for Web API use and Development Mode app owners must have Premium.

Tasks:

1. Write `spotify-query-items.jsonl` as UTF-8 JSON Lines.
2. Validate JSONL parses.
3. Search Spotify catalog and write back `spotify_uri`/metadata when possible.
4. Mark ambiguous or missing matches for user review.
5. Run a dry-run before any playlist creation.

Minimum JSONL fields:

```json
{"no":1,"artist":"Kraftwerk","track":"Musique Non Stop","query":"Kraftwerk Musique Non Stop","spotify_uri":"spotify:track:...","confidence":"high"}
```

Recommended extended fields: `source_type`, `source_ref`, `position`, `rank`, `artist_raw`, `track_raw`, `item_type`, `reason`, `recommender`, `role`, `album`, `release_date`, `spotify_url`.

End-of-stage response should be short:

```text
Stage 2 complete. Spotify matched X/Y tracks. Needs review: Z.
Dry-run order looks correct.
Create or update a Spotify playlist?
```

Do not create/update playlists until the user confirms.

## Stage 3 — Publish & share

Use only after Stage 2 is confirmed.

Before playlist creation:

- Explain that creating/modifying a playlist requires Spotify user OAuth, not just Client Credentials.
- Confirm whether the playlist should be private or public.
- Confirm whether to create a new playlist or append to an existing playlist.

Use the bundled script:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<article-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --dry-run
```

Then, only after confirmation:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<article-folder>\spotify-query-items.jsonl" --name "<playlist-name>"
```

Public playlist requires explicit user request:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<article-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --public
```

Optional poster branch:

- Do not generate a poster automatically.
- Ask whether the user wants a share poster.
- If yes, ask or infer style and dimensions from the source material.
- Use public/non-secret metadata only.
- Save generated image into the article/source folder, preferably `posters/`.
- Embed with Obsidian syntax if requested: `![[posters/example.png]]`.

End-of-stage response:

```text
Stage 3 complete. Playlist: <Spotify URL>.
Updated note: [[...]].
Poster: [[...]] if generated.
```

## Spotify credential setup guidance

If the user cannot provide Spotify credentials, stop and explain the setup requirements.

Minimum user requirements:

- a Spotify account
- a Spotify Developer App
- Client ID and Client Secret from that app
- redirect URI configured exactly as `http://127.0.0.1:8888/callback`

Important conditions:

- Creating playlists requires browser OAuth authorization.
- Development/quota modes can restrict app users; for sharing broadly, users should create their own app or apply for the appropriate quota mode.
- Do not share one private Client Secret widely.

Detailed instructions live in `references/SPOTIFY_SETUP.md`; load that reference only when credentials are missing or OAuth/redirect errors occur.

## References to load only when needed

- `references/INPUT_SOURCES.md` — YouTube, Xiaohongshu, chart screenshots, playlist screenshots, books/photos, text, multi-link triage.
- `references/DEPENDENCIES.md` — packaging, missing tools, companion skills.
- `references/SPOTIFY_SETUP.md` — Client ID/Secret setup, redirect URI, OAuth errors.
- `scripts/create_spotify_playlist.py` — playlist creation/update script.

## Verification checklist

Before claiming completion, verify only the current stage:

Stage 1:
- source type is identified
- candidate items are counted
- item type is clear: track/album/artist/label/work/mixed
- low-confidence items are reported
- source material is saved only when requested or context clearly implies it

Stage 2:
- JSONL parses
- expected item count matches
- Spotify matches are written or ambiguous items are flagged
- dry-run output is reviewed

Stage 3:
- playlist URL exists if playlist creation was requested
- note is updated if requested
- poster image exists and is embedded if poster was requested

## Common mistakes

- Treating every source as a WeChat article.
- Treating every source as a track-level Spotify playlist.
- Running all stages without user confirmation.
- Fetching YouTube comments or long transcripts by default.
- Saving private chat screenshots without asking.
- Continuing after OCR uncertainty without asking for review.
- Creating a playlist before dry-run confirmation.
- Treating Client Credentials as enough for playlist creation.
- Printing secrets or token-cache content.
- Generating a poster without explicit opt-in.
