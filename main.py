import datetime
import random
import nextcord
from nextcord.ext import commands
import nextwave
from nextwave.ext import spotify
from typing import Optional
import numpy as np
from configparser import ConfigParser
import logging
import os

# Create folder for Logs
if not os.path.exists("Logs"):
    os.makedirs("Logs")

# Create and configure logger
logging.basicConfig(
    filename=f"Logs/Frostmourne_tunes_logs_{datetime.datetime.today().strftime('%Y_%m_%d_%H%M%S')}.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filemode="w",
)
log = logging.getLogger()

config = ConfigParser()
config.read(".env")
Token = config.get("Discord", "TOKEN")
Spotify_client_id = config.get("Spotify", "CLIENT_ID")
Spotify_client_secret = config.get("Spotify", "CLIENT_SECRET")

# Add all intents
intents = nextcord.Intents(messages=True, guilds=True).all()

bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    description="\
        Greetings, mortal.\n\
        I am Arthas Menethil, the Lich King and master of this music bot.\n\
        I will play you songs that will chill your bones and freeze your soul.\n\
        Do you dare to listen?\n",
)

# some useful variables
global user_arr, user_dict
user_dict = {}
user_arr = np.array([])
setattr(nextwave.Player, "lq", False)
embed_color = nextcord.Color.from_rgb(128, 67, 255)

# Create the custom help command
bot.remove_command("help")


@bot.group(invoke_without_command=True)
async def help(ctx, helpstr: Optional[str]):
    bot_cmds = [
        skip_command,
        del_command,
        move_command,
        clear_command,
        seek_command,
        volume_command,
        skipto_command,
        shuffle_command,
        loop_command,
        disconnect_command,
        loopqueue_command,
        setrole_command,
        spotifyplay_command,
    ]
    member_cmds = [
        ping_command,
        play_command,
        pause_command,
        resume_command,
        nowplaying_command,
        queue_command,
        save_command,
    ]
    all_cmds = bot_cmds + member_cmds
    if helpstr:
        if helpstr in [cmd.name for cmd in all_cmds]:
            for cmd in all_cmds:
                if helpstr == cmd.name:
                    embed = nextcord.Embed(
                        title=f",{cmd.name}",
                        description=f"**Function**: `{cmd.help}`\n\n**Use**: {cmd.description}",
                        color=embed_color,
                    )
                    await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Command not found",
                description="The command you are looking for does not exist.\n\n\
                    Type `/help` to get a list of all commands.\n\n",
                color=embed_color,
            )
            await ctx.send(embed=embed)
    else:
        botmm = "".join(f"`/{i.name}` " for i in bot_cmds)
        mm = "".join(f"`/{j.name}` " for j in member_cmds)
        help_description = f"{bot.description}\n\n**member commands**\n{mm}\n\n**bot commands**\n{botmm}\n\n"
        embed = nextcord.Embed(
            title="Frostmourne_Tunes Help",
            description=help_description,
            color=embed_color,
        )
        embed.add_field(
            name="type /help <command name> for more information about that command",
            value="To use bot-commands, server owner/admin can provide **bot** role to the member\n",
        )
        await ctx.send(embed=embed)


# Set role command
@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="setrole",
    help="sets an existing role which are below tishmish(role) for a user",
    pass_context=True,
    description="/setrole <role name>",
)
@commands.has_permissions(administrator=True)
async def setrole_command(ctx, user: nextcord.Member, role: nextcord.Role):
    await user.add_roles(role)
    embed = nextcord.Embed(
        description=f"`{user.name}` has been given a role called: **{role.name}**",
        color=embed_color,
    )
    await ctx.send(embed=embed)


# Command to test the ping
@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(name="ping", help="displays bot's latency", description=",ping")
async def ping_command(ctx):
    log.info(f"{ctx.author} used ping command")
    embed = nextcord.Embed(
        description=f"**Pong!**\n\n`{round(bot.latency*1000)}`ms", color=embed_color
    )
    await ctx.send(embed=embed)


