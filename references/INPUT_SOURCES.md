# Input Sources and Triage

Use this reference only during Stage 1 when the input is not a simple saved WeChat article, or when the user provides mixed links/images/screenshots.

## Core idea

Treat every source as **music evidence** first. Do not assume it is already a track-level Spotify playlist.

Normalize source material into candidate items:

```json
{
  "source_type": "youtube_description",
  "source_ref": "https://youtube.com/...",
  "position": "00:05:42",
  "rank": null,
  "item_type": "track",
  "artist": "Drexciya",
  "track": "Andreaen Sand Dunes",
  "raw_text": "05:42 Drexciya - Andreaen Sand Dunes",
  "confidence": "high",
  "notes": ""
}
```

## Ask output intent when unclear

If the user only says “整理一下” and has not said where the result should go, ask one short question before heavy work:

```text
你希望这次输出到哪里？
A. 直接生成 Spotify 歌单
B. 只在聊天里整理
C. 生成 Spotify 可匹配 JSONL
D. 另存为 Obsidian/Markdown 笔记
```

If the user provides a screenshot/article/link and asks for a playlist, the default is: extract items, confirm Spotify credentials, match Spotify via the official API, dry-run, then ask before creating the playlist. Do not write to an Obsidian vault unless the user asks for a saved note.

## Supported source types

### 1. YouTube video URL / DJ set / radio show

Common signals:

- video title contains DJ set, mix, radio, live, Boiler Room, NTS, Rinse, set, tracklist
- description has timestamps
- description has repeated `Artist - Track`
- comments may contain “track ID” but should not be fetched by default

Default action:

1. Read title/channel/description if available.
2. Extract timestamped or line-based tracklist.
3. Preserve timestamps as `position`.
4. Mark `Unknown ID`, `ID?`, `unreleased`, or missing artist/title as low confidence.
5. Ask before trying comments/transcripts, because they can be long and noisy.

End Stage 1 example:

```text
Found 23 candidate tracks from the YouTube description; 5 are Unknown ID.
Continue to Spotify matching?
```

### 2. Xiaohongshu / Instagram-style cards and screenshots

Common signals:

- multiple image cards
- phrases like 最近循环, 入门, 必听, 私藏, 适合..., 推荐
- cover collage plus short captions
- may be track-level, album-level, or mixed

Default action:

1. OCR and visually inspect cards.
2. Determine item type: track, album, artist, label, or mixed.
3. Preserve image/card order.
4. Ask if the source appears album-level rather than track-level.

Clarifying question when needed:

```text
这些更像专辑/作品推荐，不一定都是单曲。你希望整理成：
A. 专辑清单
B. 尽量转成 Spotify 曲目歌单
C. 研究型听歌清单
```

### 3. Music chart / ranking screenshot

Common signals:

- rank numbers
- Top 10 / Top 50 / best of year / chart /榜单
- publication or magazine layout

Default action:

1. Preserve rank.
2. Identify item type: track, album, artist, label, mixed.
3. Do not force album charts into track playlists.
4. Ask whether to match tracks, albums, or make a research note.

### 4. Music platform playlist screenshots

Examples:

- Spotify screenshot
- Apple Music screenshot
- NetEase Cloud Music / QQ Music screenshot
- Shazam history
- YouTube Music screenshot

Default action:

1. Preserve visible order.
2. OCR title, artist, duration when available.
3. Note truncated titles/artists.
4. For non-Spotify screenshots, normalize Chinese/translated names carefully.
5. Proceed to Spotify matching only after Stage 1 confirmation.

### 5. Books, PDFs, research notes, electronic music history material

Common signals:

- book/page photo
- exhibition material
- bibliography/discography
- artist history, label history, representative works

Default action:

1. Treat as research evidence, not an immediate playlist.
2. Extract works, albums, artists, labels, catalog numbers, years.
3. Default output should be a research listening list.
4. Ask before converting to Spotify tracks.

### 6. Text paste / chat screenshots / comment snippets

Common signals:

- friend/group recommendations
- lines of `Artist - Track`
- multiple Spotify/Bandcamp/YouTube links
- chat screenshots

Default action:

1. Extract links and text separately.
2. Preserve recommender/context if visible.
3. Deduplicate only after extracting raw items.
4. Ask before saving private chat content into Obsidian.

### 7. Multi-link input

Common links:

- Spotify tracks/albums/playlists
- YouTube videos
- Bandcamp releases
- SoundCloud/Mixcloud sets
- Discogs releases

Default action:

1. Classify each link by platform.
2. Extract public metadata when available.
3. Merge into candidate items.
4. Ask whether to preserve source links in the note.

## Confidence labels

Use simple labels:

- `high`: exact artist/title or URL metadata exists.
- `medium`: likely match but OCR/title is partially uncertain.
- `low`: truncated, ambiguous, Unknown ID, or inferred from context.

Do not silently “fix” low-confidence items. Report them at the Stage 1 gate.

## When not to playlist-ify

Do not automatically turn the source into a Spotify playlist when:

- it is mostly artist names without works
- it is an album or label chart and the user did not ask for track conversion
- it contains private chat content and the user has not approved saving
- it is too blurry to verify
- it contains only one or two casual song mentions
