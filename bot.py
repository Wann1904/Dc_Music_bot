import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import subprocess
import wavelink

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    if not wavelink.Pool.nodes:
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                wavelink.Node(
                    host="tokaido.proxy.rlwy.net",
                    port="30072",
                    password="wanmusic123"
                )
            ]
        )

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

@bot.tree.command(name="play", description="Play musik lokal by name")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    guild = interaction.guild
    
    if guild.voice_client is None:
        await interaction.followup.send("❌ Bot harus join VC dulu!")
        return
    
    music_dir = "music"
    
    # Cari file yang match query
    files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
    
    # Fuzzy search - case insensitive
    matching = [f for f in files if query.lower() in f.lower()]
    
    if not matching:
        await interaction.followup.send(f"❌ Musik `{query}` tidak ditemukan!")
        await interaction.followup.send(f"Coba: `/list` untuk lihat semua musik")
        return
    
    if len(matching) > 1:
        msg = f"🔍 Found {len(matching)} matches:\n"
        for i, file in enumerate(matching[:10], 1):
            msg += f"{i}. {file}\n"
        msg += f"\nGunakan nama yang lebih spesifik!"
        await interaction.followup.send(msg)
        return
    
    # Play lagu yang cocok
    filename = matching[0]
    music_path = os.path.join(music_dir, filename)
    
    if guild.voice_client.is_playing():
        guild.voice_client.stop()
    
    try:
        audio_source = discord.FFmpegPCMAudio(music_path)
        guild.voice_client.play(audio_source)
        
        # Tampilkan nama lagu tanpa .mp3
        song_name = filename.replace('.mp3', '')
        await interaction.followup.send(f"🎵 Now Playing: **{song_name}**")
        print(f"Playing: {filename}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {type(e).__name__}")
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