async def user_connectivity(ctx: commands.Context):
    if not getattr(ctx.author.voice, "channel", None):
        await ctx.send(
            embed=nextcord.Embed(
                description="Try after joining a `voice channel`",
                color=embed_color,
            )
        )
        return False


@bot.event
async def on_ready():
    log.info(f"Logged in as: {bot.user.name}")
    print(f"Logged in as: {bot.user.name}")
    bot.loop.create_task(node_connect())
    await bot.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/help")
    )


@bot.event
async def on_nextwave_node_ready(node: nextwave.Node):
    print(f"Node {node.identifier} connected successfully")


async def node_connect():
    await bot.wait_until_ready()
    await nextwave.NodePool.create_node(
        bot=bot,
        host="lavalink.lexnet.cc",
        port=443,
        password="lexn3tl@val!nk",
        https=True,
        spotify_client=spotify.SpotifyClient(
            client_id=Spotify_client_id, client_secret=Spotify_client_secret
        ),
    )


@bot.event
async def on_nextwave_track_end(player: nextwave.Player, track: nextwave.Track, reason):
    ctx = player.ctx
    vc: player = ctx.voice_client

    if vc.loop:
        return await vc.play(track)

    try:
        if not vc.queue.is_empty:
            if vc.lq:
                vc.queue.put(vc.queue._queue[0])
            next_song = vc.queue.get()
            await vc.play(next_song)
            await ctx.send(
                embed=nextcord.Embed(
                    description=f"**Current song playing from the `QUEUE`**\n\n`{next_song.title}`",
                    color=embed_color,
                ),
                delete_after=30,
            )
            # {code to remove the song name from the numpy array}
    except Exception as e:
        print(e)
        await vc.stop()
        return await ctx.send(
            embed=nextcord.Embed(
                description="No songs in the `QUEUE`", color=embed_color
            )
        )


@bot.event
async def on_command_error(ctx: commands.Context, error):
    log.warning(f"{ctx.author} used {ctx.command.name} command, got an error: {error}")
    if isinstance(error, commands.CommandOnCooldown):
        em = nextcord.Embed(
            description=f"**Cooldown active**\ntry again in `{error.retry_after:.2f}`s*",
            color=embed_color,
        )
        await ctx.send(embed=em)
        log.warning(f"{ctx.author} is on cooldown")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=nextcord.Embed(description="Missing `arguments`", color=embed_color)
        )
        log.warning(f"{ctx.author} is missing arguments")


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(name="info", help="Shows information about the bot")
@commands.is_owner()
async def info_command(ctx: commands.Context):
    log.info(f"{ctx.author} used info command")
    await ctx.send(
        embed=nextcord.Embed(
            description=f"**Info**\nTotal server count: `{len(bot.guilds)}`",
            color=embed_color,
        )
    )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="loop_queue",
    help="starts the loop queue ==> /loop_queue start or /loop_queue enable\n\
        stops the loop queue ==> /loop_queue stop or /loop_queue disable",
    description="/loop_queue <mode>",
)
async def loopqueue_command(ctx: commands.Context, type: str):
    vc: nextwave.Player = ctx.voice_client
    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(
                description="Unable to loop `QUEUE`, try adding more songs..",
                color=embed_color,
            )
        )
    if vc.lq is False and type in {"start", "enable"}:
        vc.lq = True
        await ctx.send(
            embed=nextcord.Embed(
                description="**loop queue**: `enabled`", color=embed_color
            )
        )
        try:
            if vc._source not in vc.queue:
                vc.queue.put(vc._source)
            else:
                """"""
        except Exception as e:
            print(e)
            return ""
    if vc.lq is True and type in {"stop", "disable"}:
        vc.lq = False
        await ctx.send(
            embed=nextcord.Embed(
                description="**loopqueue**: `disabled`", color=embed_color
            )
        )
        if song_count == 1 and vc.queue._queue[0] == vc._source:
            del vc.queue._queue[0]
        else:
            return ""
    if type not in ["start", "enable", "disable", "stop"]:
        await ctx.send(
            embed=nextcord.Embed(
                description="check **/help** for **loopqueue**", color=embed_color
            )
        )


