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
LAVALINK_URI = os.getenv(
    "LAVALINK_URI",
    "http://tokaido.proxy.rlwy.net:30072"
)


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
        """
        Connect to Lavalink before the bot becomes ready.
        """

        try:
            nodes = [
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ]

            await wavelink.Pool.connect(
                nodes=nodes,
                client=self
            )

            print("✅ Berhasil terhubung ke Lavalink!")

        except Exception as e:
            print(
                f"❌ Gagal connect ke Lavalink: "
                f"{type(e).__name__}: {e}"
            )


bot = WanMusic(
    command_prefix="!",
    intents=intents
)


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
        print(
            f"❌ Gagal sync slash commands: "
            f"{type(e).__name__}: {e}"
        )


@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):

    print(
        f"🎵 Lavalink ready: "
        f"{payload.node.identifier}"
    )


# =========================
# PING
# =========================

@bot.tree.command(
    name="ping",
    description="Test apakah bot online"
)
async def ping(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎵 Djawa Adalah Koentji 👹👹"
    )


# =========================
# JOIN
# =========================

@bot.tree.command(
    name="join",
    description="Bot masuk ke voice channel"
)
async def join(interaction: discord.Interaction):

    await interaction.response.defer()

    member = interaction.user
    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    if not isinstance(member, discord.Member):
        await interaction.followup.send(
            "❌ Tidak bisa membaca member."
        )
        return

    if member.voice is None or member.voice.channel is None:
        await interaction.followup.send(
            "❌ Kamu harus berada di voice channel dulu!"
        )
        return

    channel = member.voice.channel

    # Kalau sudah ada player
    if guild.voice_client is not None:

        player = guild.voice_client

        if isinstance(player, wavelink.Player):

            if player.channel == channel:
                await interaction.followup.send(
                    "Bot sudah ada di voice channel."
                )
                return

            try:
                await player.move_to(channel)

                await interaction.followup.send(
                    f"✅ Bot pindah ke **{channel.name}** 🎵"
                )

            except Exception as e:

                print(
                    f"❌ Move error: "
                    f"{type(e).__name__}: {e}"
                )

                await interaction.followup.send(
                    f"❌ Gagal pindah: `{type(e).__name__}`"
                )

            return

    # Connect menggunakan Wavelink Player
    try:

        player: wavelink.Player = await channel.connect(
            cls=wavelink.Player
        )

        await interaction.followup.send(
            f"✅ Bot masuk ke **{channel.name}** 🎵"
        )

        print(
            f"✅ Bot join ke {channel.name}"
        )

    except Exception as e:

        print(
            f"❌ Join error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Gagal join: `{type(e).__name__}`"
        )


# =========================
# LEAVE
# =========================

