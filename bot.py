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
  /rosteraddall rank:<role>                - put EVERY server member on the roster at once, at this rank
  /roster                                 - show the current roster, grouped by rank
  /stats                                  - show roster counts per rank
  /rank [user]                            - show a member's current rank (defaults to you)
  /history [user]                         - show a member's rank/roster history (defaults to you)
  /setrosterchannel channel:<channel>     - (admin only) post a live roster embed that auto-updates in this channel
  /setranks rank1:<role> [rank2]...[rank16] - (admin only) set the ordered rank roles (highest first)
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
  /untimeout user:<member> [reason]       - remove a member's timeout early
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
  /setticketchannel channel:<channel>     - (admin only) post an Open Ticket button in this channel
  /addticketcategory name:<text> category:<category> - add a ticket type with its own Discord category
  /removeticketcategory index:<int>       - remove a ticket type
  /setticketquestions index:<int> [q1..q5] - set intake questions asked before that ticket type opens
  /listticketcategories                   - show all configured ticket types
  /ticket                                 - open a private support ticket with staff
  /rust setserver host:<ip> query_port:<int> [rcon_port] [rcon_password] - (admin only) connect to your Rust server
  /rust setchatchannel [channel]          - (admin only) bridge Discord chat with in-game chat (needs RCON)
  /rust setstatuschannel [channel]        - (admin only) post a live Rust server status embed
  /rust status                            - show current Rust server status
  /rust command cmd:<text>                - run an RCON command on the Rust server
  /rust setpopalert [role] [channel] [threshold] - (admin only) ping a role at a population threshold
  /rust setwipe [day] [hour] [channel]    - (admin only) schedule a weekly wipe countdown (24h/12h/1h announcements)
  /rust wipe                              - show time until the next scheduled Rust wipe
  /minecraft setserver host:<ip> [port] [rcon_port] [rcon_password] - (admin only) connect to your Minecraft server
  /minecraft setstatuschannel [channel]   - (admin only) post a live Minecraft server status embed
  /minecraft status                       - show current Minecraft server status
  /minecraft command cmd:<text>           - run an RCON command on the Minecraft server
  /evaluate [user]                        - show message activity for the current week (leaderboard or one person); auto-resets weekly
  /setbirthday month:<1-12> day:<1-31>    - set your own birthday
  /removebirthday                         - remove your saved birthday
  /mybirthday                             - show your currently saved birthday
  /setbirthdayrole [role]                 - (admin only) role auto-given on someone's birthday (omit to disable)
  /setbirthdaychannel [channel]           - (admin only) channel for birthday shoutouts (omit to disable)
  /weblogin                               - get a one-time code to log into the web dashboard without Discord OAuth
  /setweblogincommandrole [role]          - (admin only) restrict who can run /weblogin (omit to allow everyone)
  /setbotstatus enabled:<bool>            - (admin only) rotate the bot's Discord status through live member/Rust/Minecraft stats
  /suggest message:<text>                 - submit a suggestion for staff/community to vote on
  /setsuggestionschannel [channel]        - (admin only) set where suggestions get posted (omit to disable)
  /giveaway_start prize:<text> duration_minutes:<int> [winners] [channel] - start a giveaway
  /giveaway_end giveaway_id:<int>         - end a giveaway early and pick winners now
  /setpromotioncooldownrole [role]        - (admin only) role that blocks promotion/demotion while a member has it
  /putoncooldown user:<member>            - give a member the promotion cooldown role
  /removecooldown user:<member>           - remove the promotion cooldown role from a member
  /trivia                                 - answer a trivia question, first correct answer wins a point
  /trivialeaderboard                      - show the top trivia scorers
  /addcustomcommand trigger:<text> response:<text> - add a trigger word the bot auto-replies to
  /removecustomcommand trigger:<text>     - remove a custom trigger word
  /listcustomcommands                     - show all configured custom commands
  /refreshroster                          - force the live roster/stats embeds to update right now
  /automod_toggle enabled:<bool>          - (admin only) turn auto-moderation on or off
  /automod_settings [block_invites] [block_spam] [action] [exempt_role] - (admin only) configure auto-mod
  /automod_addword word:<text>            - add a word to the blocked list
  /automod_removeword word:<text>         - remove a word from the blocked list
  /automod_listwords                      - show the blocked word list
  /voiceactivity [user]                   - show voice channel activity (leaderboard or one person)
  /setticketautoclose enabled:<bool> [reminder_hours] [close_hours] - (admin only) auto-remind/close quiet tickets
  /namehistory [user]                     - show a member's nickname/username change history
  /report user:<member> reason:<text>     - privately report a member to staff
  /setreportschannel [channel]            - (admin only) set the private channel for member reports
  /discordauditlog [limit]                - show Discord's own audit log (bans, kicks, channel/role changes)
  /setviewerrole [role]                   - (admin only) role that gets view-only web dashboard access
  /setbanrole [role]                      - (admin only) role threshold for using /ban (Discord + web)
  /linksteam steamid:<text>               - link your SteamID for Rust whitelist auto-sync
  /linkminecraft username:<text>          - link your Minecraft username for whitelist auto-sync
  /setwhitelistsync [rank] [rust_command_template] [minecraft_enabled] - (admin only) auto-whitelist on Rust/Minecraft at a rank threshold
  /addrankbonusrole rank:<role> bonus_role:<role> - auto-grant an extra role when someone reaches a rank
  /removerankbonusrole rank:<role> bonus_role:<role> - stop auto-granting that extra role
  /listrankbonusroles                     - show which extra roles get auto-granted at each rank
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
import re
from collections import deque
import secrets
import socket
import string
import tempfile
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from gtts import gTTS
import websockets

from web import start_web_app

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

CONFIG_PATH = Path(__file__).parent / "guild_config.json"
DATABASE_URL = os.getenv("DATABASE_URL")  # optional — set this to persist settings across redeploys

# ---------- per-guild config, backed by Postgres (Neon) if configured, else a local JSON file ----------
#
# Render's free tier wipes the local filesystem on every deploy, so a local
# JSON file alone doesn't survive updates. If DATABASE_URL is set (e.g. a
# free Neon Postgres database), settings persist there instead and survive
# redeploys. Without it, the bot still works exactly as before — settings
# will just reset on each deploy, same as always.

def _pg_connect():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def load_config() -> dict:
    if DATABASE_URL:
        try:
            conn = _pg_connect()
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS bot_config (guild_id TEXT PRIMARY KEY, data JSONB NOT NULL)")
            conn.commit()
            cur.execute("SELECT guild_id, data FROM bot_config")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return {guild_id: data for guild_id, data in rows}
        except Exception as e:
            print(f"⚠️ Couldn't load config from database, starting empty: {e}")
            return {}

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def _write_config(cfg: dict) -> None:
    """Runs off the main thread (see save_config) so a slow DB write never blocks the bot."""
    if DATABASE_URL:
        try:
            conn = _pg_connect()
            cur = conn.cursor()
            for guild_id, data in cfg.items():
                cur.execute(
                    "INSERT INTO bot_config (guild_id, data) VALUES (%s, %s) "
                    "ON CONFLICT (guild_id) DO UPDATE SET data = EXCLUDED.data",
                    (guild_id, json.dumps(data)),
                )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Couldn't save config to database: {e}")
        return

    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def save_config(cfg: dict) -> None:
    threading.Thread(target=_write_config, args=(cfg,), daemon=True).start()


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
    if not weekly_voice_activity_loop.is_running():
        weekly_voice_activity_loop.start()
    if not ticket_autoclose_loop.is_running():
        ticket_autoclose_loop.start()
    if not member_count_snapshot_loop.is_running():
        member_count_snapshot_loop.start()
    if not birthday_check_loop.is_running():
        birthday_check_loop.start()
    if not rust_status_loop.is_running():
        rust_status_loop.start()
    if not minecraft_status_loop.is_running():
        minecraft_status_loop.start()
    if not backup_scheduler_loop.is_running():
        backup_scheduler_loop.start()
    if not bot_status_loop.is_running():
        bot_status_loop.start()
    if not giveaway_check_loop.is_running():
        giveaway_check_loop.start()

    # Reconnect any Rust RCON connections that were configured before a restart.
    for guild_id_str, cfg in config.items():
        if cfg.get("rust_rcon_port") and cfg.get("rust_rcon_password") and cfg.get("rust_host"):
            try:
                start_rust_connection(int(guild_id_str), cfg["rust_host"], cfg["rust_rcon_port"], cfg["rust_rcon_password"])
            except Exception as e:
                print(f"⚠️ Couldn't restart Rust RCON for guild {guild_id_str}: {e}")


# ---------- auto-moderation ----------

INVITE_LINK_PATTERN = re.compile(r"(discord\.gg/|discord(?:app)?\.com/invite/)[a-zA-Z0-9-]+", re.IGNORECASE)

# Tracks each member's last few messages in memory (not persisted) to catch
# rapid identical-message spam. Keyed by (guild_id, user_id) -> deque of (content, timestamp).
_recent_messages: dict = {}

# Tracks when each member joined their current voice channel, in memory —
# used to compute voice activity minutes on leave/switch. Keyed by (guild_id, user_id).
_voice_join_times: dict = {}


def _is_automod_exempt(member: discord.Member, cfg: dict) -> bool:
    if member.guild_permissions.administrator:
        return True
    exempt_role_id = cfg.get("automod_exempt_role_id")
    if exempt_role_id and any(r.id == exempt_role_id for r in member.roles):
        return True
    manager_role_id = cfg.get("manager_role_id")
    if manager_role_id and any(r.id == manager_role_id for r in member.roles):
        return True
    return False


