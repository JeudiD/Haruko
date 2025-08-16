Ningyo Music Bot 🎶

A standalone Python-powered Discord music bot, split from the original Ningyo Bot project to focus exclusively on music playback features.
This bot handles all voice, queue, and playback logic, while the main Ningyo Bot continues development for moderation, tracking, and utility features.

📌 Note on Hosting

Like the original, this bot can run continuously on a Windows PC as a background service (via NSSM) or on any server/VM.
It is currently configured for personal server use but can be customized for any environment.

How to Run

Create a .env file with your DISCORD_TOKEN.

Run python bot.py.

Requirements

Python 3.10+

py-cord (or discord.py master branch with voice fixes)

python-dotenv

yt-dlp

spotipy (optional, for Spotify fallback)

FFmpeg (installed and added to system PATH)

Opus library (e.g., opus.dll in the bot folder for Windows)

Commands

/join or njoin → Join your voice channel

/leave or nleave → Leave the voice channel

/play [song/URL] or nplay [song/URL] → Play or queue a track

/pause or npause → Pause playback

/resume or nresume → Resume playback

/skip or nskip → Skip current track

/stop or nstop → Stop playback and clear queue

/queue or nqueue → Show the current queue

Attribution

If you use or modify this bot, a mention or shout-out is appreciated but not required.

Steps of Bot Creation (Music-Specific)
1. Prepared Project Environment

Installed discord.py, yt-dlp, and FFmpeg.

Created base bot skeleton.

2. Implemented Voice Channel Support

Added !join to join user’s VC.

3. Verified FFmpeg Setup

Confirmed install and PATH setup.

4. Playback Errors Fixed

Resolved “ffmpeg not found” exceptions.

5. Integrated yt-dlp

Supported YouTube links and search queries.

6. Built Audio Queue

Per-guild song queues.

Auto playback with play_next().

7. Stabilized Playback

Error handling added.

Tested seamless playback.

8. Expanded Commands

Pause, resume, skip, stop, queue implemented.

9. Robust Queue + Logging

Full queue management, repeat, reconnect.

Added structured logging.

10. Persistent UI + Enhancements

Buttons for pause, resume, skip, stop, repeat, volume.

Queue pagination with navigation.

11. Polished System

Playback stability improvements.

Ephemeral slash commands for less clutter.

12. Opus Library Setup

Added opus.dll for proper voice encoding/decoding.

13. Fixed Voice Session Errors

Updated to discord.py master branch for port handling bug fix.