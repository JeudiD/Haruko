# Haruko - Music Discord Bot 🎶

A standalone Python-powered Discord music bot, split from the original Ningyo Bot project to focus exclusively on music playback features.
This bot handles all voice, queue, and playback logic, while the main Ningyo Bot continues development for moderation, tracking, and utility features.

### 📌 Note on Hosting
Like the original, this bot can run continuously on a Windows PC as a background service (via NSSM) or on any server/VM.

It is currently configured for personal server use but can be customized for any environment.

## How to Run
1. Create a .env file with your DISCORD_TOKEN.
2. Run python bot.py.

## Requirements
- Python 3.10+
- py-cord (or discord.py master branch with voice fixes)
- python-dotenv
- yt-dlp
- spotipy (optional, for Spotify fallback)
- FFmpeg (installed and added to system PATH)
- Opus library (e.g., opus.dll in the bot folder for Windows)

## Commands
- /join or njoin → Join your voice channel
- /leave or nleave → Leave the voice channel
- /play [song/URL] or nplay [song/URL] → Play or queue a track
- /pause or npause → Pause playback
- /resume or nresume → Resume playback
- /skip or nskip → Skip current track
- /stop or nstop → Stop playback and clear queue
- /queue or nqueue → Show the current queue

## Attribution

If you use or modify this bot, a simple shout-out or mention would be appreciated but is not required. Thanks for supporting my work!

# Steps of Bot Creation 

# 1. Prepared Project Environment
- Installed discord.py, yt-dlp, and FFmpeg.
- Created base bot skeleton.

# 2. Implemented Voice Channel Support
- Added !join to join user’s VC.

# 3. Verified FFmpeg Setup
- Confirmed install and PATH setup.

# 4. Playback Errors Fixed
- Resolved “ffmpeg not found” exceptions.

# 5. Integrated yt-dlp
- Supported YouTube links and search queries.

# 6. Built Audio Queue
- Per-guild song queues.
- Auto playback with play_next().

# 7. Stabilized Playback
- Error handling added.
- Tested seamless playback.

# 8. Expanded Commands
- Pause, resume, skip, stop, queue implemented.

# 9. Robust Queue + Logging
- Full queue management, repeat, reconnect.
- Added structured logging.

# 10. Persistent UI + Enhancements
- Buttons for pause, resume, skip, stop, repeat, volume.
- Queue pagination with navigation.

# 11. Polished System
- Playback stability improvements.
- Ephemeral slash commands for less clutter.

# 12. Opus Library Setup
- Added opus.dll for proper voice encoding/decoding.

# 13. Fixed Voice Session Errors
- Updated to discord.py master branch for port handling bug fix.

# 14. Queue Pagination Fix
- Added proper page tracking for the queue UI.
- Queue now correctly shows pages starting at 1/1 instead of 0/0.
- Left (⬅️) and right (➡️) page buttons work independently without resetting to the first page.

# 15. Queue UI Controls
- Moved queue-specific buttons (pagination, clear queue) to the queue UI instead of the player UI.
- Clear queue button now only affects the queue embed.

# 16. Clear Queue Behavior
- Clearing the queue resets the queue page to 1.
- Queue embed updates immediately to reflect an empty queue.

# 17. Now Playing Embed When Idle
- Now Playing embed now shows "Not currently playing anything" when the player is idle.
- Prevents misleading display of previous songs when playback stops.

# 18. Slash Command Interaction Feedback
- /play command ephemeral response changed from 🎧 to 🔍 emoji.
- Provides clear visual cue that the bot is searching/processing.

# 19. Player Volume & Repeat State Updates
Embed updates now correctly reflect volume and repeat mode in real time.
Changes triggered via buttons immediately update the player embed.

# 20. General UI Persistence
Both player and queue embeds persist in chat after song ends.
Ensures users can still view queue and last played info without misleading "Now Playing" data.

# 21. Removed Queue Command
The manual queue command (both prefix and slash) was removed.
The queue embed is now persistent and updates automatically, so the command is no longer necessary.