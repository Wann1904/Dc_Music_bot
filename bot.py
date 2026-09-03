import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink


# =========================
# ENVIRONMENT
# =========================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "wanmusic123")
LAVALINK_URI = os.getenv("LAVALINK_URI", "http://tokaido.proxy.rlwy.net:30072")


# =========================
# INTENTS
# =========================

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True
intents.guilds = True


# =========================
# BOT
# =========================

class WanMusic(commands.Bot):

    async def setup_hook(self):
        """Connect to Lavalink before the bot becomes ready."""

        try:
            nodes = [
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ]

            await wavelink.Pool.connect(nodes=nodes, client=self)
            print("✅ Berhasil terhubung ke Lavalink!")

        except Exception as e:
            print(f"❌ Gagal connect ke Lavalink: {type(e).__name__}: {e}")


bot = WanMusic(command_prefix="!", intents=intents)


# =========================
# HELPER FUNCTIONS
# =========================

def get_player(guild):
    """Get wavelink player dari guild"""
    player = guild.voice_client
    return player if isinstance(player, wavelink.Player) else None


async def ensure_in_voice(interaction: discord.Interaction) -> wavelink.Player | None:
    """Pastikan user dan bot di VC yang sama. Return player atau None."""

    await interaction.response.defer()
    
    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return None

    member = interaction.user
    if not isinstance(member, discord.Member):
        await interaction.followup.send("❌ Tidak bisa membaca member.")
        return None

    if not member.voice or not member.voice.channel:
        await interaction.followup.send("❌ Kamu harus berada di voice channel dulu!")
        return None

    user_channel = member.voice.channel
    player = get_player(guild)

    # Bot belum connect
    if player is None:
        try:
            player = await user_channel.connect(cls=wavelink.Player)
            print(f"✅ Auto-join ke {user_channel.name}")
        except Exception as e:
            print(f"❌ Auto-join error: {type(e).__name__}: {e}")
            await interaction.followup.send(f"❌ Gagal masuk VC: `{type(e).__name__}`")
            return None

    # Bot di VC berbeda
    elif player.channel != user_channel:
        try:
            await player.move_to(user_channel)
        except Exception as e:
            print(f"❌ Move error: {type(e).__name__}: {e}")
            await interaction.followup.send(f"❌ Gagal pindah VC: `{type(e).__name__}`")
            return None

    return player


# =========================
# EVENTS
# =========================

@bot.event
async def on_ready():
    print(f"✅ Bot sudah online sebagai {bot.user}")
    print(f"Bot di {len(bot.guilds)} server")

    try:
        await bot.tree.sync()
        print("✅ Slash commands sudah disinkronkan!")
    except Exception as e:
        print(f"❌ Gagal sync slash commands: {type(e).__name__}: {e}")


@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"🎵 Lavalink ready: {payload.node.identifier}")


@bot.event
async def on_wavelink_node_down(payload: wavelink.NodeDownEventPayload):
    print(f"❌ Lavalink node down: {payload.node.identifier}")
    # Bot akan reconnect otomatis via wavelink


@bot.event
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    """Otomatis mainkan track berikutnya dari queue"""
    
    player: wavelink.Player = payload.player

    if not player.queue.is_empty:
        track = player.queue.get()
        await player.play(track)
    else:
        print(f"✅ Queue selesai di {player.guild.name}")


# =========================
# COMMANDS
# =========================

@bot.tree.command(name="ping", description="Test apakah bot online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🎵 Djawa Adalah Koentji 👹👹")


@bot.tree.command(name="join", description="Bot masuk ke voice channel")
async def join(interaction: discord.Interaction):

    await interaction.response.defer()

    member = interaction.user
    guild = interaction.guild

    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    if not isinstance(member, discord.Member):
        await interaction.followup.send("❌ Tidak bisa membaca member.")
        return

    if not member.voice or not member.voice.channel:
        await interaction.followup.send("❌ Kamu harus berada di voice channel dulu!")
        return

    channel = member.voice.channel
    player = get_player(guild)

    # Bot sudah ada
    if player is not None:
        if player.channel == channel:
            await interaction.followup.send("Bot sudah ada di voice channel.")
        else:
            try:
                await player.move_to(channel)
                await interaction.followup.send(f"✅ Bot pindah ke **{channel.name}** 🎵")
            except Exception as e:
                print(f"❌ Move error: {type(e).__name__}: {e}")
                await interaction.followup.send(f"❌ Gagal pindah: `{type(e).__name__}`")
        return

    # Connect baru
    try:
        player = await channel.connect(cls=wavelink.Player)
        await interaction.followup.send(f"✅ Bot masuk ke **{channel.name}** 🎵")
        print(f"✅ Bot join ke {channel.name}")

    except Exception as e:
        print(f"❌ Join error: {type(e).__name__}: {e}")
        await interaction.followup.send(f"❌ Gagal join: `{type(e).__name__}`")


