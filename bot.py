import discord
import os
import logging
import asyncio
import yt_dlp
from dotenv import load_dotenv
from discord.ext import commands
from discord import FFmpegPCMAudio, app_commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Load env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
if not music_token:
    raise ValueError("🚨 DISCORD_TOKEN not found in environment variables.")

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
if not spotify_client_id or not spotify_client_secret:
    raise ValueError("🚨 Spotify credentials missing for music bot.")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=spotify_client_id,
    client_secret=spotify_client_secret
))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="n", intents=intents)

# Guild ID (adjust if you want)
GUILD_ID = 1030603151033769994
GUILD_OBJ = discord.Object(id=GUILD_ID)

# Music state
song_queue = []
is_playing = False
current_voice_client = None
current_player_message = None
progress_task = None
volume = 0.1
repeat_mode = 0
disconnect_task = None
disconnect_timer = 0

# yt-dlp options
ydl_opts_youtube = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch'}

# FFmpeg options
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# Helpers
def repeat_mode_to_str(mode: int) -> str:
    return {0: "Off", 1: "Repeat One", 2: "Repeat All"}.get(mode, "Unknown")

async def send_response(ctx_or_interaction, message, ephemeral=False):
    if hasattr(ctx_or_interaction, "send"):
        await ctx_or_interaction.send(message)
    else:
        try:
            await ctx_or_interaction.response.send_message(message, ephemeral=ephemeral)
        except discord.InteractionResponded:
            await ctx_or_interaction.followup.send(message, ephemeral=ephemeral)

# --- MUSIC HANDLERS ---
async def pause_handler(ctx):
    global current_voice_client
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.pause()
        await send_response(ctx, "⏸️ Paused.", ephemeral=True)
        await update_now_playing_message()
    else:
        await send_response(ctx, "Nothing is playing.", ephemeral=True)

async def resume_handler(ctx):
    global current_voice_client
    if current_voice_client and current_voice_client.is_paused():
        current_voice_client.resume()
        await send_response(ctx, "▶️ Resumed.", ephemeral=True)
        await update_now_playing_message()
    else:
        await send_response(ctx, "Nothing is paused.", ephemeral=True)

async def skip_handler(ctx):
    global current_voice_client
    if current_voice_client and current_voice_client.is_playing():
        current_voice_client.stop()
        await send_response(ctx, "⏭️ Skipped.", ephemeral=True)
    else:
        await send_response(ctx, "Nothing is playing.", ephemeral=True)

async def stop_handler(ctx):
    global song_queue, is_playing, current_voice_client, disconnect_task, disconnect_timer, current_player_message, progress_task
    song_queue.clear()
    is_playing = False
    if current_voice_client:
        current_voice_client.stop()
        await current_voice_client.disconnect()
        current_voice_client = None
    if disconnect_task and not disconnect_task.done():
        disconnect_task.cancel()
    disconnect_timer = 0
    if current_player_message:
        try:
            await current_player_message.delete()
        except:
            pass
        current_player_message = None
    if progress_task:
        progress_task.cancel()
        progress_task = None
    await send_response(ctx, "⏹️ Stopped and disconnected.", ephemeral=True)

async def join_handler(ctx):
    channel = None
    if hasattr(ctx, 'author') and ctx.author.voice:
        channel = ctx.author.voice.channel
    elif hasattr(ctx, 'user') and ctx.user.voice:
        channel = ctx.user.voice.channel
    if channel:
        global current_voice_client
        current_voice_client = await channel.connect()
        await send_response(ctx, f"✅ Connected to {channel.name}.", ephemeral=True)
    else:
        await send_response(ctx, "You must be in a voice channel.", ephemeral=True)

async def leave_handler(ctx):
    global current_voice_client
    if current_voice_client:
        await current_voice_client.disconnect()
        current_voice_client = None
        await send_response(ctx, "👋 Disconnected.", ephemeral=True)
    else:
        await send_response(ctx, "Not connected.", ephemeral=True)

async def queue_handler(ctx):
    if not song_queue:
        await send_response(ctx, "The queue is empty.", ephemeral=True)
        return
    desc = "\n".join([f"**{i+1}.** [{song['title']}]({song['webpage_url']})" for i, song in enumerate(song_queue)])
    embed = discord.Embed(title="🎶 Queue", description=desc, color=discord.Color.green())
    await send_response(ctx, embed)

async def play_handler(ctx, search: str):
    if "open.spotify.com/track" in search:
        await handle_spotify_track(ctx, search)
        return
    await handle_queue_and_play(ctx, search)