@commands.cooldown(1, 1, commands.BucketType.user)
@bot.command(
    name="play",
    help="plays the given track provided by the user",
    description="/play <song name>",
)
async def play_command(ctx: commands.Context, *, search: nextwave.YouTubeTrack):
    log.info(f"{ctx.author} used play command")
    if not getattr(ctx.author.voice, "channel", None):
        log.warning(f"{ctx.author} is not in a voice channel")
        return await ctx.send(
            embed=nextcord.Embed(
                description="Try after joining voice channel",
                color=embed_color,
            )
        )
    elif not ctx.voice_client:
        vc: nextwave.Player = await ctx.author.voice.channel.connect(
            cls=nextwave.Player
        )
    else:
        vc: nextwave.Player = ctx.voice_client

    log.info(f"{ctx.author} searched for {search}")
    if vc.queue.is_empty and vc.is_playing() is False:
        playString = await ctx.send(
            embed=nextcord.Embed(description="**searching...**", color=embed_color)
        )
        await vc.play(search)
        await playString.edit(
            embed=nextcord.Embed(
                description=f"**Search found**\n\n`{search.title}`", color=embed_color
            )
        )
    else:
        await vc.queue.put_wait(search)
        await ctx.send(
            embed=nextcord.Embed(
                description=f"Added to the `QUEUE`\n\n`{search.title}`",
                color=embed_color,
            )
        )

    vc.ctx = ctx
    setattr(vc, "loop", False)
    user_dict[search.identifier] = ctx.author.mention


