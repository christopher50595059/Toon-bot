"""
Discord Role Assignment Bot
----------------------------
Lets authorized staff assign/remove roles (staff positions, tiers, etc.)
with a simple slash command, and logs every action to a chosen channel.

Commands:
  /addrole user:<member> role:<role> reason:<text>   - give a role to a member
  /removerole user:<member> role:<role> reason:<text> - remove a role from a member
  /setlogchannel channel:<channel>        - (admin only) set where actions are logged
  /setmanagerrole role:<role>             - (admin only) set which role is allowed to use these commands
  /rosteradd user:<member> rank:<role> reason:<text>   - add/move a member on the roster AND give them that role
  /rosterremove user:<member> reason:<text>            - remove a member from the roster — asks for confirmation
  /promote user:<member> reason:<text>    - move a member up one rank (per /setranks order)
  /demote user:<member> reason:<text>     - move a member down one rank (per /setranks order) — asks for confirmation
  /rosterimport rank:<role>               - import everyone who already has a rank role onto the roster at once
  /roster                                 - show the current roster, grouped by rank
  /stats                                  - show roster counts per rank
  /rank [user]                            - show a member's current rank (defaults to you)
  /history [user]                         - show a member's rank/roster history (defaults to you)
  /setrosterchannel channel:<channel>     - (admin only) post a live roster embed that auto-updates in this channel
  /setranks rank1:<role> [rank2]...[rank8]  - (admin only) set the ordered rank roles (highest first)
  /setcooldown hours:<int> [user]         - (admin only) require a wait between promote/demote — server-wide, or just for one person
  /setinactivitydays days:<int>           - (admin only) set the silence threshold used by /inactive
  /inactive                               - show roster members who haven't sent a message in a while
  /serverstats                            - show a one-off snapshot of server stats
  /setstatschannel channel:<channel>      - (admin only) post a live server-stats embed that auto-updates in this channel
  /tournament create name:<text>          - open sign-ups for a single-elimination bracket
  /tournament start name:<text>           - (manager only) lock sign-ups and generate the bracket
  /tournament report name:<text> match:<#> winner:<member>  - (manager only) record a match result
  /tournament bracket name:<text>         - show the current bracket
  /gamenight create game:<text> date:<YYYY-MM-DD> time:<HH:MM>  - (manager only) schedule a game night with RSVPs
  /gamenight list                         - show upcoming game nights
  /gamenight cancel id:<#>                - (manager only) cancel a scheduled game night
  /mvp start title:<text> user1..user5    - (manager only) open MVP voting among up to 5 candidates
  /mvp end                                - (manager only) close voting and announce the winner
  /crosspost_add destination_channel_id:<id> - (admin only) mirror this channel to a channel in another server
  /crosspost_remove                       - (admin only) stop mirroring this channel
  /crosspost_list                         - (admin only) show all mirrors set up in this server
  /kick user:<member> reason:<text>       - kick a member — asks for confirmation
  /ban user:<member> reason:<text> [delete_days] - ban a member — asks for confirmation
  /timeout user:<member> minutes:<int> reason:<text> - temporarily mute a member
  /warn user:<member> reason:<text>       - log a warning against a member
  /warnings [user]                        - show a member's warning history (defaults to you)
  /purge amount:<1-100>                   - bulk-delete recent messages in this channel
  /lock [reason]                          - stop everyone from sending messages in this channel
  /unlock                                 - allow sending messages in this channel again
  /slowmode seconds:<0-21600>             - set this channel's slowmode delay
  /audit                                  - show the last 20 rank/roster actions across everyone
  /backup                                 - (admin only) export this server's bot config as a file
  /announce channel:<channel> title:<text> message:<text> - post a formatted announcement
  /massannounce message:<text> [title]    - post to all announcement channels AND speak it in every active voice channel
  /massrename [prefix] [suffix] [role]    - add a prefix/suffix to multiple members' nicknames — asks for confirmation
  /massaddrole role:<role> [filter_role]  - give a role to multiple members at once — asks for confirmation
  /massremoverole role:<role> [filter_role] - remove a role from multiple members at once — asks for confirmation
  /afk [reason]                           - mark yourself AFK; clears automatically when you send a message again
  /setvcgreeting user:<member> message:<text> - say something out loud whenever this person joins a voice channel
  /removevcgreeting user:<member>         - stop greeting this person when they join a VC
  /showcase add role:<role> description:<text>  - add a self-assignable role to the showcase
  /showcase remove role:<role>            - remove a role from the showcase
  /showcase setchannel channel:<channel>  - (admin only) post the live showcase here
  /showcase list                          - show the current showcase
  /evaluate [user]                        - show message activity for the current week (leaderboard or one person); auto-resets weekly
  /setbirthday month:<1-12> day:<1-31>    - set your own birthday
  /removebirthday                         - remove your saved birthday
  /mybirthday                             - show your currently saved birthday
  /setbirthdayrole [role]                 - (admin only) role auto-given on someone's birthday (omit to disable)
  /setbirthdaychannel [channel]           - (admin only) channel for birthday shoutouts (omit to disable)
  /help                                   - show every command, grouped by category

Only server admins can run the "set" commands. Only members with the
configured "manager role" (or Administrator permission) can run
/addrole and /removerole.
"""

import asyncio
import io
import json
import os
import random
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from gtts import gTTS

from web import start_web_app

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

CONFIG_PATH = Path(__file__).parent / "guild_config.json"

# ---------- simple JSON-backed per-guild config ----------

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


config = load_config()


def get_guild_cfg(guild_id: int) -> dict:
    return config.setdefault(str(guild_id), {})


# ---------- bot setup ----------

intents = discord.Intents.default()
intents.members = True          # required to look up / modify member roles
intents.message_content = True  # required to read message content for cross-posting

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}. Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Sync failed: {e}")
    if not gamenight_reminder_loop.is_running():
        gamenight_reminder_loop.start()
    if not weekly_evaluation_loop.is_running():
        weekly_evaluation_loop.start()
    if not birthday_check_loop.is_running():
        birthday_check_loop.start()


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    cfg = get_guild_cfg(message.guild.id)

    # ---- cross-posting ----
    crossposts = cfg.get("crossposts", {})
    dest_id = crossposts.get(str(message.channel.id))
    if dest_id:
        dest_channel = bot.get_channel(dest_id)
        if dest_channel:
            embed = discord.Embed(
                description=message.content or None,
                color=discord.Color.dark_teal(),
                timestamp=message.created_at,
            )
            embed.set_author(
                name=f"{message.author.display_name} — #{message.channel.name} ({message.guild.name})",
                icon_url=message.author.display_avatar.url,
            )
            if message.attachments:
                first = message.attachments[0]
                if first.content_type and first.content_type.startswith("image"):
                    embed.set_image(url=first.url)
                else:
                    embed.add_field(name="Attachment", value=first.url, inline=False)
            try:
                await dest_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # ---- AFK ----
    afk_users = cfg.setdefault("afk", {})

    # If the sender was AFK, clear it now that they're active again.
    if str(message.author.id) in afk_users:
        afk_users.pop(str(message.author.id))
        save_config(config)
        try:
            await message.channel.send(f"👋 Welcome back, {message.author.mention}! I removed your AFK status.")
        except discord.Forbidden:
            pass

    # If this message mentions anyone currently AFK, let the sender know.
    if message.mentions:
        notices = []
        for mentioned in message.mentions:
            if mentioned.id == message.author.id:
                continue
            afk_entry = afk_users.get(str(mentioned.id))
            if afk_entry:
                since = datetime.fromisoformat(afk_entry["since"])
                notices.append(f"💤 {mentioned.mention} is AFK: {afk_entry['reason']} (since <t:{int(since.timestamp())}:R>)")
        if notices:
            try:
                await message.channel.send("\n".join(notices))
            except discord.Forbidden:
                pass

    # ---- weekly message count (for /evaluate) ----
    message_counts = cfg.setdefault("message_counts", {})
    author_key = str(message.author.id)
    message_counts[author_key] = message_counts.get(author_key, 0) + 1
    cfg.setdefault("message_count_since", datetime.now(timezone.utc).isoformat())

    # ---- activity tracking (for /inactive) ----
    last_active = cfg.setdefault("last_active", {})
    now = datetime.now(timezone.utc)

    # Only write to disk if it's been a while since we last recorded this
    # person — avoids a disk write on every single message in a busy server.
    # (message_counts above is already incremented in memory either way.)
    previous = last_active.get(str(message.author.id))
    if previous:
        try:
            if now - datetime.fromisoformat(previous) < timedelta(minutes=5):
                return
        except ValueError:
            pass

    last_active[str(message.author.id)] = now.isoformat()
    save_config(config)


@bot.event
async def on_member_join(member: discord.Member):
    await refresh_server_stats_message(member.guild)


@bot.event
async def on_member_remove(member: discord.Member):
    await refresh_server_stats_message(member.guild)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return
    # Only fire when they've actually landed in a NEW voice channel (not on mute/deafen toggles, etc.)
    if after.channel is None or after.channel == before.channel:
        return

    cfg = get_guild_cfg(member.guild.id)
    greetings = cfg.get("vc_greetings", {})
    message = greetings.get(str(member.id))
    if not message:
        return

    perms = after.channel.permissions_for(member.guild.me)
    if not perms.connect or not perms.speak:
        return

    asyncio.create_task(speak_vc_greeting(member, after.channel, message))


async def send_to_log_channel(guild: discord.Guild, embed: discord.Embed):
    """Send a pre-built embed to the configured log channel, if one is set."""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("log_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass


SPACER = "\u200b"  # invisible character used as a blank-line spacer in embeds


async def log_action(
    guild: discord.Guild,
    title: str,
    color: discord.Color,
    member: discord.Member,
    moderator: discord.Member,
    fields: dict = None,
):
    """Post a structured log embed for an action taken on ONE member."""
    embed = discord.Embed(title=title, description=SPACER, color=color, timestamp=discord.utils.utcnow())
    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=member.display_avatar.url)

    if fields:
        items = list(fields.items())
        for i, (name, value) in enumerate(items):
            embed.add_field(name=name, value=value, inline=len(str(value)) <= 30)
            # Full-width spacer row between fields so groups don't feel cramped together.
            if i < len(items) - 1:
                embed.add_field(name=SPACER, value=SPACER, inline=False)

    embed.set_footer(
        text=f"Action by {moderator.display_name} • Member ID: {member.id}",
        icon_url=moderator.display_avatar.url,
    )
    await send_to_log_channel(guild, embed)


