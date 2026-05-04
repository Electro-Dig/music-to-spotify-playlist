# Spotify Setup for Playlist Automation

Use this reference only when Spotify credentials are missing, OAuth fails, or the user asks how to obtain Client ID / Client Secret.

## What the user needs

To search tracks and create playlists with Spotify Web API, the user needs:

- a Spotify account; current Spotify Web API docs say a Premium account is required to use the Web API
- a Spotify Developer App
- the app's Client ID
- the app's Client Secret
- redirect URI configured exactly as `http://127.0.0.1:8888/callback`

Playlist creation also requires user OAuth authorization in the browser. Client ID/Secret alone can search the catalog, but cannot modify a user's playlist without OAuth.

## Free vs Premium account status

As of 2026-05-02, Spotify's official Web API overview says Web API use requires a Spotify Premium account. Spotify's quota-mode docs also say apps in Development Mode have extra limits:

- the app owner must have an active Premium account
- the app can have up to 5 authenticated users
- users must be explicitly allowlisted in the app settings
- non-allowlisted users receive API errors

For shared GitHub use, assume each user needs to create their own Spotify Developer App and may need Premium. If a user only has a free account, tell them this may fail at developer app creation, authorization, or API calls and point them to Spotify's current docs.

## Important conditions

- Do not ask users to share Client Secret publicly.
- Do not commit `.env`, token caches, Client Secrets, access tokens, or refresh tokens.
- For open-source/shared use, each user should normally create their own Spotify Developer App.
- Spotify development/quota modes can restrict who may use the app. Development Mode is for small allowlisted testing; wider access requires Spotify's quota/extension review process.

## Create a Spotify Developer App

1. Open Spotify Developer Dashboard: https://developer.spotify.com/dashboard
2. Log in with a Spotify account.
3. Click **Create app**.
4. Fill in an app name and description.
5. Add this Redirect URI exactly:

```text
http://127.0.0.1:8888/callback
```

6. Accept the developer terms and create the app.
7. Open the app settings.
8. Copy the **Client ID**.
9. Reveal/copy the **Client Secret**.

## Store credentials safely

Recommended: environment variables in the current shell session:

```powershell
$env:SPOTIFY_CLIENT_ID="your_client_id"
$env:SPOTIFY_CLIENT_SECRET="your_client_secret"
```

Alternative: local `.env` file, not committed to git:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

Then pass it to the script if needed:

```powershell
python ".codex\skills\music-to-spotify-playlist\scripts\create_spotify_playlist.py" --env-file ".env" --tracks "<article-folder>\spotify-query-items.jsonl" --dry-run
```

## OAuth scopes

The bundled playlist script uses:

```text
playlist-modify-private
playlist-modify-public
```

Use `playlist-modify-private` for private playlists. `playlist-modify-public` is needed when creating or editing public playlists.

## Redirect URI error

If the browser shows:

```text
redirect_uri: Not matching configuration
```

Check all of these:

- Spotify Dashboard contains `http://127.0.0.1:8888/callback` exactly.
- It is not `localhost`.
- It has no trailing slash.
- Port is `8888`.
- The app being edited has the same Client ID used by the script.
- Changes in the Dashboard were saved.

## Official references

- Web API overview: https://developer.spotify.com/documentation/web-api
- Authorization Code Flow: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
- Redirect URIs: https://developer.spotify.com/documentation/web-api/concepts/redirect_uri
- Apps: https://developer.spotify.com/documentation/web-api/concepts/apps
- Quota modes: https://developer.spotify.com/documentation/web-api/concepts/quota-modes
- Create Playlist: https://developer.spotify.com/documentation/web-api/reference/create-playlist
- Add Items to Playlist: https://developer.spotify.com/documentation/web-api/reference/add-items-to-playlist
