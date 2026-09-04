import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "wanmusic123")

# Pakai endpoint Public Networking Railway lo
LAVALINK_URI = os.getenv(
    "LAVALINK_URI",
    "http://tokaido.proxy.rlwy.net:30072"
)

# Bersihkan Markdown link jika ada
if LAVALINK_URI.startswith("[") and "](" in LAVALINK_URI:
    LAVALINK_URI = LAVALINK_URI.split("](")[1].rstrip(")")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True
intents.guilds = True


# ============================================================
# BOT
# ============================================================

class WanMusic(commands.Bot):

    async def setup_hook(self):
        print("🔌 Connecting to Lavalink...")
        print("   URI RAW:", repr(LAVALINK_URI))
        print("   URI TYPE:", type(LAVALINK_URI))



        try:
            node = wavelink.Node(
                uri=LAVALINK_URI,
                password=LAVALINK_PASSWORD,
            )

            await wavelink.Pool.connect(
                nodes=[node],
                client=self,
            )

            print("✅ Berhasil terhubung ke Lavalink!")

        except Exception as e:
            print(
                f"❌ Gagal connect ke Lavalink: "
                f"{type(e).__name__}: {e}"
            )


bot = WanMusic(
    command_prefix="!",
    intents=intents,
)


# ============================================================
# HELPER
# ============================================================

def get_player(guild: discord.Guild):
    player = guild.voice_client

    if isinstance(player, wavelink.Player):
        return player

    return None


async def ensure_in_voice(
    interaction: discord.Interaction,
) -> wavelink.Player | None:

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return None

    member = interaction.user

    if not isinstance(member, discord.Member):
        await interaction.followup.send(
            "❌ Tidak bisa membaca member."
        )
        return None

    if not member.voice or not member.voice.channel:
        await interaction.followup.send(
            "❌ Kamu harus berada di voice channel dulu!"
        )
        return None

    user_channel = member.voice.channel
    player = get_player(guild)

    # --------------------------------------------------------
    # BOT BELUM ADA DI VC
    # --------------------------------------------------------

    if player is None:
        try:
            print(
                f"🔗 Connecting to VC: "
                f"{user_channel.name}"
            )

            player = await user_channel.connect(
                cls=wavelink.Player
            )

            print(
                f"✅ Bot masuk ke "
                f"{user_channel.name}"
            )

        except Exception as e:
            print(
                f"❌ VC connection error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal masuk VC: "
                f"`{type(e).__name__}`"
            )

            return None

    # --------------------------------------------------------
    # BOT ADA DI VC BERBEDA
    # --------------------------------------------------------

    elif player.channel != user_channel:
        try:
            print(
                f"🔄 Moving bot ke "
                f"{user_channel.name}"
            )

            await player.move_to(user_channel)

        except Exception as e:
            print(
                f"❌ Move error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal pindah VC: "
                f"`{type(e).__name__}`"
            )

            return None

    return player


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"🤖 Bot online sebagai: {bot.user}")
    print(f"🌐 Server: {len(bot.guilds)}")
    print("=" * 50)

    try:
        await bot.tree.sync()
        print("✅ Slash commands sudah disinkronkan!")

    except Exception as e:
        print(
            f"❌ Slash sync error: "
            f"{type(e).__name__}: {e}"
        )


@bot.event
async def on_wavelink_node_ready(
    payload: wavelink.NodeReadyEventPayload
):

    print(
        f"🎵 Lavalink READY: "
        f"{payload.node.identifier}"
    )


@bot.event
async def on_wavelink_track_end(
    payload: wavelink.TrackEndEventPayload
):

    player: wavelink.Player = payload.player

    if payload.track:
        print(
            f"⏹️ Track ended: "
            f"{payload.track.title}"
        )

    # --------------------------------------------------------
    # PLAY NEXT QUEUE
    # --------------------------------------------------------

    if not player.queue.is_empty:

        next_track = player.queue.get()

        print(
            f"▶️ Playing next: "
            f"{next_track.title}"
        )

        try:
            await player.play(next_track)

        except Exception as e:
            print(
                f"❌ Queue playback error: "
                f"{type(e).__name__}: {e}"
            )

    else:
        print("📭 Queue kosong.")


# ============================================================
# PING
# ============================================================

@bot.tree.command(
    name="ping",
    description="Test apakah bot online"
)
async def ping(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🎵 Djawa Adalah Koentji 👹👹"
    )


# ============================================================
# JOIN
# ============================================================