@bot.tree.command(
    name="leave",
    description="Bot keluar dari voice channel"
)
async def leave(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if player is None:
        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    try:

        if isinstance(player, wavelink.Player):
            await player.disconnect()
        else:
            await player.disconnect()

        await interaction.followup.send(
            "✅ Bot keluar dari voice channel 👋"
        )

    except Exception as e:

        print(
            f"❌ Leave error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# PLAY
# =========================

@bot.tree.command(
    name="play",
    description="Cari dan putar musik menggunakan Lavalink"
)
async def play(
    interaction: discord.Interaction,
    query: str
):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    # Pastikan user berada di VC
    member = interaction.user

    if not isinstance(member, discord.Member):
        await interaction.followup.send(
            "❌ Tidak bisa membaca member."
        )
        return

    if member.voice is None or member.voice.channel is None:
        await interaction.followup.send(
            "❌ Kamu harus berada di voice channel dulu!"
        )
        return

    user_channel = member.voice.channel

    # Ambil player
    player = guild.voice_client

    # Kalau belum connect → otomatis join
    if player is None:

        try:

            player: wavelink.Player = await user_channel.connect(
                cls=wavelink.Player
            )

            print(
                f"✅ Auto-join ke {user_channel.name}"
            )

        except Exception as e:

            print(
                f"❌ Auto-join error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal masuk VC: `{type(e).__name__}`"
            )
            return

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "❌ Voice client bukan Wavelink Player."
        )
        return

    # Kalau user ada di VC berbeda → pindah
    if player.channel != user_channel:

        try:

            await player.move_to(user_channel)

        except Exception as e:

            print(
                f"❌ Move error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal pindah VC: `{type(e).__name__}`"
            )
            return

    # =========================
    # SEARCH
    # =========================

    try:

        tracks: wavelink.Search = await wavelink.Playable.search(
            query
        )

    except Exception as e:

        print(
            f"❌ Search error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Gagal mencari lagu: `{type(e).__name__}`"
        )
        return

    if not tracks:

        await interaction.followup.send(
            f"❌ Lagu `{query}` tidak ditemukan."
        )
        return

    # Kalau hasil berupa playlist
    if isinstance(tracks, wavelink.Playlist):

        track = tracks.tracks[0]

        await player.queue.put_wait(tracks.tracks)

        if not player.playing:

            await player.play(track)

        await interaction.followup.send(
            f"🎵 Playlist **{tracks.name}** ditambahkan."
        )

        return

    # Ambil hasil pertama
    track = tracks[0]

    # =========================
    # PLAY / QUEUE
    # =========================

    if player.playing:

        await player.queue.put_wait(track)

        await interaction.followup.send(
            f"➕ Ditambahkan ke queue: "
            f"**{track.title}**"
        )

    else:

        await player.play(track)

        await interaction.followup.send(
            f"🎵 Now Playing: **{track.title}**"
        )

    print(
        f"🎵 Playing: {track.title}"
    )


# =========================
# STOP
# =========================

@bot.tree.command(
    name="stop",
    description="Stop musik"
)
async def stop(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    if not player.playing:

        await interaction.followup.send(
            "Bot tidak sedang play musik."
        )
        return

    try:

        await player.stop()

        # Bersihkan queue
        player.queue.clear()

        await interaction.followup.send(
            "⏹️ Music stopped."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# PAUSE
# =========================

@bot.tree.command(
    name="pause",
    description="Pause music"
)
async def pause(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    if not player.playing:

        await interaction.followup.send(
            "Bot tidak sedang play musik."
        )
        return

    try:

        await player.pause(True)

        await interaction.followup.send(
            "⏸️ Music paused."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# RESUME
# =========================

@bot.tree.command(
    name="resume",
    description="Resume music"
)
async def resume(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    if not player.paused:

        await interaction.followup.send(
            "Tidak ada musik yang sedang di-pause."
        )
        return

    try:

        await player.pause(False)

        await interaction.followup.send(
            "▶️ Music resumed."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# VOLUME
# =========================

@bot.tree.command(
    name="volume",
    description="Set volume (0-100)"
)
async def volume(
    interaction: discord.Interaction,
    level: int
):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    if level < 0 or level > 100:

        await interaction.followup.send(
            "❌ Volume harus 0-100!"
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    try:

        await player.set_volume(level)

        await interaction.followup.send(
            f"🔊 Volume: **{level}%**"
        )

    except Exception as e:

        print(
            f"❌ Volume error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# QUEUE
# =========================

@bot.tree.command(
    name="queue",
    description="Lihat queue musik"
)
async def queue(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    current = player.current

    if current:

        msg = (
            f"🎵 **Now Playing**\n"
            f"**{current.title}**\n\n"
        )

    else:

        msg = "🎵 **Now Playing:** Tidak ada\n\n"

    if player.queue.is_empty:

        msg += "📭 Queue kosong."

    else:

        msg += "📋 **Queue:**\n"

        for index, track in enumerate(
            list(player.queue)[:10],
            start=1
        ):

            msg += (
                f"`{index}.` {track.title}\n"
            )

    await interaction.followup.send(msg)


# =========================
# SKIP
# =========================

@bot.tree.command(
    name="skip",
    description="Skip lagu sekarang"
)
async def skip(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    if not player.current:

        await interaction.followup.send(
            "❌ Tidak ada lagu yang sedang dimainkan."
        )
        return

    try:

        await player.skip()

        await interaction.followup.send(
            "⏭️ Lagu di-skip."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# =========================
# CLEAR QUEUE
# =========================

@bot.tree.command(
    name="clear",
    description="Kosongkan queue"
)
async def clear(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command ini hanya bisa digunakan di server."
        )
        return

    player = guild.voice_client

    if not isinstance(player, wavelink.Player):

        await interaction.followup.send(
            "Bot tidak ada di voice channel."
        )
        return

    player.queue.clear()

    await interaction.followup.send(
        "🗑️ Queue berhasil dikosongkan."
    )


# =========================
# RUN
# =========================

if not DISCORD_TOKEN:

    print(
        "❌ DISCORD_TOKEN tidak ditemukan!"
    )

    raise SystemExit(1)


bot.run(DISCORD_TOKEN)