async def repeat_mode_handler(ctx):
    global repeat_mode
    repeat_mode = (repeat_mode + 1) % 3
    await send_response(ctx, f"🔁 Repeat mode set to: {repeat_mode_to_str(repeat_mode)}", ephemeral=True)
    await update_now_playing_message()

async def volume_up_handler(ctx):
    global volume
    volume = min(volume + 0.1, 1.0)
    if current_voice_client and current_voice_client.source:
        current_voice_client.source.volume = volume
    await send_response(ctx, f"🔊 Volume: {int(volume*100)}%", ephemeral=True)
    await update_now_playing_message()

async def volume_down_handler(ctx):
    global volume
    volume = max(volume - 0.1, 0.0)
    if current_voice_client and current_voice_client.source:
        current_voice_client.source.volume = volume
    await send_response(ctx, f"🔉 Volume: {int(volume*100)}%", ephemeral=True)
    await update_now_playing_message()

# --- SPOTIFY HANDLER ---
async def handle_spotify_track(ctx, url):
    match = re.search(r"track/([a-zA-Z0-9]+)", url)
    if not match:
        await send_response(ctx, "❌ Could not extract track ID.")
        return
    track_id = match.group(1)
    track = sp.track(track_id)
    title = track["name"]
    artist = track["artists"][0]["name"]
    query = f"{title} {artist}"
    await handle_queue_and_play(ctx, query)

# --- PLAYBACK HELPERS ---
async def update_now_playing_message():
    global current_player_message, is_playing, current_voice_client
    if not current_player_message or not is_playing or not current_voice_client or not current_voice_client.is_playing():
        if current_player_message:
            try: await current_player_message.delete()
            except: pass
            current_player_message = None
        return
    song = getattr(bot, "current_song", None)
    if not song: return
    embed = discord.Embed(title="🎶 Now Playing", description=f"[{song['title']}]({song['webpage_url']})", color=discord.Color.blurple())
    embed.set_thumbnail(url=song.get('thumbnail'))
    embed.add_field(name="Requested by", value=song['requester'].mention if song['requester'] else "Unknown")
    embed.add_field(name="Repeat", value=repeat_mode_to_str(repeat_mode))
    embed.add_field(name="Volume", value=f"{int(volume*100)}%")
    await current_player_message.edit(embed=embed, view=MusicControls())

async def auto_disconnect_check():
    global disconnect_timer, current_voice_client, disconnect_task
    while current_voice_client and current_voice_client.is_connected():
        if len([m for m in current_voice_client.channel.members if not m.bot]) == 0:
            disconnect_timer += 60
            if disconnect_timer >= 300:
                await current_voice_client.disconnect()
                current_voice_client = None
                disconnect_timer = 0
                disconnect_task = None
                break
        else:
            disconnect_timer = 0
        await asyncio.sleep(60)

async def progress_updater():
    global is_playing, current_voice_client
    while is_playing and current_voice_client and current_voice_client.is_playing():
        await update_now_playing_message()
        await asyncio.sleep(5)

async def play_next(ctx):
    global is_playing, song_queue, current_voice_client, current_player_message, progress_task, volume, repeat_mode
    if not song_queue:
        is_playing = False
        if current_player_message:
            try: await current_player_message.delete()
            except: pass
            current_player_message = None
        return
    is_playing = True
    if repeat_mode == 1 and hasattr(bot, "current_song"):
        song = bot.current_song
    else:
        song = song_queue.pop(0)
        bot.current_song = song
        if repeat_mode == 2: song_queue.append(song)
    url = song['url']
    source = FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    source = discord.PCMVolumeTransformer(source, volume=volume)
    current_voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    if not current_player_message:
        embed = discord.Embed(title="🎶 Now Playing", description=f"[{song['title']}]({song['webpage_url']})", color=discord.Color.blurple())
        embed.set_thumbnail(url=song.get('thumbnail'))
        embed.add_field(name="Requested by", value=song['requester'].mention if song['requester'] else "Unknown")
        embed.add_field(name="Repeat", value=repeat_mode_to_str(repeat_mode))
        embed.add_field(name="Volume", value=f"{int(volume*100)}%")
        current_player_message = await ctx.channel.send(embed=embed, view=MusicControls())
    if not progress_task or progress_task.done():
        progress_task = bot.loop.create_task(progress_updater())

