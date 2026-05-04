#!/usr/bin/env python3
"""Create or update a Spotify playlist from a JSONL track list.

This script intentionally does not print Spotify secrets. It reads credentials from
SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET first, then an optional .env file, then
an optional credentials note supplied with --credentials-note.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
import time
import warnings
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Sequence
from urllib.parse import parse_qs, urlencode, urlparse

warnings.filterwarnings("ignore", message=r"urllib3 .*charset_normalizer.*", category=Warning)

try:
    import requests
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit("Missing dependency: requests. Install with: python -m pip install requests") from exc

SPOTIFY_ACCOUNTS = "https://accounts.spotify.com"
SPOTIFY_API = "https://api.spotify.com/v1"
DEFAULT_PORT = 8888
PRIVATE_SCOPES = ("playlist-modify-private",)
PUBLIC_SCOPES = ("playlist-modify-private", "playlist-modify-public")
DEFAULT_PLAYLIST_NAME = "Obsidian Spotify Playlist"
DEFAULT_DESCRIPTION = (
    "Generated from an Obsidian JSONL track list."
)
TOKEN_CACHE = Path.home() / ".spotify_token_cache_obsidian_playlist.json"


def configure_utf8_stdio() -> None:
    """Keep Windows terminals from crashing on artist names like Thomas Köner."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_utf8_stdio()


@dataclass(frozen=True)
class Credentials:
    client_id: str
    client_secret: str


