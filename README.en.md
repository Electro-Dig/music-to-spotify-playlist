# music-to-spotify-playlist

<p align="right">
  <a href="./README.md"><img alt="中文" src="https://img.shields.io/badge/中文-切换-lightgrey"></a>
  <a href="./README.en.md"><img alt="English" src="https://img.shields.io/badge/English-current-blue"></a>
</p>

A Codex Skill that turns music screenshots, WeChat/articles, YouTube DJ sets, playlist screenshots, charts, book excerpts, and text tracklists into Spotify-ready data, then creates Spotify playlists after confirmation.

## What It Does

- Extracts candidate music items from images, articles, links, and pasted text.
- Preserves order, timestamps, chart ranks, source context, and low-confidence items.
- Writes Spotify matching JSONL.
- Matches tracks against Spotify and runs a dry-run first.
- Creates a new playlist or appends to an existing playlist after confirmation.
- Optionally saves Obsidian/Markdown notes or generates share posters.

The default flow is lightweight: extract music, confirm Spotify credentials, match Spotify, dry-run, then create the playlist. Obsidian notes, article archiving, and posters are opt-in.

## Use Cases

- Turn a music recommendation screenshot into a Spotify playlist.
- Extract mentioned tracks from a WeChat article or web article.
- Extract tracklists from YouTube DJ sets or radio show descriptions.
- Convert Spotify, Apple Music, NetEase Cloud Music, QQ Music, or Shazam screenshots to Spotify.
- Turn charts, book excerpts, and research material into candidate listening lists before deciding whether to create a playlist.

## Requirements

- A skill-capable agent environment that can read/write files and run Python, such as Codex Desktop, Codex CLI, Claude Code, or similar tools.
- Python 3.10+.
- `requests`.
- A Spotify account and Spotify Developer App.
- `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
- Browser OAuth authorization for playlist creation. Client ID/Secret alone cannot create or modify a user's playlist.

Spotify's current Web API docs say Web API use requires Premium. Development Mode apps also require a Premium app owner and are limited to up to 5 allowlisted authenticated users. Free accounts may fail during developer app setup, authorization, or API calls. See `references/SPOTIFY_SETUP.md`, [Spotify Web API](https://developer.spotify.com/documentation/web-api), and [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes).

## Install

Place this folder in a supported Codex skill root:

```text
~/.codex/skills/music-to-spotify-playlist
```

or:

```text
~/.agents/skills/music-to-spotify-playlist
```

Invoke it with:

```text
$music-to-spotify-playlist
```

## Quick Start

1. Set Spotify credentials:

```powershell
$env:SPOTIFY_CLIENT_ID="your_client_id"
$env:SPOTIFY_CLIENT_SECRET="your_client_secret"
```

2. Ask your agent:

```text
$music-to-spotify-playlist Turn the songs in this screenshot into a Spotify playlist
```

3. The agent extracts candidate tracks, reports low-confidence items, and asks whether to continue with Spotify matching.

   If local Spotify Developer App credentials are not available, the workflow stops and guides setup first. It does not use general web search as a substitute for Spotify API matching.

4. Run a dry-run after matching:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --dry-run
```

5. Create a private playlist after review:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>"
```

Create a public playlist only when explicitly requested:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --tracks "<source-folder>\spotify-query-items.jsonl" --name "<playlist-name>" --public
```

## Default Flow

1. **Collect & transcribe**: classify the source and extract candidate music items.
2. **Prepare & match**: confirm Spotify Developer App credentials, write JSONL, match Spotify, and flag uncertain items.
3. **Publish & share**: dry-run first, then create or update a playlist after confirmation.

Obsidian/Markdown output is optional and only used when note saving, archiving, or documentation is requested.

## Project Structure

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

## Privacy

Spotify credentials and OAuth tokens stay in the local environment. The script reads only environment variables, `.env`, or an explicitly supplied `--credentials-note`; it does not automatically scan private Obsidian notes.

During matching and playlist creation, the script sends track search queries and playlist write requests to the Spotify API. If Spotify credentials are unavailable, the skill stops for setup instead of using web search, lyrics sites, or other music databases to guess Spotify URIs. Saving screenshots, articles, or private chat content as Markdown/Obsidian notes is always optional.

## Cloud and Mobile Use

This skill works best on a local computer because Spotify OAuth defaults to:

```text
http://127.0.0.1:8888/callback
```

If the agent runs on a cloud server and the phone is only the chat interface, the OAuth callback may not reach the machine running the script. Cloud setups need extra handling such as port forwarding, a remote browser, or a public HTTPS callback.

## License

MIT
