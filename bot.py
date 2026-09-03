import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import subprocess

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot sudah online sebagai {bot.user}")
    print(f"Bot di {len(bot.guilds)} server")
    print("Slash commands sudah disinkronkan!")


@bot.tree.command(name="ping", description="Test apakah bot online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🎵 Djawa Adalah Koentji👹👹")


@bot.tree.command(name="join", description="Bot masuk ke voice channel")
async def join(interaction: discord.Interaction):
    await interaction.response.defer()
    
    member = interaction.user
    guild = interaction.guild
    
    if member.voice is None or member.voice.channel is None:
        await interaction.followup.send("❌ Kamu harus di voice channel dulu!")
        return
    
    channel = member.voice.channel
    
    if guild.voice_client is not None:
        await interaction.followup.send("Bot sudah ada di voice channel.")
        return
    
    try:
        await channel.connect()
        await interaction.followup.send(f"✅ Bot masuk ke **{channel.name}** 🎵")
        print(f"✅ Bot join ke {channel.name}")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        await interaction.followup.send(f"❌ Gagal join: `{type(e).__name__}`")


@bot.tree.command(name="leave", description="Bot keluar dari voice channel")
async def leave(interaction: discord.Interaction):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return
    
    try:
        await guild.voice_client.disconnect()
        await interaction.followup.send("✅ Bot keluar dari voice channel 👋")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {type(e).__name__}")


@bot.tree.command(name="play", description="Play musik dari YouTube")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("❌ Bot harus join voice channel dulu!")
        return
    
    try:
        await interaction.followup.send(f"🔍 Mencari: `{query}`...")
        print(f"DEBUG: Searching {query}")
        
        cmd = [
            'yt-dlp',
            f'ytsearch:{query}',
            '-f', 'bestaudio/best',
            '-g',
            '-q'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"DEBUG: stdout = {result.stdout}")
        print(f"DEBUG: stderr = {result.stderr}")
        print(f"DEBUG: returncode = {result.returncode}")
        
        url = result.stdout.strip().split('\n')[0]
        
        if not url:
            await interaction.followup.send(f"❌ Musik tidak ditemukan!\nError: {result.stderr}")
            return
        
        audio_source = discord.FFmpegPCMAudio(
            url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn'
        )
        
        guild.voice_client.play(audio_source)
        await interaction.followup.send(f"🎵 Playing: **{query}**")
        
    except Exception as e:
        print(f"ERROR: {repr(e)}")
        await interaction.followup.send(f"❌ Error: {type(e).__name__}: {str(e)}")
@bot.tree.command(name="stop", description="Stop music")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return
    
    if not guild.voice_client.is_playing():
        await interaction.followup.send("Bot tidak sedang play musik.")
        return
    
    guild.voice_client.stop()
    await interaction.followup.send("⏹️ Music stopped.")


@bot.tree.command(name="pause", description="Pause music")
async def pause(interaction: discord.Interaction):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return
    
    if not guild.voice_client.is_playing():
        await interaction.followup.send("Bot tidak sedang play musik.")
        return
    
    guild.voice_client.pause()
    await interaction.followup.send("⏸️ Music paused.")


@bot.tree.command(name="resume", description="Resume music")
async def resume(interaction: discord.Interaction):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return
    
    if guild.voice_client.is_playing():
        await interaction.followup.send("Bot sudah play musik.")
        return
    
    if guild.voice_client.is_paused():
        guild.voice_client.resume()
        await interaction.followup.send("▶️ Music resumed.")
    else:
        await interaction.followup.send("Tidak ada musik yang di-pause.")


@bot.tree.command(name="volume", description="Set volume (0-100)")
async def volume(interaction: discord.Interaction, level: int):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return
    
    if level < 0 or level > 100:
        await interaction.followup.send("❌ Volume harus 0-100!")
        return
    
    try:
        if guild.voice_client.is_playing():
            guild.voice_client.source.volume = level / 100
            await interaction.followup.send(f"🔊 Volume: **{level}%**")
        else:
            await interaction.followup.send("Bot tidak sedang play musik.")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {type(e).__name__}")


@bot.tree.command(name="list", description="List musik lokal")
async def list_music(interaction: discord.Interaction):
    await interaction.response.defer()
    
    music_dir = "music"
    
    if not os.path.exists(music_dir):
        await interaction.followup.send("❌ Folder musik tidak ada!")
        return
    
    files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
    
    if not files:
        await interaction.followup.send("❌ Tidak ada file MP3!")
        return
    
    msg = "🎵 **Daftar Musik:**\n"
    for i, file in enumerate(files, 1):
        msg += f"{i}. `{file}`\n"
    
    await interaction.followup.send(msg)


# Run bot
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ DISCORD_TOKEN tidak ditemukan di .env!")
    exit(1)

bot.run(token)