@dataclass(frozen=True)
class Track:
    no: int
    artist: str
    track: str
    spotify_uri: str | None = None
    spotify_id: str | None = None
    spotify_url: str | None = None

    @property
    def query_simple(self) -> str:
        return f"{self.artist} {self.track}".strip()

    @property
    def query_filter(self) -> str:
        return f"artist:{self.artist} track:{self.track}".strip()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Minimal local callback handler for Spotify authorization code flow."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - BaseHTTPRequestHandler name
        return

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        qs = parse_qs(parsed.query)
        self.server.auth_code = qs.get("code", [None])[0]  # type: ignore[attr-defined]
        self.server.auth_state = qs.get("state", [None])[0]  # type: ignore[attr-defined]
        self.server.auth_error = qs.get("error", [None])[0]  # type: ignore[attr-defined]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = """
        <html><body style="font-family: sans-serif; line-height: 1.5; padding: 2rem;">
        <h1>Spotify authorization received</h1>
        <p>You can close this tab and return to the terminal.</p>
        </body></html>
        """.encode("utf-8")
        self.wfile.write(body)


def default_tracks_path() -> Path:
    return Path(__file__).resolve().parent / "spotify-query-items.jsonl"


def load_env_file(path: Path | None) -> None:
    """Load SPOTIFY_CLIENT_ID/SECRET from a simple .env file if present.

    This avoids requiring python-dotenv and does not print values.
    Existing environment variables win.
    """
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    else:
        candidates.extend([
            Path.cwd() / ".env",
            Path(__file__).resolve().parent / ".env",
        ])
    for candidate in candidates:
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            if key not in {"SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"}:
                continue
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def read_credentials(note_path: Path | None = None) -> Credentials:
    env_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    env_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if env_id and env_secret:
        return Credentials(env_id, env_secret)

    if note_path:
        if not note_path.exists():
            raise FileNotFoundError(f"Credentials note not found: {note_path}")
        text = note_path.read_text(encoding="utf-8-sig")
        client_id = _extract_backtick_value(text, "Client ID") or _extract_env_style_value(text, "SPOTIFY_CLIENT_ID")
        client_secret = _extract_backtick_value(text, "Client Secret") or _extract_env_style_value(text, "SPOTIFY_CLIENT_SECRET")
        if client_id and client_secret:
            return Credentials(client_id, client_secret)
        raise ValueError(f"Credentials note does not contain Client ID and Client Secret: {note_path}")

    raise FileNotFoundError(
        "Spotify credentials not found. Set SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET, "
        "pass --env-file, or explicitly pass --credentials-note. "
        "Create a Spotify Developer App first if you do not have a Client ID and Client Secret. "
        "Do not use web search as a fallback for Spotify URI matching."
    )


def _extract_backtick_value(text: str, label: str) -> str | None:
    import re

    m = re.search(rf"{re.escape(label)}\s*[:：]\s*`([^`]+)`", text)
    return m.group(1).strip() if m else None


def _extract_env_style_value(text: str, key: str) -> str | None:
    import re

    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^\n#]+)", text, flags=re.M)
    return m.group(1).strip().strip('"').strip("'") if m else None


def load_tracks(path: Path) -> list[Track]:
    if not path.exists():
        raise FileNotFoundError(f"Track JSONL not found: {path}")
    tracks: list[Track] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
        track_value = obj.get("track", obj.get("title"))
        missing = [key for key in ("no", "artist") if key not in obj]
        if track_value is None:
            missing.append("track")
        if missing:
            raise ValueError(f"Missing {missing} at {path}:{line_no}")
        tracks.append(
            Track(
                no=int(obj["no"]),
                artist=str(obj["artist"]).strip(),
                track=str(track_value).strip(),
                spotify_uri=(str(obj["spotify_uri"]).strip() if obj.get("spotify_uri") else None),
                spotify_id=(str(obj["spotify_id"]).strip() if obj.get("spotify_id") else None),
                spotify_url=(str(obj["spotify_url"]).strip() if obj.get("spotify_url") else None),
            )
        )
    return tracks


def build_auth_url(client_id: str, redirect_uri: str, state: str, scopes: Sequence[str]) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "show_dialog": "false",
    }
    return f"{SPOTIFY_ACCOUNTS}/authorize?{urlencode(params)}"


def basic_auth_header(credentials: Credentials) -> str:
    raw = f"{credentials.client_id}:{credentials.client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def token_is_valid(token: dict) -> bool:
    return bool(token.get("access_token")) and float(token.get("expires_at", 0)) > time.time() + 60


def load_cached_token(cache_path: Path = TOKEN_CACHE) -> dict | None:
    if not cache_path.exists():
        return None
    try:
        token = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return token if isinstance(token, dict) else None


def save_cached_token(token: dict, cache_path: Path = TOKEN_CACHE) -> None:
    cache_path.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def add_expiry(token: dict) -> dict:
    enriched = dict(token)
    enriched["expires_at"] = time.time() + int(enriched.get("expires_in", 3600))
    return enriched


def refresh_access_token(credentials: Credentials, refresh_token: str) -> dict:
    resp = requests.post(
        f"{SPOTIFY_ACCOUNTS}/api/token",
        headers={"Authorization": basic_auth_header(credentials)},
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Spotify token refresh failed: HTTP {resp.status_code} {resp.text[:500]}")
    token = add_expiry(resp.json())
    token.setdefault("refresh_token", refresh_token)
    return token


def exchange_code_for_token(credentials: Credentials, code: str, redirect_uri: str) -> dict:
    resp = requests.post(
        f"{SPOTIFY_ACCOUNTS}/api/token",
        headers={"Authorization": basic_auth_header(credentials)},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Spotify authorization failed: HTTP {resp.status_code} {resp.text[:500]}")
    return add_expiry(resp.json())


def wait_for_auth_code(port: int, expected_state: str, timeout_seconds: int) -> str:
    server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
    server.timeout = 1
    server.auth_code = None  # type: ignore[attr-defined]
    server.auth_state = None  # type: ignore[attr-defined]
    server.auth_error = None  # type: ignore[attr-defined]
    deadline = time.time() + timeout_seconds
    try:
        while time.time() < deadline:
            server.handle_request()
            if server.auth_error:  # type: ignore[attr-defined]
                raise RuntimeError(f"Spotify authorization error: {server.auth_error}")  # type: ignore[attr-defined]
            if server.auth_code:  # type: ignore[attr-defined]
                if server.auth_state != expected_state:  # type: ignore[attr-defined]
                    raise RuntimeError("OAuth state mismatch. Refusing to continue.")
                return str(server.auth_code)  # type: ignore[attr-defined]
    finally:
        server.server_close()
    raise TimeoutError(f"Timed out after {timeout_seconds}s waiting for Spotify login callback")


def get_user_token(
    credentials: Credentials,
    redirect_uri: str,
    scopes: Sequence[str],
    port: int,
    cache_path: Path,
    no_browser: bool = False,
    timeout_seconds: int = 300,
) -> dict:
    cached = load_cached_token(cache_path)
    if cached and token_is_valid(cached):
        return cached
    if cached and cached.get("refresh_token"):
        token = refresh_access_token(credentials, str(cached["refresh_token"]))
        save_cached_token(token, cache_path)
        return token

    state = secrets.token_urlsafe(24)
    auth_url = build_auth_url(credentials.client_id, redirect_uri, state, scopes)
    print("Open this Spotify authorization URL if the browser does not open automatically:")
    print(auth_url)
    print()
    print("Waiting for Spotify login callback...")
    if not no_browser:
        webbrowser.open(auth_url)
    code = wait_for_auth_code(port, state, timeout_seconds)
    token = exchange_code_for_token(credentials, code, redirect_uri)
    save_cached_token(token, cache_path)
    return token


def spotify_api(method: str, path: str, token: dict, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token['access_token']}"
    if "json" in kwargs:
        headers.setdefault("Content-Type", "application/json")
    url = f"{SPOTIFY_API}{path}"
    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    if resp.status_code >= 400:
        raise RuntimeError(f"Spotify API {method} {path} failed: HTTP {resp.status_code} {resp.text[:500]}")
    return resp.json() if resp.text else None


def get_current_user(token: dict) -> dict:
    return spotify_api("GET", "/me", token)


def create_playlist(token: dict, user_id: str, name: str, description: str, public: bool) -> dict:
    return spotify_api(
        "POST",
        f"/users/{user_id}/playlists",
        token,
        json={"name": name, "description": description, "public": public},
    )


def add_tracks_to_playlist(token: dict, playlist_id: str, uris: Sequence[str]) -> None:
    for i in range(0, len(uris), 100):
        chunk = list(uris[i : i + 100])
        spotify_api("POST", f"/playlists/{playlist_id}/items", token, json={"uris": chunk})


def get_client_credentials_token(credentials: Credentials) -> dict:
    resp = requests.post(
        f"{SPOTIFY_ACCOUNTS}/api/token",
        headers={"Authorization": basic_auth_header(credentials)},
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Spotify client credentials auth failed: HTTP {resp.status_code} {resp.text[:500]}")
    return add_expiry(resp.json())


def search_track_uri(client_token: dict, track: Track) -> str | None:
    for query in (track.query_filter, track.query_simple):
        resp = requests.get(
            f"{SPOTIFY_API}/search",
            headers={"Authorization": f"Bearer {client_token['access_token']}"},
            params={"q": query, "type": "track", "limit": 5},
            timeout=30,
        )
        if resp.status_code != 200:
            continue
        items = resp.json().get("tracks", {}).get("items", [])
        if items:
            return items[0].get("uri")
    return None


def tracks_needing_search(tracks: Sequence[Track], refresh_search: bool) -> list[Track]:
    if refresh_search:
        return list(tracks)
    return [track for track in tracks if not track.spotify_uri]


def resolve_track_uris(
    tracks: Sequence[Track],
    credentials: Credentials,
    refresh_search: bool,
    resolve_missing: bool,
) -> list[str]:
    unresolved = tracks_needing_search(tracks, refresh_search)
    if unresolved and not resolve_missing and not refresh_search:
        details = ", ".join(f"{t.no}. {t.artist} - {t.track}" for t in unresolved)
        raise RuntimeError(
            "Track JSONL has items without spotify_uri. Finish Stage 2 matching first "
            f"or rerun with --resolve-missing. Missing: {details}"
        )

    uris: list[str] = []
    missing: list[Track] = []
    client_token: dict | None = None
    for track in tracks:
        if track.spotify_uri and not refresh_search:
            uris.append(track.spotify_uri)
            continue
        if client_token is None:
            client_token = get_client_credentials_token(credentials)
        uri = search_track_uri(client_token, track)
        if uri:
            uris.append(uri)
        else:
            missing.append(track)
    if missing:
        details = ", ".join(f"{t.no}. {t.artist} - {t.track}" for t in missing)
        raise RuntimeError(f"Could not resolve Spotify URIs for: {details}")
    return uris


def print_track_plan(tracks: Sequence[Track]) -> None:
    print(f"Track list: {len(tracks)} items")
    for track in tracks:
        suffix = f" -> {track.spotify_uri}" if track.spotify_uri else " -> needs search"
        print(f"{track.no:02d}. {track.artist} - {track.track}{suffix}")


def print_resolved_plan(tracks: Sequence[Track], uris: Sequence[str]) -> None:
    print(f"Resolved Spotify plan: {len(uris)} items")
    for track, uri in zip(tracks, uris, strict=True):
        print(f"{track.no:02d}. {track.artist} - {track.track} -> {uri}")


def scopes_for_request(public: bool) -> tuple[str, ...]:
    return PUBLIC_SCOPES if public else PRIVATE_SCOPES


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Spotify playlist from spotify-query-items.jsonl")
    parser.add_argument("--tracks", type=Path, default=default_tracks_path(), help="Path to spotify-query-items.jsonl")
    parser.add_argument("--credentials-note", type=Path, help="Optional note containing Client ID/Secret")
    parser.add_argument("--env-file", type=Path, help="Optional .env file with SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    parser.add_argument("--name", default=DEFAULT_PLAYLIST_NAME, help="Playlist name")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION, help="Playlist description")
    parser.add_argument("--public", action="store_true", help="Create a public playlist or request public-playlist scope. Default is private.")
    parser.add_argument("--playlist-id", help="Append tracks to an existing playlist instead of creating a new one")
    parser.add_argument("--resolve-missing", action="store_true", help="Search Spotify for tracks without spotify_uri instead of failing")
    parser.add_argument("--refresh-search", action="store_true", help="Ignore JSONL spotify_uri fields and re-search all tracks")
    parser.add_argument("--dry-run", action="store_true", help="Show the final Spotify URI plan without creating or modifying a playlist")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Local OAuth callback port")
    parser.add_argument("--redirect-uri", help="OAuth redirect URI. Must exactly match Spotify Dashboard setting")
    parser.add_argument("--cache", type=Path, default=TOKEN_CACHE, help="User token cache path")
    parser.add_argument("--no-browser", action="store_true", help="Print auth URL without opening the browser")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for Spotify auth callback")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    tracks = load_tracks(args.tracks)
    print_track_plan(tracks)

    if args.dry_run:
        unresolved = tracks_needing_search(tracks, args.refresh_search)
        if unresolved and not (args.resolve_missing or args.refresh_search):
            details = ", ".join(f"{t.no}. {t.artist} - {t.track}" for t in unresolved)
            raise RuntimeError(
                "Dry run failed because some tracks need Spotify search. "
                f"Finish Stage 2 matching first or pass --resolve-missing. Missing: {details}"
            )
        if unresolved:
            load_env_file(args.env_file)
            credentials = read_credentials(args.credentials_note)
            uris = resolve_track_uris(
                tracks=tracks,
                credentials=credentials,
                refresh_search=args.refresh_search,
                resolve_missing=True,
            )
        else:
            uris = [str(track.spotify_uri) for track in tracks]
        print()
        print_resolved_plan(tracks, uris)
        print("\nDry run only. No Spotify playlist was created or modified.")
        return 0

    load_env_file(args.env_file)
    credentials = read_credentials(args.credentials_note)
    uris = resolve_track_uris(
        tracks=tracks,
        credentials=credentials,
        refresh_search=args.refresh_search,
        resolve_missing=args.resolve_missing,
    )
    redirect_uri = args.redirect_uri or f"http://127.0.0.1:{args.port}/callback"
    token = get_user_token(
        credentials=credentials,
        redirect_uri=redirect_uri,
        scopes=scopes_for_request(bool(args.public)),
        port=args.port,
        cache_path=args.cache,
        no_browser=args.no_browser,
        timeout_seconds=args.timeout,
    )

    if args.playlist_id:
        playlist_id = args.playlist_id
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        print(f"Appending {len(uris)} tracks to existing playlist: {playlist_id}")
    else:
        me = get_current_user(token)
        playlist = create_playlist(
            token=token,
            user_id=me["id"],
            name=args.name,
            description=args.description,
            public=bool(args.public),
        )
        playlist_id = playlist["id"]
        playlist_url = playlist.get("external_urls", {}).get("spotify", f"https://open.spotify.com/playlist/{playlist_id}")
        print(f"Created playlist: {playlist.get('name', args.name)}")

    add_tracks_to_playlist(token, playlist_id, uris)
    print(f"Added {len(uris)} tracks.")
    print(f"Playlist URL: {playlist_url}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