@commands.cooldown(1, 1, commands.BucketType.user)
@bot.command(
    name="splay",
    help="plays the provided spotify playlist link",
    description="/splay <spotify playlist link>",
)
async def spotifyplay_command(ctx: commands.Context, search: str):
    log.info(f"{ctx.author} used splay command")
    if not getattr(ctx.author.voice, "channel", None):
        return await ctx.send(
            embed=nextcord.Embed(
                description="Try after joining voice channel",
                color=embed_color,
            )
        )
    elif not ctx.voice_client:
        vc: nextwave.Player = await ctx.author.voice.channel.connect(
            cls=nextwave.Player
        )
    else:
        vc: nextwave.Player = ctx.voice_client

    async for partial in spotify.SpotifyTrack.iterator(
        query=search, type=spotify.SpotifySearchType.playlist, partial_tracks=True
    ):
        log.info(f"playing {partial.title}")
        if vc.queue.is_empty and vc.is_playing() is False:
            await vc.play(partial)
        else:
            await vc.queue.put_wait(partial)
        song_name = await nextwave.tracks.YouTubeTrack.search(partial.title)
        user_dict[song_name[0].identifier] = ctx.author.mention

    log.info(f"finished adding {search} to queue")
    vc.ctx = ctx
    setattr(vc, "loop", False)


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="pause",
    help="pauses the current playing track",
    description=",pause",
)
async def pause_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client

    if vc._source:
        if not vc.is_paused():
            await vc.pause()
            await ctx.send(
                embed=nextcord.Embed(
                    description="`PAUSED` the music!", color=embed_color
                )
            )

        elif vc.is_paused():
            await ctx.send(
                embed=nextcord.Embed(
                    description="Already in `PAUSED State`", color=embed_color
                )
            )
    else:
        await ctx.send(
            embed=nextcord.Embed(
                description="Player is not `playing`!", color=embed_color
            )
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(name="resume", help="resumes the paused track", description=",resume")
async def resume_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client

    if vc.is_playing():
        if vc.is_paused():
            await vc.resume()
            await ctx.send(
                embed=nextcord.Embed(description="Music `RESUMED`!", color=embed_color)
            )

        elif vc.is_playing():
            await ctx.send(
                embed=nextcord.Embed(
                    description="Already in `RESUMED State`", color=embed_color
                )
            )
    else:
        await ctx.send(
            embed=nextcord.Embed(
                description="Player is not `playing`!", color=embed_color
            )
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(name="skip", help="skips to the next track", description=",s")
async def skip_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client

    if vc.loop is True:
        vclooptxt = "Disable the `LOOP` to skip | \n\
            **/loop** again to disable the `LOOP` | \n\
            Add a new song to disable the `LOOP`"
        return await ctx.send(
            embed=nextcord.Embed(description=vclooptxt, color=embed_color)
        )

    elif vc.queue.is_empty:
        await vc.stop()
        await vc.resume()
        return await ctx.send(
            embed=nextcord.Embed(
                description="Song stopped! No songs in the `QUEUE`",
                color=embed_color,
            )
        )

    else:
        await vc.stop()
        vc.queue._wakeup_next()
        await vc.resume()
        return await ctx.send(
            embed=nextcord.Embed(description="`SKIPPED`!", color=embed_color)
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="disconnect",
    help="disconnects the player from the vc",
    description=",dc",
)
async def disconnect_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    try:
        await vc.disconnect(force=True)
        await ctx.send(
            embed=nextcord.Embed(
                description="**BYE!** Have a great time!", color=embed_color
            )
        )
    except Exception as e:
        log.error(e)
        await ctx.send(
            embed=nextcord.Embed(description="Failed to destroy!", color=embed_color)
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="nowplaying",
    help="shows the current track information",
    description=",np",
)
async def nowplaying_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if not vc.is_playing():
        return await ctx.send(
            embed=nextcord.Embed(description="Not playing anything!", color=embed_color)
        )

    # vcloop conditions
    loopstr = "enabled" if vc.loop else "disabled"
    state = "paused" if vc.is_paused() else "playing"
    """numpy array usertag indexing"""
    global user_list
    user_list = list(user_dict.items())
    user_arr = np.array(user_list)
    song_index = np.flatnonzero(
        np.core.defchararray.find(user_arr, vc.track.identifier) == 0
    )
    arr_index = int(song_index / 2)

    requester = user_arr[arr_index, 1]

    nowplaying_description = (
        f"[`{vc.track.title}`]({str(vc.track.uri)})\n\n**Requested by**: {requester}"
    )
    em = nextcord.Embed(
        description=f"**Now Playing**\n\n{nowplaying_description}", color=embed_color
    )
    em.add_field(
        name="**Song Info**",
        value=f"• Author: `{vc.track.author}`\n• Duration: `{str(datetime.timedelta(seconds=vc.track.length))}`",
    )
    em.add_field(
        name="**Player Info**",
        value=f"• Player Volume: `{vc._volume}`\n• Loop: `{loopstr}`\n• Current State: `{state}`",
        inline=False,
    )

    return await ctx.send(embed=em)


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="loop",
    help="•loops the current song\n•unloops the current song",
    description=",loop",
)
async def loop_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if not vc._source:
        return await ctx.send(
            embed=nextcord.Embed(description="No song to `loop`", color=embed_color)
        )
    try:
        vc.loop ^= True
    except Exception as e:
        log.error(e)
        setattr(vc, "loop", False)
    return (
        await ctx.send(
            embed=nextcord.Embed(description="**LOOP**: `enabled`", color=embed_color)
        )
        if vc.loop
        else await ctx.send(
            embed=nextcord.Embed(description="**LOOP**: `disabled`", color=embed_color)
        )
    )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="queue",
    help="displays the current queue",
    description=",q",
)
async def queue_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client

    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(description="**QUEUE**\n\n`empty`", color=embed_color)
        )

    lqstr = "`disabled`" if vc.lq is False else "`enabled`"
    global qem
    qem = nextcord.Embed(
        description=f"**QUEUE**\n\n**loopqueue**: {lqstr}", color=embed_color
    )
    global song_count, song, song_queue
    song_queue = vc.queue.copy()
    for song_count, song in enumerate(song_queue, start=1):
        title = song.title if nextwave.tracks.PartialTrack else song.info["title"]
        qem.add_field(name="", value=f"**{song_count} **• {title}", inline=False)

    await ctx.send(embed=qem)
    return commands.Paginator(prefix=">", suffix="<", linesep="\n")


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="shuffle",
    help="shuffles the existing queue randomly",
    description=",shuffle",
)
async def shuffle_command(ctx: commands.Context):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if song_count > 2:
        random.shuffle(vc.queue._queue)
        return await ctx.send(
            embed=nextcord.Embed(description="Shuffled the `QUEUE`", color=embed_color)
        )
    elif vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(description="`QUEUE` is empty", color=embed_color)
        )
    else:
        return await ctx.send(
            embed=nextcord.Embed(
                description="`QUEUE` has less than `3 songs`",
                color=embed_color,
            )
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="del",
    help="deletes the specified track",
    description=",del <song number>",
)
async def del_command(ctx: commands.Context, position: int):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(
                description="No songs in the `QUEUE`", color=embed_color
            )
        )
    if position <= 0:
        return await ctx.send(
            embed=nextcord.Embed(
                description="Position can not be `ZERO`* or `LESSER`",
                color=embed_color,
            )
        )
    elif position > song_count:
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"Position `{position}` is outta range", color=embed_color
            )
        )
    else:
        SongToBeDeleted = vc.queue._queue[position - 1].title
        del vc.queue._queue[position - 1]
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"`{SongToBeDeleted}` removed from the QUEUE",
                color=embed_color,
            )
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="skipto",
    help="skips to the specified track",
    description=",skipto <song number>",
)
async def skipto_command(ctx: commands.Context, position: int):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(
                description="No songs in the `QUEUE`", color=embed_color
            )
        )
    if position <= 0:
        return await ctx.send(
            embed=nextcord.Embed(
                description="Position can not be `ZERO`* or `LESSER`",
                color=embed_color,
            )
        )
    elif position > song_count:
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"Position `{position}` is outta range", color=embed_color
            )
        )
    elif position == vc.queue._queue[position - 1]:
        return await ctx.send(
            embed=nextcord.Embed(
                description="Already in that `Position`!", color=embed_color
            )
        )
    else:
        vc.queue.put_at_front(vc.queue._queue[position - 1])
        del vc.queue._queue[position]
        return await skip_command(ctx)


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="move",
    help="moves the track to the specified position",
    description=",move <song number> <position>",
)
async def move_command(ctx: commands.Context, song_position: int, move_position: int):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(
                description="No songs in the `QUEUE`!", color=embed_color
            )
        )
    if song_position <= 0 or move_position <= 0:
        return await ctx.send(
            embed=nextcord.Embed(
                description="Position can not be `ZERO`* or `LESSER`",
                color=embed_color,
            )
        )
    elif song_position > song_count or move_position > song_count:
        position = song_position if song_position > song_count else move_position
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"Position `{position}` is outta range!", color=embed_color
            )
        )
    elif song_position is move_position:
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"Already in that `Position`:{move_position}",
                color=embed_color,
            )
        )
    else:
        move_index = (
            move_position - 1 if move_position < song_position else move_position
        )
        song_index = (
            song_position if move_position < song_position else song_position - 1
        )
        vc.queue.put_at_index(move_index, vc.queue._queue[song_position - 1])
        moved_song = vc.queue._queue[song_index]
        del vc.queue._queue[song_index]
        moved_song_name = moved_song.info["title"]
        return await ctx.send(
            embed=nextcord.Embed(
                description=f"**{moved_song_name}** moved at Position:`{move_position}`",
                color=embed_color,
            )
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(name="volume", help="sets the volume", description=",vol <number>")
async def volume_command(ctx: commands.Context, playervolume: int):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if vc.is_connected():
        if playervolume > 100:
            return await ctx.send(
                embed=nextcord.Embed(
                    description="**VOLUME** supported upto `100%`", color=embed_color
                )
            )
        elif playervolume < 0:
            return await ctx.send(
                embed=nextcord.Embed(
                    description="**VOLUME** can not be `negative`", color=embed_color
                )
            )
        else:
            await ctx.send(
                embed=nextcord.Embed(
                    description=f"**VOLUME**\nSet to `{playervolume}%`",
                    color=embed_color,
                )
            )
            return await vc.set_volume(playervolume)
    elif not vc.is_connected():
        return await ctx.send(
            embed=nextcord.Embed(description="Player not connected!", color=embed_color)
        )


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="seek",
    help="seeks or moves the player to specified track position",
    description=",seek <duration>",
)
async def seek_command(ctx: commands.Context, seekPosition: int):
    if await user_connectivity(ctx) is False:
        return
    vc: nextwave.Player = ctx.voice_client
    if not vc.is_playing():
        return await ctx.send(
            embed=nextcord.Embed(description="Player not playing!", color=embed_color)
        )
    elif vc.is_playing():
        if not 0 <= seekPosition <= vc.track.length:
            return await ctx.send(
                embed=nextcord.Embed(
                    description=f"SEEK length `{seekPosition}` outta range",
                    color=embed_color,
                )
            )
        msg = await ctx.send(
            embed=nextcord.Embed(description="seeking...", color=embed_color)
        )
        await vc.seek(seekPosition * 1000)
        return await msg.edit(
            embed=nextcord.Embed(
                description=f"Player SEEKED: `{seekPosition}` seconds",
                color=embed_color,
            )
        )