@bot.tree.command(name="leave", description="Bot keluar dari voice channel")
async def leave(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    try:
        await player.disconnect()
        await interaction.followup.send("✅ Bot keluar dari voice channel 👋")

    except Exception as e:
        print(f"❌ Leave error: {type(e).__name__}: {e}")
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="play", description="Cari dan putar musik menggunakan Lavalink")
async def play(interaction: discord.Interaction, query: str):

    player = await ensure_in_voice(interaction)
    if player is None:
        return

    guild = interaction.guild

    # Search
    try:
        tracks = await wavelink.Playable.search(query)

    except Exception as e:
        print(f"❌ Search error: {type(e).__name__}: {e}")
        await interaction.followup.send(f"❌ Gagal mencari lagu: `{type(e).__name__}`")
        return

    if not tracks:
        await interaction.followup.send(f"❌ Lagu `{query}` tidak ditemukan.")
        return

    # Handle playlist
    if isinstance(tracks, wavelink.Playlist):
        track_list = tracks.tracks
        await player.queue.put_wait(track_list)

        if not player.playing:
            await player.play(track_list[0])

        await interaction.followup.send(f"🎵 Playlist **{tracks.name}** ditambahkan ({len(track_list)} lagu).")
        return

    # Handle single track
    track = tracks[0]

    if player.playing:
        await player.queue.put_wait(track)
        await interaction.followup.send(f"➕ Ditambahkan ke queue: **{track.title}**")
    else:
        await player.play(track)
        await interaction.followup.send(f"🎵 Now Playing: **{track.title}**")

    print(f"🎵 Playing: {track.title}")


@bot.tree.command(name="stop", description="Stop musik")
async def stop(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    if not player.playing:
        await interaction.followup.send("Bot tidak sedang play musik.")
        return

    try:
        await player.stop()
        player.queue.clear()
        await interaction.followup.send("⏹️ Music stopped.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="pause", description="Pause music")
async def pause(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    if not player.playing:
        await interaction.followup.send("Bot tidak sedang play musik.")
        return

    try:
        await player.pause(True)
        await interaction.followup.send("⏸️ Music paused.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="resume", description="Resume music")
async def resume(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    if not player.paused:
        await interaction.followup.send("Musik tidak sedang di-pause.")
        return

    try:
        await player.pause(False)
        await interaction.followup.send("▶️ Music resumed.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="skip", description="Skip lagu sekarang")
async def skip(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    if not player.current:
        await interaction.followup.send("❌ Tidak ada lagu yang sedang dimainkan.")
        return

    try:
        await player.skip()
        await interaction.followup.send("⏭️ Lagu di-skip.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="volume", description="Set volume (0-100)")
async def volume(interaction: discord.Interaction, level: int):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    if level < 0 or level > 100:
        await interaction.followup.send("❌ Volume harus 0-100!")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    try:
        await player.set_volume(level)
        await interaction.followup.send(f"🔊 Volume: **{level}%**")

    except Exception as e:
        print(f"❌ Volume error: {type(e).__name__}: {e}")
        await interaction.followup.send(f"❌ Error: `{type(e).__name__}`")


@bot.tree.command(name="queue", description="Lihat queue musik")
async def queue_cmd(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    current = player.current

    if current:
        msg = f"🎵 **Now Playing**\n**{current.title}**\n\n"
    else:
        msg = "🎵 **Now Playing:** Tidak ada\n\n"

    if player.queue.is_empty:
        msg += "📭 Queue kosong."
    else:
        msg += "📋 **Queue:**\n"
        for index, track in enumerate(list(player.queue)[:10], start=1):
            msg += f"`{index}.` {track.title}\n"

    await interaction.followup.send(msg)


@bot.tree.command(name="clear", description="Kosongkan queue")
async def clear_queue(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Command ini hanya bisa digunakan di server.")
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send("Bot tidak ada di voice channel.")
        return

    player.queue.clear()
    await interaction.followup.send("🗑️ Queue berhasil dikosongkan.")


# =========================
# RUN
# =========================

if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN tidak ditemukan!")
    raise SystemExit(1)

bot.run(DISCORD_TOKEN)