@bot.tree.command(
    name="join",
    description="Bot masuk ke voice channel"
)
async def join(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild
    member = interaction.user

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    if not isinstance(member, discord.Member):
        await interaction.followup.send(
            "❌ Tidak bisa membaca member."
        )
        return

    if not member.voice or not member.voice.channel:
        await interaction.followup.send(
            "❌ Kamu harus berada di voice channel dulu!"
        )
        return

    channel = member.voice.channel
    player = get_player(guild)

    if player is not None:

        if player.channel == channel:

            await interaction.followup.send(
                "🎵 Bot sudah ada di voice channel."
            )

        else:

            try:
                await player.move_to(channel)

                await interaction.followup.send(
                    f"🔄 Bot pindah ke "
                    f"**{channel.name}**"
                )

            except Exception as e:

                await interaction.followup.send(
                    f"❌ Gagal pindah: "
                    f"`{type(e).__name__}`"
                )

        return

    try:

        player = await channel.connect(
            cls=wavelink.Player
        )

        await interaction.followup.send(
            f"✅ Bot masuk ke "
            f"**{channel.name}** 🎵"
        )

    except Exception as e:

        print(
            f"❌ Join error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Gagal join: "
            f"`{type(e).__name__}`"
        )


# ============================================================
# LEAVE
# ============================================================

@bot.tree.command(
    name="leave",
    description="Bot keluar dari voice channel"
)
async def leave(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )
        return

    try:

        await player.disconnect()

        await interaction.followup.send(
            "👋 Bot keluar dari voice channel."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# ============================================================
# PLAY
# ============================================================

@bot.tree.command(
    name="play",
    description="Cari dan putar musik"
)
async def play(
    interaction: discord.Interaction,
    lagu: str
):

    player = await ensure_in_voice(interaction)

    if player is None:
        return

    print()
    print("=" * 60)
    print("🔍 PLAY REQUEST")
    print(f"Query: {lagu}")
    print("=" * 60)

    # ========================================================
    # SEARCH
    #
    # IMPORTANT:
    # YouTube TIDAK DIGUNAKAN.
    #
    # Lavalink config:
    # youtube: false
    #
    # Jadi kita menggunakan SoundCloud.
    # ========================================================

    try:

        # ----------------------------------------------------
        # Kalau user memberikan URL langsung
        # ----------------------------------------------------

        if lagu.startswith(
            (
                "http://",
                "https://"
            )
        ):

            print("🌐 Loading direct URL...")

            results = await wavelink.Playable.search(lagu)

        # ----------------------------------------------------
        # Kalau user memberikan nama lagu
        # ----------------------------------------------------

        else:

            print("🔎 Searching SoundCloud...")

            results = await wavelink.Playable.search(
                f"scsearch:{lagu}"
            )

        print(
            f"📦 Result type: "
            f"{type(results).__name__}"
        )

    except Exception as e:

        print(
            f"❌ Search error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Lavalink gagal mencari lagu.\n"
            f"Error: `{type(e).__name__}`"
        )

        return

    # ========================================================
    # NO RESULT
    # ========================================================

    if not results:

        print("❌ No tracks found.")

        await interaction.followup.send(
            f"❌ Lagu tidak ditemukan: "
            f"**{lagu}**\n\n"
            f"Pastikan lagu tersedia di SoundCloud."
        )

        return

    # ========================================================
    # PLAYLIST
    # ========================================================

    if isinstance(results, wavelink.Playlist):

        tracks = list(results.tracks)

        if not tracks:

            await interaction.followup.send(
                "❌ Playlist kosong."
            )

            return

        print(
            f"📋 Playlist: "
            f"{results.name}"
        )

        print(
            f"🎵 Tracks: "
            f"{len(tracks)}"
        )

        try:

            # Jika belum playing,
            # langsung mainkan track pertama.

            if not player.playing:

                first_track = tracks[0]

                await player.play(first_track)

                # Sisanya masuk queue
                if len(tracks) > 1:

                    await player.queue.put_wait(
                        tracks[1:]
                    )

            else:

                await player.queue.put_wait(
                    tracks
                )

            await interaction.followup.send(
                f"📋 Playlist **{results.name}** "
                f"ditambahkan.\n"
                f"🎵 **{len(tracks)} lagu**"
            )

        except Exception as e:

            print(
                f"❌ Playlist error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal memainkan playlist: "
                f"`{type(e).__name__}`"
            )

        return

    # ========================================================
    # SINGLE TRACK
    # ========================================================

    track = results[0]

    print(
        f"🎵 Found: "
        f"{track.title}"
    )

    print(
        f"🆔 Identifier: "
        f"{track.identifier}"
    )

    # ========================================================
    # PLAYER ALREADY PLAYING
    # ========================================================

    if player.playing:

        try:

            await player.queue.put_wait(track)

            print(
                f"➕ Added to queue: "
                f"{track.title}"
            )

            await interaction.followup.send(
                f"➕ Ditambahkan ke queue:\n"
                f"**{track.title}**"
            )

        except Exception as e:

            print(
                f"❌ Queue error: "
                f"{type(e).__name__}: {e}"
            )

            await interaction.followup.send(
                f"❌ Gagal memasukkan queue: "
                f"`{type(e).__name__}`"
            )

        return

    # ========================================================
    # START PLAYBACK
    # ========================================================

    try:

        print(
            f"▶️ Starting playback: "
            f"{track.title}"
        )

        await player.play(track)

        await interaction.followup.send(
            f"🎵 **Now Playing**\n"
            f"**{track.title}**"
        )

        print("✅ Playback started.")

    except Exception as e:

        print(
            f"❌ Playback error: "
            f"{type(e).__name__}: {e}"
        )

        await interaction.followup.send(
            f"❌ Gagal memainkan lagu.\n"
            f"Error: `{type(e).__name__}: "
            f"{str(e)[:150]}`"
        )


# ============================================================
# STOP
# ============================================================

@bot.tree.command(
    name="stop",
    description="Stop musik"
)
async def stop(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )
        return

    try:

        player.queue.clear()

        await player.stop()

        await interaction.followup.send(
            "⏹️ Musik dihentikan dan queue dikosongkan."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# ============================================================
# PAUSE
# ============================================================

@bot.tree.command(
    name="pause",
    description="Pause music"
)
async def pause(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )
        return

    if not player.playing:
        await interaction.followup.send(
            "❌ Tidak ada musik yang sedang dimainkan."
        )
        return

    try:

        await player.pause(True)

        await interaction.followup.send(
            "⏸️ Musik di-pause."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# ============================================================
# RESUME
# ============================================================

@bot.tree.command(
    name="resume",
    description="Resume music"
)
async def resume(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )
        return

    if not player.paused:
        await interaction.followup.send(
            "❌ Musik tidak sedang di-pause."
        )
        return

    try:

        await player.pause(False)

        await interaction.followup.send(
            "▶️ Musik dilanjutkan."
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# ============================================================
# SKIP
# ============================================================

@bot.tree.command(
    name="skip",
    description="Skip lagu sekarang"
)
async def skip(interaction: discord.Interaction):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:
        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )
        return

    player = get_player(guild)

    if player is None:
        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
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


# ============================================================
# VOLUME
# ============================================================

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
            "❌ Command hanya bisa digunakan di server."
        )
        return

    if level < 0 or level > 100:

        await interaction.followup.send(
            "❌ Volume harus antara 0-100."
        )

        return

    player = get_player(guild)

    if player is None:

        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )

        return

    try:

        await player.set_volume(level)

        await interaction.followup.send(
            f"🔊 Volume: **{level}%**"
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error: `{type(e).__name__}`"
        )


# ============================================================
# QUEUE
# ============================================================

@bot.tree.command(
    name="queue",
    description="Lihat queue musik"
)
async def queue_cmd(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:

        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )

        return

    player = get_player(guild)

    if player is None:

        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )

        return

    current = player.current

    if current:

        msg = (
            f"🎵 **Now Playing**\n"
            f"**{current.title}**\n\n"
        )

    else:

        msg = (
            "🎵 **Now Playing:** Tidak ada\n\n"
        )

    if player.queue.is_empty:

        msg += "📭 Queue kosong."

    else:

        msg += "📋 **Queue:**\n"

        for index, track in enumerate(
            list(player.queue)[:10],
            start=1
        ):

            msg += (
                f"`{index}.` "
                f"{track.title}\n"
            )

    await interaction.followup.send(msg)


# ============================================================
# CLEAR
# ============================================================

@bot.tree.command(
    name="clear",
    description="Kosongkan queue"
)
async def clear_queue(
    interaction: discord.Interaction
):

    await interaction.response.defer()

    guild = interaction.guild

    if guild is None:

        await interaction.followup.send(
            "❌ Command hanya bisa digunakan di server."
        )

        return

    player = get_player(guild)

    if player is None:

        await interaction.followup.send(
            "❌ Bot tidak ada di voice channel."
        )

        return

    player.queue.clear()

    await interaction.followup.send(
        "🗑️ Queue berhasil dikosongkan."
    )


# ============================================================
# RUN
# ============================================================

if not DISCORD_TOKEN:

    print("❌ DISCORD_TOKEN tidak ditemukan!")

    raise SystemExit(1)


print("🚀 Starting WanMusic...")

bot.run(DISCORD_TOKEN)