@commands.cooldown(1, 5, commands.BucketType.user)
@bot.command(name="clear", help="clears the queue", description=",clear")
async def clear_command(ctx: commands.Context):
    vc: nextwave.Player = ctx.voice_client
    if await user_connectivity(ctx) is False:
        return
    if vc.queue.is_empty:
        return await ctx.send(
            embed=nextcord.Embed(
                description="No `SONGS` are present", color=embed_color
            )
        )
    vc.queue._queue.clear()
    vc.lq = False
    clear_command_embed = nextcord.Embed(
        description="`QUEUE` cleared", color=embed_color
    )
    return await ctx.send(embed=clear_command_embed)


@commands.cooldown(1, 2, commands.BucketType.user)
@bot.command(
    name="save",
    description=",save\n,save <song number | 'queue' | 'q'>",
    help="dms the current | specified song to the user",
)
async def save_command(ctx: commands.Context, savestr: Optional[str]):
    vc: nextwave.Player = ctx.voice_client
    if await user_connectivity(ctx) is False:
        return
    user = await bot.fetch_user(ctx.author._user.id)
    if vc._source and savestr is None:
        await user.send(
            embed=nextcord.Embed(description=f"`{vc._source}`", color=embed_color)
        )
    elif not vc.queue.is_empty and savestr == "q" or savestr == "queue":
        await user.send(embed=qem)
    elif not vc.queue.is_empty and savestr:
        if int(savestr) <= 0:
            return await ctx.send(
                embed=nextcord.Embed(
                    description="Position can not be `ZERO`* or `LESSER`",
                    color=embed_color,
                )
            )
        elif int(savestr) > song_count:
            return await ctx.send(
                embed=nextcord.Embed(
                    description=f"Position `{savestr}` is outta range",
                    color=embed_color,
                )
            )
        else:
            song_info = vc.queue._queue[int(savestr) - 1]
            em = nextcord.Embed(description=song_info.info["title"], color=embed_color)
            await user.send(embed=em)
    else:
        return await ctx.send(
            embed=nextcord.Embed(
                description="There is no `song` | `queue` available", color=embed_color
            )
        )


if __name__ == "__main__":
    bot.run(Token)