async def _apply_automod_action(message: discord.Message, cfg: dict, reason: str):
    """Deletes the message and, depending on config, also warns or times out the author."""
    try:
        await message.delete()
    except discord.Forbidden:
        pass

    action = cfg.get("automod_action", "delete_only")
    if action in ("delete_and_warn", "delete_and_timeout"):
        warnings = cfg.setdefault("warnings", {})
        warnings.setdefault(str(message.author.id), []).append({
            "reason": f"Auto-mod: {reason}", "moderator_id": bot.user.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        save_config(config)
        try:
            await message.author.send(f"⚠️ You were warned in **{message.guild.name}** by auto-mod: {reason}")
        except discord.Forbidden:
            pass

    if action == "delete_and_timeout":
        try:
            await message.author.timeout(timedelta(minutes=10), reason=f"Auto-mod: {reason}")
        except discord.Forbidden:
            pass

    log_channel_id = cfg.get("log_channel_id")
    if log_channel_id:
        log_channel = message.guild.get_channel(log_channel_id)
        if log_channel:
            try:
                await log_channel.send(
                    f"🛡️ Auto-mod removed a message from {message.author.mention} in {message.channel.mention} — {reason}"
                )
            except discord.Forbidden:
                pass


async def _run_automod_check(message: discord.Message, cfg: dict) -> bool:
    """Returns True if the message was removed by auto-mod."""
    if not isinstance(message.author, discord.Member) or _is_automod_exempt(message.author, cfg):
        return False

    content = message.content or ""

    if cfg.get("automod_block_invites") and INVITE_LINK_PATTERN.search(content):
        await _apply_automod_action(message, cfg, "posted a Discord invite link")
        return True

    banned_words = cfg.get("automod_banned_words", [])
    if banned_words:
        content_lower = content.lower()
        for word in banned_words:
            if re.search(rf"\b{re.escape(word.lower())}\b", content_lower):
                await _apply_automod_action(message, cfg, f"used a blocked word")
                return True

    if cfg.get("automod_block_spam", True) and content:
        key = (message.guild.id, message.author.id)
        history = _recent_messages.setdefault(key, deque(maxlen=5))
        now = datetime.now(timezone.utc)
        history.append((content, now))
        recent_matches = [t for c, t in history if c == content and (now - t).total_seconds() < 10]
        if len(recent_matches) >= 3:
            await _apply_automod_action(message, cfg, "repeated the same message too quickly (spam)")
            history.clear()
            return True

    return False


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    cfg = get_guild_cfg(message.guild.id)

    # ---- auto-moderation ----
    if cfg.get("automod_enabled"):
        deleted = await _run_automod_check(message, cfg)
        if deleted:
            return  # message is gone — no point cross-posting/tracking it

    # ---- Rust chat bridge (Discord -> in-game) ----
    rust_chat_channel_id = cfg.get("rust_chat_channel_id")
    if rust_chat_channel_id and message.channel.id == rust_chat_channel_id and message.content:
        conn = rust_connections.get(message.guild.id)
        if conn and conn.connected:
            safe_text = message.content.replace('"', "'")
            try:
                asyncio.create_task(conn.send_command(f'say "[Discord] {message.author.display_name}: {safe_text}"'))
            except Exception:
                pass

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

    # ---- ticket activity tracking (for auto-reminder/auto-close) ----
    tickets = cfg.get("tickets", {})
    if tickets:
        for ticket in tickets.values():
            if ticket.get("status") == "open" and ticket.get("channel_id") == message.channel.id:
                ticket["last_activity"] = datetime.now(timezone.utc).isoformat()
                ticket["reminded"] = False  # any new activity clears a pending reminder
                save_config(config)
                break

    # ---- custom commands (staff-defined trigger words) ----
    custom_commands = cfg.get("custom_commands", {})
    if custom_commands:
        content_lower = message.content.lower().strip()
        response = custom_commands.get(content_lower)
        if response:
            try:
                await message.channel.send(response)
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

    # ---- voice activity tracking (join/leave/switch — NOT pure mute/deafen toggles) ----
    if before.channel != after.channel:
        key = (member.guild.id, member.id)
        now = datetime.now(timezone.utc)
        if before.channel is not None and key in _voice_join_times:
            elapsed_minutes = (now - _voice_join_times[key]).total_seconds() / 60
            if elapsed_minutes > 0:
                cfg = get_guild_cfg(member.guild.id)
                voice_minutes = cfg.setdefault("voice_minutes", {})
                voice_minutes[str(member.id)] = voice_minutes.get(str(member.id), 0) + elapsed_minutes
                if "voice_minutes_since" not in cfg:
                    cfg["voice_minutes_since"] = now.isoformat()
                save_config(config)
            del _voice_join_times[key]
        if after.channel is not None:
            _voice_join_times[key] = now

    # Only fire the VC greeting when they've actually landed in a NEW voice channel (not on mute/deafen toggles, etc.)
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


def _record_name_change(guild_id: int, user_id: int, old_name: str, new_name: str, kind: str):
    cfg = get_guild_cfg(guild_id)
    history = cfg.setdefault("name_history", {})
    entries = history.setdefault(str(user_id), [])
    entries.append({
        "old": old_name, "new": new_name, "kind": kind,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    cfg["name_history"][str(user_id)] = entries[-25:]  # keep it capped per member
    save_config(config)


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.bot:
        return
    if before.nick != after.nick:
        _record_name_change(
            after.guild.id, after.id,
            before.nick or before.name, after.nick or after.name, "nickname",
        )


@bot.event
async def on_user_update(before: discord.User, after: discord.User):
    if before.bot or before.name == after.name:
        return
    # Global username changes aren't guild-scoped, so log it to every mutual server.
    for guild in bot.guilds:
        if guild.get_member(after.id):
            _record_name_change(guild.id, after.id, before.name, after.name, "username")


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
    embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=str(value), inline=len(str(value)) <= 30)

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


async def web_give_role(guild_id: int, user_id: int, role_id: int, reason: str, actor_id: int) -> str:
    """Give a role to a member, triggered from the web dashboard. Mirrors /addrole
    exactly — same hierarchy check, DM, and log entry — so behavior is identical
    regardless of whether staff used Discord or the browser."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    role = guild.get_role(role_id)
    actor = guild.get_member(actor_id)
    if member is None or role is None or actor is None:
        return "❌ Couldn't find that member, role, or your account in this server."

    if role >= guild.me.top_role:
        return f"❌ I can't assign @{role.name} — it's above my own role in Server Settings > Roles."
    if role in member.roles:
        return f"ℹ️ {member.display_name} already has @{role.name}."

    try:
        await member.add_roles(role, reason=f"Added by {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to assign that role."

    dm_sent = await dm_notify(
        guild, member, title="🟢 You were given a role", color=discord.Color.green(),
        fields={"Role": role.name, "Reason": reason},
    )
    await log_movement(guild, member=member, target=role.mention, reason=reason, moderator=actor)
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    return f"✅ Gave @{role.name} to {member.display_name}.{note}"


async def web_remove_role(guild_id: int, user_id: int, role_id: int, reason: str, actor_id: int) -> str:
    """Remove a role from a member, triggered from the web dashboard. Mirrors /removerole exactly."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    role = guild.get_role(role_id)
    actor = guild.get_member(actor_id)
    if member is None or role is None or actor is None:
        return "❌ Couldn't find that member, role, or your account in this server."

    if role not in member.roles:
        return f"ℹ️ {member.display_name} doesn't have @{role.name}."

    try:
        await member.remove_roles(role, reason=f"Removed by {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to remove that role."

    dm_sent = await dm_notify(
        guild, member, title="🔴 A role was removed from you", color=discord.Color.red(),
        fields={"Role": role.name, "Reason": reason},
    )
    await log_movement(guild, member=member, target=f"~~@{role.name}~~ removed", reason=reason, moderator=actor)
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    return f"✅ Removed @{role.name} from {member.display_name}.{note}"


async def web_roster_add(guild_id: int, user_id: int, rank_role_id: int, reason: str, actor_id: int) -> str:
    """Add/move a member on the roster + give them the rank role. Mirrors /rosteradd."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    rank = guild.get_role(rank_role_id)
    actor = guild.get_member(actor_id)
    if member is None or rank is None or actor is None:
        return "❌ Couldn't find that member, rank, or your account in this server."

    cfg = get_guild_cfg(guild_id)
    valid_rank_ids = cfg.get("ranks", [])
    if rank.id not in valid_rank_ids:
        return f"❌ @{rank.name} isn't a configured rank. Run /setranks first."
    if rank >= guild.me.top_role:
        return f"❌ I can't assign @{rank.name} — it's above my own role in Server Settings > Roles."

    roster = cfg.setdefault("roster", [])
    existing = next((entry for entry in roster if entry["user_id"] == member.id), None)

    try:
        if rank not in member.roles:
            await member.add_roles(rank, reason=f"Added by {actor} via web dashboard: {reason}")
        if existing:
            old_rank_role = guild.get_role(existing.get("rank_role_id"))
            if old_rank_role and old_rank_role.id != rank.id and old_rank_role in member.roles:
                await member.remove_roles(old_rank_role, reason=f"Rank changed by {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to manage that role."

    if existing:
        old_rank_role = guild.get_role(existing.get("rank_role_id"))
        old_label = old_rank_role.name if old_rank_role else "an unknown rank"
        existing["rank_role_id"] = rank.id
        save_config(config)
        dm_sent = await dm_notify(
            guild, member, title="📋 Your roster rank changed", color=discord.Color.teal(),
            fields={"Previous Rank": old_label, "New Rank": rank.name, "Reason": reason},
        )
        await log_movement(guild, member=member, target=rank.mention, reason=reason, moderator=actor)
        record_history(guild_id, member.id, "Rank Changed", f"{old_label} → {rank.mention}", actor_id, reason)
        await refresh_roster_message(guild)
        await refresh_server_stats_message(guild)
        await _maybe_sync_whitelist(guild_id, member.id)
        await _sync_rank_bonus_roles(guild_id, member.id, rank.id)
        note = "" if dm_sent else " (couldn't DM them)"
        return f"✅ Moved {member.display_name} from {old_label} to @{rank.name}.{note}"

    roster.append({"user_id": member.id, "rank_role_id": rank.id})
    save_config(config)
    dm_sent = await dm_notify(
        guild, member, title="📋 You were added to the roster", color=discord.Color.teal(),
        fields={"Rank": rank.name, "Reason": reason},
    )
    await log_movement(guild, member=member, target=f"{rank.mention} (added to roster)", reason=reason, moderator=actor)
    record_history(guild_id, member.id, "Added to Roster", rank.mention, actor_id, reason)
    await refresh_roster_message(guild)
    await refresh_server_stats_message(guild)
    await _maybe_sync_whitelist(guild_id, member.id)
    await _sync_rank_bonus_roles(guild_id, member.id, rank.id)
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ Added {member.display_name} to the roster as @{rank.name}.{note}"


async def web_roster_add_all(guild_id: int, rank_role_id: int, actor_id: int) -> str:
    """Mirrors /rosteraddall — puts every member on the roster at once, at the given rank.
    Called fire-and-forget from the web dashboard (it can take a while for large servers),
    so every outcome — success or failure — gets posted to the log channel, since there's
    no page waiting around to show a return value."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."

    async def _post_log(text: str):
        cfg = get_guild_cfg(guild_id)
        log_channel_id = cfg.get("log_channel_id")
        if not log_channel_id:
            return
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return
        try:
            await log_channel.send(text)
        except discord.Forbidden:
            pass

    rank = guild.get_role(rank_role_id)
    if rank is None:
        result = "❌ Couldn't find that rank."
        await _post_log(f"📋 Bulk roster add-all failed: {result}")
        return result

    cfg = get_guild_cfg(guild_id)
    valid_rank_ids = cfg.get("ranks", [])
    if rank.id not in valid_rank_ids:
        result = f"❌ @{rank.name} isn't a configured rank. Run /setranks first."
        await _post_log(f"📋 Bulk roster add-all failed: {result}")
        return result
    if rank >= guild.me.top_role:
        result = f"❌ I can't assign @{rank.name} — it's above my own role in Server Settings > Roles."
        await _post_log(f"📋 Bulk roster add-all failed: {result}")
        return result

    try:
        all_members = [m async for m in guild.fetch_members(limit=None) if not m.bot]
    except discord.HTTPException as e:
        result = (
            f"❌ Couldn't fetch server members ({e}). Make sure 'Server Members Intent' is enabled for this bot "
            "in the Discord Developer Portal (Bot page)."
        )
        await _post_log(f"📋 Bulk roster add-all failed: {result}")
        return result
    if not all_members:
        result = "ℹ️ No members found."
        await _post_log(f"📋 Bulk roster add-all: {result}")
        return result

    await _post_log(f"📋 Bulk roster add-all → {rank.mention}: starting on {len(all_members)} member(s). This can take a while due to Discord's rate limits — progress updates every 50.")

    roster = cfg.setdefault("roster", [])
    added, moved, role_failed = 0, 0, 0

    for i, member in enumerate(all_members, start=1):
        try:
            if rank not in member.roles:
                await member.add_roles(rank, reason=f"Bulk roster add by {actor_id} via web dashboard")

            existing = next((entry for entry in roster if entry["user_id"] == member.id), None)
            if existing is None:
                roster.append({"user_id": member.id, "rank_role_id": rank.id})
                record_history(guild_id, member.id, "Added to Roster", rank.mention, actor_id, "Bulk add-all via web")
                added += 1
            elif existing.get("rank_role_id") != rank.id:
                existing["rank_role_id"] = rank.id
                record_history(guild_id, member.id, "Rank Changed", rank.mention, actor_id, "Bulk add-all via web")
                moved += 1
            await _maybe_sync_whitelist(guild_id, member.id)
            await _sync_rank_bonus_roles(guild_id, member.id, rank.id)
        except discord.HTTPException:
            role_failed += 1
            continue

        if i % 50 == 0:
            save_config(config)  # checkpoint progress so a restart mid-run doesn't lose it
            await _post_log(f"📋 Bulk roster add-all progress: {i}/{len(all_members)} processed ({added} added, {moved} moved so far).")

    save_config(config)
    await refresh_roster_message(guild)
    await refresh_server_stats_message(guild)

    actor = guild.get_member(actor_id)
    actor_mention = actor.mention if actor else f"<@{actor_id}>"
    now_ts = int(datetime.now(timezone.utc).timestamp())
    note = f", {role_failed} role grant(s) failed" if role_failed else ""
    await _post_log(
        f"📋 Bulk roster add-all → {rank.mention} | {added} added, {moved} moved{note} | "
        f"{actor_mention} (via web dashboard) | <t:{now_ts}:f>"
    )
    return f"✅ Roster updated: {added} added, {moved} moved to @{rank.name}{note}."


async def web_roster_remove(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    """Remove a member from the roster. Mirrors /rosterremove (skips the extra
    confirm step here since submitting the web form already is the confirmation)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."

    cfg = get_guild_cfg(guild_id)
    roster = cfg.setdefault("roster", [])
    new_roster = [entry for entry in roster if entry["user_id"] != member.id]
    if len(new_roster) == len(roster):
        return f"ℹ️ {member.display_name} isn't on the roster."

    cfg["roster"] = new_roster
    save_config(config)
    dm_sent = await dm_notify(
        guild, member, title="📋 You were removed from the roster", color=discord.Color.orange(),
        fields={"Reason": reason},
    )
    await log_movement(guild, member=member, target="removed from roster", reason=reason, moderator=actor)
    record_history(guild_id, member.id, "Removed from Roster", "", actor_id, reason)
    await refresh_roster_message(guild)
    await refresh_server_stats_message(guild)
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ Removed {member.display_name} from the roster.{note}"


async def _web_change_rank(guild_id: int, user_id: int, reason: str, actor_id: int, step: int, verb: str) -> str:
    """Shared logic for web_promote (step=-1) and web_demote (step=+1). Mirrors /promote and /demote
    (skips the extra confirm step for demote — submitting the web form is the confirmation)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."

    cfg = get_guild_cfg(guild_id)
    rank_ids = cfg.get("ranks", [])
    if not rank_ids:
        return "❌ No ranks have been set up yet. Run /setranks first."

    roster = cfg.setdefault("roster", [])
    existing = next((entry for entry in roster if entry["user_id"] == member.id), None)
    if not existing or existing.get("rank_role_id") not in rank_ids:
        return f"❌ {member.display_name} isn't on the roster at a known rank yet."

    cooldown_role_id = cfg.get("promotion_cooldown_role_id")
    if cooldown_role_id:
        cooldown_role = guild.get_role(cooldown_role_id)
        if cooldown_role and cooldown_role in member.roles:
            return f"⏳ {member.display_name} has the @{cooldown_role.name} role and can't be {verb.lower()}d right now."

    user_cooldowns = cfg.get("user_cooldowns", {})
    cooldown_hours = user_cooldowns.get(str(member.id), cfg.get("cooldown_hours", 0))
    last_change_str = existing.get("last_rank_change")
    if cooldown_hours and last_change_str:
        elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last_change_str)
        remaining = timedelta(hours=cooldown_hours) - elapsed
        if remaining.total_seconds() > 0:
            hours_left = int(remaining.total_seconds() // 3600)
            minutes_left = int((remaining.total_seconds() % 3600) // 60)
            return f"⏳ {member.display_name} was rank-changed too recently. Try again in about {hours_left}h {minutes_left}m."

    current_index = rank_ids.index(existing["rank_role_id"])
    new_index = current_index + step
    if new_index < 0:
        return f"ℹ️ {member.display_name} is already at the highest rank."
    if new_index >= len(rank_ids):
        return f"ℹ️ {member.display_name} is already at the lowest rank."

    old_role = guild.get_role(rank_ids[current_index])
    new_role = guild.get_role(rank_ids[new_index])
    if new_role is None:
        return "❌ That rank's role no longer exists. Run /setranks again."
    if new_role >= guild.me.top_role:
        return f"❌ I can't assign @{new_role.name} — it's above my own role in Server Settings > Roles."

    try:
        if new_role not in member.roles:
            await member.add_roles(new_role, reason=f"{verb}d by {actor} via web dashboard: {reason}")
        if old_role and old_role in member.roles:
            await member.remove_roles(old_role, reason=f"{verb}d by {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to manage those roles."

    existing["rank_role_id"] = new_role.id
    existing["last_rank_change"] = datetime.now(timezone.utc).isoformat()
    save_config(config)

    old_label = old_role.name if old_role else "an unknown rank"
    dm_title = "⬆️ You were promoted!" if step < 0 else "⬇️ You were demoted"
    dm_color = discord.Color.gold() if step < 0 else discord.Color.dark_orange()
    dm_sent = await dm_notify(
        guild, member, title=dm_title, color=dm_color,
        fields={"Previous Rank": old_label, "New Rank": new_role.name, "Reason": reason},
    )
    await log_movement(guild, member=member, target=new_role.mention, reason=reason, moderator=actor)
    record_history(guild_id, member.id, f"{verb}d", f"{old_label} → {new_role.mention}", actor_id, reason)
    await refresh_roster_message(guild)
    await refresh_server_stats_message(guild)
    await _maybe_sync_whitelist(guild_id, member.id)
    await _sync_rank_bonus_roles(guild_id, member.id, new_role.id)
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ {verb}d {member.display_name} from {old_label} to @{new_role.name}.{note}"


async def web_promote(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    return await _web_change_rank(guild_id, user_id, reason, actor_id, step=-1, verb="Promote")


async def web_demote(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    return await _web_change_rank(guild_id, user_id, reason, actor_id, step=1, verb="Demote")


async def web_kick(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /kick (skips the extra confirm step — submitting the web form is the confirmation)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."
    if not guild.me.guild_permissions.kick_members:
        return "❌ I don't have permission to kick members."
    if member.top_role >= guild.me.top_role:
        return "❌ I can't kick that member — their role is higher than or equal to mine."

    dm_sent = await dm_notify(guild, member, title="👢 You were kicked", color=discord.Color.dark_red(), fields={"Reason": reason})
    try:
        await member.kick(reason=f"By {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to kick that member."
    await log_movement(guild, member=member, target="kicked", reason=reason, moderator=actor)
    note = "" if dm_sent else " (couldn't DM them before kicking)"
    return f"✅ Kicked {member.display_name}.{note}"


async def web_ban(guild_id: int, user_id: int, reason: str, delete_days: int, actor_id: int) -> str:
    """Mirrors /ban (skips the extra confirm step — submitting the web form is the confirmation)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."
    if not can_use_ban(guild_id, actor):
        return "❌ You don't have permission to ban members."
    if not guild.me.guild_permissions.ban_members:
        return "❌ I don't have permission to ban members."
    if member.top_role >= guild.me.top_role:
        return "❌ I can't ban that member — their role is higher than or equal to mine."
    delete_days = max(0, min(7, delete_days))

    dm_sent = await dm_notify(guild, member, title="🔨 You were banned", color=discord.Color.dark_red(), fields={"Reason": reason})
    try:
        await member.ban(reason=f"By {actor} via web dashboard: {reason}", delete_message_days=delete_days)
    except discord.Forbidden:
        return "❌ I don't have permission to ban that member."
    await log_movement(guild, member=member, target="banned", reason=reason, moderator=actor)
    await _maybe_sync_rust_ban(guild_id, user_id, reason)
    note = "" if dm_sent else " (couldn't DM them before banning)"
    return f"✅ Banned {member.display_name}.{note}"


async def web_timeout(guild_id: int, user_id: int, minutes: int, reason: str, actor_id: int) -> str:
    """Mirrors /timeout, including the pre-timeout voice channel announcement."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."
    if not guild.me.guild_permissions.moderate_members:
        return "❌ I don't have permission to time out members."
    if minutes <= 0 or minutes > 40320:
        return "❌ Minutes must be between 1 and 40320 (28 days)."
    if member.top_role >= guild.me.top_role:
        return "❌ I can't time out that member — their role is higher than or equal to mine."

    await announce_timeout_in_vc(member, minutes, reason)
    try:
        await member.timeout(timedelta(minutes=minutes), reason=f"By {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to time out that member."

    dm_sent = await dm_notify(
        guild, member, title="🔇 You were timed out", color=discord.Color.dark_orange(),
        fields={"Duration": f"{minutes} minute(s)", "Reason": reason},
    )
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ Timed out {member.display_name} for {minutes} minute(s).{note}"


async def web_untimeout(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /untimeout."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."
    if not guild.me.guild_permissions.moderate_members:
        return "❌ I don't have permission to manage timeouts."
    if member.timed_out_until is None:
        return f"ℹ️ {member.display_name} isn't currently timed out."

    try:
        await member.timeout(None, reason=f"By {actor} via web dashboard: {reason}")
    except discord.Forbidden:
        return "❌ I don't have permission to remove that member's timeout."

    dm_sent = await dm_notify(
        guild, member, title="🔊 Your timeout was removed", color=discord.Color.green(),
        fields={"Reason": reason},
    )
    await log_movement(guild, member=member, target="timeout removed", reason=reason, moderator=actor)
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ Removed timeout from {member.display_name}.{note}"


async def web_warn(guild_id: int, user_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /warn."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."

    cfg = get_guild_cfg(guild_id)
    warnings = cfg.setdefault("warnings", {})
    user_warnings = warnings.setdefault(str(member.id), [])
    user_warnings.append({
        "reason": reason, "moderator_id": actor_id, "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_config(config)

    dm_sent = await dm_notify(
        guild, member, title="⚠️ You were warned", color=discord.Color.gold(),
        fields={"Reason": reason, "Total Warnings": str(len(user_warnings))},
    )
    await log_movement(guild, member=member, target=f"warned (#{len(user_warnings)})", reason=reason, moderator=actor)
    note = "" if dm_sent else " (couldn't DM them)"
    return f"✅ Warned {member.display_name} (warning #{len(user_warnings)}).{note}"


async def web_send_dm(guild_id: int, user_id: int, message: str, actor_id: int) -> str:
    """Send a direct message to a member on behalf of staff. Web-only convenience
    tool — there's no Discord slash command equivalent since staff can already
    DM someone directly in Discord; this just saves alt-tabbing."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    actor = guild.get_member(actor_id)
    if member is None or actor is None:
        return "❌ Couldn't find that member or your account in this server."

    embed = discord.Embed(description=message, color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
    embed.set_author(name=f"Message from {guild.name} staff", icon_url=guild.icon.url if guild.icon else None)
    embed.set_footer(text=f"Sent by {actor.display_name}")
    try:
        await member.send(embed=embed)
    except Exception:
        return f"❌ Couldn't DM {member.display_name} — their DMs may be closed."
    return f"✅ Message sent to {member.display_name}."


async def web_mass_add_role(guild_id: int, role_id: int, filter_role_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /massaddrole."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    role = guild.get_role(role_id)
    actor = guild.get_member(actor_id)
    if role is None or actor is None:
        return "❌ Couldn't find that role or your account in this server."
    if role >= guild.me.top_role:
        return f"❌ I can't assign @{role.name} — it's above my own role in Server Settings > Roles."

    filter_role = guild.get_role(filter_role_id) if filter_role_id else None
    targets = [m for m in guild.members if role not in m.roles and (filter_role is None or filter_role in m.roles)]
    if not targets:
        return "ℹ️ No eligible members matched — nothing to do."

    added, failed = 0, 0
    for member in targets:
        try:
            await member.add_roles(role, reason=f"Mass add by {actor} via web dashboard: {reason}")
            added += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    scope = f"members with @{filter_role.name}" if filter_role else "all eligible members"
    await log_bulk_action(
        guild, title="🟢 Mass Role Add", color=discord.Color.green(), moderator=actor,
        description=f"Gave @{role.name} to {scope}.",
        fields={"Added": str(added), "Failed": str(failed), "Reason": reason},
    )
    fail_note = f" ⚠️ {failed} failed." if failed else ""
    return f"✅ Gave @{role.name} to {added} member(s).{fail_note}"


async def web_mass_remove_role(guild_id: int, role_id: int, filter_role_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /massremoverole."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    role = guild.get_role(role_id)
    actor = guild.get_member(actor_id)
    if role is None or actor is None:
        return "❌ Couldn't find that role or your account in this server."
    if role >= guild.me.top_role:
        return f"❌ I can't manage @{role.name} — it's above my own role in Server Settings > Roles."

    filter_role = guild.get_role(filter_role_id) if filter_role_id else None
    targets = [m for m in guild.members if role in m.roles and (filter_role is None or filter_role in m.roles)]
    if not targets:
        return "ℹ️ No eligible members matched — nothing to do."

    removed, failed = 0, 0
    for member in targets:
        try:
            await member.remove_roles(role, reason=f"Mass remove by {actor} via web dashboard: {reason}")
            removed += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    scope = f"members who also have @{filter_role.name}" if filter_role else "all members who have it"
    await log_bulk_action(
        guild, title="🔴 Mass Role Remove", color=discord.Color.red(), moderator=actor,
        description=f"Removed @{role.name} from {scope}.",
        fields={"Removed": str(removed), "Failed": str(failed), "Reason": reason},
    )
    fail_note = f" ⚠️ {failed} failed." if failed else ""
    return f"✅ Removed @{role.name} from {removed} member(s).{fail_note}"


async def web_mass_rename(guild_id: int, prefix: str, suffix: str, filter_role_id: int, reason: str, actor_id: int) -> str:
    """Mirrors /massrename."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    actor = guild.get_member(actor_id)
    if actor is None:
        return "❌ Couldn't find your account in this server."
    if not prefix and not suffix:
        return "❌ Provide at least a prefix or a suffix."
    if not guild.me.guild_permissions.manage_nicknames:
        return "❌ I don't have permission to manage nicknames."

    filter_role = guild.get_role(filter_role_id) if filter_role_id else None
    bot_top_role = guild.me.top_role
    targets = [
        m for m in guild.members
        if not m.bot and m.id != guild.owner_id and m.top_role < bot_top_role
        and (filter_role is None or filter_role in m.roles)
    ]
    if not targets:
        return "ℹ️ No eligible members matched — nothing to rename."

    renamed, failed = 0, 0
    for member in targets:
        base_name = member.nick or member.name
        new_nick = f"{prefix or ''}{base_name}{suffix or ''}"[:32]
        try:
            await member.edit(nick=new_nick, reason=f"Mass rename by {actor} via web dashboard: {reason}")
            renamed += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1

    scope = f"members with @{filter_role.name}" if filter_role else "all eligible members"
    preview = f"{prefix or ''}<name>{suffix or ''}"
    await log_bulk_action(
        guild, title="✏️ Mass Rename", color=discord.Color.dark_teal(), moderator=actor,
        description=f"Applied pattern `{preview}` to {scope}.",
        fields={"Renamed": str(renamed), "Failed": str(failed), "Reason": reason},
    )
    fail_note = f" ⚠️ {failed} failed." if failed else ""
    return f"✅ Renamed {renamed} member(s).{fail_note}"


async def web_announce(guild_id: int, channel_id: int, title: str, message: str, ping_everyone: bool, actor_id: int) -> str:
    """Mirrors /announce."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    channel = guild.get_channel(channel_id)
    actor = guild.get_member(actor_id)
    if channel is None or actor is None:
        return "❌ Couldn't find that channel or your account in this server."
    if not channel.permissions_for(guild.me).send_messages:
        return f"❌ I don't have permission to send messages in #{channel.name}."

    warn_no_ping = ping_everyone and not channel.permissions_for(guild.me).mention_everyone

    embed = discord.Embed(color=discord.Color.gold(), timestamp=discord.utils.utcnow())
    embed.title = f"📣 {title}"
    embed.description = f"{SPACER}\n{message}\n{SPACER}"
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=f"Posted by {actor.display_name}", icon_url=actor.display_avatar.url)

    content = "@everyone" if ping_everyone else None
    allowed = discord.AllowedMentions(everyone=ping_everyone)
    try:
        await channel.send(content=content, embed=embed, allowed_mentions=allowed)
    except discord.Forbidden:
        return f"❌ I don't have permission to send messages in #{channel.name}."

    note = " ⚠️ (I lack Mention Everyone permission there, so nobody was pinged)" if warn_no_ping else ""
    return f"✅ Announcement posted in #{channel.name}.{note}"


async def web_massannounce(guild_id: int, title: str, message: str, ping_everyone: bool, actor_id: int) -> str:
    """Mirrors /massannounce — posts to every 'announcement' channel and speaks
    in every active voice channel. Runs synchronously (unlike the slash command's
    background task) since the web request already waits for a result either way."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    actor = guild.get_member(actor_id)
    if actor is None:
        return "❌ Couldn't find your account in this server."

    text_channels = [c for c in guild.text_channels if "announcement" in c.name.lower()]
    active_vcs = [vc for vc in guild.voice_channels if any(not m.bot for m in vc.members)]
    if not text_channels and not active_vcs:
        return "ℹ️ Nothing to broadcast to — no channel names contain 'announcement', and no voice channels currently have anyone in them."

    await run_broadcast(guild, actor, title, message, text_channels, active_vcs, ping_everyone)
    return f"✅ Broadcast sent to {len(text_channels)} announcement channel(s) and spoken in {len(active_vcs)} voice channel(s)."


async def web_showcase_add(guild_id: int, role_id: int, description: str, actor_id: int) -> str:
    """Mirrors /showcase add."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    role = guild.get_role(role_id)
    if role is None:
        return "❌ Couldn't find that role."

    cfg = get_guild_cfg(guild_id)
    entries = cfg.setdefault("showcase_roles", [])
    existing = next((e for e in entries if e["role_id"] == role.id), None)
    if existing:
        existing["description"] = description
        msg = f"✅ Updated @{role.name}'s description in the showcase."
    else:
        if len(entries) >= 25:
            return "❌ The showcase is full — Discord allows a maximum of 25 roles per message."
        entries.append({"role_id": role.id, "description": description})
        msg = f"✅ Added @{role.name} to the showcase."

    save_config(config)
    await refresh_showcase_message(guild)
    return msg


async def web_showcase_remove(guild_id: int, role_id: int, actor_id: int) -> str:
    """Mirrors /showcase remove."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    role = guild.get_role(role_id)
    if role is None:
        return "❌ Couldn't find that role."

    cfg = get_guild_cfg(guild_id)
    entries = cfg.setdefault("showcase_roles", [])
    new_entries = [e for e in entries if e["role_id"] != role.id]
    if len(new_entries) == len(entries):
        return f"ℹ️ @{role.name} isn't in the showcase."

    cfg["showcase_roles"] = new_entries
    save_config(config)
    await refresh_showcase_message(guild)
    return f"✅ Removed @{role.name} from the showcase."


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


# ---------- tickets ----------

class TicketCloseView(discord.ui.View):
    def __init__(self, guild_id: int, ticket_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.ticket_id = ticket_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing this ticket in a few seconds...")
        await close_ticket(self.guild_id, self.ticket_id, interaction.user.id)


class TicketQuestionsModal(discord.ui.Modal):
    """Shown before a ticket channel is created, when the chosen type has
    intake questions configured. Discord modals cap at 5 fields."""

    def __init__(self, guild_id: int, ticket_type_id: int, questions: list):
        super().__init__(title="Open a Ticket")
        self.guild_id = guild_id
        self.ticket_type_id = ticket_type_id
        self._pairs = []
        for q in questions[:5]:
            text_input = discord.ui.TextInput(
                label=q[:45], style=discord.TextStyle.paragraph, required=True, max_length=1000
            )
            self._pairs.append((q, text_input))
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        answers = [(q, ti.value) for q, ti in self._pairs]
        await interaction.response.defer(ephemeral=True)
        result = await open_ticket(self.guild_id, interaction.user.id, self.ticket_type_id, answers)
        await interaction.followup.send(result, ephemeral=True)


class TicketTypeSelect(discord.ui.Select):
    def __init__(self, guild_id: int, ticket_types: dict):
        options = [
            discord.SelectOption(label=t["name"][:100], value=str(t["id"]))
            for t in ticket_types.values()
        ][:25]
        super().__init__(placeholder="Choose a ticket type...", options=options)
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        type_id = int(self.values[0])
        cfg = get_guild_cfg(self.guild_id)
        type_data = cfg.get("ticket_types", {}).get(str(type_id), {})
        questions = type_data.get("questions", [])

        if questions:
            await interaction.response.send_modal(TicketQuestionsModal(self.guild_id, type_id, questions))
            return

        await interaction.response.defer(ephemeral=True)
        result = await open_ticket(self.guild_id, interaction.user.id, type_id)
        await interaction.followup.send(result, ephemeral=True)


class TicketOpenView(discord.ui.View):
    """Shows a type-picker dropdown if ticket categories are configured,
    otherwise falls back to a single plain "Open Ticket" button."""

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        cfg = get_guild_cfg(guild_id)
        ticket_types = cfg.get("ticket_types", {})
        if ticket_types:
            self.add_item(TicketTypeSelect(guild_id, ticket_types))
        else:
            button = discord.ui.Button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
            button.callback = self._open_simple
            self.add_item(button)

    async def _open_simple(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await open_ticket(self.guild_id, interaction.user.id)
        await interaction.followup.send(result, ephemeral=True)


async def open_ticket(guild_id: int, user_id: int, ticket_type_id: int = None, answers: list = None) -> str:
    """Create a private ticket channel for this member. Used by both the
    Discord button/dropdown and the web dashboard, so behavior is identical
    either way. If ticket_type_id is given, uses that type's category;
    otherwise falls back to the single default ticket_category_id (if set)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    if member is None:
        return "❌ Couldn't find that member in this server."

    cfg = get_guild_cfg(guild_id)
    tickets = cfg.setdefault("tickets", {})

    existing = next(
        (t for t in tickets.values() if t["user_id"] == user_id and t["status"] == "open"), None
    )
    if existing:
        channel = guild.get_channel(existing["channel_id"])
        if channel:
            return f"ℹ️ You already have an open ticket: {channel.mention}"

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    manager_role_id = cfg.get("manager_role_id")
    if manager_role_id:
        manager_role = guild.get_role(manager_role_id)
        if manager_role:
            overwrites[manager_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    type_name = None
    category_id = None
    if ticket_type_id is not None:
        type_data = cfg.get("ticket_types", {}).get(str(ticket_type_id))
        if type_data is None:
            return "❌ That ticket type no longer exists."
        type_name = type_data["name"]
        category_id = type_data.get("category_id")
    else:
        category_id = cfg.get("ticket_category_id")

    category = None
    if category_id:
        maybe_category = guild.get_channel(category_id)
        if isinstance(maybe_category, discord.CategoryChannel):
            category = maybe_category

    safe_name = "".join(c for c in member.name.lower() if c.isalnum() or c == "-")[:20] or "ticket"
    channel_name = f"ticket-{safe_name}"
    if type_name:
        type_slug = "".join(c for c in type_name.lower() if c.isalnum() or c == "-")[:15] or "ticket"
        channel_name = f"{type_slug}-{safe_name}"[:100]

    try:
        channel = await guild.create_text_channel(
            name=channel_name, category=category, overwrites=overwrites,
            reason=f"Ticket opened by {member}" + (f" ({type_name})" if type_name else ""),
        )
    except discord.Forbidden:
        return "❌ I don't have permission to create channels here."

    next_id = cfg.get("ticket_next_id", 1)
    cfg["ticket_next_id"] = next_id + 1
    tickets[str(next_id)] = {
        "id": next_id, "user_id": user_id, "channel_id": channel.id, "status": "open",
        "type_id": ticket_type_id, "type_name": type_name, "answers": answers or None,
        "created_at": datetime.now(timezone.utc).isoformat(), "closed_at": None, "closed_by": None,
    }
    save_config(config)

    embed = discord.Embed(
        title=f"🎫 Ticket #{next_id}" + (f" — {type_name}" if type_name else ""),
        description=f"Hey {member.mention}! Staff will be with you shortly. Explain what you need help with below.",
        color=discord.Color.blurple(),
    )
    await channel.send(embed=embed, view=TicketCloseView(guild_id, next_id))

    if answers:
        qa_embed = discord.Embed(title="📋 Intake Form", color=discord.Color.blurple())
        for question, answer in answers:
            qa_embed.add_field(name=question[:256], value=(answer or "—")[:1024], inline=False)
        await channel.send(embed=qa_embed)

    return f"✅ Ticket created: {channel.mention}"


async def close_ticket(guild_id: int, ticket_id: int, closed_by_id: int) -> str:
    """Close and delete a ticket channel. Used by both the Discord button and web dashboard."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."

    cfg = get_guild_cfg(guild_id)
    tickets = cfg.setdefault("tickets", {})
    ticket = tickets.get(str(ticket_id))
    if ticket is None:
        return "❌ Ticket not found."
    if ticket["status"] == "closed":
        return "ℹ️ That ticket is already closed."

    ticket["status"] = "closed"
    ticket["closed_at"] = datetime.now(timezone.utc).isoformat()
    ticket["closed_by"] = closed_by_id
    save_config(config)

    channel = guild.get_channel(ticket["channel_id"])
    if channel:
        try:
            await asyncio.sleep(3)
            await channel.delete(reason=f"Ticket #{ticket_id} closed")
        except discord.Forbidden:
            return f"⚠️ Ticket #{ticket_id} marked closed, but I couldn't delete the channel (missing permission)."

    return f"✅ Ticket #{ticket_id} closed."


@tasks.loop(hours=1)
async def ticket_autoclose_loop():
    now = datetime.now(timezone.utc)
    for guild_id_str in list(config.keys()):
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        cfg = config.get(guild_id_str, {})
        if not cfg.get("ticket_autoclose_enabled"):
            continue
        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        reminder_hours = cfg.get("ticket_reminder_hours", 24)
        close_hours = cfg.get("ticket_autoclose_hours", 48)

        for ticket_id_str, ticket in list(cfg.get("tickets", {}).items()):
            if ticket.get("status") != "open":
                continue
            last_activity_str = ticket.get("last_activity") or ticket.get("created_at")
            if not last_activity_str:
                continue
            last_activity = datetime.fromisoformat(last_activity_str)
            quiet_hours = (now - last_activity).total_seconds() / 3600

            channel = guild.get_channel(ticket.get("channel_id"))
            if channel is None:
                continue

            if quiet_hours >= close_hours:
                try:
                    await channel.send(f"🔒 This ticket has been inactive for over {close_hours} hour(s) and is being closed automatically.")
                except discord.Forbidden:
                    pass
                await close_ticket(guild_id, int(ticket_id_str), bot.user.id)
            elif quiet_hours >= reminder_hours and not ticket.get("reminded"):
                try:
                    await channel.send(
                        f"👋 This ticket has been quiet for a while. Reply within "
                        f"{close_hours - reminder_hours} hour(s) or it'll be closed automatically."
                    )
                except discord.Forbidden:
                    pass
                ticket["reminded"] = True
                save_config(config)


@bot.tree.command(name="setticketautoclose", description="Configure automatic reminders/closing for quiet tickets.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    enabled="Turn auto-reminder/auto-close on or off",
    reminder_hours="Post a reminder after this many quiet hours",
    close_hours="Auto-close after this many quiet hours (must be more than reminder_hours)",
)
async def setticketautoclose(interaction: discord.Interaction, enabled: bool, reminder_hours: int = 24, close_hours: int = 48):
    if close_hours <= reminder_hours:
        await interaction.response.send_message("❌ close_hours must be greater than reminder_hours.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["ticket_autoclose_enabled"] = enabled
    cfg["ticket_reminder_hours"] = reminder_hours
    cfg["ticket_autoclose_hours"] = close_hours
    save_config(config)
    if enabled:
        await interaction.response.send_message(
            f"✅ Quiet tickets get a reminder after {reminder_hours}h and auto-close after {close_hours}h.", ephemeral=True
        )
    else:
        await interaction.response.send_message("✅ Ticket auto-reminder/auto-close disabled.", ephemeral=True)


async def web_set_ticket_autoclose(guild_id: int, enabled: bool, reminder_hours: int, close_hours: int, actor_id: int) -> str:
    """Mirrors /setticketautoclose."""
    if close_hours <= reminder_hours:
        return "❌ Close hours must be greater than reminder hours."
    cfg = get_guild_cfg(guild_id)
    cfg["ticket_autoclose_enabled"] = enabled
    cfg["ticket_reminder_hours"] = reminder_hours
    cfg["ticket_autoclose_hours"] = close_hours
    save_config(config)
    if enabled:
        return f"✅ Quiet tickets get a reminder after {reminder_hours}h and auto-close after {close_hours}h."
    return "✅ Ticket auto-reminder/auto-close disabled."


async def web_get_ticket_messages(guild_id: int, ticket_id: int, limit: int = 100) -> list:
    """Returns recent messages from a ticket's channel for display on the web dashboard."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return []
    cfg = get_guild_cfg(guild_id)
    ticket = cfg.get("tickets", {}).get(str(ticket_id))
    if not ticket:
        return []
    channel = guild.get_channel(ticket.get("channel_id"))
    if channel is None:
        return []

    messages = []
    try:
        async for msg in channel.history(limit=limit, oldest_first=True):
            content = msg.content or ""
            for e in msg.embeds:
                parts = []
                if e.title:
                    parts.append(e.title)
                if e.description:
                    parts.append(e.description)
                for f in e.fields:
                    parts.append(f"{f.name}: {f.value}")
                if parts:
                    content += ("\n" if content else "") + "\n".join(parts)
            if not content:
                continue
            messages.append({
                "author": msg.author.display_name,
                "is_bot": msg.author.bot,
                "content": content,
                "timestamp": msg.created_at.isoformat(),
            })
    except discord.Forbidden:
        pass
    return messages


async def web_send_ticket_message(guild_id: int, ticket_id: int, actor_id: int, message: str) -> str:
    """Sends a reply into a ticket's channel on behalf of staff, from the web dashboard."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    cfg = get_guild_cfg(guild_id)
    ticket = cfg.get("tickets", {}).get(str(ticket_id))
    if not ticket:
        return "❌ Ticket not found."
    if ticket.get("status") == "closed":
        return "❌ This ticket is already closed."
    channel = guild.get_channel(ticket.get("channel_id"))
    if channel is None:
        return "❌ That ticket's channel no longer exists."
    actor = guild.get_member(actor_id)
    actor_name = actor.display_name if actor else "Staff"

    try:
        await channel.send(f"**{actor_name}** (via dashboard):\n{message}")
    except discord.Forbidden:
        return "❌ I don't have permission to send messages in that channel."
    return "✅ Message sent."


async def web_set_ticket_channel(guild_id: int, channel_id: int, actor_id: int) -> str:
    """Mirrors /setticketchannel — posts the Open Ticket panel and stores the channel."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    channel = guild.get_channel(channel_id)
    if channel is None:
        return "❌ Couldn't find that channel."

    cfg = get_guild_cfg(guild_id)
    cfg["ticket_channel_id"] = channel_id
    save_config(config)

    embed = discord.Embed(
        title="🎫 Need help?",
        description="Click the button below to open a private ticket with staff.",
        color=discord.Color.blurple(),
    )
    try:
        message = await channel.send(embed=embed, view=TicketOpenView(guild_id))
        cfg["ticket_panel_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        return f"❌ I don't have permission to post in #{channel.name}."
    return f"✅ Ticket panel posted in #{channel.name}."


@bot.tree.command(name="setticketchannel", description="Post a button here that lets members open a support ticket.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel to post the 'Open Ticket' button in")
async def setticketchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["ticket_channel_id"] = channel.id
    save_config(config)

    embed = discord.Embed(
        title="🎫 Need help?",
        description="Click the button below to open a private ticket with staff.",
        color=discord.Color.blurple(),
    )
    try:
        message = await channel.send(embed=embed, view=TicketOpenView(interaction.guild_id))
        cfg["ticket_panel_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ I don't have permission to post in {channel.mention}.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Ticket panel posted in {channel.mention}.", ephemeral=True)


@bot.tree.command(name="ticket", description="Open a private support ticket with staff.")
async def ticket_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    result = await open_ticket(interaction.guild_id, interaction.user.id)
    await interaction.followup.send(result, ephemeral=True)


async def refresh_ticket_panel(guild_id: int):
    """Re-posts the ticket panel's view so the type dropdown reflects the
    current list of categories. Called whenever categories are added/removed."""
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("ticket_channel_id")
    message_id = cfg.get("ticket_panel_message_id")
    if not channel_id or not message_id:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    try:
        message = await channel.fetch_message(message_id)
        await message.edit(view=TicketOpenView(guild_id))
    except (discord.NotFound, discord.Forbidden):
        pass


ticketcategory_group = app_commands.Group(name="ticketcategory", description="Manage ticket types/categories")
bot.tree.add_command(ticketcategory_group)


@ticketcategory_group.command(name="add", description="Add a ticket type (e.g. 'Support', 'Report Player') with its own category.")
@app_commands.describe(
    name="What this ticket type is called", category="The Discord category new ticket channels of this type go under",
    q1="Optional intake question 1", q2="Optional intake question 2", q3="Optional intake question 3",
    q4="Optional intake question 4", q5="Optional intake question 5",
)
async def addticketcategory(
    interaction: discord.Interaction, name: str, category: discord.CategoryChannel,
    q1: str = None, q2: str = None, q3: str = None, q4: str = None, q5: str = None,
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    questions = [q for q in [q1, q2, q3, q4, q5] if q]
    cfg = get_guild_cfg(interaction.guild_id)
    types = cfg.setdefault("ticket_types", {})
    next_id = cfg.get("ticket_type_next_id", 1)
    cfg["ticket_type_next_id"] = next_id + 1
    types[str(next_id)] = {"id": next_id, "name": name, "category_id": category.id, "questions": questions}
    save_config(config)
    await refresh_ticket_panel(interaction.guild_id)

    note = f" They'll be asked {len(questions)} question(s) before the channel is created." if questions else ""
    await interaction.response.send_message(
        f"✅ Added ticket type **{name}** → {category.name}. It'll show up as an option next time someone opens a ticket.{note}",
        ephemeral=True,
    )


@ticketcategory_group.command(name="remove", description="Remove a ticket type.")
@app_commands.describe(index="The number shown in /ticketcategory list")
async def removeticketcategory(interaction: discord.Interaction, index: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    types = cfg.get("ticket_types", {})
    ids = list(types.keys())
    if index < 1 or index > len(ids):
        await interaction.response.send_message("❌ Invalid index — check `/ticketcategory list`.", ephemeral=True)
        return
    removed = types.pop(ids[index - 1])
    save_config(config)
    await refresh_ticket_panel(interaction.guild_id)
    await interaction.response.send_message(f"✅ Removed ticket type **{removed['name']}**.", ephemeral=True)


@ticketcategory_group.command(name="setquestions", description="Set or update the intake questions asked for a ticket type.")
@app_commands.describe(
    index="The number shown in /ticketcategory list",
    q1="Question 1 (leave all blank to remove questions)", q2="Question 2", q3="Question 3", q4="Question 4", q5="Question 5",
)
async def setticketquestions(
    interaction: discord.Interaction, index: int,
    q1: str = None, q2: str = None, q3: str = None, q4: str = None, q5: str = None,
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    types = cfg.get("ticket_types", {})
    ids = list(types.keys())
    if index < 1 or index > len(ids):
        await interaction.response.send_message("❌ Invalid index — check `/ticketcategory list`.", ephemeral=True)
        return

    questions = [q for q in [q1, q2, q3, q4, q5] if q]
    type_data = types[ids[index - 1]]
    type_data["questions"] = questions
    save_config(config)

    note = f"{len(questions)} question(s) set" if questions else "questions cleared"
    await interaction.response.send_message(f"✅ **{type_data['name']}**: {note}.", ephemeral=True)


@ticketcategory_group.command(name="list", description="Show all configured ticket types.")
async def listticketcategories(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    types = cfg.get("ticket_types", {})
    if not types:
        await interaction.response.send_message(
            "No ticket types configured yet — tickets currently just use the plain 'Open Ticket' button.", ephemeral=True
        )
        return
    lines = []
    for i, t in enumerate(types.values(), start=1):
        category = interaction.guild.get_channel(t.get("category_id"))
        q_count = len(t.get("questions", []))
        q_note = f" ({q_count} question(s))" if q_count else ""
        lines.append(f"{i}. **{t['name']}** → {category.name if category else '(deleted category)'}{q_note}")
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def web_add_ticket_category(guild_id: int, name: str, category_id: int, questions: list, actor_id: int) -> str:
    """Mirrors /addticketcategory."""
    guild = bot.get_guild(guild_id)
    category = guild.get_channel(category_id) if guild else None
    if not isinstance(category, discord.CategoryChannel):
        return "❌ Couldn't find that category."

    cfg = get_guild_cfg(guild_id)
    types = cfg.setdefault("ticket_types", {})
    next_id = cfg.get("ticket_type_next_id", 1)
    cfg["ticket_type_next_id"] = next_id + 1
    types[str(next_id)] = {"id": next_id, "name": name, "category_id": category_id, "questions": questions[:5]}
    save_config(config)
    await refresh_ticket_panel(guild_id)
    return f"✅ Added ticket type **{name}** → {category.name}."


async def web_set_ticket_questions(guild_id: int, type_id: int, questions: list, actor_id: int) -> str:
    """Mirrors /setticketquestions."""
    cfg = get_guild_cfg(guild_id)
    types = cfg.get("ticket_types", {})
    type_data = types.get(str(type_id))
    if type_data is None:
        return "❌ That ticket type wasn't found."
    type_data["questions"] = questions[:5]
    save_config(config)
    note = f"{len(type_data['questions'])} question(s) set" if type_data["questions"] else "questions cleared"
    return f"✅ **{type_data['name']}**: {note}."


async def web_remove_ticket_category(guild_id: int, type_id: int, actor_id: int) -> str:
    """Mirrors /removeticketcategory."""
    cfg = get_guild_cfg(guild_id)
    types = cfg.get("ticket_types", {})
    removed = types.pop(str(type_id), None)
    if removed is None:
        return "❌ That ticket type wasn't found."
    save_config(config)
    await refresh_ticket_panel(guild_id)
    return f"✅ Removed ticket type **{removed['name']}**."


# ---------- Rust server integration ----------
#
# Two independent pieces:
#   1. Live status via Steam's A2S_INFO query protocol (public, no password
#      needed) — player count, map, server name.
#   2. RCON over WebSocket (Rust's "WebRcon") — needed for the chat bridge
#      and running commands. Requires the server's RCON port + password.
# Either can be set up without the other. Note: exact RCON behavior can vary
# slightly by host/version — this follows the commonly documented protocol,
# but hasn't been tested against a live server from this environment.

def _a2s_query_sync(host: str, port: int, timeout: float = 5.0) -> dict:
    """Blocking Source Engine Query (A2S_INFO), including the challenge
    handshake newer servers require. Run this off the event loop."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        def read_cstring(buf, offset):
            end = buf.index(b"\x00", offset)
            return buf[offset:end].decode("utf-8", errors="replace"), end + 1

        request = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
        sock.sendto(request, (host, port))
        data, _ = sock.recvfrom(4096)

        if data[4:5] == b"\x41":  # challenge required
            challenge = data[5:9]
            sock.sendto(request + challenge, (host, port))
            data, _ = sock.recvfrom(4096)

        if data[4:5] != b"\x49":
            raise ValueError("Unexpected response from server.")

        offset = 6  # header(4) + type(1) + protocol(1)
        name, offset = read_cstring(data, offset)
        map_name, offset = read_cstring(data, offset)
        _, offset = read_cstring(data, offset)  # folder
        _, offset = read_cstring(data, offset)  # game
        offset += 2  # app id
        players = data[offset]
        max_players = data[offset + 1]
        return {"name": name, "map": map_name, "players": players, "max_players": max_players}
    finally:
        sock.close()


async def query_rust_server(host: str, port: int) -> dict:
    """Async wrapper — the actual query is blocking network I/O."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _a2s_query_sync, host, port)


class RustRconConnection:
    """One persistent WebRcon connection per guild. Auto-reconnects on drop."""

    def __init__(self, guild_id: int, host: str, port: int, password: str):
        self.guild_id = guild_id
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.task: asyncio.Task = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future] = {}
        self.connected = False

    async def connect_and_listen(self):
        url = f"ws://{self.host}:{self.port}/{self.password}"
        while True:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    self.ws = ws
                    self.connected = True
                    async for raw in ws:
                        await self._handle_message(raw)
            except asyncio.CancelledError:
                self.connected = False
                raise
            except Exception as e:
                print(f"⚠️ Rust RCON connection issue (guild {self.guild_id}): {e}")
            self.connected = False
            self.ws = None
            await asyncio.sleep(15)

    async def _handle_message(self, raw: str):
        try:
            data = json.loads(raw)
        except Exception:
            return

        identifier = data.get("Identifier")
        if identifier in self._pending:
            fut = self._pending.pop(identifier)
            if not fut.done():
                fut.set_result(data.get("Message", ""))
            return

        if data.get("Type") == "Chat":
            await relay_rust_chat_to_discord(self.guild_id, data.get("Message", ""))
        elif data.get("Type") == "Generic":
            await relay_rust_joinleave_to_discord(self.guild_id, data.get("Message", ""))

    async def send_command(self, command: str, timeout: float = 10.0) -> str:
        if self.ws is None or not self.connected:
            raise ConnectionError("Not connected to the Rust server's RCON.")
        identifier = self._next_id
        self._next_id += 1
        fut = asyncio.get_event_loop().create_future()
        self._pending[identifier] = fut
        payload = json.dumps({"Identifier": identifier, "Message": command, "Name": "WebRcon"})
        await self.ws.send(payload)
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self._pending.pop(identifier, None)


rust_connections: dict[int, RustRconConnection] = {}  # guild_id -> connection


def start_rust_connection(guild_id: int, host: str, port: int, password: str):
    """(Re)start the RCON connection for a guild. Safe to call to reconnect
    after changing settings."""
    old = rust_connections.get(guild_id)
    if old and old.task and not old.task.done():
        old.task.cancel()
    conn = RustRconConnection(guild_id, host, port, password)
    conn.task = asyncio.create_task(conn.connect_and_listen())
    rust_connections[guild_id] = conn


async def relay_rust_chat_to_discord(guild_id: int, raw_message: str):
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("rust_chat_channel_id")
    if not channel_id:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    # Rust's chat messages arrive as a JSON string nested inside Message.
    try:
        chat_data = json.loads(raw_message)
        username = chat_data.get("Username", "Player")
        text = chat_data.get("Message", "")
    except Exception:
        username = "Server"
        text = raw_message

    if not text:
        return
    try:
        await channel.send(f"🎮 **{username}**: {text}")
    except discord.Forbidden:
        pass


async def relay_rust_joinleave_to_discord(guild_id: int, raw_message: str):
    """Rust's console broadcasts join/disconnect notices as 'Generic' RCON
    messages, wording varies a bit by server version (e.g. Facepunch vs
    Carbon/Oxide), so this matches loosely on keywords rather than a strict
    format. Anything that doesn't look like a join/leave line is ignored."""
    if not raw_message:
        return
    text = raw_message.strip()
    text_lower = text.lower()
    if "joined" not in text_lower and "disconnecting" not in text_lower and "disconnected" not in text_lower:
        return

    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("rust_joinleave_channel_id")
    if not channel_id:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    # Typical formats: "PlayerName/76561198000000000/1.2.3.4 joined [...]"
    # or "PlayerName/76561198000000000/1.2.3.4 disconnecting: reason"
    name_part = text.split("/")[0].strip() if "/" in text else text.split(" ")[0]
    is_join = "joined" in text_lower

    try:
        if is_join:
            await channel.send(f"🟢 **{name_part}** joined the server.")
        else:
            await channel.send(f"🔴 **{name_part}** left the server.")
    except discord.Forbidden:
        pass


class RustConnectView(discord.ui.View):
    """A single link-style button that opens Steam and connects straight to
    the server — no callback needed, Discord handles link buttons natively."""
    def __init__(self, host: str, connect_port: int):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🔗 Connect", style=discord.ButtonStyle.link, url=f"steam://connect/{host}:{connect_port}"))


def build_rust_status_embed(server_name: str, info: dict = None, error: str = None, seed: str = None, worldsize: str = None, fps: str = None) -> discord.Embed:
    embed = discord.Embed(title=f"🦀 {server_name}", color=discord.Color.dark_orange())
    if error:
        embed.description = f"⚠️ Couldn't reach the server: {error}"
        return embed
    embed.add_field(name="Server Name", value=info["name"], inline=False)
    embed.add_field(name="Map", value=info["map"], inline=True)
    embed.add_field(name="Players", value=f"{info['players']} / {info['max_players']}", inline=True)
    if fps:
        embed.add_field(name="FPS", value=fps, inline=True)
    if seed and worldsize:
        embed.add_field(name="Seed / Size", value=f"{seed} / {worldsize}", inline=True)
        embed.add_field(name="Map Viewer", value=f"[RustMaps](https://rustmaps.com/map/{worldsize}_{seed})", inline=True)
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Last updated")
    return embed


async def _get_rust_seed_worldsize(guild_id: int):
    """Returns (seed, worldsize) strings via RCON, or (None, None) if RCON
    isn't connected or the query fails."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return None, None
    try:
        seed_raw = await conn.send_command("server.seed")
        size_raw = await conn.send_command("server.worldsize")
        seed = "".join(c for c in seed_raw if c.isdigit())
        worldsize = "".join(c for c in size_raw if c.isdigit())
        return (seed or None), (worldsize or None)
    except Exception:
        return None, None


async def _get_rust_fps(guild_id: int):
    """Returns the server's current FPS as a string via RCON, or None if
    RCON isn't connected, the query fails, or the output can't be parsed."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return None
    try:
        raw = await conn.send_command("server.fps")
        digits = "".join(c for c in raw if c.isdigit())
        return digits or None
    except Exception:
        return None


async def refresh_rust_status_message(guild_id: int):
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("rust_status_channel_id")
    host = cfg.get("rust_host")
    query_port = cfg.get("rust_query_port")
    if not channel_id or not host or not query_port:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    try:
        info = await query_rust_server(host, query_port)
        seed, worldsize = await _get_rust_seed_worldsize(guild_id)
        fps = await _get_rust_fps(guild_id)
        embed = build_rust_status_embed(host, info=info, seed=seed, worldsize=worldsize, fps=fps)
    except Exception as e:
        embed = build_rust_status_embed(host, error=str(e))

    connect_port = cfg.get("rust_connect_port") or query_port
    view = RustConnectView(host, connect_port)

    message_id = cfg.get("rust_status_message_id")
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed, view=view)
            return
        except (discord.NotFound, discord.Forbidden):
            pass
    try:
        message = await channel.send(embed=embed, view=view)
        cfg["rust_status_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        pass


async def check_rust_downtime(guild_id: int):
    """Posts an alert when the Rust server's online/offline state changes.
    Independent of the live status embed — uses its own alert channel."""
    cfg = get_guild_cfg(guild_id)
    alert_channel_id = cfg.get("rust_alert_channel_id")
    host = cfg.get("rust_host")
    query_port = cfg.get("rust_query_port")
    if not alert_channel_id or not host or not query_port:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(alert_channel_id)
    if channel is None:
        return

    was_online = cfg.get("rust_was_online", True)  # assume online on first check, avoids a false "back online" on startup
    try:
        await query_rust_server(host, query_port)
        is_online = True
    except Exception:
        is_online = False

    if is_online != was_online:
        cfg["rust_was_online"] = is_online
        save_config(config)
        try:
            if is_online:
                await channel.send(f"🟢 **{host}** is back online.")
            else:
                await channel.send(f"🔴 **{host}** appears to be offline.")
        except discord.Forbidden:
            pass


async def check_rust_population(guild_id: int):
    """Pings a role when the server crosses a configured population
    threshold — going from below to at/above it ('full'), or dropping back
    below after having been at/above it ('opened up'). Independent of the
    live status embed — uses its own alert channel."""
    cfg = get_guild_cfg(guild_id)
    alert_channel_id = cfg.get("rust_pop_alert_channel_id")
    role_id = cfg.get("rust_pop_alert_role_id")
    host = cfg.get("rust_host")
    query_port = cfg.get("rust_query_port")
    if not alert_channel_id or not role_id or not host or not query_port:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(alert_channel_id)
    role = guild.get_role(role_id)
    if channel is None or role is None:
        return

    try:
        info = await query_rust_server(host, query_port)
    except Exception:
        return  # downtime is handled separately by check_rust_downtime

    threshold = cfg.get("rust_pop_threshold") or info["max_players"]  # defaults to "full"
    is_at_threshold = info["players"] >= threshold
    was_at_threshold = cfg.get("rust_pop_was_at_threshold", False)

    if is_at_threshold != was_at_threshold:
        cfg["rust_pop_was_at_threshold"] = is_at_threshold
        save_config(config)
        try:
            if is_at_threshold:
                await channel.send(f"📢 {role.mention} **{host}** just hit {info['players']}/{info['max_players']} players!")
            else:
                await channel.send(f"📉 {role.mention} **{host}** dropped back below {threshold} players — room to hop in ({info['players']}/{info['max_players']}).")
        except discord.Forbidden:
            pass


RUST_WIPE_ANNOUNCE_THRESHOLDS_HOURS = [24, 12, 1]


def _next_rust_wipe_datetime(wipe_day: int, wipe_hour: int) -> datetime:
    """wipe_day: 0=Monday ... 6=Sunday (matches datetime.weekday()). Returns
    the next occurrence of that weekday+hour, in UTC."""
    now = datetime.now(timezone.utc)
    days_ahead = (wipe_day - now.weekday()) % 7
    candidate = (now + timedelta(days=days_ahead)).replace(hour=wipe_hour, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


async def check_rust_wipe_countdown(guild_id: int):
    """Posts a countdown announcement at 24h, 12h, and 1h before the
    configured weekly wipe time."""
    cfg = get_guild_cfg(guild_id)
    wipe_day = cfg.get("rust_wipe_day")
    wipe_hour = cfg.get("rust_wipe_hour")
    channel_id = cfg.get("rust_wipe_channel_id")
    if wipe_day is None or wipe_hour is None or not channel_id:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    next_wipe = _next_rust_wipe_datetime(wipe_day, wipe_hour)
    hours_left = (next_wipe - datetime.now(timezone.utc)).total_seconds() / 3600

    announced = set(cfg.get("rust_wipe_announced", []))
    if hours_left > 24 * 6:  # freshly recalculated to next week — a wipe just passed, reset tracking
        if announced:
            cfg["rust_wipe_announced"] = []
            save_config(config)
        announced = set()

    for threshold in RUST_WIPE_ANNOUNCE_THRESHOLDS_HOURS:
        if hours_left <= threshold and threshold not in announced:
            try:
                await channel.send(f"🔧 **Wipe in ~{threshold} hour(s)!** Get your last runs in. <t:{int(next_wipe.timestamp())}:R>")
            except discord.Forbidden:
                pass
            announced.add(threshold)
            cfg["rust_wipe_announced"] = list(announced)
            save_config(config)


rust_group = app_commands.Group(name="rust", description="Rust server integration")


@rust_group.command(name="setwipe", description="Schedule a weekly wipe countdown — auto-announces at 24h, 12h, and 1h before.")
@app_commands.describe(day="Day of the week the server wipes", hour="Hour of the wipe, 0-23 UTC", channel="Where to post countdown announcements")
@app_commands.choices(day=[
    app_commands.Choice(name="Monday", value=0), app_commands.Choice(name="Tuesday", value=1),
    app_commands.Choice(name="Wednesday", value=2), app_commands.Choice(name="Thursday", value=3),
    app_commands.Choice(name="Friday", value=4), app_commands.Choice(name="Saturday", value=5),
    app_commands.Choice(name="Sunday", value=6),
])
async def setrustwipe(interaction: discord.Interaction, day: app_commands.Choice[int] = None, hour: int = None, channel: discord.TextChannel = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if day is None:
        cfg.pop("rust_wipe_day", None)
        cfg.pop("rust_wipe_hour", None)
        cfg.pop("rust_wipe_channel_id", None)
        cfg.pop("rust_wipe_announced", None)
        save_config(config)
        await interaction.response.send_message("✅ Wipe countdown disabled.", ephemeral=True)
        return
    if hour is None or hour < 0 or hour > 23:
        await interaction.response.send_message("❌ Give an hour between 0-23 (UTC).", ephemeral=True)
        return
    if channel is None:
        await interaction.response.send_message("❌ Pick a channel too — that's where countdowns get posted.", ephemeral=True)
        return

    cfg["rust_wipe_day"] = day.value
    cfg["rust_wipe_hour"] = hour
    cfg["rust_wipe_channel_id"] = channel.id
    cfg["rust_wipe_announced"] = []
    save_config(config)

    next_wipe = _next_rust_wipe_datetime(day.value, hour)
    await interaction.response.send_message(
        f"✅ Wipe scheduled for every **{day.name} at {hour:02d}:00 UTC**, with countdowns posted in {channel.mention}. "
        f"Next wipe: <t:{int(next_wipe.timestamp())}:F> (<t:{int(next_wipe.timestamp())}:R>).",
        ephemeral=True,
    )


@rust_group.command(name="wipe", description="Show the time until the next scheduled Rust wipe.")
async def rustwipe(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    wipe_day = cfg.get("rust_wipe_day")
    wipe_hour = cfg.get("rust_wipe_hour")
    if wipe_day is None or wipe_hour is None:
        await interaction.response.send_message("❌ No wipe schedule set up yet. Ask an admin to run /rust setwipe.", ephemeral=True)
        return
    next_wipe = _next_rust_wipe_datetime(wipe_day, wipe_hour)
    await interaction.response.send_message(
        f"🔧 Next wipe: <t:{int(next_wipe.timestamp())}:F> (<t:{int(next_wipe.timestamp())}:R>)."
    )


@tasks.loop(minutes=2)
async def rust_status_loop():
    for guild_id_str in list(config.keys()):
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        cfg = config.get(guild_id_str, {})
        if cfg.get("rust_status_channel_id"):
            await refresh_rust_status_message(guild_id)
        if cfg.get("rust_alert_channel_id"):
            await check_rust_downtime(guild_id)
        if cfg.get("rust_pop_alert_channel_id"):
            await check_rust_population(guild_id)
        if cfg.get("rust_wipe_channel_id"):
            await check_rust_wipe_countdown(guild_id)
        if cfg.get("rust_recurring_announcements"):
            await check_rust_recurring_announcements(guild_id)


@rust_group.command(name="setserver", description="Connect this server to your Rust game server.")
@app_commands.describe(
    host="Your Rust server's IP address or domain (no port)",
    query_port="Steam query port for live status (often the same as your game port)",
    rcon_port="RCON WebSocket port (optional — needed for chat bridge and commands)",
    rcon_password="RCON password (optional — needed for chat bridge and commands)",
    connect_port="Game port players actually connect on, for the one-click Connect button (omit to use query_port)",
)
async def setrustserver(
    interaction: discord.Interaction,
    host: str,
    query_port: int,
    rcon_port: int = None,
    rcon_password: str = None,
    connect_port: int = None,
):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["rust_host"] = host
    cfg["rust_query_port"] = query_port
    cfg["rust_connect_port"] = connect_port or query_port
    save_config(config)

    msg = f"✅ Rust server set: `{host}:{query_port}`."
    if rcon_port and rcon_password:
        cfg["rust_rcon_port"] = rcon_port
        cfg["rust_rcon_password"] = rcon_password
        save_config(config)
        start_rust_connection(interaction.guild_id, host, rcon_port, rcon_password)
        msg += " RCON is connecting now — check `/rust status` in a moment to confirm."

    await interaction.response.send_message(msg, ephemeral=True)


@rust_group.command(name="setpopalert", description="Ping a role when your Rust server hits a population threshold.")
@app_commands.describe(
    role="Role to ping when the threshold is crossed — omit to disable",
    channel="Channel to post the alert in",
    threshold="Player count that counts as 'full' — omit to use the server's actual max player count",
)
async def setrustpopalert(interaction: discord.Interaction, role: discord.Role = None, channel: discord.TextChannel = None, threshold: int = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if role is None:
        cfg.pop("rust_pop_alert_role_id", None)
        cfg.pop("rust_pop_alert_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Rust population alerts disabled.", ephemeral=True)
        return
    if channel is None:
        await interaction.response.send_message("❌ Pick a channel too — that's where the alert gets posted.", ephemeral=True)
        return

    cfg["rust_pop_alert_role_id"] = role.id
    cfg["rust_pop_alert_channel_id"] = channel.id
    if threshold is not None:
        cfg["rust_pop_threshold"] = threshold
    else:
        cfg.pop("rust_pop_threshold", None)
    save_config(config)

    threshold_label = f"{threshold} players" if threshold is not None else "the server's max player count (full)"
    await interaction.response.send_message(
        f"✅ {role.mention} will be pinged in {channel.mention} when the server hits {threshold_label}.", ephemeral=True
    )


@rust_group.command(name="setchatchannel", description="Bridge this channel's chat with your Rust server (both ways).")
@app_commands.describe(channel="The channel to bridge (omit to disable)")
async def setrustchatchannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("rust_chat_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Chat bridge disabled.", ephemeral=True)
        return
    cfg["rust_chat_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ {channel.mention} is now bridged with your Rust server's in-game chat. Requires RCON to be connected (see `/rust setserver`).",
        ephemeral=True,
    )


@rust_group.command(name="setjoinleavechannel", description="Post an announcement whenever someone joins or leaves the Rust server.")
@app_commands.describe(channel="The channel for join/leave announcements (omit to disable)")
async def setrustjoinleavechannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("rust_joinleave_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Join/leave announcements disabled.", ephemeral=True)
        return
    cfg["rust_joinleave_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Join/leave announcements will now post in {channel.mention}. Requires RCON to be connected (see `/rust setserver`). "
        "Note: exact message wording from the server varies a bit by version, so this uses best-effort matching.",
        ephemeral=True,
    )


@rust_group.command(name="setstatuschannel", description="Post a live server status embed in this channel.")
@app_commands.describe(channel="The channel to post live status in (omit to disable)")
async def setruststatuschannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("rust_status_channel_id", None)
        cfg.pop("rust_status_message_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Live status disabled.", ephemeral=True)
        return
    cfg["rust_status_channel_id"] = channel.id
    cfg.pop("rust_status_message_id", None)
    save_config(config)
    await interaction.response.send_message(f"✅ Live server status will now be posted in {channel.mention}.", ephemeral=True)
    await refresh_rust_status_message(interaction.guild_id)


@rust_group.command(name="status", description="Show the Rust server's current status.")
async def ruststatus(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    host = cfg.get("rust_host")
    query_port = cfg.get("rust_query_port")
    if not host or not query_port:
        await interaction.response.send_message("❌ No Rust server set up yet. Run `/rust setserver` first.", ephemeral=True)
        return

    await interaction.response.defer()
    try:
        info = await query_rust_server(host, query_port)
        seed, worldsize = await _get_rust_seed_worldsize(interaction.guild_id)
        fps = await _get_rust_fps(interaction.guild_id)
        embed = build_rust_status_embed(host, info=info, seed=seed, worldsize=worldsize, fps=fps)
    except Exception as e:
        embed = build_rust_status_embed(host, error=str(e))

    conn = rust_connections.get(interaction.guild_id)
    rcon_status = "🟢 Connected" if (conn and conn.connected) else ("🔴 Not connected" if cfg.get("rust_rcon_port") else "— Not configured")
    embed.add_field(name="RCON", value=rcon_status, inline=True)
    connect_port = cfg.get("rust_connect_port") or query_port
    await interaction.followup.send(embed=embed, view=RustConnectView(host, connect_port))


@rust_group.command(name="command", description="Run a command on the Rust server via RCON.")
@app_commands.describe(cmd="The RCON command to run")
async def rustcommand(interaction: discord.Interaction, cmd: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    conn = rust_connections.get(interaction.guild_id)
    if conn is None or not conn.connected:
        await interaction.response.send_message(
            "❌ RCON isn't connected. Run `/rust setserver` with your RCON port and password first.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        response = await conn.send_command(cmd)
    except Exception as e:
        await interaction.followup.send(f"❌ Command failed: {e}", ephemeral=True)
        return

    display = response.strip() if response and response.strip() else "*(no output)*"
    if len(display) > 1800:
        display = display[:1800] + "\n... (truncated)"
    await interaction.followup.send(f"```\n{display}\n```", ephemeral=True)


@rust_group.command(name="save", description="Force an immediate server save.")
async def rustsave(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    conn = rust_connections.get(interaction.guild_id)
    if conn is None or not conn.connected:
        await interaction.response.send_message("❌ RCON isn't connected. Run `/rust setserver` with your RCON port and password first.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        await conn.send_command("server.save")
    except Exception as e:
        await interaction.followup.send(f"❌ Save failed: {e}", ephemeral=True)
        return
    await interaction.followup.send("✅ Server save triggered.", ephemeral=True)


@rust_group.command(name="restart", description="Schedule a server restart with a countdown warning — asks for confirmation.")
@app_commands.describe(seconds="How many seconds until restart (players get a countdown warning)")
async def rustrestart(interaction: discord.Interaction, seconds: int = 60):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    conn = rust_connections.get(interaction.guild_id)
    if conn is None or not conn.connected:
        await interaction.response.send_message("❌ RCON isn't connected. Run `/rust setserver` with your RCON port and password first.", ephemeral=True)
        return
    if seconds < 10:
        await interaction.response.send_message("❌ Give players at least 10 seconds of warning.", ephemeral=True)
        return

    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        f"⚠️ Restart the Rust server in {seconds} seconds? This kicks everyone offline briefly.",
        view=view, ephemeral=True,
    )
    await view.wait()
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no restart scheduled." if view.confirmed is False else "⏱️ Timed out — no restart scheduled.", view=None)
        return

    try:
        await conn.send_command(f"restart {seconds}")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Restart command failed: {e}", view=None)
        return
    await interaction.edit_original_response(content=f"✅ Restart scheduled — server will restart in {seconds} seconds.", view=None)


@rust_group.command(name="announce", description="Broadcast a message to everyone in-game.")
@app_commands.describe(message="What to broadcast in Rust's chat")
async def rustannounce(interaction: discord.Interaction, message: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    conn = rust_connections.get(interaction.guild_id)
    if conn is None or not conn.connected:
        await interaction.response.send_message("❌ RCON isn't connected. Run `/rust setserver` with your RCON port and password first.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        await conn.send_command(f'say "{message}"')
    except Exception as e:
        await interaction.followup.send(f"❌ Announce failed: {e}", ephemeral=True)
        return
    await interaction.followup.send(f"✅ Broadcasted to the server: {message}", ephemeral=True)


rustmacro_group = app_commands.Group(name="rustmacro", description="Recurring announcements and saved RCON macros for Rust")


@rustmacro_group.command(name="addannouncement", description="Add a message that auto-broadcasts to the server on a repeating timer.")
@app_commands.describe(message="What to broadcast", interval_minutes="How often to repeat it, in minutes")
async def rustaddannouncement(interaction: discord.Interaction, message: str, interval_minutes: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if interval_minutes < 5:
        await interaction.response.send_message("❌ Minimum interval is 5 minutes.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    announcements = cfg.setdefault("rust_recurring_announcements", [])
    announcements.append({
        "message": message, "interval_minutes": interval_minutes,
        "last_sent": datetime.now(timezone.utc).isoformat(),
    })
    save_config(config)
    await interaction.response.send_message(
        f"✅ Added — will broadcast every {interval_minutes} minute(s): \"{message}\"", ephemeral=True
    )


@rustmacro_group.command(name="removeannouncement", description="Remove a recurring announcement.")
@app_commands.describe(index="The number shown in /rustmacro listannouncements")
async def rustremoveannouncement(interaction: discord.Interaction, index: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    announcements = cfg.get("rust_recurring_announcements", [])
    if index < 1 or index > len(announcements):
        await interaction.response.send_message("❌ Invalid index — check `/rustmacro listannouncements`.", ephemeral=True)
        return
    removed = announcements.pop(index - 1)
    save_config(config)
    await interaction.response.send_message(f"✅ Removed: \"{removed['message']}\"", ephemeral=True)


@rustmacro_group.command(name="listannouncements", description="Show all recurring announcements.")
async def rustlistannouncements(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    announcements = cfg.get("rust_recurring_announcements", [])
    if not announcements:
        await interaction.response.send_message("No recurring announcements configured yet.", ephemeral=True)
        return
    lines = [f"{i}. Every {a['interval_minutes']}min — \"{a['message']}\"" for i, a in enumerate(announcements, start=1)]
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def check_rust_recurring_announcements(guild_id: int):
    cfg = get_guild_cfg(guild_id)
    announcements = cfg.get("rust_recurring_announcements", [])
    if not announcements:
        return
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return

    now = datetime.now(timezone.utc)
    changed = False
    for a in announcements:
        last_sent = datetime.fromisoformat(a["last_sent"])
        if (now - last_sent).total_seconds() / 60 >= a["interval_minutes"]:
            try:
                await conn.send_command(f'say "{a["message"]}"')
                a["last_sent"] = now.isoformat()
                changed = True
            except Exception as e:
                print(f"⚠️ Recurring Rust announcement failed ({guild_id}): {e}")
    if changed:
        save_config(config)


@rustmacro_group.command(name="macroadd", description="Save a named RCON command shortcut, so you don't have to retype it every time.")
@app_commands.describe(
    name="A short name for this macro",
    command="The RCON command to run — use {player} anywhere you want a target's SteamID substituted in",
)
async def rustmacroadd(interaction: discord.Interaction, name: str, command: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    macros = cfg.setdefault("rust_macros", {})
    name_key = name.lower().strip()
    is_update = name_key in macros
    macros[name_key] = command
    save_config(config)
    verb = "Updated" if is_update else "Saved"
    await interaction.response.send_message(f"✅ {verb} macro `{name_key}`: `{command}`", ephemeral=True)


@rustmacro_group.command(name="macrorun", description="Run a saved RCON macro.")
@app_commands.describe(name="The macro's name", player="SteamID to substitute for {player} in the macro, if it uses that placeholder")
async def rustmacrorun(interaction: discord.Interaction, name: str, player: str = None):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    macros = cfg.get("rust_macros", {})
    name_key = name.lower().strip()
    if name_key not in macros:
        await interaction.response.send_message(f"❌ No macro named `{name_key}`. Check `/rustmacro macrolist`.", ephemeral=True)
        return
    conn = rust_connections.get(interaction.guild_id)
    if conn is None or not conn.connected:
        await interaction.response.send_message("❌ RCON isn't connected. Run `/rust setserver` with your RCON port and password first.", ephemeral=True)
        return

    command = macros[name_key]
    if "{player}" in command:
        if not player:
            await interaction.response.send_message(f"❌ This macro needs a `player` value — it uses the {{player}} placeholder.", ephemeral=True)
            return
        command = command.format(player=player)

    await interaction.response.defer(ephemeral=True)
    try:
        response = await conn.send_command(command)
    except Exception as e:
        await interaction.followup.send(f"❌ Macro failed: {e}", ephemeral=True)
        return
    display = response.strip() if response and response.strip() else "*(no output)*"
    if len(display) > 1700:
        display = display[:1700] + "\n... (truncated)"
    await interaction.followup.send(f"✅ Ran `{name_key}`:\n```\n{display}\n```", ephemeral=True)


@rustmacro_group.command(name="macroremove", description="Remove a saved RCON macro.")
@app_commands.describe(name="The macro's name")
async def rustmacroremove(interaction: discord.Interaction, name: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    macros = cfg.get("rust_macros", {})
    name_key = name.lower().strip()
    if name_key not in macros:
        await interaction.response.send_message(f"❌ No macro named `{name_key}`.", ephemeral=True)
        return
    del macros[name_key]
    save_config(config)
    await interaction.response.send_message(f"✅ Removed macro `{name_key}`.", ephemeral=True)


@rustmacro_group.command(name="macrolist", description="Show all saved RCON macros.")
async def rustmacrolist(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    macros = cfg.get("rust_macros", {})
    if not macros:
        await interaction.response.send_message("No macros saved yet.", ephemeral=True)
        return
    lines = [f"**{name}** → `{command}`" for name, command in macros.items()]
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


bot.tree.add_command(rustmacro_group)


@rust_group.command(name="setbansync", description="Auto-ban on Rust too whenever someone is Discord-banned (if they've linked their SteamID).")
@app_commands.describe(
    enabled="Turn ban sync on or off",
    command_template="RCON command to run, with {steamid} and {reason} placeholders — omit to use the default",
)
async def rustsetbansync(interaction: discord.Interaction, enabled: bool, command_template: str = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["rust_ban_sync_enabled"] = enabled
    if command_template:
        cfg["rust_ban_sync_command_template"] = command_template
    save_config(config)
    if enabled:
        template = cfg.get("rust_ban_sync_command_template", 'ban {steamid} "{reason}"')
        await interaction.response.send_message(f"✅ Ban sync is ON. Command used: `{template}`", ephemeral=True)
    else:
        await interaction.response.send_message("✅ Ban sync is OFF.", ephemeral=True)


async def _maybe_sync_rust_ban(guild_id: int, user_id: int, reason: str):
    """Called after a Discord ban. Also bans on Rust if sync is enabled and
    the member has a linked SteamID. Silent no-op otherwise — this runs
    automatically in the background, not as something the banning staff
    member needs to babysit."""
    cfg = get_guild_cfg(guild_id)
    if not cfg.get("rust_ban_sync_enabled"):
        return
    steamid = cfg.get("linked_steam_ids", {}).get(str(user_id))
    if not steamid:
        return
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return

    template = cfg.get("rust_ban_sync_command_template", 'ban {steamid} "{reason}"')
    try:
        command = template.format(steamid=steamid, reason=reason)
        await conn.send_command(command)
        guild = bot.get_guild(guild_id)
        log_channel_id = cfg.get("log_channel_id")
        if guild and log_channel_id:
            log_channel = guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(f"🦀 Also banned on Rust (SteamID `{steamid}`) as part of the Discord ban.")
    except Exception as e:
        print(f"⚠️ Rust ban sync failed ({guild_id}/{user_id}): {e}")


@rust_group.command(name="players", description="Show who's currently online on the Rust server.")
async def rustplayers(interaction: discord.Interaction):
    data = await rust_get_players(interaction.guild_id)
    if data.get("error"):
        await interaction.response.send_message(f"❌ {data['error']}", ephemeral=True)
        return

    players = data.get("players", [])
    embed = discord.Embed(title="🎮 Rust — Online Now", color=discord.Color.dark_orange())
    if not players:
        embed.description = "Nobody online right now."
    else:
        lines = []
        for p in players[:25]:  # embed field limits — keep it reasonable
            name = p.get("DisplayName", "Unknown")
            ping = p.get("Ping", "—")
            connected = p.get("ConnectedSeconds", 0)
            mins = connected // 60 if isinstance(connected, int) else "—"
            lines.append(f"**{name}** — {ping}ms, {mins}m online")
        embed.description = "\n".join(lines)
        if len(players) > 25:
            embed.set_footer(text=f"Showing 25 of {len(players)} online")
    await interaction.response.send_message(embed=embed)


@rust_group.command(name="kick", description="Kick a player from the Rust server.")
@app_commands.describe(steam_id="The player's SteamID64", reason="Why you're kicking them")
async def rustkick(interaction: discord.Interaction, steam_id: str, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    result = await rust_kick_player(interaction.guild_id, steam_id, reason, interaction.user.id)
    await interaction.followup.send(result, ephemeral=True)


@rust_group.command(name="ban", description="Ban a player from the Rust server.")
@app_commands.describe(steam_id="The player's SteamID64", reason="Why you're banning them")
async def rustban(interaction: discord.Interaction, steam_id: str, reason: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    result = await rust_ban_player(interaction.guild_id, steam_id, reason, interaction.user.id)
    await interaction.followup.send(result, ephemeral=True)


@rust_group.command(name="unban", description="Unban a player from the Rust server.")
@app_commands.describe(steam_id="The player's SteamID64")
async def rustunban(interaction: discord.Interaction, steam_id: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    result = await rust_unban_player(interaction.guild_id, steam_id, interaction.user.id)
    await interaction.followup.send(result, ephemeral=True)


@rust_group.command(name="banlist", description="Show everyone currently banned from the Rust server.")
async def rustbanlist(interaction: discord.Interaction):
    data = await rust_get_banlist(interaction.guild_id)
    if data.get("error"):
        await interaction.response.send_message(f"❌ {data['error']}", ephemeral=True)
        return
    bans = data.get("bans", [])
    embed = discord.Embed(title="🚫 Rust — Ban List", color=discord.Color.dark_red())
    if not bans:
        embed.description = "No bans on record."
    else:
        lines = [f"**{b.get('name', b.get('steam_id', 'Unknown'))}** — {b.get('reason', 'No reason given')}" for b in bans[:25]]
        embed.description = "\n".join(lines)
        if len(bans) > 25:
            embed.set_footer(text=f"Showing 25 of {len(bans)} bans")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@rust_group.command(name="setrules", description="Save server rules/info text shown by /rust info.")
@app_commands.describe(text="Your server rules or info — supports multiple lines")
async def rustsetrules(interaction: discord.Interaction, text: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["rust_rules_text"] = text
    save_config(config)
    await interaction.response.send_message("✅ Rules/info text saved. Run `/rust info` to see how it looks.", ephemeral=True)


@rust_group.command(name="info", description="Post a static server info card — rules, wipe schedule, and a connect button.")
async def rustinfo(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    host = cfg.get("rust_host")
    if not host:
        await interaction.response.send_message("❌ No Rust server set up yet. Run `/rust setserver` first.", ephemeral=True)
        return

    embed = discord.Embed(title=f"🦀 {host}", color=discord.Color.dark_orange())
    rules_text = cfg.get("rust_rules_text")
    if rules_text:
        embed.add_field(name="📋 Rules", value=rules_text[:1024], inline=False)

    wipe_day = cfg.get("rust_wipe_day")
    wipe_hour = cfg.get("rust_wipe_hour")
    if wipe_day is not None and wipe_hour is not None:
        next_wipe = _next_rust_wipe_datetime(wipe_day, wipe_hour)
        embed.add_field(name="🔧 Wipe Schedule", value=f"<t:{int(next_wipe.timestamp())}:F> (<t:{int(next_wipe.timestamp())}:R>)", inline=False)

    if not rules_text and wipe_day is None:
        embed.description = "No rules or wipe schedule set up yet — this will still show a Connect button below."

    connect_port = cfg.get("rust_connect_port") or cfg.get("rust_query_port")
    view = RustConnectView(host, connect_port) if connect_port else None
    await interaction.response.send_message(embed=embed, view=view)


bot.tree.add_command(rust_group)


# ---------- Minecraft server integration ----------
#
# Status uses the standard "Server List Ping" protocol every Java Edition
# server supports out of the box (no config needed). RCON uses Minecraft's
# built-in RCON (enable-rcon=true in server.properties) — same underlying
# protocol as Source RCON, just framed slightly differently. Both are pure
# socket implementations here, following the documented protocols.

def _mc_pack_varint(value: int) -> bytes:
    value &= 0xFFFFFFFF
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def _mc_pack_string(s: str) -> bytes:
    data = s.encode("utf-8")
    return _mc_pack_varint(len(data)) + data


def _mc_recv_exact(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed unexpectedly.")
        buf += chunk
    return buf


def _mc_read_varint_from_socket(sock) -> int:
    value = 0
    position = 0
    while True:
        byte = sock.recv(1)
        if not byte:
            raise ConnectionError("Connection closed while reading.")
        b = byte[0]
        value |= (b & 0x7F) << position
        if not (b & 0x80):
            break
        position += 7
    return value


def _mc_read_varint_from_bytes(buf: bytes, offset: int):
    value = 0
    position = 0
    while True:
        b = buf[offset]
        offset += 1
        value |= (b & 0x7F) << position
        if not (b & 0x80):
            break
        position += 7
    return value, offset


def _minecraft_status_sync(host: str, port: int, timeout: float = 5.0) -> dict:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))

        handshake = bytearray()
        handshake += b"\x00"
        handshake += _mc_pack_varint(760)  # protocol version — servers ignore this for status
        handshake += _mc_pack_string(host)
        handshake += port.to_bytes(2, "big")
        handshake += _mc_pack_varint(1)  # next state: status
        sock.sendall(_mc_pack_varint(len(handshake)) + bytes(handshake))

        sock.sendall(_mc_pack_varint(1) + b"\x00")  # status request, empty payload

        length = _mc_read_varint_from_socket(sock)
        data = _mc_recv_exact(sock, length)
        _, idx = _mc_read_varint_from_bytes(data, 0)  # packet id
        json_len, idx = _mc_read_varint_from_bytes(data, idx)
        info = json.loads(data[idx:idx + json_len].decode("utf-8"))

        players = info.get("players", {})
        description = info.get("description", "")
        if isinstance(description, dict):
            description = description.get("text", "")
        return {
            "motd": str(description),
            "online": players.get("online", 0),
            "max": players.get("max", 0),
            "version": info.get("version", {}).get("name", "unknown"),
        }
    finally:
        sock.close()


async def query_minecraft_server(host: str, port: int) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _minecraft_status_sync, host, port)


def _mc_rcon_send_packet(sock, packet_id: int, packet_type: int, payload: str):
    import struct
    body = struct.pack("<ii", packet_id, packet_type) + payload.encode("utf-8") + b"\x00\x00"
    sock.sendall(struct.pack("<i", len(body)) + body)


def _mc_rcon_read_packet(sock):
    import struct
    length = struct.unpack("<i", _mc_recv_exact(sock, 4))[0]
    data = _mc_recv_exact(sock, length)
    packet_id, packet_type = struct.unpack("<ii", data[:8])
    payload = data[8:-2].decode("utf-8", errors="replace")
    return packet_id, packet_type, payload


def _minecraft_rcon_command_sync(host: str, port: int, password: str, command: str, timeout: float = 8.0) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        _mc_rcon_send_packet(sock, 1, 3, password)  # SERVERDATA_AUTH
        packet_id, _, _ = _mc_rcon_read_packet(sock)
        if packet_id == -1:
            raise ValueError("RCON authentication failed — check the password.")

        _mc_rcon_send_packet(sock, 2, 2, command)  # SERVERDATA_EXECCOMMAND
        _, _, response = _mc_rcon_read_packet(sock)
        return response
    finally:
        sock.close()


async def minecraft_rcon_command(host: str, port: int, password: str, command: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _minecraft_rcon_command_sync, host, port, password, command)


async def minecraft_get_players(guild_id: int) -> dict:
    """Returns {"players": [names], "error": None} using RCON's `list` command.
    (Unlike Rust's playerlist, Minecraft's server list ping only gives a
    limited sample, so RCON is the only reliable way to get everyone.)"""
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return {"players": [], "error": "RCON isn't set up. Set an RCON port and password on the Overview page first."}
    try:
        raw = await minecraft_rcon_command(host, rcon_port, rcon_password, "list")
        # Vanilla format: "There are 2 of a max of 20 players online: Alice, Bob"
        if ":" in raw:
            names_part = raw.split(":", 1)[1].strip()
            players = [n.strip() for n in names_part.split(",") if n.strip()]
        else:
            players = []
        return {"players": players, "error": None}
    except Exception as e:
        return {"players": [], "error": str(e)}


async def minecraft_kick_player(guild_id: int, player_name: str, reason: str, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return "❌ RCON isn't set up."
    try:
        await minecraft_rcon_command(host, rcon_port, rcon_password, f"kick {player_name} {reason}")
    except Exception as e:
        return f"❌ Kick failed: {e}"
    return f"✅ Kicked {player_name}."


async def minecraft_ban_player(guild_id: int, player_name: str, reason: str, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return "❌ RCON isn't set up."
    try:
        await minecraft_rcon_command(host, rcon_port, rcon_password, f"ban {player_name} {reason}")
    except Exception as e:
        return f"❌ Ban failed: {e}"
    return f"✅ Banned {player_name}."


async def minecraft_get_banlist(guild_id: int) -> dict:
    """Returns {"bans": [...], "error": None}. Parses vanilla Minecraft's
    `banlist` output — best-effort, since exact wording can vary slightly
    by server software (vanilla/Spigot/Paper). If this looks wrong once
    tested, run the raw command via the RCON console and share the output."""
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return {"bans": [], "error": "RCON isn't set up. Set an RCON port and password on the Overview page first."}
    try:
        raw = await minecraft_rcon_command(host, rcon_port, rcon_password, "banlist")
        bans = []
        for line in raw.splitlines()[1:]:  # first line is the "There are N banned players:" summary
            line = line.strip()
            if not line or "was banned by" not in line:
                continue
            name, rest = line.split(" was banned by", 1)
            reason = rest.split(":", 1)[1].strip() if ":" in rest else ""
            bans.append({"name": name.strip(), "reason": reason})
        return {"bans": bans, "error": None}
    except Exception as e:
        return {"bans": [], "error": str(e)}


async def minecraft_unban_player(guild_id: int, player_name: str, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return "❌ RCON isn't set up."
    try:
        await minecraft_rcon_command(host, rcon_port, rcon_password, f"pardon {player_name}")
    except Exception as e:
        return f"❌ Unban failed: {e}"
    return f"✅ Unbanned {player_name}."


def build_minecraft_status_embed(host: str, info: dict = None, error: str = None) -> discord.Embed:
    embed = discord.Embed(title=f"⛏️ {host}", color=discord.Color.green())
    if error:
        embed.description = f"⚠️ Couldn't reach the server: {error}"
        return embed
    embed.add_field(name="MOTD", value=info["motd"] or "—", inline=False)
    embed.add_field(name="Players", value=f"{info['online']} / {info['max']}", inline=True)
    embed.add_field(name="Version", value=info["version"], inline=True)
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Last updated")
    return embed


async def refresh_minecraft_status_message(guild_id: int):
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("mc_status_channel_id")
    host = cfg.get("mc_host")
    port = cfg.get("mc_port")
    if not channel_id or not host or not port:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    try:
        info = await query_minecraft_server(host, port)
        embed = build_minecraft_status_embed(host, info=info)
    except Exception as e:
        embed = build_minecraft_status_embed(host, error=str(e))

    message_id = cfg.get("mc_status_message_id")
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            return
        except (discord.NotFound, discord.Forbidden):
            pass
    try:
        message = await channel.send(embed=embed)
        cfg["mc_status_message_id"] = message.id
        save_config(config)
    except discord.Forbidden:
        pass


async def check_minecraft_downtime(guild_id: int):
    """Posts an alert when the Minecraft server's online/offline state changes."""
    cfg = get_guild_cfg(guild_id)
    alert_channel_id = cfg.get("mc_alert_channel_id")
    host = cfg.get("mc_host")
    port = cfg.get("mc_port")
    if not alert_channel_id or not host or not port:
        return
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(alert_channel_id)
    if channel is None:
        return

    was_online = cfg.get("mc_was_online", True)
    try:
        await query_minecraft_server(host, port)
        is_online = True
    except Exception:
        is_online = False

    if is_online != was_online:
        cfg["mc_was_online"] = is_online
        save_config(config)
        try:
            if is_online:
                await channel.send(f"🟢 **{host}** is back online.")
            else:
                await channel.send(f"🔴 **{host}** appears to be offline.")
        except discord.Forbidden:
            pass


@tasks.loop(minutes=2)
async def minecraft_status_loop():
    for guild_id_str in list(config.keys()):
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        cfg = config.get(guild_id_str, {})
        if cfg.get("mc_status_channel_id"):
            await refresh_minecraft_status_message(guild_id)
        if cfg.get("mc_alert_channel_id"):
            await check_minecraft_downtime(guild_id)


# ---------- rotating bot status ----------
#
# The bot's Discord presence is global (shared across every server it's in,
# since it's tied to one gateway connection) — not per-guild like everything
# else. Any guild that turns this on contributes its stats to the rotation;
# with multiple guilds enabled, the status just cycles through all of them.

_bot_status_index = 0


@tasks.loop(seconds=45)
async def bot_status_loop():
    global _bot_status_index
    lines = []
    for guild_id_str in list(config.keys()):
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        cfg = config.get(guild_id_str, {})
        if not cfg.get("bot_status_enabled"):
            continue
        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        lines.append(f"👥 {guild.member_count} members")

        if cfg.get("rust_host") and cfg.get("rust_query_port"):
            try:
                info = await query_rust_server(cfg["rust_host"], cfg["rust_query_port"])
                lines.append(f"🦀 {info['players']}/{info['max_players']} on Rust")
            except Exception:
                pass

        if cfg.get("mc_host") and cfg.get("mc_port"):
            try:
                info = await query_minecraft_server(cfg["mc_host"], cfg["mc_port"])
                lines.append(f"⛏️ {info['online']}/{info['max']} on Minecraft")
            except Exception:
                pass

    if not lines:
        return

    line = lines[_bot_status_index % len(lines)]
    _bot_status_index += 1
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=line))
    except Exception:
        pass


@bot.tree.command(name="setbotstatus", description="Show a rotating live status (members + Rust/Minecraft players) as the bot's Discord status.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(enabled="Turn the rotating status on or off")
async def setbotstatus(interaction: discord.Interaction, enabled: bool):
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["bot_status_enabled"] = enabled
    save_config(config)
    if enabled:
        await interaction.response.send_message(
            "✅ The bot's Discord status will now rotate through this server's live stats — "
            "member count, plus Rust/Minecraft player counts if connected.", ephemeral=True
        )
    else:
        await interaction.response.send_message("✅ Disabled — this server's stats won't feed into the bot's status anymore.", ephemeral=True)


async def web_set_bot_status(guild_id: int, enabled: bool, actor_id: int) -> str:
    """Mirrors /setbotstatus."""
    cfg = get_guild_cfg(guild_id)
    cfg["bot_status_enabled"] = enabled
    save_config(config)
    if enabled:
        return "✅ The bot's Discord status will now rotate through this server's live stats."
    return "✅ Disabled — this server's stats won't feed into the bot's status anymore."


minecraft_group = app_commands.Group(name="minecraft", description="Minecraft server integration")
bot.tree.add_command(minecraft_group)


@minecraft_group.command(name="setserver", description="Connect this server to your Minecraft server.")
@app_commands.describe(
    host="Your Minecraft server's IP address or domain (no port)",
    port="Server port (default 25565)",
    rcon_port="RCON port (optional — needed to run commands)",
    rcon_password="RCON password (optional — needed to run commands)",
)
async def setminecraftserver(
    interaction: discord.Interaction,
    host: str,
    port: int = 25565,
    rcon_port: int = None,
    rcon_password: str = None,
):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["mc_host"] = host
    cfg["mc_port"] = port
    if rcon_port and rcon_password:
        cfg["mc_rcon_port"] = rcon_port
        cfg["mc_rcon_password"] = rcon_password
    save_config(config)
    await interaction.response.send_message(f"✅ Minecraft server set: `{host}:{port}`.", ephemeral=True)


@minecraft_group.command(name="setstatuschannel", description="Post a live Minecraft server status embed in this channel.")
@app_commands.describe(channel="The channel to post live status in (omit to disable)")
async def setminecraftstatuschannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("mc_status_channel_id", None)
        cfg.pop("mc_status_message_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Live status disabled.", ephemeral=True)
        return
    cfg["mc_status_channel_id"] = channel.id
    cfg.pop("mc_status_message_id", None)
    save_config(config)
    await interaction.response.send_message(f"✅ Live server status will now be posted in {channel.mention}.", ephemeral=True)
    await refresh_minecraft_status_message(interaction.guild_id)


@minecraft_group.command(name="status", description="Show the Minecraft server's current status.")
async def minecraftstatus(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    host = cfg.get("mc_host")
    port = cfg.get("mc_port")
    if not host or not port:
        await interaction.response.send_message("❌ No Minecraft server set up yet. Run `/minecraft setserver` first.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        info = await query_minecraft_server(host, port)
        embed = build_minecraft_status_embed(host, info=info)
    except Exception as e:
        embed = build_minecraft_status_embed(host, error=str(e))
    await interaction.followup.send(embed=embed)


@minecraft_group.command(name="command", description="Run a command on the Minecraft server via RCON.")
@app_commands.describe(cmd="The command to run (without the leading /)")
async def minecraftcommand(interaction: discord.Interaction, cmd: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        await interaction.response.send_message(
            "❌ RCON isn't set up. Run `/minecraft setserver` with an RCON port and password first.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        response = await minecraft_rcon_command(host, rcon_port, rcon_password, cmd)
    except Exception as e:
        await interaction.followup.send(f"❌ Command failed: {e}", ephemeral=True)
        return

    display = response.strip() if response and response.strip() else "*(no output)*"
    if len(display) > 1800:
        display = display[:1800] + "\n... (truncated)"
    await interaction.followup.send(f"```\n{display}\n```", ephemeral=True)


async def web_set_minecraft_server(guild_id: int, host: str, port: int, rcon_port, rcon_password, actor_id: int) -> str:
    """Mirrors /setminecraftserver."""
    cfg = get_guild_cfg(guild_id)
    cfg["mc_host"] = host
    cfg["mc_port"] = port
    if rcon_port and rcon_password:
        cfg["mc_rcon_port"] = rcon_port
        cfg["mc_rcon_password"] = rcon_password
    save_config(config)
    return f"✅ Minecraft server set: {host}:{port}."


async def web_set_minecraft_status_channel(guild_id: int, channel_id, actor_id: int) -> str:
    """Mirrors /setminecraftstatuschannel."""
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("mc_status_channel_id", None)
        cfg.pop("mc_status_message_id", None)
        save_config(config)
        return "✅ Live status disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["mc_status_channel_id"] = channel_id
    cfg.pop("mc_status_message_id", None)
    save_config(config)
    await refresh_minecraft_status_message(guild_id)
    return f"✅ Live server status will now be posted in #{channel.name}."


async def web_set_minecraft_alert_channel(guild_id: int, channel_id, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("mc_alert_channel_id", None)
        save_config(config)
        return "✅ Downtime alerts disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["mc_alert_channel_id"] = channel_id
    save_config(config)
    return f"✅ Downtime alerts will now post in #{channel.name}."


async def web_get_minecraft_status(guild_id: int) -> dict:
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    port = cfg.get("mc_port")
    result = {"host": host, "port": port, "info": None, "error": None}
    if not host or not port:
        result["error"] = "No Minecraft server configured yet."
        return result
    try:
        result["info"] = await query_minecraft_server(host, port)
    except Exception as e:
        result["error"] = str(e)
    result["rcon_configured"] = bool(cfg.get("mc_rcon_port"))
    return result


async def web_minecraft_command(guild_id: int, cmd: str, actor_id: int) -> str:
    """Mirrors /minecraftcommand."""
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("mc_host")
    rcon_port = cfg.get("mc_rcon_port")
    rcon_password = cfg.get("mc_rcon_password")
    if not host or not rcon_port or not rcon_password:
        return "❌ RCON isn't set up yet. Set an RCON port and password first."
    try:
        response = await minecraft_rcon_command(host, rcon_port, rcon_password, cmd)
    except Exception as e:
        return f"❌ Command failed: {e}"
    return response.strip() if response and response.strip() else "(no output)"


# ---------- generic incoming webhooks ----------

async def relay_incoming_webhook(guild_id: int, payload: dict) -> bool:
    """Called by web.py when an external service posts to a guild's webhook
    URL. Formats and relays the payload into the configured Discord channel."""
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("webhook_channel_id")
    if not channel_id:
        return False
    guild = bot.get_guild(guild_id)
    if guild is None:
        return False
    channel = guild.get_channel(channel_id)
    if channel is None:
        return False

    title = str(payload.get("title") or payload.get("event") or "📩 Webhook received")
    text = payload.get("text") or payload.get("message") or payload.get("content") or ""
    if not text:
        # Fall back to dumping the raw payload if nothing recognizable was found.
        text = "```\n" + json.dumps(payload, indent=2)[:1500] + "\n```"

    embed = discord.Embed(title=str(title)[:256], description=str(text)[:4000], color=discord.Color.dark_teal())
    embed.timestamp = discord.utils.utcnow()
    try:
        await channel.send(embed=embed)
        return True
    except discord.Forbidden:
        return False


async def web_set_rust_server(guild_id: int, host: str, query_port: int, rcon_port, rcon_password, actor_id: int, connect_port=None) -> str:
    """Mirrors /rust setserver."""
    cfg = get_guild_cfg(guild_id)
    cfg["rust_host"] = host
    cfg["rust_query_port"] = query_port
    cfg["rust_connect_port"] = connect_port or query_port
    save_config(config)

    msg = f"✅ Rust server set: {host}:{query_port}."
    if rcon_port and rcon_password:
        cfg["rust_rcon_port"] = rcon_port
        cfg["rust_rcon_password"] = rcon_password
        save_config(config)
        start_rust_connection(guild_id, host, rcon_port, rcon_password)
        msg += " RCON is connecting now — check the status page in a moment to confirm."
    return msg


async def web_set_rust_status_channel(guild_id: int, channel_id, actor_id: int) -> str:
    """Mirrors /setruststatuschannel."""
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("rust_status_channel_id", None)
        cfg.pop("rust_status_message_id", None)
        save_config(config)
        return "✅ Live status disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["rust_status_channel_id"] = channel_id
    cfg.pop("rust_status_message_id", None)
    save_config(config)
    await refresh_rust_status_message(guild_id)
    return f"✅ Live server status will now be posted in #{channel.name}."


async def web_set_rust_alert_channel(guild_id: int, channel_id, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("rust_alert_channel_id", None)
        save_config(config)
        return "✅ Downtime alerts disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["rust_alert_channel_id"] = channel_id
    save_config(config)
    return f"✅ Downtime alerts will now post in #{channel.name}."


async def web_get_rust_status(guild_id: int) -> dict:
    """Returns a plain dict (not a Discord embed) for the web page to render."""
    cfg = get_guild_cfg(guild_id)
    host = cfg.get("rust_host")
    query_port = cfg.get("rust_query_port")
    result = {"host": host, "query_port": query_port, "info": None, "error": None}
    if not host or not query_port:
        result["error"] = "No Rust server configured yet."
        return result
    try:
        result["info"] = await query_rust_server(host, query_port)
    except Exception as e:
        result["error"] = str(e)

    conn = rust_connections.get(guild_id)
    result["rcon_connected"] = bool(conn and conn.connected)
    result["rcon_configured"] = bool(cfg.get("rust_rcon_port"))
    return result


async def web_rust_command(guild_id: int, cmd: str, actor_id: int) -> str:
    """Mirrors /rust command."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected. Set up your RCON port and password first."
    try:
        response = await conn.send_command(cmd)
    except Exception as e:
        return f"❌ Command failed: {e}"
    return response.strip() if response and response.strip() else "(no output)"


async def web_rust_set_wipe(guild_id: int, day, hour, channel_id, actor_id: int) -> str:
    """Mirrors /rust setwipe."""
    cfg = get_guild_cfg(guild_id)
    if day is None:
        cfg.pop("rust_wipe_day", None)
        cfg.pop("rust_wipe_hour", None)
        cfg.pop("rust_wipe_channel_id", None)
        cfg.pop("rust_wipe_announced", None)
        save_config(config)
        return "✅ Wipe countdown disabled."
    if hour is None or hour < 0 or hour > 23 or channel_id is None:
        return "❌ Pick a day, an hour (0-23 UTC), and a channel."
    cfg["rust_wipe_day"] = day
    cfg["rust_wipe_hour"] = hour
    cfg["rust_wipe_channel_id"] = channel_id
    cfg["rust_wipe_announced"] = []
    save_config(config)
    next_wipe = _next_rust_wipe_datetime(day, hour)
    return f"✅ Wipe scheduled. Next wipe: <t:{int(next_wipe.timestamp())}:F>."


async def web_rust_set_popalert(guild_id: int, role_id, channel_id, threshold, actor_id: int) -> str:
    """Mirrors /rust setpopalert."""
    cfg = get_guild_cfg(guild_id)
    if role_id is None:
        cfg.pop("rust_pop_alert_role_id", None)
        cfg.pop("rust_pop_alert_channel_id", None)
        save_config(config)
        return "✅ Rust population alerts disabled."
    if channel_id is None:
        return "❌ Pick a channel too."
    cfg["rust_pop_alert_role_id"] = role_id
    cfg["rust_pop_alert_channel_id"] = channel_id
    if threshold is not None:
        cfg["rust_pop_threshold"] = threshold
    else:
        cfg.pop("rust_pop_threshold", None)
    save_config(config)
    return "✅ Population alerts configured."


async def web_rust_set_joinleave_channel(guild_id: int, channel_id, actor_id: int) -> str:
    """Mirrors /rust setjoinleavechannel."""
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("rust_joinleave_channel_id", None)
        save_config(config)
        return "✅ Join/leave announcements disabled."
    cfg["rust_joinleave_channel_id"] = channel_id
    save_config(config)
    return "✅ Join/leave announcements enabled."


async def web_rust_set_bansync(guild_id: int, enabled: bool, command_template, actor_id: int) -> str:
    """Mirrors /rust setbansync."""
    cfg = get_guild_cfg(guild_id)
    cfg["rust_ban_sync_enabled"] = enabled
    if command_template:
        cfg["rust_ban_sync_command_template"] = command_template
    save_config(config)
    return f"✅ Ban sync is {'ON' if enabled else 'OFF'}."


async def web_rust_set_rules(guild_id: int, text: str, actor_id: int) -> str:
    """Mirrors /rust setrules."""
    cfg = get_guild_cfg(guild_id)
    cfg["rust_rules_text"] = text
    save_config(config)
    return "✅ Rules/info text saved."


async def web_rust_save(guild_id: int, actor_id: int) -> str:
    """Mirrors /rust save."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    try:
        await conn.send_command("server.save")
    except Exception as e:
        return f"❌ Save failed: {e}"
    return "✅ Server save triggered."


async def web_rust_restart(guild_id: int, seconds: int, actor_id: int) -> str:
    """Mirrors /rust restart — no confirmation step, submitting the web form is the confirmation."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    if seconds < 10:
        return "❌ Give players at least 10 seconds of warning."
    try:
        await conn.send_command(f"restart {seconds}")
    except Exception as e:
        return f"❌ Restart failed: {e}"
    return f"✅ Restart scheduled in {seconds} seconds."


async def web_rust_announce(guild_id: int, message: str, actor_id: int) -> str:
    """Mirrors /rust announce."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    try:
        await conn.send_command(f'say "{message}"')
    except Exception as e:
        return f"❌ Announce failed: {e}"
    return f"✅ Broadcasted: {message}"


async def web_rust_macro_add(guild_id: int, name: str, command: str, actor_id: int) -> str:
    """Mirrors /rustmacro macroadd."""
    cfg = get_guild_cfg(guild_id)
    macros = cfg.setdefault("rust_macros", {})
    name_key = name.lower().strip()
    is_update = name_key in macros
    macros[name_key] = command
    save_config(config)
    return f"✅ {'Updated' if is_update else 'Saved'} macro `{name_key}`."


async def web_rust_macro_remove(guild_id: int, name: str, actor_id: int) -> str:
    """Mirrors /rustmacro macroremove."""
    cfg = get_guild_cfg(guild_id)
    macros = cfg.get("rust_macros", {})
    name_key = name.lower().strip()
    if name_key not in macros:
        return f"❌ No macro named `{name_key}`."
    del macros[name_key]
    save_config(config)
    return f"✅ Removed macro `{name_key}`."


async def web_rust_macro_run(guild_id: int, name: str, player, actor_id: int) -> str:
    """Mirrors /rustmacro macrorun."""
    cfg = get_guild_cfg(guild_id)
    macros = cfg.get("rust_macros", {})
    name_key = name.lower().strip()
    if name_key not in macros:
        return f"❌ No macro named `{name_key}`."
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    command = macros[name_key]
    if "{player}" in command:
        if not player:
            return "❌ This macro needs a player value."
        command = command.format(player=player)
    try:
        response = await conn.send_command(command)
    except Exception as e:
        return f"❌ Macro failed: {e}"
    display = response.strip() if response and response.strip() else "(no output)"
    return f"✅ Ran `{name_key}`: {display}"


async def web_rust_announcement_add(guild_id: int, message: str, interval_minutes: int, actor_id: int) -> str:
    """Mirrors /rustmacro addannouncement."""
    if interval_minutes < 5:
        return "❌ Minimum interval is 5 minutes."
    cfg = get_guild_cfg(guild_id)
    announcements = cfg.setdefault("rust_recurring_announcements", [])
    announcements.append({
        "message": message, "interval_minutes": interval_minutes,
        "last_sent": datetime.now(timezone.utc).isoformat(),
    })
    save_config(config)
    return f"✅ Added — every {interval_minutes} minute(s): \"{message}\""


async def web_rust_announcement_remove(guild_id: int, index: int, actor_id: int) -> str:
    """Mirrors /rustmacro removeannouncement."""
    cfg = get_guild_cfg(guild_id)
    announcements = cfg.get("rust_recurring_announcements", [])
    if index < 1 or index > len(announcements):
        return "❌ Invalid index."
    removed = announcements.pop(index - 1)
    save_config(config)
    return f"✅ Removed: \"{removed['message']}\""


async def rust_get_players(guild_id: int) -> dict:
    """Returns {"players": [...]} or {"error": "..."}. Uses Rust's built-in
    `playerlist` RCON command, which returns JSON on modern servers."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return {"error": "RCON isn't connected. Set up your RCON port and password first.", "players": []}
    try:
        raw = await conn.send_command("playerlist")
        data = json.loads(raw)
        if isinstance(data, list):
            return {"players": data, "error": None}
        return {"players": [], "error": "Unexpected response format from playerlist."}
    except json.JSONDecodeError:
        return {"players": [], "error": "Couldn't parse the server's player list response."}
    except Exception as e:
        return {"players": [], "error": str(e)}


async def rust_kick_player(guild_id: int, steam_id: str, reason: str, actor_id: int) -> str:
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    safe_reason = reason.replace('"', "'")
    try:
        await conn.send_command(f'kick {steam_id} "{safe_reason}"')
    except Exception as e:
        return f"❌ Kick failed: {e}"
    return f"✅ Kicked {steam_id}."


async def rust_ban_player(guild_id: int, steam_id: str, reason: str, actor_id: int) -> str:
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    safe_reason = reason.replace('"', "'")
    try:
        await conn.send_command(f'ban {steam_id} "{safe_reason}"')
    except Exception as e:
        return f"❌ Ban failed: {e}"
    return f"✅ Banned {steam_id}."


async def rust_get_banlist(guild_id: int) -> dict:
    """Returns {"bans": [...]} or {"error": "..."}. Parses Rust's `banlistex`
    output — best-effort, since exact formatting can vary slightly by
    version. If this comes back empty/wrong, run the raw command via the
    RCON console below and share the output so parsing can be adjusted."""
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return {"error": "RCON isn't connected. Set up your RCON port and password first.", "bans": []}
    try:
        raw = await conn.send_command("banlistex")
        bans = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[0].isdigit():
                bans.append({
                    "steam_id": parts[0],
                    "name": parts[1] if len(parts) > 1 else "",
                    "reason": parts[2] if len(parts) > 2 else "",
                })
        return {"bans": bans, "error": None}
    except Exception as e:
        return {"bans": [], "error": str(e)}


async def rust_unban_player(guild_id: int, steam_id: str, actor_id: int) -> str:
    conn = rust_connections.get(guild_id)
    if conn is None or not conn.connected:
        return "❌ RCON isn't connected."
    try:
        await conn.send_command(f"unban {steam_id}")
    except Exception as e:
        return f"❌ Unban failed: {e}"
    return f"✅ Unbanned {steam_id}."


# ---------- scheduled automatic backups ----------

async def run_guild_backup(guild_id: int) -> str:
    """Posts a config backup file to the guild's configured backup channel.
    Shared by the scheduled task and the manual 'Run Backup Now' button."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    cfg = get_guild_cfg(guild_id)
    channel_id = cfg.get("backup_channel_id")
    if not channel_id:
        return "❌ No backup channel set."
    channel = guild.get_channel(channel_id)
    if channel is None:
        return "❌ That backup channel no longer exists."

    data = json.dumps(cfg, indent=2)
    file_bytes = io.BytesIO(data.encode("utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    file = discord.File(file_bytes, filename=f"backup-{guild_id}-{stamp}.json")
    try:
        await channel.send(f"🗄️ Automatic backup — {stamp}", file=file)
    except discord.Forbidden:
        return "❌ I don't have permission to send files in that channel."

    cfg["last_backup_at"] = datetime.now(timezone.utc).isoformat()
    save_config(config)
    return f"✅ Backup posted to #{channel.name}."


@tasks.loop(hours=24)
async def backup_scheduler_loop():
    now = datetime.now(timezone.utc)
    for guild_id_str in list(config.keys()):
        cfg = config.get(guild_id_str, {})
        channel_id = cfg.get("backup_channel_id")
        interval_days = cfg.get("backup_interval_days")
        if not channel_id or not interval_days:
            continue
        last_backup_str = cfg.get("last_backup_at")
        if last_backup_str:
            last_backup = datetime.fromisoformat(last_backup_str)
            if (now - last_backup) < timedelta(days=interval_days):
                continue
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        await run_guild_backup(guild_id)


async def web_set_backup_settings(guild_id: int, channel_id, interval_days: int, actor_id: int) -> str:
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("backup_channel_id", None)
        cfg.pop("backup_interval_days", None)
        save_config(config)
        return "✅ Automatic backups disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["backup_channel_id"] = channel_id
    cfg["backup_interval_days"] = max(1, interval_days)
    save_config(config)
    return f"✅ Automatic backups will post to #{channel.name} every {cfg['backup_interval_days']} day(s)."


async def web_run_backup_now(guild_id: int, actor_id: int) -> str:
    return await run_guild_backup(guild_id)


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

    # Group entries by rank role, preserving the configured rank order.
    grouped = {rid: [] for rid in rank_role_ids}
    unranked = []
    for entry in roster:
        rid = entry.get("rank_role_id")
        if rid in grouped:
            grouped[rid].append(entry)
        else:
            unranked.append(entry)

    populated_groups = [g for g in grouped.values() if g] + ([unranked] if unranked else [])
    # Discord caps a single embed at 6000 characters total AND 1024 per field
    # value. With enough rank groups populated, splitting that budget evenly
    # keeps the whole embed safely under both limits instead of crashing.
    field_budget = min(1000, max(150, 4500 // max(1, len(populated_groups))))

    def member_mentions(entries):
        names = []
        for entry in entries:
            member = guild.get_member(entry["user_id"])
            names.append(member.mention if member else f"<@{entry['user_id']}> (left)")
        text = ", ".join(names)
        if len(text) <= field_budget:
            return text
        truncated = []
        running_len = 0
        for name in names:
            add_len = len(name) + 2  # +2 for ", "
            if running_len + add_len > field_budget - 20:  # leave room for the "+N more" suffix
                break
            truncated.append(name)
            running_len += add_len
        remaining = len(names) - len(truncated)
        return ", ".join(truncated) + f", … +{remaining} more"

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

    # guild.get_member() only checks the local cache — after a restart (or
    # for a large server that hasn't fully synced yet), that cache can be
    # incomplete, which shows up as a wall of raw <@id> mentions instead of
    # real names. Force a full sync first so everyone resolves correctly.
    if not guild.chunked:
        try:
            await guild.chunk()
        except discord.HTTPException:
            pass

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
    except discord.HTTPException:
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


def can_use_ban(guild_id: int, member: discord.Member) -> bool:
    """True if this member can use /ban (Discord or web) — admins and the
    manager role always can, same as everything else. On top of that, a
    separate configurable role threshold: anyone whose top role is at or
    above the chosen role in Server Settings > Roles can also ban, even
    without the manager role. Set via /setbanrole or the web dashboard."""
    if member.guild_permissions.administrator:
        return True
    cfg = get_guild_cfg(guild_id)
    manager_role_id = cfg.get("manager_role_id")
    if manager_role_id and any(r.id == manager_role_id for r in member.roles):
        return True
    ban_role_id = cfg.get("ban_role_threshold_id")
    if ban_role_id:
        threshold_role = member.guild.get_role(ban_role_id)
        if threshold_role and member.top_role >= threshold_role:
            return True
    return False


# ---------- web dashboard login codes (fallback when Discord OAuth doesn't work) ----------
#
# A one-time, short-lived code generated via a slash command, redeemable on
# the dashboard's login page. Lets someone log in as themselves without
# going through Discord's OAuth web flow at all — useful if that flow is
# blocked (corporate firewall, browser cookie settings, etc.) while Discord
# itself still works fine for them.

web_login_codes: dict[str, dict] = {}  # code -> {"user_id": int, "expires_at": iso str}


@bot.tree.command(name="weblogin", description="Get a one-time code to log into the web dashboard without Discord OAuth.")
async def weblogin(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    weblogin_role_id = cfg.get("weblogin_role_id")
    member = interaction.user
    if weblogin_role_id and isinstance(member, discord.Member):
        has_role = any(r.id == weblogin_role_id for r in member.roles)
        if not (member.guild_permissions.administrator or has_role):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

    code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    web_login_codes[code] = {"user_id": interaction.user.id, "expires_at": expires_at.isoformat()}

    await interaction.response.send_message(
        f"🔑 Your one-time login code: **{code}**\n"
        f"Valid for 10 minutes. Go to the dashboard's login page and click \"Use a login code instead.\"",
        ephemeral=True,
    )


@bot.tree.command(name="setweblogincommandrole", description="Restrict /weblogin to a specific role (admins can always use it).")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="Who can run /weblogin — omit to allow everyone")
async def setweblogincommandrole(interaction: discord.Interaction, role: discord.Role = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if role is None:
        cfg.pop("weblogin_role_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Anyone can now use /weblogin.", ephemeral=True)
        return
    cfg["weblogin_role_id"] = role.id
    save_config(config)
    await interaction.response.send_message(f"✅ Only Administrators and @{role.name} can now use /weblogin.", ephemeral=True)


@bot.tree.command(name="setpromotioncooldownrole", description="Set the role that blocks a member from being promoted/demoted while they have it.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="The cooldown role — omit to disable this feature")
async def setpromotioncooldownrole(interaction: discord.Interaction, role: discord.Role = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if role is None:
        cfg.pop("promotion_cooldown_role_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Promotion cooldown role disabled.", ephemeral=True)
        return
    cfg["promotion_cooldown_role_id"] = role.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Members with @{role.name} can no longer be promoted or demoted until it's removed from them.",
        ephemeral=True,
    )


@bot.tree.command(name="setviewerrole", description="Set the rank threshold for view-only web dashboard access — that rank and everyone below it.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(rank="A configured rank — this rank and every rank below it gets view-only access. Omit to disable.")
async def setviewerrole(interaction: discord.Interaction, rank: discord.Role = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if rank is None:
        cfg.pop("viewer_rank_threshold_id", None)
        save_config(config)
        await interaction.response.send_message("✅ View-only dashboard access disabled.", ephemeral=True)
        return

    ranks = cfg.get("ranks", [])
    if rank.id not in ranks:
        valid_mentions = ", ".join(r.mention for rid in ranks if (r := interaction.guild.get_role(rid)))
        await interaction.response.send_message(
            f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions or '(none set — run /setranks first)'}",
            ephemeral=True,
        )
        return

    cfg["viewer_rank_threshold_id"] = rank.id
    save_config(config)
    lower_ranks = ranks[ranks.index(rank.id):]
    lower_mentions = ", ".join(f"<@&{rid}>" for rid in lower_ranks)
    await interaction.response.send_message(
        f"✅ Members ranked {rank.mention} or below can now view the dashboard (read-only). That's: {lower_mentions}.",
        ephemeral=True,
    )


@bot.tree.command(name="setbanrole", description="Set the role threshold for using /ban — that role and anyone above it in Server Settings > Roles.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="The threshold role — omit to disable (admins/managers can always still ban)")
async def setbanrole(interaction: discord.Interaction, role: discord.Role = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if role is None:
        cfg.pop("ban_role_threshold_id", None)
        save_config(config)
        await interaction.response.send_message(
            "✅ Ban role threshold disabled. Only admins and the manager role can use /ban now.", ephemeral=True
        )
        return
    cfg["ban_role_threshold_id"] = role.id
    save_config(config)
    await interaction.response.send_message(
        f"✅ Anyone whose top role is {role.mention} or higher (in Server Settings > Roles) can now use /ban, "
        "both in Discord and on the web dashboard — same access level as your manager role.",
        ephemeral=True,
    )


@bot.tree.command(name="putoncooldown", description="Give a member the promotion cooldown role, blocking promotions/demotions for them.")
@app_commands.describe(user="The member to put on cooldown")
async def putoncooldown(interaction: discord.Interaction, user: discord.Member):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    role_id = cfg.get("promotion_cooldown_role_id")
    if not role_id:
        await interaction.response.send_message("❌ No cooldown role set up yet. Run /setpromotioncooldownrole first.", ephemeral=True)
        return
    role = interaction.guild.get_role(role_id)
    if role is None:
        await interaction.response.send_message("❌ That role no longer exists.", ephemeral=True)
        return
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(f"❌ I can't assign @{role.name} — it's above my own role.", ephemeral=True)
        return
    try:
        await user.add_roles(role, reason=f"Put on promotion cooldown by {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to manage that role.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ {user.mention} is now on promotion cooldown.", ephemeral=True)


@bot.tree.command(name="removecooldown", description="Remove the promotion cooldown role from a member.")
@app_commands.describe(user="The member to take off cooldown")
async def removecooldown(interaction: discord.Interaction, user: discord.Member):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    role_id = cfg.get("promotion_cooldown_role_id")
    if not role_id:
        await interaction.response.send_message("❌ No cooldown role set up yet.", ephemeral=True)
        return
    role = interaction.guild.get_role(role_id)
    if role is None:
        await interaction.response.send_message("❌ That role no longer exists.", ephemeral=True)
        return
    try:
        await user.remove_roles(role, reason=f"Removed from promotion cooldown by {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to manage that role.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ {user.mention} is off promotion cooldown.", ephemeral=True)


async def web_put_on_cooldown(guild_id: int, user_id: int, actor_id: int) -> str:
    """Mirrors /putoncooldown."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    if member is None:
        return "❌ Couldn't find that member."
    cfg = get_guild_cfg(guild_id)
    role_id = cfg.get("promotion_cooldown_role_id")
    if not role_id:
        return "❌ No cooldown role set up yet."
    role = guild.get_role(role_id)
    if role is None:
        return "❌ That role no longer exists."
    if role >= guild.me.top_role:
        return f"❌ I can't assign @{role.name} — it's above my own role."
    try:
        await member.add_roles(role, reason="Put on promotion cooldown via web dashboard")
    except discord.Forbidden:
        return "❌ I don't have permission to manage that role."
    return f"✅ {member.display_name} is now on promotion cooldown."


async def web_remove_cooldown(guild_id: int, user_id: int, actor_id: int) -> str:
    """Mirrors /removecooldown."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    member = guild.get_member(user_id)
    if member is None:
        return "❌ Couldn't find that member."
    cfg = get_guild_cfg(guild_id)
    role_id = cfg.get("promotion_cooldown_role_id")
    if not role_id:
        return "❌ No cooldown role set up yet."
    role = guild.get_role(role_id)
    if role is None:
        return "❌ That role no longer exists."
    try:
        await member.remove_roles(role, reason="Removed from promotion cooldown via web dashboard")
    except discord.Forbidden:
        return "❌ I don't have permission to manage that role."
    return f"✅ {member.display_name} is off promotion cooldown."


# ---------- game account linking + whitelist auto-sync ----------

@bot.tree.command(name="linksteam", description="Link your Steam ID, so reaching the right rank can auto-whitelist you on Rust.")
@app_commands.describe(steamid="Your 17-digit SteamID64 (find it at steamid.io)")
async def linksteam(interaction: discord.Interaction, steamid: str):
    steamid = steamid.strip()
    if not steamid.isdigit() or len(steamid) != 17:
        await interaction.response.send_message("❌ That doesn't look like a SteamID64 — it should be exactly 17 digits. You can look yours up at steamid.io.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    links = cfg.setdefault("linked_steam_ids", {})
    links[str(interaction.user.id)] = steamid
    save_config(config)
    await interaction.response.send_message(f"✅ Linked SteamID `{steamid}` to your account.", ephemeral=True)
    await _maybe_sync_whitelist(interaction.guild_id, interaction.user.id)


@bot.tree.command(name="linkminecraft", description="Link your Minecraft username, so reaching the right rank can auto-whitelist you.")
@app_commands.describe(username="Your exact Minecraft username")
async def linkminecraft(interaction: discord.Interaction, username: str):
    username = username.strip()
    if not username or len(username) > 16:
        await interaction.response.send_message("❌ That doesn't look like a valid Minecraft username.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    links = cfg.setdefault("linked_minecraft_names", {})
    links[str(interaction.user.id)] = username
    save_config(config)
    await interaction.response.send_message(f"✅ Linked Minecraft username `{username}` to your account.", ephemeral=True)
    await _maybe_sync_whitelist(interaction.guild_id, interaction.user.id)


@bot.tree.command(name="setwhitelistsync", description="Auto-whitelist members on Rust/Minecraft once they reach a certain rank.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    rank="Reaching this rank or higher triggers whitelisting — omit to disable",
    rust_command_template="RCON command to run for Rust, with {steamid} as a placeholder (e.g. 'whitelist add {steamid}' or your plugin's command)",
    minecraft_enabled="Also whitelist on Minecraft using its built-in whitelist command",
)
async def setwhitelistsync(
    interaction: discord.Interaction, rank: discord.Role = None,
    rust_command_template: str = None, minecraft_enabled: bool = None,
):
    cfg = get_guild_cfg(interaction.guild_id)
    if rank is None and rust_command_template is None and minecraft_enabled is None:
        cfg.pop("whitelist_sync_rank_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Whitelist auto-sync disabled.", ephemeral=True)
        return

    if rank is not None:
        ranks = cfg.get("ranks", [])
        if rank.id not in ranks:
            valid_mentions = ", ".join(r.mention for rid in ranks if (r := interaction.guild.get_role(rid)))
            await interaction.response.send_message(
                f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions or '(none set — run /setranks first)'}",
                ephemeral=True,
            )
            return
        cfg["whitelist_sync_rank_id"] = rank.id
    if rust_command_template is not None:
        cfg["whitelist_rust_command_template"] = rust_command_template
    if minecraft_enabled is not None:
        cfg["whitelist_minecraft_enabled"] = minecraft_enabled
    save_config(config)

    parts = []
    if rank is not None:
        parts.append(f"rank threshold: {rank.mention} or higher")
    if rust_command_template is not None:
        parts.append(f"Rust command: `{rust_command_template}`")
    if minecraft_enabled is not None:
        parts.append(f"Minecraft: {'on' if minecraft_enabled else 'off'}")
    await interaction.response.send_message(f"✅ Whitelist sync updated — {', '.join(parts)}.", ephemeral=True)


async def web_set_whitelist_sync(guild_id: int, rank_id, rust_command_template, minecraft_enabled, actor_id: int) -> str:
    """Mirrors /setwhitelistsync."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    cfg = get_guild_cfg(guild_id)
    if rank_id is None and rust_command_template is None and minecraft_enabled is None:
        cfg.pop("whitelist_sync_rank_id", None)
        save_config(config)
        return "✅ Whitelist auto-sync disabled."

    if rank_id is not None:
        ranks = cfg.get("ranks", [])
        if rank_id not in ranks:
            return "❌ That isn't a configured rank."
        cfg["whitelist_sync_rank_id"] = rank_id
    if rust_command_template is not None:
        cfg["whitelist_rust_command_template"] = rust_command_template
    if minecraft_enabled is not None:
        cfg["whitelist_minecraft_enabled"] = minecraft_enabled
    save_config(config)
    return "✅ Whitelist sync settings saved."


async def _maybe_sync_whitelist(guild_id: int, user_id: int):
    """Called after any rank change/roster addition. Whitelists the member on
    Rust/Minecraft if they've reached the configured threshold rank and have
    a linked game account. Silently does nothing if sync isn't set up, the
    member hasn't reached the threshold, or they haven't linked an account —
    this is meant to run automatically in the background, not report errors
    to whoever triggered the rank change."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    cfg = get_guild_cfg(guild_id)
    threshold_id = cfg.get("whitelist_sync_rank_id")
    if not threshold_id:
        return
    ranks = cfg.get("ranks", [])
    if threshold_id not in ranks:
        return

    roster = cfg.get("roster", [])
    entry = next((e for e in roster if e["user_id"] == user_id), None)
    if not entry or entry.get("rank_role_id") not in ranks:
        return
    # Lower index = higher rank. "Reached the threshold" means at or above it.
    if ranks.index(entry["rank_role_id"]) > ranks.index(threshold_id):
        return

    member = guild.get_member(user_id)
    if member is None:
        return

    rust_template = cfg.get("whitelist_rust_command_template")
    if rust_template and cfg.get("rust_host") and cfg.get("rust_rcon_port"):
        steamid = cfg.get("linked_steam_ids", {}).get(str(user_id))
        conn = rust_connections.get(guild_id)
        if steamid and conn is not None and conn.connected:
            try:
                command = rust_template.format(steamid=steamid)
                await conn.send_command(command)
                log_channel_id = cfg.get("log_channel_id")
                if log_channel_id:
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(f"🦀 Auto-whitelisted {member.mention} on Rust (SteamID `{steamid}`).")
            except Exception as e:
                print(f"⚠️ Whitelist sync failed for Rust ({guild_id}/{user_id}): {e}")

    if cfg.get("whitelist_minecraft_enabled") and cfg.get("mc_host") and cfg.get("mc_rcon_port"):
        mc_username = cfg.get("linked_minecraft_names", {}).get(str(user_id))
        if mc_username:
            try:
                await minecraft_rcon_command(cfg["mc_host"], cfg["mc_rcon_port"], cfg.get("mc_rcon_password", ""), f"whitelist add {mc_username}")
                log_channel_id = cfg.get("log_channel_id")
                if log_channel_id:
                    log_channel = guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(f"⛏️ Auto-whitelisted {member.mention} on Minecraft (`{mc_username}`).")
            except Exception as e:
                print(f"⚠️ Whitelist sync failed for Minecraft ({guild_id}/{user_id}): {e}")


# ---------- rank bonus roles (auto-grant extra roles at a rank) ----------

@bot.tree.command(name="addrankbonusrole", description="When someone reaches a rank, automatically give them this extra role too.")
@app_commands.describe(rank="A configured rank", bonus_role="The extra role to auto-grant at that rank")
async def addrankbonusrole(interaction: discord.Interaction, rank: discord.Role, bonus_role: discord.Role):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    ranks = cfg.get("ranks", [])
    if rank.id not in ranks:
        valid_mentions = ", ".join(r.mention for rid in ranks if (r := interaction.guild.get_role(rid)))
        await interaction.response.send_message(
            f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions or '(none set — run /setranks first)'}",
            ephemeral=True,
        )
        return
    if bonus_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(f"❌ I can't assign {bonus_role.mention} — it's above my own role.", ephemeral=True)
        return

    bonus_map = cfg.setdefault("rank_bonus_roles", {})
    bonus_list = bonus_map.setdefault(str(rank.id), [])
    if bonus_role.id in bonus_list:
        await interaction.response.send_message(f"ℹ️ {bonus_role.mention} is already a bonus role for {rank.mention}.", ephemeral=True)
        return
    bonus_list.append(bonus_role.id)
    save_config(config)
    await interaction.response.send_message(f"✅ Reaching {rank.mention} will now also grant {bonus_role.mention}.", ephemeral=True)


@bot.tree.command(name="removerankbonusrole", description="Stop auto-granting an extra role at a rank.")
@app_commands.describe(rank="A configured rank", bonus_role="The bonus role to remove")
async def removerankbonusrole(interaction: discord.Interaction, rank: discord.Role, bonus_role: discord.Role):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    bonus_list = cfg.get("rank_bonus_roles", {}).get(str(rank.id), [])
    if bonus_role.id not in bonus_list:
        await interaction.response.send_message(f"❌ {bonus_role.mention} isn't a bonus role for {rank.mention}.", ephemeral=True)
        return
    bonus_list.remove(bonus_role.id)
    save_config(config)
    await interaction.response.send_message(f"✅ Removed {bonus_role.mention} as a bonus role for {rank.mention}.", ephemeral=True)


@bot.tree.command(name="listrankbonusroles", description="Show which extra roles get auto-granted at each rank.")
async def listrankbonusroles(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    bonus_map = cfg.get("rank_bonus_roles", {})
    ranks = cfg.get("ranks", [])
    if not bonus_map or not any(bonus_map.get(str(rid)) for rid in ranks):
        await interaction.response.send_message("No rank bonus roles configured yet.", ephemeral=True)
        return

    lines = []
    for rid in ranks:
        bonus_list = bonus_map.get(str(rid), [])
        if not bonus_list:
            continue
        rank_role = interaction.guild.get_role(rid)
        rank_label = rank_role.mention if rank_role else f"(deleted rank {rid})"
        bonus_mentions = ", ".join(f"<@&{bid}>" for bid in bonus_list)
        lines.append(f"{rank_label} → {bonus_mentions}")
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


async def _sync_rank_bonus_roles(guild_id: int, user_id: int, new_rank_id: int):
    """Called right after a member's rank is set to new_rank_id. Grants any
    bonus roles configured for that rank — additive only, doesn't remove
    bonus roles tied to a previous rank (so demoting someone never strips
    roles they might still need for unrelated reasons)."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    member = guild.get_member(user_id)
    if member is None:
        return
    cfg = get_guild_cfg(guild_id)
    bonus_list = cfg.get("rank_bonus_roles", {}).get(str(new_rank_id), [])
    if not bonus_list:
        return

    for bonus_role_id in bonus_list:
        role = guild.get_role(bonus_role_id)
        if role is None or role in member.roles or role >= guild.me.top_role:
            continue
        try:
            await member.add_roles(role, reason=f"Rank bonus role for reaching rank {new_rank_id}")
        except discord.Forbidden:
            print(f"⚠️ Rank bonus role grant failed (no permission) for {guild_id}/{user_id}/{bonus_role_id}")


async def web_add_rank_bonus_role(guild_id: int, rank_id: int, bonus_role_id: int, actor_id: int) -> str:
    """Mirrors /addrankbonusrole."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    rank = guild.get_role(rank_id)
    bonus_role = guild.get_role(bonus_role_id)
    if rank is None or bonus_role is None:
        return "❌ Couldn't find that rank or role."
    cfg = get_guild_cfg(guild_id)
    ranks = cfg.get("ranks", [])
    if rank_id not in ranks:
        return f"❌ @{rank.name} isn't a configured rank."
    if bonus_role >= guild.me.top_role:
        return f"❌ I can't assign @{bonus_role.name} — it's above my own role."
    bonus_map = cfg.setdefault("rank_bonus_roles", {})
    bonus_list = bonus_map.setdefault(str(rank_id), [])
    if bonus_role_id in bonus_list:
        return f"ℹ️ @{bonus_role.name} is already a bonus role for @{rank.name}."
    bonus_list.append(bonus_role_id)
    save_config(config)
    return f"✅ Reaching @{rank.name} will now also grant @{bonus_role.name}."


async def web_remove_rank_bonus_role(guild_id: int, rank_id: int, bonus_role_id: int, actor_id: int) -> str:
    """Mirrors /removerankbonusrole."""
    cfg = get_guild_cfg(guild_id)
    bonus_list = cfg.get("rank_bonus_roles", {}).get(str(rank_id), [])
    if bonus_role_id not in bonus_list:
        return "❌ That bonus role isn't set for that rank."
    bonus_list.remove(bonus_role_id)
    save_config(config)
    return "✅ Removed."



def redeem_web_login_code(code: str):
    """Returns the Discord user ID if the code is valid and unexpired, else
    None. One-time use — the code is removed either way once checked."""
    entry = web_login_codes.pop(code.strip().upper(), None)
    if entry is None:
        return None
    expires_at = datetime.fromisoformat(entry["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return None
    return entry["user_id"]


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


# ---------- web command console ----------
#
# Lets an admin run (almost) any slash command from the web dashboard by
# introspecting the bot's actual command tree, instead of hand-building a
# form for every single command. Two safety properties that matter here:
#
# 1. Commands that use ConfirmView (a real Discord button someone has to
#    click) are excluded entirely — that flow can't be faked from a web
#    form POST, so those keep using their existing dedicated pages.
# 2. This whole feature is gated to genuine server Administrators, checked
#    independently here AND on the web page. That's stricter than several
#    individual commands' own internal checks (some just require the
#    manager role) — necessary because calling a command's underlying
#    function directly bypasses any @app_commands.checks.has_permissions(...)
#    decorator, which normally only Discord's own invocation path enforces.

CONSOLE_CONFIRMATION_REQUIRED = {
    "rust restart", "rosterremove", "promote", "demote", "rosteraddall",
    "kick", "ban", "massrename", "massaddrole", "massremoverole",
}
CONSOLE_DEDICATED_PAGES = {
    "rust restart": "rust_page", "rosterremove": "roster_page", "promote": "roster_page",
    "demote": "roster_page", "rosteraddall": "roster_page", "kick": "moderation_page",
    "ban": "moderation_page", "massrename": "mass_page", "massaddrole": "mass_page",
    "massremoverole": "mass_page",
}
def _build_console_type_map():
    """Built defensively — if discord.py's enum reference path is ever
    different than expected, this falls back to an empty map (meaning every
    parameter just gets treated as a plain string) instead of crashing the
    entire bot at import time."""
    try:
        return {
            discord.AppCommandOptionType.string: "string",
            discord.AppCommandOptionType.integer: "integer",
            discord.AppCommandOptionType.number: "number",
            discord.AppCommandOptionType.boolean: "boolean",
            discord.AppCommandOptionType.user: "user",
            discord.AppCommandOptionType.channel: "channel",
            discord.AppCommandOptionType.role: "role",
        }
    except AttributeError as e:
        print(f"⚠️ Command console: couldn't build type map ({e}) — all parameters will be treated as plain text.")
        return {}


CONSOLE_TYPE_MAP = _build_console_type_map()


def get_console_commands() -> list:
    """Walks the entire live command tree (including subcommands inside
    groups) and returns a flat, sorted list of every runnable command with
    enough metadata to build a dynamic form for it."""
    results = []

    def walk(cmd, prefix=""):
        full_name = f"{prefix}{cmd.name}".strip()
        if isinstance(cmd, app_commands.Group):
            for sub in cmd.commands:
                walk(sub, prefix=f"{full_name} ")
            return
        params = []
        for p in cmd.parameters:
            choices = [{"name": c.name, "value": c.value} for c in p.choices] if p.choices else None
            params.append({
                "name": p.name,
                "description": p.description or "",
                "type": CONSOLE_TYPE_MAP.get(p.type, "string"),
                "required": p.required,
                "choices": choices,
            })
        results.append({
            "name": full_name,
            "description": cmd.description or "",
            "parameters": params,
            "requires_confirmation": full_name in CONSOLE_CONFIRMATION_REQUIRED,
            "dedicated_page": CONSOLE_DEDICATED_PAGES.get(full_name),
        })

    for cmd in bot.tree.get_commands():
        walk(cmd)
    return sorted(results, key=lambda c: c["name"])


def _resolve_console_command_object(full_name: str):
    """Finds the actual app_commands.Command object for a dotted console name
    like 'rust setwipe', so its .callback can be invoked directly."""
    parts = full_name.split(" ")
    commands_list = bot.tree.get_commands()
    obj = None
    for i, part in enumerate(parts):
        obj = discord.utils.get(commands_list, name=part)
        if obj is None:
            return None
        if i < len(parts) - 1:
            if not isinstance(obj, app_commands.Group):
                return None
            commands_list = obj.commands
    return obj


class _ConsoleFakeResponse:
    def __init__(self, fake_interaction):
        self._fi = fake_interaction
        self._done = False

    async def send_message(self, content=None, *, embed=None, embeds=None, view=None, ephemeral=False, **kwargs):
        self._done = True
        await self._fi._handle_output(content, embed, embeds, view, ephemeral)

    async def defer(self, *, ephemeral=False, thinking=False):
        self._done = True

    def is_done(self):
        return self._done


class _ConsoleFakeFollowup:
    def __init__(self, fake_interaction):
        self._fi = fake_interaction

    async def send(self, content=None, *, embed=None, embeds=None, view=None, ephemeral=False, **kwargs):
        await self._fi._handle_output(content, embed, embeds, view, ephemeral)


class ConsoleFakeInteraction:
    """Mimics enough of discord.Interaction's surface for non-confirmation
    slash commands to run correctly when triggered from the web console."""
    def __init__(self, guild: discord.Guild, user: discord.Member, output_channel=None):
        self.guild = guild
        self.guild_id = guild.id
        self.user = user
        self.channel = output_channel
        self.channel_id = output_channel.id if output_channel else None
        self.response = _ConsoleFakeResponse(self)
        self.followup = _ConsoleFakeFollowup(self)
        self.result_texts = []
        self._last_sent_message = None
        self.client = bot

    async def _handle_output(self, content, embed, embeds, view, ephemeral):
        # A command posting something WITH an interactive view (a real
        # button UI — giveaway entry, tournament sign-up, etc.) needs a real,
        # trackable Discord message — send it for real to the chosen channel.
        if view is not None and not ephemeral:
            if self.channel is None:
                self.result_texts.append(
                    "⚠️ This command wants to post an interactive message, but no output channel was selected — nothing was sent."
                )
                return
            try:
                msg = await self.channel.send(content=content, embed=embed, view=view)
                self._last_sent_message = msg
                self.result_texts.append(f"✅ Posted to #{self.channel.name} (with an interactive component attached).")
            except discord.Forbidden:
                self.result_texts.append(f"❌ I don't have permission to post in #{self.channel.name}.")
            return
        if content:
            self.result_texts.append(content)
        if embed:
            self.result_texts.append(f"**{embed.title or ''}**\n{embed.description or ''}".strip())
        if embeds:
            for e in embeds:
                self.result_texts.append(f"**{e.title or ''}**\n{e.description or ''}".strip())

    async def original_response(self):
        if self._last_sent_message:
            return self._last_sent_message
        class _Dummy:
            id = None
        return _Dummy()

    async def edit_original_response(self, *, content=None, embed=None, view=None, **kwargs):
        await self._handle_output(content, embed, None, view, False)


async def run_console_command(guild_id: int, command_full_name: str, raw_params: dict, actor_id: int, output_channel_id=None) -> dict:
    """Runs a slash command from the web console. Returns
    {"success": bool, "messages": [str, ...]}. Requires the acting member to
    be a genuine server Administrator — see the module note above for why."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return {"success": False, "messages": ["❌ Server not found."]}
    actor = guild.get_member(actor_id)
    if actor is None:
        return {"success": False, "messages": ["❌ Couldn't find your account in this server."]}
    if not actor.guild_permissions.administrator:
        return {"success": False, "messages": ["❌ The command console requires Administrator permission."]}

    all_commands = get_console_commands()
    cmd_info = next((c for c in all_commands if c["name"] == command_full_name), None)
    if cmd_info is None:
        return {"success": False, "messages": [f"❌ Unknown command: {command_full_name}"]}
    if cmd_info["requires_confirmation"]:
        return {"success": False, "messages": [
            f"❌ /{command_full_name} requires interactive Discord confirmation and can't run from the console — "
            "use its dedicated dashboard page instead."
        ]}

    cmd_obj = _resolve_console_command_object(command_full_name)
    if cmd_obj is None:
        return {"success": False, "messages": [f"❌ Couldn't resolve command: {command_full_name}"]}

    kwargs = {}
    for p in cmd_info["parameters"]:
        raw_value = (raw_params.get(p["name"]) or "").strip()
        if not raw_value:
            if p["required"]:
                return {"success": False, "messages": [f"❌ Missing required parameter: {p['name']}"]}
            continue
        try:
            if p["type"] == "integer":
                kwargs[p["name"]] = int(raw_value)
            elif p["type"] == "number":
                kwargs[p["name"]] = float(raw_value)
            elif p["type"] == "boolean":
                kwargs[p["name"]] = raw_value.lower() in ("true", "1", "yes")
            elif p["type"] == "user":
                member = guild.get_member(int(raw_value))
                if member is None:
                    return {"success": False, "messages": [f"❌ Couldn't find a member with ID {raw_value}."]}
                kwargs[p["name"]] = member
            elif p["type"] == "role":
                role = guild.get_role(int(raw_value))
                if role is None:
                    return {"success": False, "messages": [f"❌ Couldn't find a role with ID {raw_value}."]}
                kwargs[p["name"]] = role
            elif p["type"] == "channel":
                channel = guild.get_channel(int(raw_value))
                if channel is None:
                    return {"success": False, "messages": [f"❌ Couldn't find a channel with ID {raw_value}."]}
                kwargs[p["name"]] = channel
            else:
                kwargs[p["name"]] = raw_value
        except ValueError:
            return {"success": False, "messages": [f"❌ Invalid value for {p['name']}: {raw_value}"]}

    output_channel = guild.get_channel(output_channel_id) if output_channel_id else None
    fake_interaction = ConsoleFakeInteraction(guild, actor, output_channel)

    try:
        await cmd_obj.callback(fake_interaction, **kwargs)
    except Exception as e:
        return {"success": False, "messages": [f"❌ Command raised an error: {e}"]}

    return {"success": True, "messages": fake_interaction.result_texts or ["✅ Command ran (no reply was produced)."]}


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
    rank7="7th rank role", rank8="8th rank role", rank9="9th rank role",
    rank10="10th rank role", rank11="11th rank role", rank12="12th rank role",
    rank13="13th rank role", rank14="14th rank role", rank15="15th rank role",
    rank16="16th rank role (lowest)",
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
    rank9: discord.Role = None,
    rank10: discord.Role = None,
    rank11: discord.Role = None,
    rank12: discord.Role = None,
    rank13: discord.Role = None,
    rank14: discord.Role = None,
    rank15: discord.Role = None,
    rank16: discord.Role = None,
):
    roles_in_order = [
        r for r in [
            rank1, rank2, rank3, rank4, rank5, rank6, rank7, rank8,
            rank9, rank10, rank11, rank12, rank13, rank14, rank15, rank16,
        ]
        if r is not None
    ]

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
        await _maybe_sync_whitelist(interaction.guild_id, user.id)
        await _sync_rank_bonus_roles(interaction.guild_id, user.id, rank.id)
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
    await _maybe_sync_whitelist(interaction.guild_id, user.id)
    await _sync_rank_bonus_roles(interaction.guild_id, user.id, rank.id)


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

    cooldown_role_id = cfg.get("promotion_cooldown_role_id")
    if cooldown_role_id:
        cooldown_role = interaction.guild.get_role(cooldown_role_id)
        if cooldown_role and cooldown_role in user.roles:
            await interaction.response.send_message(
                f"⏳ {user.mention} has the @{cooldown_role.name} role and can't be {verb.lower()}d right now.",
                ephemeral=True,
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
    await _maybe_sync_whitelist(interaction.guild_id, user.id)
    await _sync_rank_bonus_roles(interaction.guild_id, user.id, new_role.id)


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
            continue
        await _maybe_sync_whitelist(interaction.guild_id, member.id)
        await _sync_rank_bonus_roles(interaction.guild_id, member.id, rank.id)

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


@bot.tree.command(name="rosteraddall", description="Put EVERY server member on the roster at once, at a given rank.")
@app_commands.describe(rank="The rank to assign to everyone — this also grants them the role")
async def rosteraddall(interaction: discord.Interaction, rank: discord.Role):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    valid_rank_ids = cfg.get("ranks", [])
    if rank.id not in valid_rank_ids:
        valid_mentions = ", ".join(r.mention for rid in valid_rank_ids if (r := interaction.guild.get_role(rid)))
        await interaction.response.send_message(
            f"❌ {rank.mention} isn't a configured rank. Choose from: {valid_mentions or '(none set — run /setranks first)'}",
            ephemeral=True,
        )
        return

    bot_top_role = interaction.guild.me.top_role
    if rank >= bot_top_role:
        await interaction.response.send_message(
            f"❌ I can't assign {rank.mention} — it's higher than or equal to my own top role. "
            "Move my bot role above it in Server Settings > Roles.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        all_members = [m async for m in interaction.guild.fetch_members(limit=None) if not m.bot]
    except discord.HTTPException as e:
        await interaction.followup.send(
            f"❌ Couldn't fetch server members ({e}). Make sure 'Server Members Intent' is enabled for this bot "
            "in the Discord Developer Portal (Bot page).",
            ephemeral=True,
        )
        return

    if not all_members:
        await interaction.followup.send("ℹ️ No members found.", ephemeral=True)
        return

    view = ConfirmView(interaction.user.id)
    await interaction.followup.send(
        f"⚠️ Put **all {len(all_members)}** member(s) on the roster at {rank.mention}? "
        "This also grants them the role if they don't already have it.",
        view=view, ephemeral=True,
    )
    await view.wait()
    if view.confirmed is None:
        await interaction.edit_original_response(content="⏱️ Timed out — no changes made.", view=None)
        return
    if not view.confirmed:
        await interaction.edit_original_response(content="❌ Cancelled — no changes made.", view=None)
        return

    await interaction.edit_original_response(content=f"⏳ Adding {len(all_members)} member(s) to the roster... (this can take a while due to Discord's rate limits)", view=None)

    roster = cfg.setdefault("roster", [])
    added_members, moved_members, role_failed = [], [], 0

    for i, member in enumerate(all_members, start=1):
        try:
            if rank not in member.roles:
                await member.add_roles(rank, reason=f"Bulk roster add by {interaction.user}")

            existing = next((entry for entry in roster if entry["user_id"] == member.id), None)
            if existing is None:
                roster.append({"user_id": member.id, "rank_role_id": rank.id})
                record_history(interaction.guild_id, member.id, "Added to Roster", rank.mention, interaction.user.id, "Bulk add-all")
                added_members.append(member)
            elif existing.get("rank_role_id") != rank.id:
                existing["rank_role_id"] = rank.id
                record_history(interaction.guild_id, member.id, "Rank Changed", rank.mention, interaction.user.id, "Bulk add-all")
                moved_members.append(member)
            await _maybe_sync_whitelist(interaction.guild_id, member.id)
            await _sync_rank_bonus_roles(interaction.guild_id, member.id, rank.id)
        except discord.HTTPException:
            role_failed += 1
            continue

        if i % 50 == 0:
            save_config(config)  # checkpoint progress so a restart mid-run doesn't lose it
            try:
                await interaction.edit_original_response(
                    content=f"⏳ Progress: {i}/{len(all_members)} processed ({len(added_members)} added, {len(moved_members)} moved so far)...",
                )
            except discord.HTTPException:
                pass

    save_config(config)

    embed = discord.Embed(title="📋 Roster Add-All Complete", color=discord.Color.teal())
    embed.description = f"Put everyone on the roster at {rank.mention}."
    embed.add_field(name="Added", value=str(len(added_members)), inline=True)
    embed.add_field(name="Moved", value=str(len(moved_members)), inline=True)
    if role_failed:
        embed.add_field(name="Role grant failed", value=str(role_failed), inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)

    cfg_log2 = get_guild_cfg(interaction.guild_id)
    log_channel_id2 = cfg_log2.get("log_channel_id")
    if log_channel_id2:
        log_channel2 = interaction.guild.get_channel(log_channel_id2)
        if log_channel2:
            now_ts2 = int(datetime.now(timezone.utc).timestamp())
            try:
                await log_channel2.send(
                    f"📋 Bulk roster add-all → {rank.mention} | {len(added_members)} added, {len(moved_members)} moved | "
                    f"{interaction.user.mention} | <t:{now_ts2}:f>"
                )
            except discord.Forbidden:
                pass

    await refresh_roster_message(interaction.guild)
    await refresh_server_stats_message(interaction.guild)


@bot.tree.command(name="roster", description="Show the current roster.")
async def roster(interaction: discord.Interaction):
    await interaction.response.defer()
    if not interaction.guild.chunked:
        try:
            await interaction.guild.chunk()
        except discord.HTTPException:
            pass
    embed = build_roster_embed(interaction.guild)
    await interaction.followup.send(embed=embed)


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


@bot.tree.command(name="namehistory", description="Show a member's nickname/username change history.")
@app_commands.describe(user="The member to look up (defaults to you)")
async def namehistory(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    cfg = get_guild_cfg(interaction.guild_id)
    entries = cfg.get("name_history", {}).get(str(user.id), [])

    embed = discord.Embed(title=f"📝 Name History for {user.display_name}", color=discord.Color.dark_grey())
    embed.set_thumbnail(url=user.display_avatar.url)

    if not entries:
        embed.description = "No recorded name changes yet."
        await interaction.response.send_message(embed=embed)
        return

    recent = list(reversed(entries))[:15]
    lines = []
    for entry in recent:
        ts = datetime.fromisoformat(entry["timestamp"])
        icon = "🏷️" if entry["kind"] == "nickname" else "👤"
        lines.append(f"{icon} `{entry['old']}` → `{entry['new']}` — <t:{int(ts.timestamp())}:R>")

    embed.description = "\n".join(lines)
    if len(entries) > 15:
        embed.set_footer(text=f"Showing 15 most recent of {len(entries)} total changes")
    await interaction.response.send_message(embed=embed)


# ---------- member reports ----------

@bot.tree.command(name="report", description="Privately report a member to staff.")
@app_commands.describe(user="Who you're reporting", reason="What happened")
async def report(interaction: discord.Interaction, user: discord.Member, reason: str):
    cfg = get_guild_cfg(interaction.guild_id)
    channel_id = cfg.get("reports_channel_id")
    if not channel_id:
        await interaction.response.send_message("❌ Reports aren't set up on this server yet. Ask an admin to run /setreportschannel.", ephemeral=True)
        return
    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("❌ The configured reports channel no longer exists.", ephemeral=True)
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't report yourself.", ephemeral=True)
        return

    next_id = cfg.get("report_next_id", 1)
    cfg["report_next_id"] = next_id + 1
    report_entry = {
        "id": next_id, "reporter_id": interaction.user.id, "reported_user_id": user.id,
        "reason": reason, "status": "open", "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    cfg.setdefault("reports", {})[str(next_id)] = report_entry
    save_config(config)

    embed = discord.Embed(title=f"🚩 Report #{next_id}", color=discord.Color.red())
    embed.add_field(name="Reported", value=user.mention, inline=True)
    embed.add_field(name="Reported by", value=interaction.user.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.timestamp = discord.utils.utcnow()
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass

    await interaction.response.send_message("✅ Your report has been sent to staff privately. Thank you.", ephemeral=True)


@bot.tree.command(name="setreportschannel", description="Set the private channel where member reports get sent.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The staff-only channel for reports (omit to disable)")
async def setreportschannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("reports_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Reports disabled.", ephemeral=True)
        return
    cfg["reports_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(f"✅ Reports will now be sent to {channel.mention}.", ephemeral=True)


async def web_set_reports_channel(guild_id: int, channel_id, actor_id: int) -> str:
    """Mirrors /setreportschannel."""
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("reports_channel_id", None)
        save_config(config)
        return "✅ Reports disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["reports_channel_id"] = channel_id
    save_config(config)
    return f"✅ Reports will now be sent to #{channel.name}."


async def web_report_set_status(guild_id: int, report_id: int, status: str, actor_id: int) -> str:
    """Mark a report as resolved or dismissed from the web dashboard."""
    cfg = get_guild_cfg(guild_id)
    report_entry = cfg.get("reports", {}).get(str(report_id))
    if not report_entry:
        return "❌ Report not found."
    report_entry["status"] = status
    save_config(config)
    return f"✅ Report #{report_id} marked {status}."




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


tournament_group = app_commands.Group(name="tournament", description="Run bracket tournaments")
bot.tree.add_command(tournament_group)


@tournament_group.command(name="create", description="Open sign-ups for a single-elimination tournament.")
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


@tournament_group.command(name="start", description="Lock sign-ups and generate the bracket.")
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


@tournament_group.command(name="report", description="Record the winner of a match.")
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


@tournament_group.command(name="bracket", description="Show the current bracket for a tournament.")
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


def build_voice_activity_embed(guild: discord.Guild, cfg: dict, top_n: int = 10) -> discord.Embed:
    minutes_map = cfg.get("voice_minutes", {})
    since_str = cfg.get("voice_minutes_since")
    since = datetime.fromisoformat(since_str) if since_str else datetime.now(timezone.utc)

    embed = discord.Embed(title="🎙️ Voice Activity", color=discord.Color.dark_purple())
    embed.description = f"Counting voice time since <t:{int(since.timestamp())}:D> (<t:{int(since.timestamp())}:R>)"

    if not minutes_map:
        embed.description += "\n\nNo voice activity recorded yet this period."
        return embed

    ranked = sorted(minutes_map.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    lines = []
    for i, (user_id, mins) in enumerate(ranked, start=1):
        member = guild.get_member(int(user_id))
        name = member.mention if member else f"<@{user_id}> (left)"
        hours, remainder_mins = divmod(int(mins), 60)
        duration = f"{hours}h {remainder_mins}m" if hours else f"{remainder_mins}m"
        medal = RANK_TIER_ICONS[i - 1] if i - 1 < len(RANK_TIER_ICONS) else "▪️"
        lines.append(f"{medal} {name} — **{duration}**")
    embed.add_field(name=f"Top {len(ranked)}", value="\n".join(lines), inline=False)
    embed.set_footer(text=f"{len(minutes_map)} member(s) with recorded voice activity this period")
    return embed


@bot.tree.command(name="voiceactivity", description="Show voice channel activity — leaderboard or one person.")
@app_commands.describe(user="Show just this person's voice time (omit for the leaderboard)")
async def voiceactivity(interaction: discord.Interaction, user: discord.Member = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if user is None:
        embed = build_voice_activity_embed(interaction.guild, cfg)
        await interaction.response.send_message(embed=embed)
        return

    minutes_map = cfg.get("voice_minutes", {})
    mins = minutes_map.get(str(user.id), 0)
    hours, remainder_mins = divmod(int(mins), 60)
    duration = f"{hours}h {remainder_mins}m" if hours else f"{remainder_mins}m"
    await interaction.response.send_message(f"🎙️ {user.mention} has spent **{duration}** in voice channels this period.")


@tasks.loop(hours=24)
async def weekly_voice_activity_loop():
    now = datetime.now(timezone.utc)
    for guild in bot.guilds:
        cfg = get_guild_cfg(guild.id)
        since_str = cfg.get("voice_minutes_since")
        if not since_str:
            continue
        since = datetime.fromisoformat(since_str)
        if now - since < timedelta(days=7):
            continue

        log_channel_id = cfg.get("log_channel_id")
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                embed = build_voice_activity_embed(guild, cfg)
                embed.title = "🎙️ Weekly Voice Activity Report"
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        cfg["voice_minutes"] = {}
        cfg["voice_minutes_since"] = now.isoformat()
        save_config(config)


@tasks.loop(hours=24)
async def member_count_snapshot_loop():
    """Records one member-count data point per day per guild, for the growth
    analytics chart. There's no historical data before this feature existed —
    the chart naturally fills in day by day from whenever this first runs."""
    today = datetime.now(timezone.utc).date().isoformat()
    for guild in bot.guilds:
        cfg = get_guild_cfg(guild.id)
        history = cfg.setdefault("member_count_history", [])
        if history and history[-1]["date"] == today:
            continue  # already recorded today
        history.append({"date": today, "count": guild.member_count})
        cfg["member_count_history"] = history[-180:]  # keep roughly the last 6 months
    save_config(config)


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


async def web_tournament_create(guild_id: int, name: str, channel_id: int, actor_id: int) -> str:
    """Mirrors /tournament_create."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    channel = guild.get_channel(channel_id)
    if channel is None:
        return "❌ Couldn't find that channel."

    cfg = get_guild_cfg(guild_id)
    tournaments = cfg.setdefault("tournaments", {})
    existing = tournaments.get(name)
    if existing and existing["status"] != "complete":
        return f"❌ A tournament named **{name}** is already in progress."

    data = {"status": "signup", "players": [], "rounds": [], "channel_id": channel_id}
    tournaments[name] = data
    save_config(config)

    view = TournamentJoinView(guild_id, name)
    try:
        msg = await channel.send(embed=build_tournament_signup_embed(name, data), view=view)
        data["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        return "❌ I don't have permission to post in that channel."
    return f"✅ Tournament **{name}** created in #{channel.name} — members can join with the buttons there."


async def web_tournament_start(guild_id: int, name: str, actor_id: int) -> str:
    """Mirrors /tournament_start."""
    guild = bot.get_guild(guild_id)
    cfg = get_guild_cfg(guild_id)
    data = cfg.get("tournaments", {}).get(name)
    if not data or data["status"] != "signup":
        return f"❌ No open sign-ups found for **{name}**."
    if len(data["players"]) < 2:
        return "❌ Need at least 2 players to start."

    data["rounds"] = [make_tournament_pairings(data["players"], shuffle=True)]
    data["status"] = "in_progress"
    save_config(config)

    channel = guild.get_channel(data["channel_id"]) if guild else None
    if channel:
        try:
            await channel.send(embed=build_tournament_bracket_embed(name, data))
        except discord.Forbidden:
            pass
    return f"✅ Tournament **{name}** started with {len(data['players'])} player(s)."


async def web_tournament_report(guild_id: int, name: str, match: int, winner_id: int, actor_id: int) -> str:
    """Mirrors /tournament_report."""
    guild = bot.get_guild(guild_id)
    cfg = get_guild_cfg(guild_id)
    data = cfg.get("tournaments", {}).get(name)
    if not data or data["status"] != "in_progress":
        return f"❌ No in-progress tournament found named **{name}**."

    current_round = data["rounds"][-1]
    if match < 1 or match > len(current_round):
        return f"❌ Match number must be between 1 and {len(current_round)}."

    m = current_round[match - 1]
    if winner_id not in (m["p1"], m["p2"]):
        return "❌ That person isn't in this match."
    m["winner"] = winner_id

    if all(mm["winner"] is not None for mm in current_round):
        winners = [mm["winner"] for mm in current_round]
        if len(winners) == 1:
            data["status"] = "complete"
            data["champion"] = winners[0]
        else:
            data["rounds"].append(make_tournament_pairings(winners, shuffle=False))

    save_config(config)
    channel = guild.get_channel(data["channel_id"]) if guild else None
    if channel:
        try:
            await channel.send(embed=build_tournament_bracket_embed(name, data))
        except discord.Forbidden:
            pass
    return f"✅ Match {match} result recorded for **{name}**."


async def web_gamenight_create(guild_id: int, game: str, when_iso: str, channel_id: int, actor_id: int) -> str:
    """Mirrors /gamenight_create."""
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    try:
        when = datetime.fromisoformat(when_iso)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    except ValueError:
        return "❌ Invalid date/time."
    if when <= datetime.now(timezone.utc):
        return "❌ That time is in the past."

    cfg = get_guild_cfg(guild_id)
    next_id = cfg.get("gamenight_next_id", 1)
    cfg["gamenight_next_id"] = next_id + 1
    data = {
        "id": next_id, "game": game, "when": when.isoformat(),
        "channel_id": channel_id, "going": [], "maybe": [], "cant": [], "reminded": False,
    }
    cfg.setdefault("gamenights", {})[str(next_id)] = data
    save_config(config)

    view = GameNightRSVPView(guild_id, str(next_id))
    try:
        msg = await channel.send(embed=build_gamenight_embed(data), view=view)
        data["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        return "❌ I don't have permission to post in that channel."
    return f"✅ Game night #{next_id} scheduled in #{channel.name}."


async def web_gamenight_cancel(guild_id: int, gamenight_id: int, actor_id: int) -> str:
    """Mirrors /gamenight_cancel."""
    guild = bot.get_guild(guild_id)
    cfg = get_guild_cfg(guild_id)
    gamenights = cfg.get("gamenights", {})
    data = gamenights.pop(str(gamenight_id), None)
    if not data:
        return f"❌ No game night found with ID {gamenight_id}."
    save_config(config)

    channel = guild.get_channel(data["channel_id"]) if guild else None
    if channel and data.get("message_id"):
        try:
            msg = await channel.fetch_message(data["message_id"])
            await msg.edit(content="🚫 This game night was cancelled.", embed=None, view=None)
        except (discord.NotFound, discord.Forbidden):
            pass
    return f"✅ Cancelled game night #{gamenight_id} ({data['game']})."


async def web_mvp_start(guild_id: int, title: str, candidate_ids: list, channel_id: int, actor_id: int) -> str:
    """Mirrors /mvp_start."""
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg = get_guild_cfg(guild_id)
    if cfg.get("mvp_poll"):
        return "❌ There's already an active MVP vote. End it first."
    if not candidate_ids:
        return "❌ Pick at least one candidate."

    poll = {"title": title, "candidates": candidate_ids[:5], "votes": {}, "channel_id": channel_id}
    cfg["mvp_poll"] = poll
    save_config(config)

    view = MVPVoteView(guild, poll)
    try:
        msg = await channel.send(embed=build_mvp_embed(guild, poll), view=view)
        poll["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        return "❌ I don't have permission to post in that channel."
    return f"✅ MVP vote started: **{title}**."


async def web_mvp_end(guild_id: int, actor_id: int) -> str:
    """Mirrors /mvp_end."""
    guild = bot.get_guild(guild_id)
    cfg = get_guild_cfg(guild_id)
    poll = cfg.get("mvp_poll")
    if not poll:
        return "❌ There's no active MVP vote."

    tally = {}
    for cid in poll["votes"].values():
        tally[cid] = tally.get(cid, 0) + 1

    if not tally:
        cfg["mvp_poll"] = None
        save_config(config)
        return "ℹ️ No votes were cast — nobody to announce."

    top_votes = max(tally.values())
    winners = [cid for cid, v in tally.items() if v == top_votes]
    if len(winners) == 1:
        result = f"🏆 **{poll['title']}** MVP: <@{winners[0]}> with {top_votes} vote(s)!"
    else:
        names = ", ".join(f"<@{w}>" for w in winners)
        result = f"🏆 **{poll['title']}** ended in a tie between {names} with {top_votes} vote(s) each!"

    channel = guild.get_channel(poll["channel_id"]) if guild else None
    if channel and poll.get("message_id"):
        try:
            msg = await channel.fetch_message(poll["message_id"])
            await msg.edit(embed=build_mvp_embed(guild, poll), view=None)
        except (discord.NotFound, discord.Forbidden):
            pass
    if channel:
        try:
            await channel.send(result)
        except discord.Forbidden:
            pass

    cfg["mvp_poll"] = None
    save_config(config)
    return f"✅ MVP vote ended. {result}"


# ---------- suggestions ----------

def build_suggestion_embed(suggestion: dict) -> discord.Embed:
    status = suggestion.get("status", "pending")
    color = {"pending": discord.Color.blurple(), "approved": discord.Color.green(), "denied": discord.Color.red()}[status]
    status_label = {"pending": "🗳️ Pending", "approved": "✅ Approved", "denied": "❌ Denied"}[status]
    embed = discord.Embed(title=f"💡 Suggestion #{suggestion['id']}", description=suggestion["message"], color=color)
    embed.add_field(name="👍", value=str(len(suggestion.get("upvotes", []))), inline=True)
    embed.add_field(name="👎", value=str(len(suggestion.get("downvotes", []))), inline=True)
    embed.add_field(name="Status", value=status_label, inline=True)
    embed.set_footer(text=f"Suggested by user ID {suggestion['user_id']}")
    return embed


class SuggestionView(discord.ui.View):
    def __init__(self, guild_id: int, suggestion_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.suggestion_id = suggestion_id

    async def _get_suggestion(self):
        cfg = get_guild_cfg(self.guild_id)
        return cfg.get("suggestions", {}).get(str(self.suggestion_id))

    @discord.ui.button(label="Upvote", style=discord.ButtonStyle.success, emoji="👍")
    async def upvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        suggestion = await self._get_suggestion()
        if not suggestion or suggestion.get("status") != "pending":
            await interaction.response.send_message("❌ This suggestion is no longer open.", ephemeral=True)
            return
        uid = interaction.user.id
        suggestion.setdefault("downvotes", [])
        if uid in suggestion["downvotes"]:
            suggestion["downvotes"].remove(uid)
        upvotes = suggestion.setdefault("upvotes", [])
        if uid in upvotes:
            upvotes.remove(uid)
        else:
            upvotes.append(uid)
        save_config(config)
        await interaction.response.edit_message(embed=build_suggestion_embed(suggestion))

    @discord.ui.button(label="Downvote", style=discord.ButtonStyle.danger, emoji="👎")
    async def downvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        suggestion = await self._get_suggestion()
        if not suggestion or suggestion.get("status") != "pending":
            await interaction.response.send_message("❌ This suggestion is no longer open.", ephemeral=True)
            return
        uid = interaction.user.id
        suggestion.setdefault("upvotes", [])
        if uid in suggestion["upvotes"]:
            suggestion["upvotes"].remove(uid)
        downvotes = suggestion.setdefault("downvotes", [])
        if uid in downvotes:
            downvotes.remove(uid)
        else:
            downvotes.append(uid)
        save_config(config)
        await interaction.response.edit_message(embed=build_suggestion_embed(suggestion))

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.secondary, emoji="✅", row=1)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_authorized(interaction):
            await interaction.response.send_message("❌ You don't have permission to do that.", ephemeral=True)
            return
        suggestion = await self._get_suggestion()
        if not suggestion:
            await interaction.response.send_message("❌ Suggestion not found.", ephemeral=True)
            return
        suggestion["status"] = "approved"
        save_config(config)
        await interaction.response.edit_message(embed=build_suggestion_embed(suggestion), view=self)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.secondary, emoji="❌", row=1)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_authorized(interaction):
            await interaction.response.send_message("❌ You don't have permission to do that.", ephemeral=True)
            return
        suggestion = await self._get_suggestion()
        if not suggestion:
            await interaction.response.send_message("❌ Suggestion not found.", ephemeral=True)
            return
        suggestion["status"] = "denied"
        save_config(config)
        await interaction.response.edit_message(embed=build_suggestion_embed(suggestion), view=self)


@bot.tree.command(name="suggest", description="Submit a suggestion for staff and the community to vote on.")
@app_commands.describe(message="Your suggestion")
async def suggest(interaction: discord.Interaction, message: str):
    cfg = get_guild_cfg(interaction.guild_id)
    channel_id = cfg.get("suggestions_channel_id")
    if not channel_id:
        await interaction.response.send_message("❌ No suggestions channel has been set up yet. Ask an admin to run /setsuggestionschannel.", ephemeral=True)
        return
    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("❌ The configured suggestions channel no longer exists.", ephemeral=True)
        return

    next_id = cfg.get("suggestion_next_id", 1)
    cfg["suggestion_next_id"] = next_id + 1
    suggestion = {
        "id": next_id, "user_id": interaction.user.id, "message": message, "status": "pending",
        "upvotes": [], "downvotes": [], "created_at": datetime.now(timezone.utc).isoformat(),
    }
    cfg.setdefault("suggestions", {})[str(next_id)] = suggestion
    save_config(config)

    view = SuggestionView(interaction.guild_id, next_id)
    try:
        msg = await channel.send(embed=build_suggestion_embed(suggestion), view=view)
        suggestion["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to post in the suggestions channel.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Suggestion #{next_id} posted in {channel.mention}!", ephemeral=True)


@bot.tree.command(name="setsuggestionschannel", description="Set the channel where suggestions get posted.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel for suggestions (omit to disable)")
async def setsuggestionschannel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    cfg = get_guild_cfg(interaction.guild_id)
    if channel is None:
        cfg.pop("suggestions_channel_id", None)
        save_config(config)
        await interaction.response.send_message("✅ Suggestions disabled.", ephemeral=True)
        return
    cfg["suggestions_channel_id"] = channel.id
    save_config(config)
    await interaction.response.send_message(f"✅ Suggestions will now be posted in {channel.mention}.", ephemeral=True)


async def web_set_suggestions_channel(guild_id: int, channel_id, actor_id: int) -> str:
    """Mirrors /setsuggestionschannel."""
    cfg = get_guild_cfg(guild_id)
    if channel_id is None:
        cfg.pop("suggestions_channel_id", None)
        save_config(config)
        return "✅ Suggestions disabled."
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if channel is None:
        return "❌ Couldn't find that channel."
    cfg["suggestions_channel_id"] = channel_id
    save_config(config)
    return f"✅ Suggestions will now be posted in #{channel.name}."


async def web_suggestion_set_status(guild_id: int, suggestion_id: int, status: str, actor_id: int) -> str:
    """Approve or deny a suggestion from the web dashboard."""
    guild = bot.get_guild(guild_id)
    cfg = get_guild_cfg(guild_id)
    suggestion = cfg.get("suggestions", {}).get(str(suggestion_id))
    if not suggestion:
        return "❌ Suggestion not found."
    suggestion["status"] = status
    save_config(config)

    if guild:
        channel_id = cfg.get("suggestions_channel_id")
        channel = guild.get_channel(channel_id) if channel_id else None
        if channel and suggestion.get("message_id"):
            try:
                msg = await channel.fetch_message(suggestion["message_id"])
                view = SuggestionView(guild_id, suggestion_id) if status == "pending" else None
                await msg.edit(embed=build_suggestion_embed(suggestion), view=view)
            except (discord.NotFound, discord.Forbidden):
                pass

    return f"✅ Suggestion #{suggestion_id} marked {status}."


# ---------- giveaways ----------

def build_giveaway_embed(giveaway: dict, ended: bool = False) -> discord.Embed:
    end_dt = datetime.fromisoformat(giveaway["end_time"])
    color = discord.Color.gold() if not ended else discord.Color.dark_grey()
    title = f"🎉 GIVEAWAY: {giveaway['prize']}" + (" (ENDED)" if ended else "")
    embed = discord.Embed(title=title, color=color)
    if not ended:
        embed.description = f"Click **Enter** below to join!\nEnds: <t:{int(end_dt.timestamp())}:R>"
    embed.add_field(name="Winners", value=str(giveaway["winner_count"]), inline=True)
    embed.add_field(name="Entrants", value=str(len(giveaway.get("entrants", []))), inline=True)
    return embed


class GiveawayEnterView(discord.ui.View):
    def __init__(self, guild_id: int, giveaway_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="Enter 🎉", style=discord.ButtonStyle.success)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_guild_cfg(self.guild_id)
        giveaway = cfg.get("giveaways", {}).get(str(self.giveaway_id))
        if not giveaway or giveaway.get("ended"):
            await interaction.response.send_message("❌ This giveaway has ended.", ephemeral=True)
            return
        entrants = giveaway.setdefault("entrants", [])
        uid = interaction.user.id
        if uid in entrants:
            entrants.remove(uid)
            save_config(config)
            await interaction.response.send_message("↩️ You've left the giveaway.", ephemeral=True)
        else:
            entrants.append(uid)
            save_config(config)
            await interaction.response.send_message("🎉 You're entered! Good luck.", ephemeral=True)
        try:
            await interaction.message.edit(embed=build_giveaway_embed(giveaway))
        except discord.Forbidden:
            pass


async def end_giveaway(guild_id: int, giveaway_id: int) -> str:
    """Picks winners and announces them. Shared by the auto-end loop and manual /giveaway_end."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    cfg = get_guild_cfg(guild_id)
    giveaway = cfg.get("giveaways", {}).get(str(giveaway_id))
    if not giveaway:
        return "❌ Giveaway not found."
    if giveaway.get("ended"):
        return "ℹ️ This giveaway already ended."

    entrants = giveaway.get("entrants", [])
    winner_count = min(giveaway["winner_count"], len(entrants))
    winners = random.sample(entrants, winner_count) if winner_count > 0 else []
    giveaway["ended"] = True
    giveaway["winners"] = winners
    save_config(config)

    channel = guild.get_channel(giveaway["channel_id"])
    if channel and giveaway.get("message_id"):
        try:
            msg = await channel.fetch_message(giveaway["message_id"])
            await msg.edit(embed=build_giveaway_embed(giveaway, ended=True), view=None)
        except (discord.NotFound, discord.Forbidden):
            pass

    if channel:
        try:
            if winners:
                mentions = ", ".join(f"<@{w}>" for w in winners)
                await channel.send(f"🎉 Congratulations {mentions} — you won **{giveaway['prize']}**!")
            else:
                await channel.send(f"😕 No one entered the giveaway for **{giveaway['prize']}** — no winner.")
        except discord.Forbidden:
            pass

    return f"✅ Giveaway ended. {len(winners)} winner(s) picked from {len(entrants)} entrant(s)."


@tasks.loop(seconds=30)
async def giveaway_check_loop():
    now = datetime.now(timezone.utc)
    for guild_id_str in list(config.keys()):
        try:
            guild_id = int(guild_id_str)
        except ValueError:
            continue
        cfg = config.get(guild_id_str, {})
        for gid_str, giveaway in list(cfg.get("giveaways", {}).items()):
            if giveaway.get("ended"):
                continue
            end_time = datetime.fromisoformat(giveaway["end_time"])
            if now >= end_time:
                await end_giveaway(guild_id, int(gid_str))


@bot.tree.command(name="giveaway_start", description="Start a giveaway.")
@app_commands.describe(
    prize="What's being given away", duration_minutes="How long the giveaway runs, in minutes",
    winners="How many winners to pick", channel="Where to post it (defaults to this channel)",
)
async def giveaway_start(
    interaction: discord.Interaction, prize: str, duration_minutes: int, winners: int = 1,
    channel: discord.TextChannel = None,
):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if duration_minutes < 1:
        await interaction.response.send_message("❌ Duration must be at least 1 minute.", ephemeral=True)
        return
    if winners < 1:
        await interaction.response.send_message("❌ Need at least 1 winner.", ephemeral=True)
        return

    target_channel = channel or interaction.channel
    cfg = get_guild_cfg(interaction.guild_id)
    next_id = cfg.get("giveaway_next_id", 1)
    cfg["giveaway_next_id"] = next_id + 1
    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    giveaway = {
        "id": next_id, "prize": prize, "channel_id": target_channel.id,
        "end_time": end_time.isoformat(), "winner_count": winners, "entrants": [], "ended": False,
    }
    cfg.setdefault("giveaways", {})[str(next_id)] = giveaway
    save_config(config)

    view = GiveawayEnterView(interaction.guild_id, next_id)
    try:
        msg = await target_channel.send(embed=build_giveaway_embed(giveaway), view=view)
        giveaway["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to post there.", ephemeral=True)
        return

    await interaction.response.send_message(f"✅ Giveaway #{next_id} started in {target_channel.mention}!", ephemeral=True)


@bot.tree.command(name="giveaway_end", description="End a giveaway early and pick winners now.")
@app_commands.describe(giveaway_id="The giveaway's ID (shown when it was started)")
async def giveaway_end(interaction: discord.Interaction, giveaway_id: int):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    result = await end_giveaway(interaction.guild_id, giveaway_id)
    await interaction.followup.send(result, ephemeral=True)


async def web_giveaway_start(guild_id: int, prize: str, duration_minutes: int, winner_count: int, channel_id: int, actor_id: int) -> str:
    """Mirrors /giveaway_start."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    channel = guild.get_channel(channel_id)
    if channel is None:
        return "❌ Couldn't find that channel."
    if duration_minutes < 1 or winner_count < 1:
        return "❌ Duration and winner count must be at least 1."

    cfg = get_guild_cfg(guild_id)
    next_id = cfg.get("giveaway_next_id", 1)
    cfg["giveaway_next_id"] = next_id + 1
    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    giveaway = {
        "id": next_id, "prize": prize, "channel_id": channel_id,
        "end_time": end_time.isoformat(), "winner_count": winner_count, "entrants": [], "ended": False,
    }
    cfg.setdefault("giveaways", {})[str(next_id)] = giveaway
    save_config(config)

    view = GiveawayEnterView(guild_id, next_id)
    try:
        msg = await channel.send(embed=build_giveaway_embed(giveaway), view=view)
        giveaway["message_id"] = msg.id
        save_config(config)
    except discord.Forbidden:
        return "❌ I don't have permission to post in that channel."
    return f"✅ Giveaway #{next_id} started in #{channel.name}."


async def web_giveaway_end(guild_id: int, giveaway_id: int, actor_id: int) -> str:
    """Mirrors /giveaway_end."""
    return await end_giveaway(guild_id, giveaway_id)


# ---------- trivia ----------

TRIVIA_QUESTIONS = [
    ("What year was the original Minecraft released?", ["2009", "2011", "2013", "2008"], 1),
    ("In Rust, what do you need to craft a bow?", ["Wood + String", "Wood only", "Metal + Wood", "Cloth + Wood"], 0),
    ("Which company developed Fortnite?", ["Valve", "Epic Games", "Riot Games", "Blizzard"], 1),
    ("What does 'GG' mean in gaming?", ["Great Game", "Good Game", "Go Go", "Great Guy"], 1),
    ("What is the best-selling video game of all time?", ["Tetris", "Minecraft", "GTA V", "Wii Sports"], 1),
    ("Which console was released first?", ["Xbox", "PlayStation", "Nintendo 64", "Sega Genesis"], 3),
    ("What does 'FPS' stand for in gaming?", ["Frames Per Second / First Person Shooter", "Fast Paced Strategy", "Final Player Score", "Free Play Server"], 0),
    ("In Discord, what's the maximum length of a server name?", ["50 characters", "100 characters", "32 characters", "20 characters"], 1),
    ("Which game popularized the Battle Royale genre?", ["Fortnite", "PUBG", "Apex Legends", "Warzone"], 1),
    ("What programming language is Minecraft's Java Edition written in?", ["C++", "Python", "Java", "C#"], 2),
    ("How many players are on a standard Rust server wipe day typically highest?", ["It varies wildly by server size", "Always exactly 100", "Always exactly 50", "Always exactly 200"], 0),
    ("What year was Discord founded?", ["2013", "2015", "2017", "2011"], 1),
    ("Which of these is NOT a Minecraft mob?", ["Creeper", "Enderman", "Grubber", "Skeleton"], 2),
    ("What's the max level in vanilla Minecraft enchanting normally?", ["Level 30", "Level 50", "Level 100", "Level 20"], 0),
    ("In Rust, what resource is needed to research most items?", ["Scrap", "Wood", "Stone", "Metal Fragments"], 0),
    ("What does 'AFK' stand for?", ["Away From Keyboard", "Always Fighting Killers", "Attack From Kill-zone", "After Final Kill"], 0),
    ("Which game engine does Fortnite use?", ["Unity", "Unreal Engine", "Source", "CryEngine"], 1),
    ("What's the rarest ore color-coded in Minecraft (pre-1.17)?", ["Diamond", "Emerald", "Netherite", "Gold"], 1),
    ("How many hearts does a default Minecraft player have?", ["10", "20 (health points, 10 hearts)", "15", "25"], 1),
    ("What was the first ever video game widely credited as such?", ["Pong", "Tennis for Two", "Spacewar!", "Pac-Man"], 1),
]


class TriviaView(discord.ui.View):
    def __init__(self, guild_id: int, correct_index: int, channel_id: int, message_id_holder: dict):
        super().__init__(timeout=20)
        self.guild_id = guild_id
        self.correct_index = correct_index
        self.channel_id = channel_id
        self.message_id_holder = message_id_holder
        self.answered_by = None
        labels = ["🅰️", "🅱️", "🅲️", "🅳️"]
        for i in range(4):
            button = discord.ui.Button(label=labels[i], style=discord.ButtonStyle.primary)
            button.callback = self._make_callback(i)
            self.add_item(button)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            if self.answered_by is not None:
                await interaction.response.send_message("❌ Someone already answered this one!", ephemeral=True)
                return
            self.answered_by = interaction.user
            for item in self.children:
                item.disabled = True
            if index == self.correct_index:
                cfg = get_guild_cfg(self.guild_id)
                scores = cfg.setdefault("trivia_scores", {})
                uid = str(interaction.user.id)
                scores[uid] = scores.get(uid, 0) + 1
                save_config(config)
                await interaction.response.edit_message(
                    content=f"✅ **{interaction.user.display_name}** got it right! (+1 point)", view=self
                )
            else:
                await interaction.response.edit_message(
                    content=f"❌ **{interaction.user.display_name}** guessed wrong. The correct answer was option {['🅰️','🅱️','🅲️','🅳️'][self.correct_index]}.",
                    view=self,
                )
            self.stop()
        return callback

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        guild = bot.get_guild(self.guild_id)
        channel = guild.get_channel(self.channel_id) if guild else None
        message_id = self.message_id_holder.get("id")
        if channel and message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(content=f"⏱️ Time's up! Nobody answered in time.", view=self)
            except (discord.NotFound, discord.Forbidden):
                pass


@bot.tree.command(name="trivia", description="Answer a trivia question — first correct answer wins a point!")
async def trivia(interaction: discord.Interaction):
    question, options, correct_index = random.choice(TRIVIA_QUESTIONS)
    embed = discord.Embed(title="🧠 Trivia Time!", description=question, color=discord.Color.purple())
    labels = ["🅰️", "🅱️", "🅲️", "🅳️"]
    for i, opt in enumerate(options):
        embed.add_field(name=labels[i], value=opt, inline=False)
    embed.set_footer(text="You have 20 seconds to answer!")

    message_id_holder = {}
    view = TriviaView(interaction.guild_id, correct_index, interaction.channel_id, message_id_holder)
    await interaction.response.send_message(embed=embed, view=view)
    sent = await interaction.original_response()
    message_id_holder["id"] = sent.id


@bot.tree.command(name="trivialeaderboard", description="Show the top trivia scorers in this server.")
async def trivialeaderboard(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    scores = cfg.get("trivia_scores", {})
    if not scores:
        await interaction.response.send_message("No trivia games played yet — run /trivia to start!", ephemeral=True)
        return

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:10]
    lines = []
    for i, (uid, score) in enumerate(ranked, start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"Unknown ({uid})"
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        lines.append(f"{medal} {name} — {score} point(s)")

    embed = discord.Embed(title="🧠 Trivia Leaderboard", description="\n".join(lines), color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)


# ---------- custom commands ----------

@bot.tree.command(name="addcustomcommand", description="Add a custom trigger word — the bot replies automatically when someone types it.")
@app_commands.describe(trigger="The exact word/phrase that triggers this (not case-sensitive)", response="What the bot replies with")
async def addcustomcommand(interaction: discord.Interaction, trigger: str, response: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    custom_commands = cfg.setdefault("custom_commands", {})
    trigger_key = trigger.lower().strip()
    if not trigger_key:
        await interaction.response.send_message("❌ Trigger can't be empty.", ephemeral=True)
        return
    is_update = trigger_key in custom_commands
    custom_commands[trigger_key] = response
    save_config(config)
    verb = "Updated" if is_update else "Added"
    await interaction.response.send_message(f"✅ {verb} custom command: when someone types `{trigger_key}`, I'll reply with your message.", ephemeral=True)


@bot.tree.command(name="removecustomcommand", description="Remove a custom trigger word.")
@app_commands.describe(trigger="The trigger word to remove")
async def removecustomcommand(interaction: discord.Interaction, trigger: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    custom_commands = cfg.get("custom_commands", {})
    trigger_key = trigger.lower().strip()
    if trigger_key not in custom_commands:
        await interaction.response.send_message(f"❌ No custom command found for `{trigger_key}`.", ephemeral=True)
        return
    del custom_commands[trigger_key]
    save_config(config)
    await interaction.response.send_message(f"✅ Removed custom command `{trigger_key}`.", ephemeral=True)


@bot.tree.command(name="listcustomcommands", description="Show all configured custom commands.")
async def listcustomcommands(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    custom_commands = cfg.get("custom_commands", {})
    if not custom_commands:
        await interaction.response.send_message("No custom commands configured yet.", ephemeral=True)
        return
    lines = [f"**{trigger}** → {response[:80]}{'...' if len(response) > 80 else ''}" for trigger, response in custom_commands.items()]
    await interaction.response.send_message("\n".join(lines)[:2000], ephemeral=True)


async def web_add_custom_command(guild_id: int, trigger: str, response: str, actor_id: int) -> str:
    """Mirrors /addcustomcommand."""
    cfg = get_guild_cfg(guild_id)
    custom_commands = cfg.setdefault("custom_commands", {})
    trigger_key = trigger.lower().strip()
    if not trigger_key:
        return "❌ Trigger can't be empty."
    is_update = trigger_key in custom_commands
    custom_commands[trigger_key] = response
    save_config(config)
    verb = "Updated" if is_update else "Added"
    return f"✅ {verb} custom command: `{trigger_key}`."


async def web_remove_custom_command(guild_id: int, trigger: str, actor_id: int) -> str:
    """Mirrors /removecustomcommand."""
    cfg = get_guild_cfg(guild_id)
    custom_commands = cfg.get("custom_commands", {})
    trigger_key = trigger.lower().strip()
    if trigger_key not in custom_commands:
        return f"❌ No custom command found for `{trigger_key}`."
    del custom_commands[trigger_key]
    save_config(config)
    return f"✅ Removed custom command `{trigger_key}`."


automod_group = app_commands.Group(name="automod", description="Auto-moderation settings")
bot.tree.add_command(automod_group)


@automod_group.command(name="toggle", description="Turn auto-moderation on or off.")
@app_commands.describe(enabled="Turn auto-mod on or off")
async def automod_toggle(interaction: discord.Interaction, enabled: bool):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    cfg["automod_enabled"] = enabled
    save_config(config)
    await interaction.response.send_message(f"✅ Auto-mod is now {'ON' if enabled else 'OFF'}.", ephemeral=True)


@automod_group.command(name="settings", description="Configure auto-mod behavior.")
@app_commands.describe(
    block_invites="Automatically delete Discord invite links",
    block_spam="Automatically delete rapid repeated messages",
    action="What happens in addition to deleting the message",
    exempt_role="Role that's exempt from auto-mod (staff, etc.) — omit to leave unchanged",
)
@app_commands.choices(action=[
    app_commands.Choice(name="Delete only", value="delete_only"),
    app_commands.Choice(name="Delete + warn", value="delete_and_warn"),
    app_commands.Choice(name="Delete + 10 minute timeout", value="delete_and_timeout"),
])
async def automod_settings(
    interaction: discord.Interaction, block_invites: bool = None, block_spam: bool = None,
    action: app_commands.Choice[str] = None, exempt_role: discord.Role = None,
):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    changes = []
    if block_invites is not None:
        cfg["automod_block_invites"] = block_invites
        changes.append(f"block invites: {block_invites}")
    if block_spam is not None:
        cfg["automod_block_spam"] = block_spam
        changes.append(f"block spam: {block_spam}")
    if action is not None:
        cfg["automod_action"] = action.value
        changes.append(f"action: {action.name}")
    if exempt_role is not None:
        cfg["automod_exempt_role_id"] = exempt_role.id
        changes.append(f"exempt role: @{exempt_role.name}")
    save_config(config)
    if not changes:
        await interaction.response.send_message("ℹ️ No changes made — pass at least one setting to update.", ephemeral=True)
        return
    await interaction.response.send_message(f"✅ Updated: {', '.join(changes)}.", ephemeral=True)


@automod_group.command(name="addword", description="Add a word to the auto-mod blocked word list.")
@app_commands.describe(word="The word to block")
async def automod_addword(interaction: discord.Interaction, word: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    words = cfg.setdefault("automod_banned_words", [])
    word_lower = word.lower().strip()
    if word_lower in words:
        await interaction.response.send_message(f"ℹ️ `{word_lower}` is already blocked.", ephemeral=True)
        return
    words.append(word_lower)
    save_config(config)
    await interaction.response.send_message(f"✅ Added `{word_lower}` to the blocked word list.", ephemeral=True)


@automod_group.command(name="removeword", description="Remove a word from the auto-mod blocked word list.")
@app_commands.describe(word="The word to unblock")
async def automod_removeword(interaction: discord.Interaction, word: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    words = cfg.get("automod_banned_words", [])
    word_lower = word.lower().strip()
    if word_lower not in words:
        await interaction.response.send_message(f"❌ `{word_lower}` isn't on the blocked list.", ephemeral=True)
        return
    words.remove(word_lower)
    save_config(config)
    await interaction.response.send_message(f"✅ Removed `{word_lower}` from the blocked word list.", ephemeral=True)


@automod_group.command(name="listwords", description="Show the auto-mod blocked word list.")
async def automod_listwords(interaction: discord.Interaction):
    cfg = get_guild_cfg(interaction.guild_id)
    words = cfg.get("automod_banned_words", [])
    if not words:
        await interaction.response.send_message("No blocked words configured.", ephemeral=True)
        return
    await interaction.response.send_message(f"Blocked words: {', '.join(f'`{w}`' for w in words)}", ephemeral=True)


async def web_automod_toggle(guild_id: int, enabled: bool, actor_id: int) -> str:
    """Mirrors /automod_toggle."""
    cfg = get_guild_cfg(guild_id)
    cfg["automod_enabled"] = enabled
    save_config(config)
    return f"✅ Auto-mod is now {'ON' if enabled else 'OFF'}."


async def web_automod_settings(guild_id: int, block_invites: bool, block_spam: bool, action: str, exempt_role_id, actor_id: int) -> str:
    """Mirrors /automod_settings."""
    cfg = get_guild_cfg(guild_id)
    cfg["automod_block_invites"] = block_invites
    cfg["automod_block_spam"] = block_spam
    cfg["automod_action"] = action
    if exempt_role_id is None:
        cfg.pop("automod_exempt_role_id", None)
    else:
        cfg["automod_exempt_role_id"] = exempt_role_id
    save_config(config)
    return "✅ Auto-mod settings saved."


async def web_automod_add_word(guild_id: int, word: str, actor_id: int) -> str:
    """Mirrors /automod_addword."""
    cfg = get_guild_cfg(guild_id)
    words = cfg.setdefault("automod_banned_words", [])
    word_lower = word.lower().strip()
    if not word_lower:
        return "❌ Enter a word."
    if word_lower in words:
        return f"ℹ️ `{word_lower}` is already blocked."
    words.append(word_lower)
    save_config(config)
    return f"✅ Added `{word_lower}` to the blocked word list."


async def web_automod_remove_word(guild_id: int, word: str, actor_id: int) -> str:
    """Mirrors /automod_removeword."""
    cfg = get_guild_cfg(guild_id)
    words = cfg.get("automod_banned_words", [])
    word_lower = word.lower().strip()
    if word_lower not in words:
        return f"❌ `{word_lower}` isn't on the blocked list."
    words.remove(word_lower)
    save_config(config)
    return f"✅ Removed `{word_lower}`."



crosspost_group = app_commands.Group(name="crosspost", description="Mirror messages between servers")
bot.tree.add_command(crosspost_group)


@crosspost_group.command(name="add", description="Mirror messages from THIS channel to a channel in another server the bot is also in.")
@app_commands.describe(destination_channel_id="The channel ID to mirror into (right-click the channel in the other server → Copy Channel ID)")
async def crosspost_add(interaction: discord.Interaction, destination_channel_id: str):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
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


@crosspost_group.command(name="remove", description="Stop mirroring THIS channel to another server.")
async def crosspost_remove(interaction: discord.Interaction):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    cfg = get_guild_cfg(interaction.guild_id)
    crossposts = cfg.setdefault("crossposts", {})
    if str(interaction.channel_id) not in crossposts:
        await interaction.response.send_message("ℹ️ This channel isn't currently being mirrored anywhere.", ephemeral=True)
        return

    crossposts.pop(str(interaction.channel_id))
    save_config(config)
    await interaction.response.send_message("✅ This channel will no longer be mirrored.", ephemeral=True)


@crosspost_group.command(name="list", description="Show all cross-posting mirrors set up in this server.")
async def crosspost_list(interaction: discord.Interaction):
    if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
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
    if not can_use_ban(interaction.guild_id, interaction.user):
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
    await _maybe_sync_rust_ban(interaction.guild_id, user.id, reason)


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


@bot.tree.command(name="untimeout", description="Remove a member's timeout early.")
@app_commands.describe(user="The member to remove the timeout from", reason="Why you're removing it")
async def untimeout(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason given"):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ I don't have permission to manage timeouts.", ephemeral=True)
        return
    if user.timed_out_until is None:
        await interaction.response.send_message(f"ℹ️ {user.mention} isn't currently timed out.", ephemeral=True)
        return

    try:
        await user.timeout(None, reason=f"By {interaction.user} via /untimeout: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to remove that member's timeout.", ephemeral=True)
        return

    dm_sent = await dm_notify(
        interaction.guild, user,
        title="🔊 Your timeout was removed",
        color=discord.Color.green(),
        fields={"Reason": reason},
    )
    note = "" if dm_sent else " (couldn't DM them)"
    await interaction.response.send_message(f"✅ Removed timeout from {user.mention}.{note}", ephemeral=True)
    await log_movement(
        interaction.guild, member=user, target="timeout removed", reason=reason, moderator=interaction.user
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


@bot.tree.command(name="slowmode", description="Set slowmode delay for this channel.")
@app_commands.describe(seconds="Seconds between messages per person — omit or use 0 to disable, max 21600")
async def slowmode(interaction: discord.Interaction, seconds: int = 0):
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
        await interaction.response.send_message("✅ Slowmode disabled.", ephemeral=True)
    else:
        await interaction.response.send_message(f"✅ Slowmode set to {seconds} second(s).", ephemeral=True)


# ---------- admin utility ----------

@bot.tree.command(name="refreshroster", description="Force the live roster and server stats embeds to update right now.")
async def refreshroster(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        await refresh_roster_message(interaction.guild)
        await refresh_server_stats_message(interaction.guild)
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ Couldn't refresh the embeds: {e}", ephemeral=True)
        return
    await interaction.followup.send("✅ Roster and stats embeds refreshed.", ephemeral=True)


async def web_refresh_roster(guild_id: int, actor_id: int) -> str:
    """Mirrors /refreshroster."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return "❌ Server not found."
    try:
        await refresh_roster_message(guild)
        await refresh_server_stats_message(guild)
    except discord.HTTPException as e:
        return f"❌ Couldn't refresh the embeds: {e}"
    return "✅ Roster and stats embeds refreshed."


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


DISCORD_AUDIT_ACTION_LABELS = {
    discord.AuditLogAction.kick: "👢 Kick",
    discord.AuditLogAction.ban: "🔨 Ban",
    discord.AuditLogAction.unban: "✅ Unban",
    discord.AuditLogAction.member_role_update: "🎭 Role Change",
    discord.AuditLogAction.member_update: "✏️ Member Update",
    discord.AuditLogAction.channel_create: "➕ Channel Created",
    discord.AuditLogAction.channel_delete: "🗑️ Channel Deleted",
    discord.AuditLogAction.channel_update: "✏️ Channel Updated",
    discord.AuditLogAction.role_create: "➕ Role Created",
    discord.AuditLogAction.role_delete: "🗑️ Role Deleted",
    discord.AuditLogAction.role_update: "✏️ Role Updated",
    discord.AuditLogAction.message_delete: "🗑️ Message Deleted",
    discord.AuditLogAction.message_bulk_delete: "🗑️ Messages Bulk Deleted",
    discord.AuditLogAction.invite_create: "🔗 Invite Created",
    discord.AuditLogAction.invite_delete: "🔗 Invite Deleted",
    discord.AuditLogAction.emoji_create: "😀 Emoji Added",
    discord.AuditLogAction.emoji_delete: "😀 Emoji Removed",
    discord.AuditLogAction.webhook_create: "🔌 Webhook Created",
    discord.AuditLogAction.webhook_update: "🔌 Webhook Updated",
    discord.AuditLogAction.bot_add: "🤖 Bot Added",
}


async def fetch_discord_audit_log(guild_id: int, limit: int = 50) -> dict:
    """Pulls Discord's own native audit log — bans/kicks/channel changes/role
    changes/etc — not just this bot's own action history. Returns
    {"entries": [...], "error": None} or {"entries": [], "error": "..."}."""
    guild = bot.get_guild(guild_id)
    if guild is None:
        return {"entries": [], "error": "Server not found."}
    if not guild.me.guild_permissions.view_audit_log:
        return {"entries": [], "error": "I don't have the 'View Audit Log' permission in this server."}

    try:
        entries = []
        async for entry in guild.audit_logs(limit=limit):
            label = DISCORD_AUDIT_ACTION_LABELS.get(entry.action, str(entry.action).replace("AuditLogAction.", "").replace("_", " ").title())
            target_label = str(entry.target) if entry.target else "—"
            entries.append({
                "action": label,
                "moderator": str(entry.user) if entry.user else "Unknown",
                "moderator_id": entry.user.id if entry.user else None,
                "target": target_label,
                "reason": entry.reason or "",
                "timestamp": entry.created_at.isoformat(),
            })
        return {"entries": entries, "error": None}
    except discord.Forbidden:
        return {"entries": [], "error": "I don't have permission to view this server's audit log."}
    except discord.HTTPException as e:
        return {"entries": [], "error": str(e)}


@bot.tree.command(name="discordauditlog", description="Show Discord's own audit log (bans, kicks, channel/role changes, etc).")
@app_commands.describe(limit="How many entries to show (max 50)")
async def discordauditlog(interaction: discord.Interaction, limit: int = 20):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    result = await fetch_discord_audit_log(interaction.guild_id, min(limit, 50))
    if result["error"]:
        await interaction.followup.send(f"❌ {result['error']}", ephemeral=True)
        return

    embed = discord.Embed(title="🗂️ Discord Audit Log", color=discord.Color.dark_grey())
    if not result["entries"]:
        embed.description = "No recent audit log entries."
    else:
        lines = []
        for e in result["entries"][:20]:
            ts = datetime.fromisoformat(e["timestamp"])
            reason = f" — {e['reason']}" if e["reason"] else ""
            lines.append(f"{e['action']} → **{e['target']}**{reason} • by {e['moderator']} • <t:{int(ts.timestamp())}:R>")
        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Showing {min(len(result['entries']), 20)} of {len(result['entries'])} fetched entries")
    await interaction.followup.send(embed=embed, ephemeral=True)



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
    "🦀 Rust Server": [
        ("/rust setserver", "Connect to your Rust server (status + optional RCON)"),
        ("/rust setchatchannel", "Bridge Discord chat with in-game chat"),
        ("/rust setstatuschannel", "Live server status embed (includes seed/size/RustMaps link)"),
        ("/rust status", "Show current server status"),
        ("/rust command", "Run an RCON command on the server"),
        ("/rust setpopalert", "(admin) Ping a role at a population threshold"),
        ("/rust setwipe / wipe", "Schedule and check a weekly wipe countdown"),
    ],
    "⛏️ Minecraft Server": [
        ("/minecraft setserver", "Connect to your Minecraft server (status + optional RCON)"),
        ("/minecraft setstatuschannel", "Live server status embed"),
        ("/minecraft status", "Show current server status"),
        ("/minecraft command", "Run an RCON command on the server"),
    ],
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
        ("/rosteraddall", "Put EVERY server member on the roster at once"),
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
        ("/suggest / setsuggestionschannel", "Community suggestions with voting + staff approval"),
        ("/giveaway_start / _end", "Run a giveaway with a random winner picker"),
        ("/setpromotioncooldownrole / _putoncooldown / _removecooldown", "Role-based promotion/demotion cooldown"),
    ],
    "🛡️ Moderation": [
        ("/kick", "Kick a member (confirmation required)"),
        ("/ban", "Ban a member (confirmation required)"),
        ("/timeout", "Temporarily mute a member"),
        ("/untimeout", "Remove a member's timeout early"),
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
    "🎮 Fun": [
        ("/trivia", "Answer a trivia question — first correct answer wins a point"),
        ("/trivialeaderboard", "Show the top trivia scorers"),
    ],
    "💬 Custom Commands": [
        ("/addcustomcommand", "Add a trigger word the bot auto-replies to"),
        ("/removecustomcommand", "Remove a custom trigger word"),
        ("/listcustomcommands", "Show all configured custom commands"),
    ],
    "🛡️ Auto-Moderation": [
        ("/automod_toggle", "(admin) Turn auto-mod on or off"),
        ("/automod_settings", "(admin) Configure invites/spam/action/exempt role"),
        ("/automod_addword / _removeword / _listwords", "Manage the blocked word list"),
    ],
    "🎙️ Voice & Tickets": [
        ("/voiceactivity", "Voice channel activity leaderboard or one person"),
        ("/setticketautoclose", "(admin) Auto-remind/close tickets that go quiet"),
        ("/namehistory", "Show a member's nickname/username change history"),
    ],
    "🚩 Reports": [
        ("/report", "Privately report a member to staff"),
        ("/setreportschannel", "(admin) Set the private channel for reports"),
    ],
    "🗂️ Discord Audit Log": [
        ("/discordauditlog", "Show Discord's own audit log (bans, kicks, channel/role changes)"),
        ("/setviewerrole", "(admin) Role that gets view-only web dashboard access"),
    ],
    "🎮 Whitelist Auto-Sync": [
        ("/linksteam", "Link your SteamID for Rust whitelist auto-sync"),
        ("/linkminecraft", "Link your Minecraft username for whitelist auto-sync"),
        ("/setwhitelistsync", "(admin) Auto-whitelist on Rust/Minecraft at a rank threshold"),
    ],
    "🎁 Rank Bonus Roles": [
        ("/addrankbonusrole", "Auto-grant an extra role when someone reaches a rank"),
        ("/removerankbonusrole", "Stop auto-granting that extra role"),
        ("/listrankbonusroles", "Show which extra roles get auto-granted at each rank"),
    ],
    "🔧 Utility": [
        ("/afk", "Mark yourself AFK"),
        ("/weblogin", "Get a one-time code to log into the web dashboard"),
        ("/setweblogincommandrole", "(admin) Restrict who can run /weblogin"),
        ("/setbotstatus", "(admin) Rotate the bot's Discord status through live stats"),
        ("/announce", "Post a formatted announcement to one channel"),
        ("/massannounce", "Post + speak an announcement everywhere (text + VC)"),
        ("/setvcgreeting / removevcgreeting", "Bot speaks a custom greeting when someone joins a VC"),
        ("/setbirthday / mybirthday / removebirthday", "Set your birthday"),
        ("/setbirthdayrole / _channel", "(admin) Auto-role + shoutout on birthdays"),
        ("/showcase add / remove / setchannel / list", "Self-assignable role showcase with a live channel"),
        ("/setticketchannel / /ticket", "Support ticket system — private channel per member"),
        ("/addticketcategory / _remove / _list", "Multiple ticket types, each with their own category"),
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
@backup.error
@setbirthdayrole.error
@setbirthdaychannel.error
@setticketchannel.error
@setweblogincommandrole.error
@setbotstatus.error
@setsuggestionschannel.error
@setpromotioncooldownrole.error
@setticketautoclose.error
@setreportschannel.error
@setviewerrole.error
@setbanrole.error
@setwhitelistsync.error
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
    start_web_app(
        bot, config, save_config, get_guild_cfg,
        web_give_role, web_remove_role, web_roster_add, web_roster_remove,
        web_promote, web_demote, web_kick, web_ban,
        web_timeout, web_untimeout, web_warn, web_mass_add_role,
        web_mass_remove_role, web_mass_rename, web_announce, web_massannounce,
        web_showcase_add, web_showcase_remove, open_ticket, close_ticket,
        web_set_ticket_channel, web_send_dm, web_set_rust_server, web_set_rust_status_channel,
        web_get_rust_status, web_rust_command, rust_get_players, rust_kick_player,
        rust_ban_player, rust_get_banlist, rust_unban_player, web_set_rust_alert_channel,
        web_set_minecraft_server, web_set_minecraft_status_channel, web_get_minecraft_status, web_minecraft_command,
        web_set_minecraft_alert_channel, relay_incoming_webhook, web_tournament_create, web_tournament_start,
        web_tournament_report, web_gamenight_create, web_gamenight_cancel, web_mvp_start,
        web_mvp_end, web_add_ticket_category, web_remove_ticket_category, web_set_ticket_questions,
        web_get_ticket_messages, web_send_ticket_message, web_set_backup_settings, web_run_backup_now,
        redeem_web_login_code,
        minecraft_get_players, minecraft_kick_player, minecraft_ban_player, minecraft_get_banlist, minecraft_unban_player,
        web_set_bot_status,
        web_roster_add_all,
        web_set_suggestions_channel, web_suggestion_set_status,
        web_giveaway_start, web_giveaway_end,
        web_put_on_cooldown, web_remove_cooldown,
        web_add_custom_command, web_remove_custom_command,
        web_refresh_roster,
        web_automod_toggle, web_automod_settings, web_automod_add_word, web_automod_remove_word,
        web_set_ticket_autoclose,
        web_set_reports_channel, web_report_set_status,
        fetch_discord_audit_log,
        web_rust_set_wipe, web_rust_set_popalert, web_rust_set_joinleave_channel, web_rust_set_bansync,
        web_rust_set_rules, web_rust_save, web_rust_restart, web_rust_announce,
        web_rust_macro_add, web_rust_macro_remove, web_rust_macro_run,
        web_rust_announcement_add, web_rust_announcement_remove,
        web_add_rank_bonus_role, web_remove_rank_bonus_role,
        web_set_whitelist_sync,
        get_console_commands, run_console_command,
    )
    bot.run(TOKEN)