async def handle_queue_and_play(ctx, search):
    def blocking_extract():
        with yt_dlp.YoutubeDL(ydl_opts_youtube) as ydl:
            return ydl.extract_info(search, download=False)
    try:
        info = await asyncio.to_thread(blocking_extract)
    except Exception as e:
        await send_response(ctx, f"Error: {e}")
        return
    if 'entries' in info: info = info['entries'][0]
    url = info.get('url') or info.get('webpage_url')
    song = {
        'url': url,
        'title': info.get('title', 'Unknown'),
        'webpage_url': info.get('webpage_url', url),
        'thumbnail': info.get('thumbnail'),
        'requester': getattr(ctx, 'author', getattr(ctx, 'user', None))
    }
    was_empty = len(song_queue) == 0
    song_queue.append(song)
    if was_empty and (not current_voice_client or not current_voice_client.is_playing()):
        await send_response(ctx, f"▶️ Now playing: **{song['title']}**")
        await play_next(ctx)
    else:
        await send_response(ctx, f"✅ Queued: **{song['title']}**")

# --- UI VIEWS ---
class MusicControls(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.primary, custom_id="pause_btn")
    async def pause(self, i, b): await pause_handler(i)
    @discord.ui.button(label="▶️ Resume", style=discord.ButtonStyle.success, custom_id="resume_btn")
    async def resume(self, i, b): await resume_handler(i)
    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary, custom_id="skip_btn")
    async def skip(self, i, b): await skip_handler(i)
    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.danger, custom_id="stop_btn")
    async def stop(self, i, b): await stop_handler(i)
    @discord.ui.button(label="🔁 Repeat", style=discord.ButtonStyle.primary, custom_id="repeat_btn")
    async def repeat(self, i, b): await repeat_mode_handler(i)
    @discord.ui.button(label="🔊 Vol +", style=discord.ButtonStyle.secondary, custom_id="volup_btn")
    async def volup(self, i, b): await volume_up_handler(i)
    @discord.ui.button(label="🔉 Vol -", style=discord.ButtonStyle.secondary, custom_id="voldown_btn")
    async def voldown(self, i, b): await volume_down_handler(i)

# --- EVENTS ---
@bot.event
async def on_ready():
    logging.info(f"✅ Bot online as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Baseball"))
    await bot.tree.sync(guild=GUILD_OBJ)
    bot.add_view(MusicControls())

# --- PREFIX COMMANDS ---
@bot.command()
async def pause(ctx):
    await pause_handler(ctx)

@bot.command()
async def resume(ctx):
    await resume_handler(ctx)

@bot.command()
async def skip(ctx):
    await skip_handler(ctx)

@bot.command()
async def stop(ctx):
    await stop_handler(ctx)

@bot.command()
async def join(ctx):
    await join_handler(ctx)

@bot.command()
async def leave(ctx):
    await leave_handler(ctx)

@bot.command()
async def queue(ctx):
    await queue_handler(ctx)

@bot.command()
async def play(ctx, *, search: str):
    await play_handler(ctx, search)


# --- SLASH COMMANDS ---
@bot.tree.command(name="pause", description="Pause", guild=GUILD_OBJ)
async def slash_pause(interaction: discord.Interaction):
    await pause_handler(interaction)

@bot.tree.command(name="resume", description="Resume", guild=GUILD_OBJ)
async def slash_resume(interaction: discord.Interaction):
    await resume_handler(interaction)

@bot.tree.command(name="skip", description="Skip", guild=GUILD_OBJ)
async def slash_skip(interaction: discord.Interaction):
    await skip_handler(interaction)

@bot.tree.command(name="stop", description="Stop", guild=GUILD_OBJ)
async def slash_stop(interaction: discord.Interaction):
    await stop_handler(interaction)

@bot.tree.command(name="join", description="Join VC", guild=GUILD_OBJ)
async def slash_join(interaction: discord.Interaction):
    await join_handler(interaction)

@bot.tree.command(name="leave", description="Leave VC", guild=GUILD_OBJ)
async def slash_leave(interaction: discord.Interaction):
    await leave_handler(interaction)

@bot.tree.command(name="queue", description="Show queue", guild=GUILD_OBJ)
async def slash_queue(interaction: discord.Interaction):
    await queue_handler(interaction)

@bot.tree.command(name="play", description="Play music", guild=GUILD_OBJ)
@app_commands.describe(search="YouTube/Spotify/SoundCloud URL or search")
async def slash_play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    await play_handler(interaction, search)


# --- RUN ---
bot.run(token)