async def log_movement(
    guild: discord.Guild,
    member: discord.Member,
    target: str,
    reason: str,
    moderator: discord.Member,
):
    """Post a compact one-line log entry for a role/roster 'movement':
    Member → Target | Reason | Moderator | Timestamp"""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("log_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    now_ts = int(datetime.now(timezone.utc).timestamp())
    line = f"{member.mention} → {target} | {reason} | {moderator.mention} | <t:{now_ts}:f>"
    try:
        await channel.send(line)
    except discord.Forbidden:
        pass


async def log_bulk_action(
    guild: discord.Guild,
    title: str,
    color: discord.Color,
    moderator: discord.Member,
    description: str,
    fields: dict = None,
):
    """Post a log embed for an action that isn't about a single member (e.g. bulk import)."""
    embed = discord.Embed(title=title, description=f"{description}\n{SPACER}", color=color, timestamp=discord.utils.utcnow())

    if fields:
        items = list(fields.items())
        for i, (name, value) in enumerate(items):
            embed.add_field(name=name, value=value, inline=len(str(value)) <= 30)
            if i < len(items) - 1:
                embed.add_field(name=SPACER, value=SPACER, inline=False)

    embed.set_footer(
        text=f"Run by {moderator.display_name} • Moderator ID: {moderator.id}",
        icon_url=moderator.display_avatar.url,
    )
    await send_to_log_channel(guild, embed)


def record_history(guild_id: int, user_id: int, action: str, detail: str, moderator_id: int, reason: str = None):
    """Append an entry to a member's rank/roster history."""
    cfg = get_guild_cfg(guild_id)
    history = cfg.setdefault("history", {})
    user_history = history.setdefault(str(user_id), [])
    user_history.append({
        "action": action,
        "detail": detail,
        "moderator_id": moderator_id,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_config(config)


async def dm_notify(
    guild: discord.Guild,
    member: discord.Member,
    title: str,
    color: discord.Color,
    fields: dict = None,
) -> bool:
    """DM a member about an action taken on them. Returns False if the DM couldn't be sent
    (e.g. they have DMs closed) so the caller can let the moderator know.
    NOTE: role/rank values in `fields` should be plain names, not mentions —
    Discord can't resolve role mentions inside a DM (shows as '@unknown-role')."""
    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.description = f"Your roles were changed in **{guild.name}**."

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

    try:
        await member.send(embed=embed)
        return True
    except Exception:
        # Any failure to DM (closed DMs, blocked, can't DM the bot itself, etc.)
        # should never crash the command — just report it as "couldn't DM them".
        return False


async def generate_tts_file(text: str) -> str:
    """Generate an MP3 file for the given text via gTTS. Blocking network call,
    so it's run off the event loop. Returns the temp file path."""
    loop = asyncio.get_event_loop()
    result = {}

    def make_tts_file():
        tts = gTTS(text=text)
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        tts.save(path)
        result["path"] = path

    await loop.run_in_executor(None, make_tts_file)
    return result["path"]


async def play_tts_in_voice_channel(voice_channel: discord.VoiceChannel, tmp_path: str):
    """Join a voice channel, play the given MP3 file, wait for it to finish, then leave."""
    guild = voice_channel.guild
    loop = asyncio.get_event_loop()

    voice_client = guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    done = asyncio.Event()

    def after_playback(error):
        loop.call_soon_threadsafe(done.set)

    source = discord.FFmpegPCMAudio(tmp_path)
    voice_client.play(source, after=after_playback)
    await done.wait()
    await voice_client.disconnect()


async def announce_timeout_in_vc(member: discord.Member, minutes: int, reason: str):
    """If the member is currently in a voice channel, join it, speak their name,
    the timeout duration, and the reason via TTS, then leave. Never raises —
    any failure here (permissions, no voice library, etc.) is swallowed so it
    can't break the /timeout command itself."""
    try:
        if member.voice is None or member.voice.channel is None:
            return

        text = f"{member.display_name} is about to be timed out for {minutes} minutes, reason: {reason}"
        tmp_path = await generate_tts_file(text)
        try:
            await play_tts_in_voice_channel(member.voice.channel, tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception:
        pass


vc_greeting_locks: dict[int, asyncio.Lock] = {}  # guild_id -> Lock, prevents overlapping VC joins


async def speak_vc_greeting(member: discord.Member, voice_channel: discord.VoiceChannel, message: str):
    """Join the member's voice channel and speak their custom greeting, then leave.
    Serialized per-guild so two people joining at once don't collide over the
    bot's single voice connection. Never raises."""
    lock = vc_greeting_locks.setdefault(member.guild.id, asyncio.Lock())
    try:
        async with lock:
            tmp_path = await generate_tts_file(message)
            try:
                await play_tts_in_voice_channel(voice_channel, tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
    except Exception:
        pass


RANK_TIER_ICONS = ["🥇", "🥈", "🥉", "🔹", "🔸", "▪️", "▪️", "▪️"]


def build_showcase_embed(guild: discord.Guild, cfg: dict) -> discord.Embed:
    entries = cfg.get("showcase_roles", [])
    embed = discord.Embed(title="🎭 Role Showcase", color=discord.Color.blurple())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    if not entries:
        embed.description = "No roles have been added to the showcase yet."
        return embed

    embed.description = "Click a button below to get (or remove) that role for yourself."
    for entry in entries:
        role = guild.get_role(entry["role_id"])
        label = role.name if role else "(deleted role)"  # field names can't render mentions
        member_count = len(role.members) if role else 0
        embed.add_field(
            name=f"🔸 {label} — {member_count} member(s)",
            value=entry.get("description") or "*No description.*",
            inline=False,
        )
    embed.set_footer(text="Last updated")
    embed.timestamp = discord.utils.utcnow()
    return embed


class ShowcaseView(discord.ui.View):
    """One toggle button per showcased role — clicking gives you the role if
    you don't have it, or removes it if you do."""

    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=None)
        for entry in entries[:25]:  # Discord's hard cap on buttons per message
            role_id = entry["role_id"]
            role = guild.get_role(role_id)
            label = role.name if role else "Deleted role"
            button = discord.ui.Button(label=label[:80], style=discord.ButtonStyle.secondary)
            button.callback = self._make_callback(guild.id, role_id)
            self.add_item(button)

    def _make_callback(self, guild_id: int, role_id: int):
        async def callback(interaction: discord.Interaction):
            guild = interaction.guild
            role = guild.get_role(role_id)
            if role is None:
                await interaction.response.send_message("❌ That role no longer exists.", ephemeral=True)
                return
            if role >= guild.me.top_role:
                await interaction.response.send_message(
                    "❌ I can't manage that role — it's above my own role in the server settings.", ephemeral=True
                )
                return

            member = interaction.user
            try:
                if role in member.roles:
                    await member.remove_roles(role, reason="Self-removed via /showcase")
                    await interaction.response.send_message(f"✅ Removed {role.mention}.", ephemeral=True)
                else:
                    await member.add_roles(role, reason="Self-assigned via /showcase")
                    await interaction.response.send_message(f"✅ Gave you {role.mention}.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to manage that role.", ephemeral=True)
        return callback


async def refresh_showcase_message(guild: discord.Guild):
    """Edit the live showcase embed in the configured channel, if one is set."""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("showcase_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    entries = cfg.get("showcase_roles", [])
    embed = build_showcase_embed(guild, cfg)
    view = ShowcaseView(guild, entries) if entries else None
    message_id = cfg.get("showcase_message_id")

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed, view=view)
            return
        except (discord.NotFound, discord.Forbidden):
            pass  # fall through and post a fresh message

    try:
        message = await channel.send(embed=embed, view=view)
        cfg["showcase_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        pass


def build_roster_embed(guild: discord.Guild) -> discord.Embed:
    cfg = get_guild_cfg(guild.id)
    roster = cfg.get("roster", [])  # list of {"user_id": int, "rank_role_id": int}
    rank_role_ids = cfg.get("ranks", [])  # ordered list of role IDs, highest first

    embed = discord.Embed(title="📋 Server Roster", color=discord.Color.teal())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    if not roster:
        embed.description = "The roster is currently empty."
        return embed

    embed.description = f"**{len(roster)}** total member(s)"

    def member_mentions(entries):
        names = []
        for entry in entries:
            member = guild.get_member(entry["user_id"])
            names.append(member.mention if member else f"<@{entry['user_id']}> (left)")
        return ", ".join(names)

    # Group entries by rank role, preserving the configured rank order.
    grouped = {rid: [] for rid in rank_role_ids}
    unranked = []
    for entry in roster:
        rid = entry.get("rank_role_id")
        if rid in grouped:
            grouped[rid].append(entry)
        else:
            unranked.append(entry)

    for position, rid in enumerate(rank_role_ids):
        members = grouped[rid]
        if not members:
            continue
        role = guild.get_role(rid)
        label = role.name if role else "Deleted role"  # NOTE: field names can't render role mentions — plain text only
        icon = RANK_TIER_ICONS[position] if position < len(RANK_TIER_ICONS) else "▪️"
        embed.add_field(name=f"{icon} {label} — {len(members)}", value=member_mentions(members), inline=False)

    if unranked:
        embed.add_field(name=f"❔ Unranked — {len(unranked)}", value=member_mentions(unranked), inline=False)

    embed.set_footer(text=f"{len(roster)} member(s) on the roster • Last updated")
    embed.timestamp = discord.utils.utcnow()
    return embed


async def refresh_roster_message(guild: discord.Guild):
    """Edit the live roster embed in the configured roster channel, if one is set."""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("roster_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    embed = build_roster_embed(guild)
    message_id = cfg.get("roster_message_id")

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            return
        except (discord.NotFound, discord.Forbidden):
            pass  # fall through and post a fresh message

    try:
        message = await channel.send(embed=embed)
        cfg["roster_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        pass


def build_server_stats_embed(guild: discord.Guild) -> discord.Embed:
    cfg = get_guild_cfg(guild.id)
    roster = cfg.get("roster", [])

    humans = sum(1 for m in guild.members if not m.bot)
    bots = sum(1 for m in guild.members if m.bot)

    embed = discord.Embed(title=f"📈 {guild.name} — Server Stats", color=discord.Color.dark_blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.description = (
        f"👥 **{guild.member_count}** total members "
        f"(`{bar(humans, guild.member_count, 8)}` {humans} human, "
        f"`{bar(bots, guild.member_count, 8)}` {bots} bot)\n"
        f"{SPACER}"
    )

    embed.add_field(name="🧑‍🤝‍🧑 Humans", value=str(humans), inline=True)
    embed.add_field(name="🤖 Bots", value=str(bots), inline=True)
    embed.add_field(name=SPACER, value=SPACER, inline=True)
    embed.add_field(name="📋 Roster Size", value=str(len(roster)), inline=True)
    embed.add_field(name="🚀 Server Boosts", value=str(guild.premium_subscription_count or 0), inline=True)
    embed.add_field(name=SPACER, value=SPACER, inline=True)
    embed.add_field(name="🎂 Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name=SPACER, value=SPACER, inline=True)
    embed.add_field(name=SPACER, value=SPACER, inline=True)

    embed.set_footer(text="Last updated")
    embed.timestamp = discord.utils.utcnow()
    return embed


async def refresh_server_stats_message(guild: discord.Guild):
    """Edit the live server-stats embed in the configured stats channel, if one is set."""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("stats_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    embed = build_server_stats_embed(guild)
    message_id = cfg.get("stats_message_id")

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            return
        except (discord.NotFound, discord.Forbidden):
            pass  # fall through and post a fresh message

    try:
        message = await channel.send(embed=embed)
        cfg["stats_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        pass


def bar(value: int, total: int, length: int = 12) -> str:
    """A little unicode progress bar, e.g. '███████░░░░░' — used to visualize proportions."""
    if total <= 0:
        return "░" * length
    filled = round(length * value / total)
    filled = max(0, min(length, filled))
    return "█" * filled + "░" * (length - filled)


def action_embed(
    title: str,
    description: str,
    color: discord.Color,
    member: discord.Member = None,
    moderator: discord.Member = None,
) -> discord.Embed:
    """A spaced-out embed for command confirmation responses (as opposed to
    the log channel embeds, which include a footer credit to the moderator)."""
    embed = discord.Embed(title=title, description=f"{SPACER}\n{description}\n{SPACER}", color=color)
    if member is not None:
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
    if moderator is not None:
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url)
    embed.timestamp = discord.utils.utcnow()
    return embed


def is_authorized(interaction: discord.Interaction) -> bool:
    """True if the invoking member can manage roles via this bot."""
    member = interaction.user
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    cfg = get_guild_cfg(interaction.guild_id)
    manager_role_id = cfg.get("manager_role_id")
    if manager_role_id is None:
        return False
    return any(r.id == manager_role_id for r in member.roles)


class ConfirmView(discord.ui.View):
    """A Confirm/Cancel button pair for actions that deserve a second look
    (e.g. demotes, roster removals) before they take effect."""

    def __init__(self, author_id: int, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.confirmed: bool | None = None  # None = timed out

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Only the person who ran this command can respond to it.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.defer()


# ---------- admin config commands ----------

@bot.tree.command(name="setlogchannel", description="Set the channel where role changes are logged.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel to send role-change logs to")
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["log_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Role-change logs will now be posted in {channel.mention}.", ephemeral=True
    )


@bot.tree.command(name="setmanagerrole", description="Set which role is allowed to assign/remove roles with this bot.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="The role whose members are allowed to run /addrole and /removerole")
async def setmanagerrole(interaction: discord.Interaction, role: discord.Role):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["manager_role_id"] = role.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Members with the {role.mention} role can now use /addrole and /removerole.", ephemeral=True
    )


@bot.tree.command(name="setrosterchannel", description="Post a live roster embed that auto-updates in this channel.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel to post the live roster in")
async def setrosterchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["roster_channel_id"] = channel.id
    cfg.pop("roster_message_id", None)  # force a fresh message in the new channel
    save_config(config)
    await interaction.response.send_message(
        f"✅ The live roster will now be posted and kept updated in {channel.mention}.", ephemeral=True
    )
    await refresh_roster_message(interaction.guild)


@bot.tree.command(name="setranks", description="Set the ordered rank roles for the roster (highest first).")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    rank1="Highest rank role", rank2="2nd rank role", rank3="3rd rank role",
    rank4="4th rank role", rank5="5th rank role", rank6="6th rank role",
    rank7="7th rank role", rank8="8th rank role (lowest)",
)
async def setranks(
    interaction: discord.Interaction,
    rank1: discord.Role,
    rank2: discord.Role = None,
    rank3: discord.Role = None,
    rank4: discord.Role = None,
    rank5: discord.Role = None,
    rank6: discord.Role = None,
    rank7: discord.Role = None,
    rank8: discord.Role = None,
):
    roles_in_order = [r for r in [rank1, rank2, rank3, rank4, rank5, rank6, rank7, rank8] if r is not None]

    cfg = get_guild_cfg(interaction.guild_id)
    cfg["ranks"] = [r.id for r in roles_in_order]
    save_config(config)

    await interaction.response.send_message(
        f"✅ Ranks set (highest to lowest): {' > '.join(r.mention for r in roles_in_order)}", ephemeral=True
    )
    await refresh_roster_message(interaction.guild)


@bot.tree.command(name="setcooldown", description="Set a cooldown period before someone can be promoted/demoted again.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    hours="Hours between rank changes (0 to disable)",
    user="Only apply this to one specific person (omit to set the server-wide default)",
)
async def setcooldown(interaction: discord.Interaction, hours: int, user: discord.Member = None):
    if hours < 0:
        await interaction.response.send_message("❌ Hours can't be negative.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)

    if user is not None:
        user_cooldowns = cfg.setdefault("user_cooldowns", {})
        if hours == 0:
            user_cooldowns.pop(str(user.id), None)
            save_config(config)
            await interaction.response.send_message(
                f"✅ Removed {user.mention}'s personal cooldown — they'll use the server default now.", ephemeral=True
            )
        else:
            user_cooldowns[str(user.id)] = hours
            save_config(config)
            await interaction.response.send_message(
                f"✅ {user.mention} must now wait **{hours} hour(s)** between promotions/demotions "
                "(this overrides the server default for them specifically).",
                ephemeral=True,
            )
        return

    cfg["cooldown_hours"] = hours
    save_config(config)

    if hours == 0:
        await interaction.response.send_message("✅ Promote/demote cooldown disabled server-wide.", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"✅ Members must now wait **{hours} hour(s)** between promotions/demotions by default "
            "(anyone with a personal override from `/setcooldown user:...` keeps their own value).",
            ephemeral=True,
        )


@bot.tree.command(name="setinactivitydays", description="Set how many days of silence counts as 'inactive' for /inactive.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(days="Days without a message before someone shows up in /inactive (0 to disable)")
async def setinactivitydays(interaction: discord.Interaction, days: int):
    if days < 0:
        await interaction.response.send_message("❌ Days can't be negative.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    cfg["inactivity_days"] = days
    save_config(config)

    if days == 0:
        await interaction.response.send_message("✅ Inactivity tracking disabled.", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"✅ Roster members with no messages in **{days} day(s)** will show up in /inactive.", ephemeral=True
        )


@bot.tree.command(name="setstatschannel", description="Post a live server-stats embed that auto-updates in this channel.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel to post live server stats in")
async def setstatschannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["stats_channel_id"] = channel.id
    cfg.pop("stats_message_id", None)  # force a fresh message in the new channel
    save_config(config)
    await interaction.response.send_message(
        f"✅ Live server stats will now be posted and kept updated in {channel.mention}.", ephemeral=True
    )
    await refresh_server_stats_message(interaction.guild)


# ---------- role assignment commands ----------

@bot.tree.command(name="addrole", description="Give a role to a member (e.g. promote to staff or a tier).")
@app_commands.describe(user="The member to give the role to", role="The role to assign", reason="Why you're giving this role")
async def addrole(interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    # Prevent assigning a role higher than or equal to the bot's own top role
    bot_member = interaction.guild.me
    if role >= bot_member.top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {role.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    if role in user.roles:
        await interaction.response.send_message(
            f"ℹ️ {user.mention} already has {role.mention}.", ephemeral=True
        )
        return

    await user.add_roles(role, reason=f"Added by {interaction.user} via /addrole: {reason}")
    dm_sent = await dm_notify(
        interaction.guild, user,
        title="🟢 You were given a role",
        color=discord.Color.green(),
        fields={"Role": role.name, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "🟢 Role Given",
        f"Gave {role.mention} to {user.mention}.\n**Reason:** {reason}{note}",
        discord.Color.green(),
        member=user,
        moderator=interaction.user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_movement(
        interaction.guild,
        member=user,
        target=role.mention,
        reason=reason,
        moderator=interaction.user,
    )


@bot.tree.command(name="removerole", description="Remove a role from a member.")
@app_commands.describe(user="The member to remove the role from", role="The role to remove", reason="Why you're removing this role")
async def removerole(interaction: discord.Interaction, user: discord.Member, role: discord.Role, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    if role not in user.roles:
        await interaction.response.send_message(
            f"ℹ️ {user.mention} doesn't have {role.mention}.", ephemeral=True
        )
        return

    await user.remove_roles(role, reason=f"Removed by {interaction.user} via /removerole: {reason}")
    dm_sent = await dm_notify(
        interaction.guild, user,
        title="🔴 A role was removed from you",
        color=discord.Color.red(),
        fields={"Role": role.name, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "🔴 Role Removed",
        f"Removed {role.mention} from {user.mention}.\n**Reason:** {reason}{note}",
        discord.Color.red(),
        member=user,
        moderator=interaction.user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_movement(
        interaction.guild,
        member=user,
        target=f"~~{role.mention}~~ removed",
        reason=reason,
        moderator=interaction.user,
    )


# ---------- roster commands ----------

@bot.tree.command(name="rosteradd", description="Add a member to the roster at a rank and give them that role.")
@app_commands.describe(user="The member to add to the roster", rank="The rank role to place them at", reason="Why you're adding/moving them")
async def rosteradd(interaction: discord.Interaction, user: discord.Member, rank: discord.Role, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    valid_rank_ids = cfg.get("ranks", [])

    if not valid_rank_ids:
        await interaction.response.send_message(
            "❌ No ranks have been set up yet. An admin needs to run /setranks first.", ephemeral=True
        )
        return

    if rank.id not in valid_rank_ids:
        valid_mentions = ", ".join(
            r.mention for rid in valid_rank_ids if (r := interaction.guild.get_role(rid))
        )
        await interaction.response.send_message(
            f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions}", ephemeral=True
        )
        return

    # Same hierarchy safety check as /addrole — the bot can't grant a role above its own.
    bot_member = interaction.guild.me
    if rank >= bot_member.top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {rank.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    roster = cfg.setdefault("roster", [])
    existing = next((entry for entry in roster if entry["user_id"] == user.id), None)

    role_change_notes = []
    try:
        if rank not in user.roles:
            await user.add_roles(rank, reason=f"Added by {interaction.user} via /rosteradd: {reason}")
            role_change_notes.append(f"gave them {rank.mention}")

        if existing:
            old_rank_role = interaction.guild.get_role(existing.get("rank_role_id"))
            if old_rank_role and old_rank_role.id != rank.id and old_rank_role in user.roles:
                await user.remove_roles(old_rank_role, reason=f"Rank changed by {interaction.user} via /rosteradd: {reason}")
                role_change_notes.append(f"removed {old_rank_role.mention}")
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to manage that role. Check my role position and permissions.",
            ephemeral=True,
        )
        return

    if existing:
        old_rank_role = interaction.guild.get_role(existing.get("rank_role_id"))
        old_label = old_rank_role.mention if old_rank_role else "an unknown rank"
        old_label_name = old_rank_role.name if old_rank_role else "an unknown rank"
        existing["rank_role_id"] = rank.id
        save_config(config)
        summary = f" ({', '.join(role_change_notes)})" if role_change_notes else ""
        dm_sent = await dm_notify(
            interaction.guild, user,
            title="📋 Your roster rank changed",
            color=discord.Color.teal(),
            fields={"Previous Rank": old_label_name, "New Rank": rank.name, "Reason": reason},
        )
        note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
        embed = action_embed(
            "📋 Rank Changed",
            f"Moved {user.mention} from {old_label} to {rank.mention}.\n**Reason:** {reason}{note}",
            discord.Color.teal(),
            member=user,
            moderator=interaction.user,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_movement(
            interaction.guild,
            member=user,
            target=rank.mention,
            reason=reason,
            moderator=interaction.user,
        )
        record_history(
            interaction.guild_id, user.id, "Rank Changed", f"{old_label} → {rank.mention}",
            interaction.user.id, reason,
        )
        await refresh_roster_message(interaction.guild)
        await refresh_server_stats_message(interaction.guild)
        return

    roster.append({"user_id": user.id, "rank_role_id": rank.id})
    save_config(config)

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="📋 You were added to the roster",
        color=discord.Color.teal(),
        fields={"Rank": rank.name, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "📋 Added to Roster",
        f"Added {user.mention} to the roster and gave them {rank.mention}.\n**Reason:** {reason}{note}",
        discord.Color.teal(),
        member=user,
        moderator=interaction.user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_movement(
        interaction.guild,
        member=user,
        target=f"{rank.mention} (added to roster)",
        reason=reason,
        moderator=interaction.user,
    )
    record_history(interaction.guild_id, user.id, "Added to Roster", rank.mention, interaction.user.id, reason)
    await refresh_roster_message(interaction.guild)
    await refresh_server_stats_message(interaction.guild)


@bot.tree.command(name="rosterremove", description="Remove a member from the roster.")
@app_commands.describe(user="The member to remove from the roster", reason="Why you're removing them")
async def rosterremove(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    roster = cfg.setdefault("roster", [])

    if not any(entry["user_id"] == user.id for entry in roster):
        await interaction.response.send_message(
            f"ℹ️ {user.mention} isn't on the roster.", ephemeral=True
        )
        return

    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ Remove {user.mention} from the roster? Reason: {reason}", view=view, ephemeral=True
    )
    await view.wait()

    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    # Re-check in case the roster changed during the confirmation delay.
    roster = cfg.setdefault("roster", [])
    new_roster = [entry for entry in roster if entry["user_id"] != user.id]
    if len(new_roster) == len(roster):
        await interaction.edit_original_response(content=f"ℹ️ {user.mention} isn't on the roster anymore.", view=None)
        return

    cfg["roster"] = new_roster
    save_config(config)

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="📋 You were removed from the roster",
        color=discord.Color.orange(),
        fields={"Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "📋 Removed from Roster",
        f"Removed {user.mention} from the roster.\n**Reason:** {reason}{note}",
        discord.Color.orange(),
        member=user,
        moderator=interaction.user,
    )
    await interaction.edit_original_response(content=None, embed=embed, view=None)
    await log_movement(
        interaction.guild,
        member=user,
        target="removed from roster",
        reason=reason,
        moderator=interaction.user,
    )
    record_history(interaction.guild_id, user.id, "Removed from Roster", "", interaction.user.id, reason)
    await refresh_roster_message(interaction.guild)
    await refresh_server_stats_message(interaction.guild)


async def _change_rank(interaction: discord.Interaction, user: discord.Member, reason: str, step: int, verb: str):
    """Shared logic for /promote (step=-1) and /demote (step=+1)."""
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    rank_ids = cfg.get("ranks", [])

    if not rank_ids:
        await interaction.response.send_message(
            "❌ No ranks have been set up yet. An admin needs to run /setranks first.", ephemeral=True
        )
        return

    roster = cfg.setdefault("roster", [])
    existing = next((entry for entry in roster if entry["user_id"] == user.id), None)

    if not existing or existing.get("rank_role_id") not in rank_ids:
        await interaction.response.send_message(
            f"❌ {user.mention} isn't on the roster at a known rank yet. Use /rosteradd first.", ephemeral=True
        )
        return

    user_cooldowns = cfg.get("user_cooldowns", {})
    cooldown_hours = user_cooldowns.get(str(user.id), cfg.get("cooldown_hours", 0))
    last_change_str = existing.get("last_rank_change")
    if cooldown_hours and last_change_str:
        last_change = datetime.fromisoformat(last_change_str)
        elapsed = datetime.now(timezone.utc) - last_change
        remaining = timedelta(hours=cooldown_hours) - elapsed
        if remaining.total_seconds() > 0:
            hours_left = int(remaining.total_seconds() // 3600)
            minutes_left = int((remaining.total_seconds() % 3600) // 60)
            await interaction.response.send_message(
                f"⏳ {user.mention} was ranked-changed too recently. "
                f"Try again in about {hours_left}h {minutes_left}m.",
                ephemeral=True,
            )
            return

    current_index = rank_ids.index(existing["rank_role_id"])
    new_index = current_index + step

    if new_index < 0:
        await interaction.response.send_message(
            f"ℹ️ {user.mention} is already at the highest rank.", ephemeral=True
        )
        return
    if new_index >= len(rank_ids):
        await interaction.response.send_message(
            f"ℹ️ {user.mention} is already at the lowest rank.", ephemeral=True
        )
        return

    old_role = interaction.guild.get_role(rank_ids[current_index])
    new_role = interaction.guild.get_role(rank_ids[new_index])

    if new_role is None:
        await interaction.response.send_message(
            "❌ That rank's role no longer exists on this server. Ask an admin to run /setranks again.", ephemeral=True
        )
        return

    bot_member = interaction.guild.me
    if new_role >= bot_member.top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {new_role.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    is_demote = step > 0
    old_label = old_role.mention if old_role else "an unknown rank"
    old_label_name = old_role.name if old_role else "an unknown rank"

    if is_demote:
        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(
            f"⚠️ Demote {user.mention} from {old_label} to {new_role.mention}? Reason: {reason}",
            view=view, ephemeral=True,
        )
        await view.wait()
        if view.confirmed is None:
            await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
            return
        if not view.confirmed:
            await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
            return

    try:
        if new_role not in user.roles:
            await user.add_roles(new_role, reason=f"{verb}d by {interaction.user} via /{verb}: {reason}")
        if old_role and old_role in user.roles:
            await user.remove_roles(old_role, reason=f"{verb}d by {interaction.user} via /{verb}: {reason}")
    except discord.Forbidden:
        message = "❌ I don't have permission to manage those roles. Check my role position and permissions."
        if is_demote:
            await interaction.edit_original_response(content=message, view=None)
        else:
            await interaction.response.send_message(message, ephemeral=True)
        return

    existing["rank_role_id"] = new_role.id
    existing["last_rank_change"] = datetime.now(timezone.utc).isoformat()
    save_config(config)

    dm_title = "⬆️ You were promoted!" if step < 0 else "⬇️ You were demoted"
    dm_color = discord.Color.gold() if step < 0 else discord.Color.dark_orange()
    dm_sent = await dm_notify(
        interaction.guild, user,
        title=dm_title,
        color=dm_color,
        fields={"Previous Rank": old_label_name, "New Rank": new_role.name, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    result_embed = action_embed(
        f"{dm_title.split(' ', 1)[0]} {verb}d",
        f"{verb}d {user.mention} from {old_label} to {new_role.mention}.\n**Reason:** {reason}{note}",
        dm_color,
        member=user,
        moderator=interaction.user,
    )
    if is_demote:
        await interaction.edit_original_response(content=None, embed=result_embed, view=None)
    else:
        await interaction.response.send_message(embed=result_embed, ephemeral=True)
    await log_movement(
        interaction.guild,
        member=user,
        target=new_role.mention,
        reason=reason,
        moderator=interaction.user,
    )
    record_history(
        interaction.guild_id, user.id, f"{verb}d", f"{old_label} → {new_role.mention}",
        interaction.user.id, reason,
    )
    await refresh_roster_message(interaction.guild)


@bot.tree.command(name="promote", description="Move a member up one rank (toward the top of your /setranks list).")
@app_commands.describe(user="The member to promote", reason="Why you're promoting them")
async def promote(interaction: discord.Interaction, user: discord.Member, reason: str):
    await _change_rank(interaction, user, reason, step=-1, verb="Promote")


@bot.tree.command(name="demote", description="Move a member down one rank (toward the bottom of your /setranks list).")
@app_commands.describe(user="The member to demote", reason="Why you're demoting them")
async def demote(interaction: discord.Interaction, user: discord.Member, reason: str):
    await _change_rank(interaction, user, reason, step=1, verb="Demote")


@bot.tree.command(name="rosterimport", description="Import everyone who already has a rank role onto the roster at once.")
@app_commands.describe(rank="The rank role to import — everyone who currently has this role gets added at this rank")
async def rosterimport(interaction: discord.Interaction, rank: discord.Role):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    valid_rank_ids = cfg.get("ranks", [])

    if rank.id not in valid_rank_ids:
        valid_mentions = ", ".join(
            r.mention for rid in valid_rank_ids if (r := interaction.guild.get_role(rid))
        )
        await interaction.response.send_message(
            f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions or '(none set — run /setranks first)'}",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    # Make sure we have the full, current member list rather than a possibly-stale cache.
    matching_members = [m async for m in interaction.guild.fetch_members(limit=None) if rank in m.roles and not m.bot]

    if not matching_members:
        await interaction.followup.send(f"ℹ️ No members currently have {rank.mention}.", ephemeral=True)
        return

    roster = cfg.setdefault("roster", [])
    added_members, moved_members, skipped = [], [], 0

    for member in matching_members:
        existing = next((entry for entry in roster if entry["user_id"] == member.id), None)
        if existing is None:
            roster.append({"user_id": member.id, "rank_role_id": rank.id})
            record_history(interaction.guild_id, member.id, "Added to Roster", rank.mention, interaction.user.id, "Bulk import")
            added_members.append(member)
        elif existing.get("rank_role_id") != rank.id:
            old_role = interaction.guild.get_role(existing.get("rank_role_id"))
            old_label = old_role.mention if old_role else "an unknown rank"
            existing["rank_role_id"] = rank.id
            record_history(
                interaction.guild_id, member.id, "Rank Changed", f"{old_label} → {rank.mention}",
                interaction.user.id, "Bulk import",
            )
            moved_members.append(member)
        else:
            skipped += 1

    save_config(config)

    added, moved = len(added_members), len(moved_members)
    embed = discord.Embed(title="📋 Roster Import Complete", color=discord.Color.teal())
    embed.description = f"Imported everyone with {rank.mention} onto the roster."
    embed.add_field(name="Added", value=str(added), inline=True)
    embed.add_field(name="Moved", value=str(moved), inline=True)
    embed.add_field(name="Already Correct", value=str(skipped), inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)

    cfg_log = get_guild_cfg(interaction.guild_id)
    log_channel_id = cfg_log.get("log_channel_id")
    if log_channel_id:
        log_channel = interaction.guild.get_channel(log_channel_id)
        if log_channel:
            added_text = ", ".join(m.mention for m in added_members) if added_members else "none"
            moved_text = ", ".join(m.mention for m in moved_members) if moved_members else "none"
            now_ts = int(datetime.now(timezone.utc).timestamp())
            line = (
                f"📋 Bulk import → {rank.mention} | Added: {added_text} | Moved: {moved_text} | "
                f"{interaction.user.mention} | <t:{now_ts}:f>"
            )
            try:
                await log_channel.send(line)
            except discord.Forbidden:
                pass

    await refresh_roster_message(interaction.guild)
    await refresh_server_stats_message(interaction.guild)


@bot.tree.command(name="roster", description="Show the current roster.")
async def roster(interaction: discord.Interaction):
    embed = build_roster_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stats", description="Show roster counts per rank.")
async def stats(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    roster = cfg.get("roster", [])
    rank_role_ids = cfg.get("ranks", [])

    embed = discord.Embed(title="📊 Roster Stats", color=discord.Color.dark_blue())
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    if not rank_role_ids:
        embed.description = "No ranks have been set up yet. Run /setranks first."
        await interaction.response.send_message(embed=embed)
        return

    counts = {rid: 0 for rid in rank_role_ids}
    unranked = 0
    for entry in roster:
        rid = entry.get("rank_role_id")
        if rid in counts:
            counts[rid] += 1
        else:
            unranked += 1

    for position, rid in enumerate(rank_role_ids):
        role = interaction.guild.get_role(rid)
        label = role.name if role else "Deleted role"  # NOTE: field names can't render role mentions — plain text only
        icon = RANK_TIER_ICONS[position] if position < len(RANK_TIER_ICONS) else "▪️"
        embed.add_field(
            name=f"{icon} {label} — {counts[rid]}",
            value=f"`{bar(counts[rid], len(roster))}`",
            inline=False,
        )

    if unranked:
        embed.add_field(
            name=f"❔ Unranked — {unranked}",
            value=f"`{bar(unranked, len(roster))}`",
            inline=False,
        )

    embed.set_footer(text=f"{len(roster)} member(s) total on the roster")
    embed.timestamp = discord.utils.utcnow()
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverstats", description="Show a snapshot of server stats (member counts, roster size, etc).")
async def serverstats(interaction: discord.Interaction):
    embed = build_server_stats_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="inactive", description="Show roster members who've gone quiet for a while.")
async def inactive(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    threshold_days = cfg.get("inactivity_days", 0)

    if not threshold_days:
        await interaction.response.send_message(
            "❌ Inactivity tracking isn't set up yet. An admin needs to run /setinactivitydays first.",
            ephemeral=True,
        )
        return

    roster = cfg.get("roster", [])
    last_active = cfg.get("last_active", {})
    now = datetime.now(timezone.utc)
    threshold = timedelta(days=threshold_days)

    flagged = []
    for entry in roster:
        user_id = entry["user_id"]
        last_seen_str = last_active.get(str(user_id))
        member = interaction.guild.get_member(user_id)
        name = member.mention if member else f"<@{user_id}> (left server)"

        if last_seen_str is None:
            flagged.append((name, "No activity recorded yet"))
            continue

        last_seen = datetime.fromisoformat(last_seen_str)
        idle_for = now - last_seen
        if idle_for >= threshold:
            days_idle = idle_for.days
            flagged.append((name, f"Quiet for {days_idle} day(s)"))

    embed = discord.Embed(
        title="🌙 Inactive Roster Members",
        color=discord.Color.dark_grey(),
        description=f"Threshold: {threshold_days} day(s) of silence",
    )

    if not flagged:
        embed.description += "\n\nNobody's currently flagged as inactive. 🎉"
    else:
        value = "\n".join(f"• {name} — {status}" for name, status in flagged[:25])
        embed.add_field(name=f"{len(flagged)} flagged", value=value, inline=False)
        if len(flagged) > 25:
            embed.set_footer(text=f"Showing 25 of {len(flagged)} flagged members")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rank", description="Show a member's current rank.")
@app_commands.describe(user="The member to look up (defaults to you)")
async def rank(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    cfg = get_guild_cfg(interaction.guild_id)
    roster = cfg.get("roster", [])
    rank_role_ids = cfg.get("ranks", [])

    entry = next((e for e in roster if e["user_id"] == user.id), None)

    embed = discord.Embed(color=discord.Color.purple())
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)

    if not entry:
        embed.description = f"{user.mention} isn't on the roster."
        await interaction.response.send_message(embed=embed)
        return

    role = interaction.guild.get_role(entry.get("rank_role_id"))
    rank_label = role.mention if role else "(deleted role)"

    if role and role.id in rank_role_ids:
        position = rank_role_ids.index(role.id)
        icon = RANK_TIER_ICONS[position] if position < len(RANK_TIER_ICONS) else "▪️"
        tier_line = f"{icon} Tier {position + 1} of {len(rank_role_ids)}"
    else:
        tier_line = ""

    embed.add_field(name="Current Rank", value=f"{rank_label}\n{tier_line}", inline=True)
    if user.joined_at:
        embed.add_field(name="Joined Server", value=f"<t:{int(user.joined_at.timestamp())}:D>", inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="history", description="Show a member's rank/roster history.")
@app_commands.describe(user="The member to look up (defaults to you)")
async def history(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    cfg = get_guild_cfg(interaction.guild_id)
    user_history = cfg.get("history", {}).get(str(user.id), [])

    embed = discord.Embed(title=f"🕓 History for {user.display_name}", color=discord.Color.dark_purple())
    embed.set_thumbnail(url=user.display_avatar.url)

    if not user_history:
        embed.description = "No recorded history yet."
        await interaction.response.send_message(embed=embed)
        return

    # Most recent first, capped to the last 10 entries so the embed doesn't overflow.
    recent = list(reversed(user_history))[:10]
    for entry in recent:
        moderator = interaction.guild.get_member(entry["moderator_id"])
        mod_label = moderator.mention if moderator else f"<@{entry['moderator_id']}>"
        ts = datetime.fromisoformat(entry["timestamp"])
        timestamp_label = f"<t:{int(ts.timestamp())}:R>"

        value_lines = [f"By {mod_label} • {timestamp_label}"]
        if entry.get("detail"):
            value_lines.append(entry["detail"])
        if entry.get("reason"):
            value_lines.append(f"Reason: {entry['reason']}")

        embed.add_field(name=entry["action"], value="\n".join(value_lines), inline=False)

    if len(user_history) > 10:
        embed.set_footer(text=f"Showing 10 most recent of {len(user_history)} total entries")

    await interaction.response.send_message(embed=embed)


# ---------- tournaments ----------

def build_tournament_signup_embed(name: str, data: dict) -> discord.Embed:
    embed = discord.Embed(title=f"🏆 Tournament: {name}", color=discord.Color.gold())
    if data["status"] == "signup":
        embed.description = "Sign-ups are open! Click **Join** below to enter."
        if data["players"]:
            embed.add_field(
                name=f"Players ({len(data['players'])})",
                value="\n".join(f"• <@{pid}>" for pid in data["players"]),
                inline=False,
            )
        else:
            embed.add_field(name="Players (0)", value="Nobody has joined yet.", inline=False)
    else:
        embed.description = "Sign-ups are closed — the tournament has started."
    return embed


class TournamentJoinView(discord.ui.View):
    def __init__(self, guild_id: int, name: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.name = name

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_guild_cfg(self.guild_id)
        data = cfg.get("tournaments", {}).get(self.name)
        if not data or data["status"] != "signup":
            await interaction.response.send_message("❌ Sign-ups are closed for this tournament.", ephemeral=True)
            return
        if interaction.user.id not in data["players"]:
            data["players"].append(interaction.user.id)
            save_config(config)
        await interaction.response.edit_message(embed=build_tournament_signup_embed(self.name, data))

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_guild_cfg(self.guild_id)
        data = cfg.get("tournaments", {}).get(self.name)
        if not data or data["status"] != "signup":
            await interaction.response.send_message("❌ Sign-ups are closed for this tournament.", ephemeral=True)
            return
        if interaction.user.id in data["players"]:
            data["players"].remove(interaction.user.id)
            save_config(config)
        await interaction.response.edit_message(embed=build_tournament_signup_embed(self.name, data))


def make_tournament_pairings(player_ids: list, shuffle: bool = False) -> list:
    ids = list(player_ids)
    if shuffle:
        random.shuffle(ids)
    matches = []
    i = 0
    while i < len(ids):
        if i + 1 < len(ids):
            matches.append({"p1": ids[i], "p2": ids[i + 1], "winner": None})
            i += 2
        else:
            # Odd one out gets a bye and auto-advances.
            matches.append({"p1": ids[i], "p2": None, "winner": ids[i]})
            i += 1
    return matches


def build_tournament_bracket_embed(name: str, data: dict) -> discord.Embed:
    if data["status"] == "complete":
        embed = discord.Embed(
            title=f"🏆 {name} — Champion: <@{data['champion']}>! 🎉",
            color=discord.Color.gold(),
        )
    else:
        embed = discord.Embed(title=f"🏆 Tournament: {name}", color=discord.Color.dark_gold())

    for round_idx, round_matches in enumerate(data["rounds"], start=1):
        lines = []
        for match_idx, m in enumerate(round_matches, start=1):
            p1 = f"<@{m['p1']}>" if m["p1"] else "BYE"
            p2 = f"<@{m['p2']}>" if m["p2"] else "BYE"
            if m["winner"]:
                lines.append(f"Match {match_idx}: {p1} vs {p2} → 🏆 <@{m['winner']}>")
            else:
                lines.append(f"Match {match_idx}: {p1} vs {p2} → TBD")
        embed.add_field(name=f"Round {round_idx}", value="\n".join(lines), inline=False)

    return embed


@bot.tree.command(name="tournament_create", description="Open sign-ups for a single-elimination tournament.")
@app_commands.describe(name="A short name for this tournament")
async def tournament_create(interaction: discord.Interaction, name: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    tournaments = cfg.setdefault("tournaments", {})
    existing = tournaments.get(name)
    if existing and existing["status"] != "complete":
        await interaction.response.send_message(
            f"❌ A tournament named **{name}** is already in progress.", ephemeral=True
        )
        return

    data = {"status": "signup", "players": [], "rounds": [], "channel_id": interaction.channel_id}
    tournaments[name] = data
    save_config(config)

    view = TournamentJoinView(interaction.guild_id, name)
    await interaction.response.send_message(embed=build_tournament_signup_embed(name, data), view=view)
    sent = await interaction.original_response()
    data["message_id"] = sent.id
    save_config(config)


@bot.tree.command(name="tournament_start", description="Lock sign-ups and generate the bracket.")
@app_commands.describe(name="The tournament's name")
async def tournament_start(interaction: discord.Interaction, name: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    data = cfg.get("tournaments", {}).get(name)
    if not data or data["status"] != "signup":
        await interaction.response.send_message(f"❌ No open sign-ups found for **{name}**.", ephemeral=True)
        return
    if len(data["players"]) < 2:
        await interaction.response.send_message("❌ Need at least 2 players to start.", ephemeral=True)
        return

    data["rounds"] = [make_tournament_pairings(data["players"], shuffle=True)]
    data["status"] = "in_progress"
    save_config(config)

    await interaction.response.send_message(embed=build_tournament_bracket_embed(name, data))


@bot.tree.command(name="tournament_report", description="Record the winner of a match.")
@app_commands.describe(name="The tournament's name", match="Match number in the current round", winner="Who won")
async def tournament_report(interaction: discord.Interaction, name: str, match: int, winner: discord.Member):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    data = cfg.get("tournaments", {}).get(name)
    if not data or data["status"] != "in_progress":
        await interaction.response.send_message(f"❌ No in-progress tournament found named **{name}**.", ephemeral=True)
        return

    current_round = data["rounds"][-1]
    if match < 1 or match > len(current_round):
        await interaction.response.send_message(f"❌ Match number must be between 1 and {len(current_round)}.", ephemeral=True)
        return

    m = current_round[match - 1]
    if winner.id not in (m["p1"], m["p2"]):
        await interaction.response.send_message("❌ That person isn't in this match.", ephemeral=True)
        return

    m["winner"] = winner.id

    if all(mm["winner"] is not None for mm in current_round):
        winners = [mm["winner"] for mm in current_round]
        if len(winners) == 1:
            data["status"] = "complete"
            data["champion"] = winners[0]
        else:
            data["rounds"].append(make_tournament_pairings(winners, shuffle=False))

    save_config(config)
    await interaction.response.send_message(embed=build_tournament_bracket_embed(name, data))


@bot.tree.command(name="tournament_bracket", description="Show the current bracket for a tournament.")
@app_commands.describe(name="The tournament's name")
async def tournament_bracket(interaction: discord.Interaction, name: str):
    cfg = get_guild_cfg(interaction.guild_id)
    data = cfg.get("tournaments", {}).get(name)
    if not data or not data["rounds"]:
        await interaction.response.send_message(f"❌ No bracket found for **{name}** yet.", ephemeral=True)
        return
    await interaction.response.send_message(embed=build_tournament_bracket_embed(name, data))


# ---------- game nights ----------

def build_gamenight_embed(data: dict) -> discord.Embed:
    when = int(datetime.fromisoformat(data["when"]).timestamp())
    embed = discord.Embed(title=f"🎮 Game Night: {data['game']}", color=discord.Color.blue())
    embed.add_field(name="When", value=f"<t:{when}:F> (<t:{when}:R>)", inline=False)
    embed.add_field(name=f"✅ Going ({len(data['going'])})", value="\n".join(f"<@{u}>" for u in data["going"]) or "—", inline=True)
    embed.add_field(name=f"❓ Maybe ({len(data['maybe'])})", value="\n".join(f"<@{u}>" for u in data["maybe"]) or "—", inline=True)
    embed.add_field(name=f"❌ Can't Go ({len(data['cant'])})", value="\n".join(f"<@{u}>" for u in data["cant"]) or "—", inline=True)
    return embed


class GameNightRSVPView(discord.ui.View):
    def __init__(self, guild_id: int, gamenight_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.gamenight_id = gamenight_id

    def _get_data(self):
        cfg = get_guild_cfg(self.guild_id)
        return cfg.get("gamenights", {}).get(self.gamenight_id)

    async def _rsvp(self, interaction: discord.Interaction, list_name: str):
        data = self._get_data()
        if not data:
            await interaction.response.send_message("❌ This game night no longer exists.", ephemeral=True)
            return
        uid = interaction.user.id
        for key in ("going", "maybe", "cant"):
            if uid in data[key]:
                data[key].remove(uid)
        data[list_name].append(uid)
        save_config(config)
        await interaction.response.edit_message(embed=build_gamenight_embed(data))

    @discord.ui.button(label="Going", style=discord.ButtonStyle.success, emoji="✅")
    async def going(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "going")

    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.secondary, emoji="❓")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "maybe")

    @discord.ui.button(label="Can't Go", style=discord.ButtonStyle.danger, emoji="❌")
    async def cant(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._rsvp(interaction, "cant")


@bot.tree.command(name="gamenight_create", description="Schedule a game night with RSVPs (time is UTC).")
@app_commands.describe(game="What you're playing", date="Date as YYYY-MM-DD", time="Time as HH:MM, 24-hour, UTC")
async def gamenight_create(interaction: discord.Interaction, game: str, date: str, time: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    try:
        when = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        await interaction.response.send_message(
            "❌ Couldn't parse that date/time. Use YYYY-MM-DD for the date and HH:MM (24-hour, UTC) for the time.",
            ephemeral=True,
        )
        return

    if when <= datetime.now(timezone.utc):
        await interaction.response.send_message("❌ That time is in the past.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    next_id = cfg.get("gamenight_next_id", 1)
    cfg["gamenight_next_id"] = next_id + 1

    data = {
        "id": next_id, "game": game, "when": when.isoformat(),
        "channel_id": interaction.channel_id, "going": [], "maybe": [], "cant": [], "reminded": False,
    }
    cfg.setdefault("gamenights", {})[str(next_id)] = data
    save_config(config)

    view = GameNightRSVPView(interaction.guild_id, str(next_id))
    await interaction.response.send_message(embed=build_gamenight_embed(data), view=view)
    sent = await interaction.original_response()
    data["message_id"] = sent.id
    save_config(config)


@bot.tree.command(name="gamenight_list", description="Show upcoming game nights.")
async def gamenight_list(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    gamenights = cfg.get("gamenights", {})
    now = datetime.now(timezone.utc)
    upcoming = sorted(
        (d for d in gamenights.values() if datetime.fromisoformat(d["when"]) > now),
        key=lambda d: d["when"],
    )

    embed = discord.Embed(title="🎮 Upcoming Game Nights", color=discord.Color.blue())
    if not upcoming:
        embed.description = "Nothing scheduled right now."
    else:
        for d in upcoming:
            when = int(datetime.fromisoformat(d["when"]).timestamp())
            embed.add_field(
                name=f"#{d['id']} — {d['game']}",
                value=f"<t:{when}:F> (<t:{when}:R>) • {len(d['going'])} going",
                inline=False,
            )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="gamenight_cancel", description="Cancel a scheduled game night.")
@app_commands.describe(id="The game night's ID number, shown in /gamenight_list")
async def gamenight_cancel(interaction: discord.Interaction, id: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    gamenights = cfg.get("gamenights", {})
    data = gamenights.pop(str(id), None)
    if not data:
        await interaction.response.send_message(f"❌ No game night found with ID {id}.", ephemeral=True)
        return
    save_config(config)

    channel = interaction.guild.get_channel(data["channel_id"])
    if channel and data.get("message_id"):
        try:
            msg = await channel.fetch_message(data["message_id"])
            await msg.edit(content="🚫 This game night was cancelled.", embed=None, view=None)
        except (discord.NotFound, discord.Forbidden):
            pass

    await interaction.response.send_message(f"✅ Cancelled game night #{id} ({data['game']}).", ephemeral=True)


@tasks.loop(minutes=1)
async def gamenight_reminder_loop():
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        cfg = get_guild_cfg(guild.id)
        gamenights = cfg.get("gamenights", {})
        changed = False
        for data in gamenights.values():
            if data.get("reminded"):
                continue
            when = datetime.fromisoformat(data["when"])
            if timedelta(0) <= (when - now) <= timedelta(minutes=15):
                channel = guild.get_channel(data["channel_id"])
                if channel:
                    pings = " ".join(f"<@{u}>" for u in data["going"]) or "No one has RSVP'd going yet!"
                    try:
                        await channel.send(f"⏰ **{data['game']}** starts soon! {pings}")
                    except discord.Forbidden:
                        pass
                data["reminded"] = True
                changed = True
        if changed:
            save_config(config)


def build_evaluation_embed(guild: discord.Guild, cfg: dict, top_n: int = 10) -> discord.Embed:
    counts = cfg.get("message_counts", {})
    since_str = cfg.get("message_count_since")
    since = datetime.fromisoformat(since_str) if since_str else datetime.now(timezone.utc)

    embed = discord.Embed(title="📈 Message Activity", color=discord.Color.dark_teal())
    embed.description = f"Counting messages since <t:{int(since.timestamp())}:D> (<t:{int(since.timestamp())}:R>)"

    if not counts:
        embed.description += "\n\nNo messages recorded yet this period."
        return embed

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    lines = []
    for i, (user_id, count) in enumerate(ranked, start=1):
        member = guild.get_member(int(user_id))
        name = member.mention if member else f"<@{user_id}> (left)"
        medal = RANK_TIER_ICONS[i - 1] if i - 1 < len(RANK_TIER_ICONS) else "▪️"
        lines.append(f"{medal} {name} — **{count}** message(s)")
    embed.add_field(name=f"Top {len(ranked)}", value="\n".join(lines), inline=False)
    embed.set_footer(text=f"{len(counts)} member(s) with recorded activity this period")
    return embed


@tasks.loop(hours=24)
async def weekly_evaluation_loop():
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        cfg = get_guild_cfg(guild.id)
        since_str = cfg.get("message_count_since")
        if not since_str:
            continue
        since = datetime.fromisoformat(since_str)
        if now - since < timedelta(days=7):
            continue

        log_channel_id = cfg.get("log_channel_id")
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                embed = build_evaluation_embed(guild, cfg)
                embed.title = "📈 Weekly Message Activity Report"
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        cfg["message_counts"] = {}
        cfg["message_count_since"] = now.isoformat()
        save_config(config)


@tasks.loop(hours=1)
async def birthday_check_loop():
    """Runs hourly but only actually acts once per UTC day per guild — checking
    hourly (rather than a plain 24h loop) makes it resilient to the bot
    restarting/redeploying at odd times, since it just compares dates."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%m-%d")
    today_date = now.date().isoformat()

    for guild in bot.guilds:
        cfg = get_guild_cfg(guild.id)
        if cfg.get("birthday_last_checked") == today_date:
            continue
        cfg["birthday_last_checked"] = today_date

        role_id = cfg.get("birthday_role_id")
        role = guild.get_role(role_id) if role_id else None
        birthdays = cfg.get("birthdays", {})

        # Remove the role from anyone who had it for a birthday that isn't today anymore.
        holders = cfg.get("birthday_role_holders", [])
        still_holding = []
        if role:
            for uid in holders:
                member = guild.get_member(uid)
                if member and birthdays.get(str(uid)) == today_str:
                    still_holding.append(uid)  # still their birthday somehow — keep it
                elif member and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Birthday role expired")
                    except discord.Forbidden:
                        pass
        cfg["birthday_role_holders"] = still_holding

        # Grant the role (and announce) for anyone whose birthday is today.
        channel_id = cfg.get("birthday_channel_id")
        channel = guild.get_channel(channel_id) if channel_id else None

        for uid_str, bday in birthdays.items():
            if bday != today_str:
                continue
            member = guild.get_member(int(uid_str))
            if not member:
                continue

            if role and role < guild.me.top_role and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Happy birthday!")
                    cfg.setdefault("birthday_role_holders", [])
                    if member.id not in cfg["birthday_role_holders"]:
                        cfg["birthday_role_holders"].append(member.id)
                except discord.Forbidden:
                    pass

            if channel:
                try:
                    await channel.send(f"🎉🎂 Happy Birthday, {member.mention}! Hope it's a great one!")
                except discord.Forbidden:
                    pass

        save_config(config)


# ---------- MVP voting ----------

def build_mvp_embed(guild: discord.Guild, poll: dict) -> discord.Embed:
    embed = discord.Embed(title=f"⭐ MVP Vote: {poll['title']}", color=discord.Color.fuchsia())
    tally = {}
    for cid in poll["votes"].values():
        tally[cid] = tally.get(cid, 0) + 1

    lines = []
    for cid in poll["candidates"]:
        member = guild.get_member(cid)
        name = member.mention if member else f"<@{cid}>"
        lines.append(f"{name} — **{tally.get(cid, 0)}** vote(s)")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"{len(poll['votes'])} total vote(s) cast")
    return embed


class MVPVoteView(discord.ui.View):
    def __init__(self, guild: discord.Guild, poll: dict):
        super().__init__(timeout=None)
        self.guild_id = guild.id
        for cid in poll["candidates"]:
            member = guild.get_member(cid)
            label = member.display_name if member else str(cid)
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            button.callback = self._make_callback(cid)
            self.add_item(button)

    def _make_callback(self, candidate_id: int):
        async def callback(interaction: discord.Interaction):
            cfg = get_guild_cfg(self.guild_id)
            poll = cfg.get("mvp_poll")
            if not poll:
                await interaction.response.send_message("❌ This vote has closed.", ephemeral=True)
                return
            poll["votes"][str(interaction.user.id)] = candidate_id
            save_config(config)
            await interaction.response.edit_message(embed=build_mvp_embed(interaction.guild, poll))
        return callback


@bot.tree.command(name="mvp_start", description="Open MVP voting among up to 5 candidates.")
@app_commands.describe(
    title="What this vote is for, e.g. 'Scrim vs Team X'",
    user1="Candidate 1", user2="Candidate 2", user3="Candidate 3", user4="Candidate 4", user5="Candidate 5",
)
async def mvp_start(
    interaction: discord.Interaction,
    title: str,
    user1: discord.Member,
    user2: discord.Member = None,
    user3: discord.Member = None,
    user4: discord.Member = None,
    user5: discord.Member = None,
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    if cfg.get("mvp_poll"):
        await interaction.response.send_message(
            "❌ There's already an active MVP vote. Run /mvp_end to close it first.", ephemeral=True
        )
        return

    candidates = [u.id for u in [user1, user2, user3, user4, user5] if u is not None]
    poll = {"title": title, "candidates": candidates, "votes": {}, "channel_id": interaction.channel_id}
    cfg["mvp_poll"] = poll
    save_config(config)

    view = MVPVoteView(interaction.guild, poll)
    await interaction.response.send_message(embed=build_mvp_embed(interaction.guild, poll), view=view)
    sent = await interaction.original_response()
    poll["message_id"] = sent.id
    save_config(config)


@bot.tree.command(name="mvp_end", description="Close MVP voting and announce the winner.")
async def mvp_end(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    poll = cfg.get("mvp_poll")
    if not poll:
        await interaction.response.send_message("❌ There's no active MVP vote.", ephemeral=True)
        return

    tally = {}
    for cid in poll["votes"].values():
        tally[cid] = tally.get(cid, 0) + 1

    if not tally:
        await interaction.response.send_message("ℹ️ No votes were cast — nobody to announce.", ephemeral=True)
        cfg["mvp_poll"] = None
        save_config(config)
        return

    top_votes = max(tally.values())
    winners = [cid for cid, v in tally.items() if v == top_votes]

    if len(winners) == 1:
        result = f"🏆 **{poll['title']}** MVP: <@{winners[0]}> with {top_votes} vote(s)!"
    else:
        names = ", ".join(f"<@{w}>" for w in winners)
        result = f"🏆 **{poll['title']}** ended in a tie between {names} with {top_votes} vote(s) each!"

    channel = interaction.guild.get_channel(poll["channel_id"])
    if channel and poll.get("message_id"):
        try:
            msg = await channel.fetch_message(poll["message_id"])
            await msg.edit(embed=build_mvp_embed(interaction.guild, poll), view=None)
        except (discord.NotFound, discord.Forbidden):
            pass

    cfg["mvp_poll"] = None
    save_config(config)
    await interaction.response.send_message(result)


# ---------- cross-posting ----------

@bot.tree.command(name="crosspost_add", description="Mirror messages from THIS channel to a channel in another server the bot is also in.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(destination_channel_id="The channel ID to mirror into (right-click the channel in the other server → Copy Channel ID)")
async def crosspost_add(interaction: discord.Interaction, destination_channel_id: str):
    try:
        dest_id = int(destination_channel_id)
    except ValueError:
        await interaction.response.send_message("❌ That doesn't look like a valid channel ID.", ephemeral=True)
        return

    dest_channel = bot.get_channel(dest_id)
    if dest_channel is None:
        await interaction.response.send_message(
            "❌ I can't see that channel. Make sure the bot is invited to that server and has access to that "
            "channel, then try again.",
            ephemeral=True,
        )
        return
    if not isinstance(dest_channel, discord.TextChannel):
        await interaction.response.send_message("❌ That has to be a text channel.", ephemeral=True)
        return
    if not dest_channel.permissions_for(dest_channel.guild.me).send_messages:
        await interaction.response.send_message(
            f"❌ I don't have permission to send messages in {dest_channel.mention} over in **{dest_channel.guild.name}**.",
            ephemeral=True,
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    crossposts = cfg.setdefault("crossposts", {})
    crossposts[str(interaction.channel_id)] = dest_id
    save_config(config)

    await interaction.response.send_message(
        f"✅ Messages sent in {interaction.channel.mention} will now be mirrored to "
        f"**#{dest_channel.name}** in **{dest_channel.guild.name}**.",
        ephemeral=True,
    )


@bot.tree.command(name="crosspost_remove", description="Stop mirroring THIS channel to another server.")
@app_commands.checks.has_permissions(administrator=True)
async def crosspost_remove(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    crossposts = cfg.setdefault("crossposts", {})
    if str(interaction.channel_id) not in crossposts:
        await interaction.response.send_message("ℹ️ This channel isn't currently being mirrored anywhere.", ephemeral=True)
        return

    crossposts.pop(str(interaction.channel_id))
    save_config(config)
    await interaction.response.send_message("✅ This channel will no longer be mirrored.", ephemeral=True)


@bot.tree.command(name="crosspost_list", description="Show all cross-posting mirrors set up in this server.")
@app_commands.checks.has_permissions(administrator=True)
async def crosspost_list(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    crossposts = cfg.get("crossposts", {})

    embed = discord.Embed(title="🔀 Cross-Posting Mirrors", color=discord.Color.dark_teal())
    if not crossposts:
        embed.description = "No mirrors set up in this server."
    else:
        lines = []
        for source_id, dest_id in crossposts.items():
            source_channel = interaction.guild.get_channel(int(source_id))
            dest_channel = bot.get_channel(dest_id)
            source_label = source_channel.mention if source_channel else f"(deleted channel {source_id})"
            dest_label = f"#{dest_channel.name} in {dest_channel.guild.name}" if dest_channel else f"(unreachable channel {dest_id})"
            lines.append(f"{source_label} → {dest_label}")
        embed.description = "\n".join(lines)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------- moderation ----------

@bot.tree.command(name="kick", description="Kick a member from the server.")
@app_commands.describe(user="The member to kick", reason="Why you're kicking them")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.kick_members:
        await interaction.response.send_message("❌ I don't have permission to kick members.", ephemeral=True)
        return
    if user.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I can't kick that member — their role is higher than or equal to mine.", ephemeral=True
        )
        return

    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ Kick {user.mention} from the server? Reason: {reason}", view=view, ephemeral=True
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="👢 You were kicked",
        color=discord.Color.dark_red(),
        fields={"Reason": reason},
    )
    try:
        await user.kick(reason=f"By {interaction.user} via /kick: {reason}")
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to kick that member.", view=None)
        return

    note = "\n\n*(couldn't DM them before kicking)*" if not dm_sent else ""
    await interaction.edit_original_response(content=f"✅ Kicked {user.mention}. Reason: {reason}{note}", view=None)
    await log_movement(interaction.guild, member=user, target="kicked", reason=reason, moderator=interaction.user)


@bot.tree.command(name="ban", description="Ban a member from the server.")
@app_commands.describe(user="The member to ban", reason="Why you're banning them", delete_days="Days of their message history to delete (0-7)")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str, delete_days: int = 0):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ I don't have permission to ban members.", ephemeral=True)
        return
    if user.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I can't ban that member — their role is higher than or equal to mine.", ephemeral=True
        )
        return
    delete_days = max(0, min(7, delete_days))

    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ **Ban** {user.mention} from the server? Reason: {reason}", view=view, ephemeral=True
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="🔨 You were banned",
        color=discord.Color.dark_red(),
        fields={"Reason": reason},
    )
    try:
        await user.ban(reason=f"By {interaction.user} via /ban: {reason}", delete_message_days=delete_days)
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to ban that member.", view=None)
        return

    note = "\n\n*(couldn't DM them before banning)*" if not dm_sent else ""
    await interaction.edit_original_response(content=f"✅ Banned {user.mention}. Reason: {reason}{note}", view=None)
    await log_movement(interaction.guild, member=user, target="banned", reason=reason, moderator=interaction.user)


@bot.tree.command(name="timeout", description="Temporarily mute a member.")
@app_commands.describe(user="The member to time out", minutes="How long, in minutes", reason="Why you're timing them out")
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ I don't have permission to time out members.", ephemeral=True)
        return
    if minutes <= 0 or minutes > 40320:  # Discord's cap is 28 days
        await interaction.response.send_message("❌ Minutes must be between 1 and 40320 (28 days).", ephemeral=True)
        return
    if user.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I can't time out that member — their role is higher than or equal to mine.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # Announce in their voice channel BEFORE the timeout actually takes effect,
    # so they (and anyone with them) hear it land in real time.
    await announce_timeout_in_vc(user, minutes, reason)

    try:
        await user.timeout(timedelta(minutes=minutes), reason=f"By {interaction.user} via /timeout: {reason}")
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to time out that member.", ephemeral=True)
        return

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="🔇 You were timed out",
        color=discord.Color.dark_orange(),
        fields={"Duration": f"{minutes} minute(s)", "Reason": reason},
    )
    note = "\n\n*(couldn't DM them)*" if not dm_sent else ""
    await interaction.followup.send(
        f"✅ Timed out {user.mention} for {minutes} minute(s). Reason: {reason}{note}", ephemeral=True
    )
    await log_movement(
        interaction.guild, member=user, target=f"timed out ({minutes}m)", reason=reason, moderator=interaction.user
    )


@bot.tree.command(name="warn", description="Log a warning against a member.")
@app_commands.describe(user="The member to warn", reason="Why you're warning them")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    warnings = cfg.setdefault("warnings", {})
    user_warnings = warnings.setdefault(str(user.id), [])
    user_warnings.append({
        "reason": reason,
        "moderator_id": interaction.user.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_config(config)

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="⚠️ You were warned",
        color=discord.Color.gold(),
        fields={"Reason": reason, "Total Warnings": str(len(user_warnings))},
    )
    note = "\n\n*(couldn't DM them)*" if not dm_sent else ""
    await interaction.response.send_message(
        f"✅ Warned {user.mention} (warning #{len(user_warnings)}). Reason: {reason}{note}", ephemeral=True
    )
    await log_movement(
        interaction.guild, member=user, target=f"warned (#{len(user_warnings)})", reason=reason, moderator=interaction.user
    )


@bot.tree.command(name="warnings", description="Show a member's warning history.")
@app_commands.describe(user="The member to look up (defaults to you)")
async def warnings_cmd(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    cfg = get_guild_cfg(interaction.guild_id)
    user_warnings = cfg.get("warnings", {}).get(str(user.id), [])

    embed = discord.Embed(title=f"⚠️ Warnings for {user.display_name}", color=discord.Color.gold())
    embed.set_thumbnail(url=user.display_avatar.url)

    if not user_warnings:
        embed.description = "No warnings on record."
    else:
        for i, w in enumerate(reversed(user_warnings[-10:]), start=1):
            moderator = interaction.guild.get_member(w["moderator_id"])
            mod_label = moderator.mention if moderator else f"<@{w['moderator_id']}>"
            ts = datetime.fromisoformat(w["timestamp"])
            embed.add_field(
                name=f"Warning #{len(user_warnings) - i + 1}",
                value=f"{w['reason']}\nBy {mod_label} • <t:{int(ts.timestamp())}:R>",
                inline=False,
            )
        embed.set_footer(text=f"{len(user_warnings)} total warning(s)")

    await interaction.response.send_message(embed=embed)


# ---------- channel control ----------

@bot.tree.command(name="purge", description="Bulk-delete recent messages in this channel.")
@app_commands.describe(amount="How many messages to delete (1-100)")
async def purge(interaction: discord.Interaction, amount: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message("❌ I don't have permission to delete messages here.", ephemeral=True)
        return
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Deleted {len(deleted)} message(s).", ephemeral=True)
    await log_movement(
        interaction.guild, member=interaction.user, target=f"purged {len(deleted)} messages in {interaction.channel.mention}",
        reason="—", moderator=interaction.user,
    )


@bot.tree.command(name="lock", description="Prevent everyone from sending messages in this channel.")
@app_commands.describe(reason="Why you're locking this channel")
async def lock(interaction: discord.Interaction, reason: str = "No reason given"):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
        await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
        return

    everyone = interaction.guild.default_role
    overwrite = interaction.channel.overwrites_for(everyone)
    overwrite.send_messages = False
    try:
        await interaction.channel.set_permissions(everyone, overwrite=overwrite, reason=f"Locked by {interaction.user}: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to edit this channel's permissions.", ephemeral=True)
        return

    await interaction.response.send_message(f"🔒 Channel locked. Reason: {reason}")
    await log_movement(
        interaction.guild, member=interaction.user, target=f"locked {interaction.channel.mention}",
        reason=reason, moderator=interaction.user,
    )


@bot.tree.command(name="unlock", description="Allow everyone to send messages in this channel again.")
async def unlock(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
        await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
        return

    everyone = interaction.guild.default_role
    overwrite = interaction.channel.overwrites_for(everyone)
    overwrite.send_messages = None  # reset to default rather than explicitly True
    try:
        await interaction.channel.set_permissions(everyone, overwrite=overwrite, reason=f"Unlocked by {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to edit this channel's permissions.", ephemeral=True)
        return

    await interaction.response.send_message("🔓 Channel unlocked.")
    await log_movement(
        interaction.guild, member=interaction.user, target=f"unlocked {interaction.channel.mention}",
        reason="—", moderator=interaction.user,
    )


@bot.tree.command(name="slowmode", description="Set slowmode delay for this channel.")
@app_commands.describe(seconds="Seconds between messages per person (0 to disable, max 21600)")
async def slowmode(interaction: discord.Interaction, seconds: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
        await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
        return
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message("❌ Seconds must be between 0 and 21600 (6 hours).", ephemeral=True)
        return

    await interaction.channel.edit(slowmode_delay=seconds, reason=f"Set by {interaction.user}")
    if seconds == 0:
        await interaction.response.send_message("✅ Slowmode disabled.")
    else:
        await interaction.response.send_message(f"✅ Slowmode set to {seconds} second(s).")


# ---------- admin utility ----------

@bot.tree.command(name="audit", description="Show the last 20 rank/roster actions across everyone in this server.")
async def audit(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    history = cfg.get("history", {})

    all_entries = []
    for user_id_str, entries in history.items():
        for entry in entries:
            all_entries.append((int(user_id_str), entry))

    all_entries.sort(key=lambda pair: pair[1]["timestamp"], reverse=True)
    recent = all_entries[:20]

    embed = discord.Embed(title="🗂️ Server Audit Log", color=discord.Color.dark_grey())
    if not recent:
        embed.description = "No recorded actions yet."
    else:
        lines = []
        for user_id, entry in recent:
            moderator = interaction.guild.get_member(entry["moderator_id"])
            mod_label = moderator.mention if moderator else f"<@{entry['moderator_id']}>"
            ts = datetime.fromisoformat(entry["timestamp"])
            detail = f" — {entry['detail']}" if entry.get("detail") else ""
            lines.append(f"<@{user_id}> **{entry['action']}**{detail} • by {mod_label} • <t:{int(ts.timestamp())}:R>")
        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Showing {len(recent)} most recent of {len(all_entries)} total entries")

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="backup", description="Export this server's bot configuration as a downloadable file.")
@app_commands.checks.has_permissions(administrator=True)
async def backup(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    data = json.dumps(cfg, indent=2)
    file_bytes = io.BytesIO(data.encode("utf-8"))
    file = discord.File(file_bytes, filename=f"backup-{interaction.guild_id}.json")
    await interaction.response.send_message(
        "✅ Here's a backup of this server's bot configuration (ranks, channels, roster, settings, history).",
        file=file,
        ephemeral=True,
    )


@bot.tree.command(name="announce", description="Post a formatted announcement to a channel.")
@app_commands.describe(
    channel="Where to post it", title="Announcement title", message="The announcement text",
    ping_everyone="Ping @everyone in that channel? (default: yes)",
)
async def announce(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    message: str,
    ping_everyone: bool = True,
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}.", ephemeral=True)
        return

    warn_no_ping_perm = ping_everyone and not channel.permissions_for(interaction.guild.me).mention_everyone

    embed = discord.Embed(color=discord.Color.gold(), timestamp=discord.utils.utcnow())
    embed.title = f"📣 {title}"
    embed.description = f"{SPACER}\n{message}\n{SPACER}"
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    embed.set_footer(text=f"Posted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    content = "@everyone" if ping_everyone else None
    allowed = discord.AllowedMentions(everyone=ping_everyone)

    try:
        await channel.send(content=content, embed=embed, allowed_mentions=allowed)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Announcement posted in {channel.mention}.", ephemeral=True)
    if warn_no_ping_perm:
        await interaction.followup.send(
            "⚠️ Note: I don't have the **Mention @everyone** permission in that channel, so the ping "
            "didn't actually notify anyone — the announcement posted, just silently.",
            ephemeral=True,
        )


async def run_broadcast(
    guild: discord.Guild,
    moderator: discord.Member,
    title: str,
    message: str,
    text_channels: list,
    voice_channels: list,
    ping_everyone: bool = True,
):
    """Background worker for /massannounce — posts the embed, then speaks the
    announcement in each active voice channel one at a time (a bot can only
    be connected to one voice channel per server at once)."""
    embed = discord.Embed(color=discord.Color.gold(), timestamp=discord.utils.utcnow())
    embed.title = f"📣 {title}"
    embed.description = f"{SPACER}\n{message}\n{SPACER}"
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=f"Posted by {moderator.display_name}", icon_url=moderator.display_avatar.url)

    content = "@everyone" if ping_everyone else None
    allowed = discord.AllowedMentions(everyone=ping_everyone)

    posted = 0
    for channel in text_channels:
        try:
            await channel.send(content=content, embed=embed, allowed_mentions=allowed)
            posted += 1
        except (discord.Forbidden, discord.HTTPException):
            pass

    announced = 0
    if voice_channels:
        spoken_text = f"Announcement, {message}"
        try:
            tmp_path = await generate_tts_file(spoken_text)
        except Exception:
            tmp_path = None

        if tmp_path:
            for vc in voice_channels:
                try:
                    await play_tts_in_voice_channel(vc, tmp_path)
                    announced += 1
                except Exception:
                    continue
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


@bot.tree.command(name="massannounce", description="Send an announcement to all announcement channels and speak it in every active voice channel.")
@app_commands.describe(
    message="The announcement text", title="Optional title (defaults to 'Announcement')",
    ping_everyone="Ping @everyone in each channel? (default: yes)",
)
async def massannounce(interaction: discord.Interaction, message: str, title: str = "Announcement", ping_everyone: bool = True):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    text_channels = [c for c in interaction.guild.text_channels if "announcement" in c.name.lower()]
    active_vcs = [vc for vc in interaction.guild.voice_channels if any(not m.bot for m in vc.members)]

    if not text_channels and not active_vcs:
        await interaction.response.send_message(
            "ℹ️ Nothing to broadcast to — no channel names contain 'announcement', and no voice channels currently have anyone in them.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"📢 Broadcasting to {len(text_channels)} announcement channel(s) and speaking in {len(active_vcs)} active voice channel(s)...",
        ephemeral=True,
    )
    asyncio.create_task(
        run_broadcast(interaction.guild, interaction.user, title, message, text_channels, active_vcs, ping_everyone)
    )


# ---------- mass rename ----------

@bot.tree.command(name="massrename", description="Add a prefix/suffix to multiple members' nicknames at once.")
@app_commands.describe(
    prefix="Text to add before each name (optional)",
    suffix="Text to add after each name (optional)",
    role="Only rename members with this role (omit to target everyone eligible)",
    reason="Why you're doing this",
)
async def massrename(
    interaction: discord.Interaction,
    prefix: str = None,
    suffix: str = None,
    role: discord.Role = None,
    reason: str = "Mass rename",
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not prefix and not suffix:
        await interaction.response.send_message("❌ Provide at least a prefix or a suffix.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.manage_nicknames:
        await interaction.response.send_message("❌ I don't have permission to manage nicknames.", ephemeral=True)
        return

    bot_top_role = interaction.guild.me.top_role
    targets = [
        m for m in interaction.guild.members
        if not m.bot
        and m.id != interaction.guild.owner_id
        and m.top_role < bot_top_role
        and (role is None or role in m.roles)
    ]

    if not targets:
        await interaction.response.send_message("ℹ️ No eligible members matched — nothing to rename.", ephemeral=True)
        return

    preview = f"{prefix or ''}<name>{suffix or ''}"
    view = ConfirmView(interaction.user.id)
    scope = f"members with {role.mention}" if role else "all eligible members"
    await interaction.response.send_message(
        f"⚠️ Rename **{len(targets)}** {scope} to the pattern `{preview}`? This can't be easily undone in bulk.",
        view=view, ephemeral=True,
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    await interaction.edit_original_response(content=f"⏳ Renaming {len(targets)} member(s)...", view=None)

    renamed, failed = 0, 0
    for member in targets:
        base_name = member.nick or member.name
        new_nick = f"{prefix or ''}{base_name}{suffix or ''}"[:32]  # Discord's nickname length limit
        try:
            await member.edit(nick=new_nick, reason=f"Mass rename by {interaction.user}: {reason}")
            renamed += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    summary = f"✅ Renamed {renamed} member(s)."
    if failed:
        summary += f" ⚠️ {failed} failed (likely a permissions issue)."
    await interaction.followup.send(summary, ephemeral=True)

    await log_bulk_action(
        interaction.guild,
        title="✏️ Mass Rename",
        color=discord.Color.dark_teal(),
        moderator=interaction.user,
        description=f"Applied pattern `{preview}` to {scope}.",
        fields={"Renamed": str(renamed), "Failed": str(failed), "Reason": reason},
    )


# ---------- mass role add/remove ----------

@bot.tree.command(name="massaddrole", description="Give a role to multiple members at once.")
@app_commands.describe(
    role="The role to give",
    filter_role="Only target members who already have this role (omit to target everyone eligible)",
    reason="Why you're doing this",
)
async def massaddrole(
    interaction: discord.Interaction,
    role: discord.Role,
    filter_role: discord.Role = None,
    reason: str = "Mass role add",
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    bot_top_role = interaction.guild.me.top_role
    if role >= bot_top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {role.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    targets = [
        m for m in interaction.guild.members
        if role not in m.roles
        and (filter_role is None or filter_role in m.roles)
    ]

    if not targets:
        await interaction.response.send_message("ℹ️ No eligible members matched — nothing to do.", ephemeral=True)
        return

    scope = f"members with {filter_role.mention}" if filter_role else "all eligible members"
    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ Give {role.mention} to **{len(targets)}** {scope}?", view=view, ephemeral=True
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    await interaction.edit_original_response(content=f"⏳ Adding {role.mention} to {len(targets)} member(s)...", view=None)

    added, failed = 0, 0
    for member in targets:
        try:
            await member.add_roles(role, reason=f"Mass add by {interaction.user}: {reason}")
            added += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    summary = f"✅ Gave {role.mention} to {added} member(s)."
    if failed:
        summary += f" ⚠️ {failed} failed (likely a permissions issue)."
    await interaction.followup.send(summary, ephemeral=True)

    await log_bulk_action(
        interaction.guild,
        title="🟢 Mass Role Add",
        color=discord.Color.green(),
        moderator=interaction.user,
        description=f"Gave {role.mention} to {scope}.",
        fields={"Added": str(added), "Failed": str(failed), "Reason": reason},
    )


@bot.tree.command(name="massremoverole", description="Remove a role from multiple members at once.")
@app_commands.describe(
    role="The role to remove",
    filter_role="Only target members who also have this role (omit to target everyone with the role)",
    reason="Why you're doing this",
)
async def massremoverole(
    interaction: discord.Interaction,
    role: discord.Role,
    filter_role: discord.Role = None,
    reason: str = "Mass role remove",
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    bot_top_role = interaction.guild.me.top_role
    if role >= bot_top_role:
        await interaction.response.send_message(
            f"❌ I can't manage {role.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    targets = [
        m for m in interaction.guild.members
        if role in m.roles
        and (filter_role is None or filter_role in m.roles)
    ]

    if not targets:
        await interaction.response.send_message("ℹ️ No eligible members matched — nothing to do.", ephemeral=True)
        return

    scope = f"members who also have {filter_role.mention}" if filter_role else "all members who have it"
    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ Remove {role.mention} from **{len(targets)}** {scope}?", view=view, ephemeral=True
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    await interaction.edit_original_response(content=f"⏳ Removing {role.mention} from {len(targets)} member(s)...", view=None)

    removed, failed = 0, 0
    for member in targets:
        try:
            await member.remove_roles(role, reason=f"Mass remove by {interaction.user}: {reason}")
            removed += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    summary = f"✅ Removed {role.mention} from {removed} member(s)."
    if failed:
        summary += f" ⚠️ {failed} failed (likely a permissions issue)."
    await interaction.followup.send(summary, ephemeral=True)

    await log_bulk_action(
        interaction.guild,
        title="🔴 Mass Role Remove",
        color=discord.Color.red(),
        moderator=interaction.user,
        description=f"Removed {role.mention} from {scope}.",
        fields={"Removed": str(removed), "Failed": str(failed), "Reason": reason},
    )


# ---------- AFK ----------

@bot.tree.command(name="afk", description="Mark yourself as AFK. Clears automatically next time you send a message.")
@app_commands.describe(reason="Why you're AFK (optional)")
async def afk(interaction: discord.Interaction, reason: str = "AFK"):
    cfg = get_guild_cfg(interaction.guild_id)
    afk_users = cfg.setdefault("afk", {})
    afk_users[str(interaction.user.id)] = {
        "reason": reason,
        "since": datetime.now(timezone.utc).isoformat(),
    }
    save_config(config)
    await interaction.response.send_message(f"💤 {interaction.user.mention} is now AFK: {reason}")


# ---------- help ----------

HELP_CATEGORIES = {
    "🎭 Roles": [
        ("/addrole", "Give a role to a member"),
        ("/removerole", "Remove a role from a member"),
    ],
    "📋 Roster & Ranks": [
        ("/rosteradd", "Add/move a member on the roster + give them the role"),
        ("/rosterremove", "Remove a member from the roster"),
        ("/promote", "Move a member up one rank"),
        ("/demote", "Move a member down one rank"),
        ("/rosterimport", "Bulk-import everyone with a rank role onto the roster"),
        ("/roster", "Show the current roster"),
        ("/stats", "Show roster counts per rank"),
        ("/rank", "Show a member's current rank"),
        ("/history", "Show a member's rank/roster history"),
    ],
    "⚙️ Setup (admin)": [
        ("/setlogchannel", "Set where actions are logged"),
        ("/setmanagerrole", "Set who can use the role/roster commands"),
        ("/setranks", "Set the ordered rank roles"),
        ("/setrosterchannel", "Live auto-updating roster embed"),
        ("/setstatschannel", "Live auto-updating server stats embed"),
        ("/setcooldown", "Cooldown between promotions/demotions"),
        ("/setinactivitydays", "Silence threshold for /inactive"),
        ("/crosspost_add / _remove / _list", "Mirror a channel to another server"),
        ("/backup", "Export the server's bot config as a file"),
    ],
    "📊 Server Info": [
        ("/serverstats", "One-off server stats snapshot"),
        ("/inactive", "Roster members who've gone quiet"),
        ("/audit", "Last 20 rank/roster actions, server-wide"),
        ("/evaluate", "Message activity leaderboard for the current week"),
    ],
    "🏆 Events & Competition": [
        ("/tournament_create / _start / _report / _bracket", "Run a bracket tournament"),
        ("/gamenight_create / _list / _cancel", "Schedule game nights with RSVPs"),
        ("/mvp_start / _end", "Vote for MVP among candidates"),
    ],
    "🛡️ Moderation": [
        ("/kick", "Kick a member (confirmation required)"),
        ("/ban", "Ban a member (confirmation required)"),
        ("/timeout", "Temporarily mute a member"),
        ("/warn", "Log a warning against a member"),
        ("/warnings", "Show a member's warning history"),
        ("/purge", "Bulk-delete recent messages"),
        ("/lock / /unlock", "Stop/allow messages in this channel"),
        ("/slowmode", "Set this channel's slowmode delay"),
    ],
    "🧰 Mass Actions": [
        ("/massrename", "Prefix/suffix multiple nicknames at once"),
        ("/massaddrole", "Give a role to multiple members at once"),
        ("/massremoverole", "Remove a role from multiple members at once"),
    ],
    "🔧 Utility": [
        ("/afk", "Mark yourself AFK"),
        ("/announce", "Post a formatted announcement to one channel"),
        ("/massannounce", "Post + speak an announcement everywhere (text + VC)"),
        ("/setvcgreeting / removevcgreeting", "Bot speaks a custom greeting when someone joins a VC"),
        ("/setbirthday / mybirthday / removebirthday", "Set your birthday"),
        ("/setbirthdayrole / _channel", "(admin) Auto-role + shoutout on birthdays"),
        ("/showcase add / remove / setchannel / list", "Self-assignable role showcase with a live channel"),
    ],
}


@bot.tree.command(name="help", description="Show every command this bot has, grouped by category.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Bot Commands",
        description="Everything this bot can do, grouped by category.",
        color=discord.Color.blurple(),
    )
    if bot.user:
        embed.set_thumbnail(url=bot.user.display_avatar.url)

    for category, commands_list in HELP_CATEGORIES.items():
        value = "\n".join(f"**{name}** — {desc}" for name, desc in commands_list)
        embed.add_field(name=category, value=value, inline=False)

    embed.set_footer(text="Most commands require the manager role or Administrator permission")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------- VC greetings ----------

@bot.tree.command(name="setvcgreeting", description="The bot will say something out loud whenever this person joins any voice channel.")
@app_commands.describe(user="Who to greet", message="What the bot should say when they join a VC")
async def setvcgreeting(interaction: discord.Interaction, user: discord.Member, message: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    greetings = cfg.setdefault("vc_greetings", {})
    greetings[str(user.id)] = message
    save_config(config)

    await interaction.response.send_message(
        f"✅ From now on, when {user.mention} joins a voice channel I'll say: \"{message}\"", ephemeral=True
    )


@bot.tree.command(name="removevcgreeting", description="Stop announcing when this person joins a voice channel.")
@app_commands.describe(user="Who to stop greeting")
async def removevcgreeting(interaction: discord.Interaction, user: discord.Member):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    greetings = cfg.setdefault("vc_greetings", {})
    if str(user.id) not in greetings:
        await interaction.response.send_message(f"ℹ️ {user.mention} doesn't have a VC greeting set.", ephemeral=True)
        return

    greetings.pop(str(user.id))
    save_config(config)
    await interaction.response.send_message(f"✅ Removed {user.mention}'s VC greeting.", ephemeral=True)


# ---------- message activity ----------

@bot.tree.command(name="evaluate", description="Show message activity for the current weekly period.")
@app_commands.describe(user="Show just this member's count instead of the leaderboard")
async def evaluate(interaction: discord.Interaction, user: discord.Member = None):
    cfg = get_guild_cfg(interaction.guild_id)

    if user is not None:
        counts = cfg.get("message_counts", {})
        count = counts.get(str(user.id), 0)
        since_str = cfg.get("message_count_since")
        since = datetime.fromisoformat(since_str) if since_str else datetime.now(timezone.utc)

        embed = discord.Embed(title=f"📈 Activity — {user.display_name}", color=discord.Color.dark_teal())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.description = f"**{count}** message(s) since <t:{int(since.timestamp())}:D> (<t:{int(since.timestamp())}:R>)"
        await interaction.response.send_message(embed=embed)
        return

    embed = build_evaluation_embed(interaction.guild, cfg)
    await interaction.response.send_message(embed=embed)


# ---------- birthdays ----------

@bot.tree.command(name="setbirthday", description="Set your birthday (no year needed).")
@app_commands.describe(month="Birth month (1-12)", day="Birth day (1-31)")
async def setbirthday(interaction: discord.Interaction, month: app_commands.Range[int, 1, 12], day: app_commands.Range[int, 1, 31]):
    try:
        # Use a leap year (2000) so Feb 29 validates correctly; only the month/day is stored.
        date(2000, month, day)
    except ValueError:
        await interaction.response.send_message("❌ That's not a valid date.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    birthdays = cfg.setdefault("birthdays", {})
    birthdays[str(interaction.user.id)] = f"{month:02d}-{day:02d}"
    save_config(config)

    await interaction.response.send_message(
        f"🎂 Got it — your birthday is set to **{month:02d}-{day:02d}**.", ephemeral=True
    )


@bot.tree.command(name="removebirthday", description="Remove your saved birthday.")
async def removebirthday(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    birthdays = cfg.setdefault("birthdays", {})
    if str(interaction.user.id) not in birthdays:
        await interaction.response.send_message("ℹ️ You don't have a birthday saved.", ephemeral=True)
        return
    birthdays.pop(str(interaction.user.id))
    save_config(config)
    await interaction.response.send_message("✅ Your birthday has been removed.", ephemeral=True)


@bot.tree.command(name="mybirthday", description="Show your currently saved birthday.")
async def mybirthday(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    bday = cfg.get("birthdays", {}).get(str(interaction.user.id))
    if not bday:
        await interaction.response.send_message("ℹ️ You haven't set a birthday yet — use `/setbirthday`.", ephemeral=True)
        return
    await interaction.response.send_message(f"🎂 Your saved birthday is **{bday}**.", ephemeral=True)


@bot.tree.command(name="setbirthdayrole", description="Set the role members automatically get on their birthday.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="The role to auto-assign on someone's birthday (omit to turn this off)")
async def setbirthdayrole(interaction: discord.Interaction, role: discord.Role = None):
    cfg = get_guild_cfg(interaction.guild_id)

    if role is None:
        cfg.pop("birthday_role_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Birthday role disabled.", ephemeral=True)
        return

    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {role.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    cfg["birthday_role_id"] = role.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Members will now automatically get {role.mention} on their birthday.", ephemeral=True
    )


@bot.tree.command(name="setbirthdaychannel", description="Post a shoutout here whenever it's someone's birthday.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel to post birthday shoutouts in (omit to turn this off)")
async def setbirthdaychannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    cfg = get_guild_cfg(interaction.guild_id)

    if channel is None:
        cfg.pop("birthday_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Birthday shoutouts disabled.", ephemeral=True)
        return

    cfg["birthday_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(f"✅ Birthday shoutouts will now be posted in {channel.mention}.", ephemeral=True)


# ---------- role showcase ----------

showcase_group = app_commands.Group(name="showcase", description="Manage the self-assignable role showcase.")


@showcase_group.command(name="add", description="Add a role to the showcase with a description.")
@app_commands.describe(role="The role to showcase", description="What this role is for / how to earn it")
async def showcase_add(interaction: discord.Interaction, role: discord.Role, description: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    entries = cfg.setdefault("showcase_roles", [])
    existing = next((e for e in entries if e["role_id"] == role.id), None)

    if existing:
        existing["description"] = description
        msg = f"✅ Updated {role.mention}'s description in the showcase."
    else:
        if len(entries) >= 25:
            await interaction.response.send_message(
                "❌ The showcase is full — Discord allows a maximum of 25 roles per message.", ephemeral=True
            )
            return
        entries.append({"role_id": role.id, "description": description})
        msg = f"✅ Added {role.mention} to the showcase."

    save_config(config)
    await interaction.response.send_message(msg, ephemeral=True)
    await refresh_showcase_message(interaction.guild)


@showcase_group.command(name="remove", description="Remove a role from the showcase.")
@app_commands.describe(role="The role to remove")
async def showcase_remove(interaction: discord.Interaction, role: discord.Role):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    entries = cfg.setdefault("showcase_roles", [])
    new_entries = [e for e in entries if e["role_id"] != role.id]
    if len(new_entries) == len(entries):
        await interaction.response.send_message(f"ℹ️ {role.mention} isn't in the showcase.", ephemeral=True)
        return

    cfg["showcase_roles"] = new_entries
    save_config(config)
    await interaction.response.send_message(f"✅ Removed {role.mention} from the showcase.", ephemeral=True)
    await refresh_showcase_message(interaction.guild)


@showcase_group.command(name="setchannel", description="Post the live role showcase in this channel.")
@app_commands.describe(channel="The channel to post the showcase in")
async def showcase_setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    cfg["showcase_channel_id"] = channel.id
    cfg.pop("showcase_message_id", None)  # force a fresh message in the new channel
    save_config(config)
    await interaction.response.send_message(
        f"✅ The role showcase will now be posted and kept updated in {channel.mention}.", ephemeral=True
    )
    await refresh_showcase_message(interaction.guild)


@showcase_group.command(name="list", description="Show the current role showcase.")
async def showcase_list(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    embed = build_showcase_embed(interaction.guild, cfg)
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.tree.add_command(showcase_group)


# ---------- error handling ----------

@setlogchannel.error
@setmanagerrole.error
@setrosterchannel.error
@setranks.error
@setcooldown.error
@setinactivitydays.error
@setstatschannel.error
@crosspost_add.error
@crosspost_remove.error
@crosspost_list.error
@backup.error
@setbirthdayrole.error
@setbirthdaychannel.error
async def admin_error_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Only server administrators can use this command.", ephemeral=True
        )
    else:
        await interaction.response.send_message(f"⚠️ Error: {error}", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "No token found. Copy .env.example to .env and add your bot token as DISCORD_TOKEN."
        )
    start_web_app(bot, config, save_config, get_guild_cfg)
    bot.run(TOKEN)
