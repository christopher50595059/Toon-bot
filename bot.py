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
  /setcooldown hours:<int>                - (admin only) require a wait between promote/demote for the same person
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

Only server admins can run the "set" commands. Only members with the
configured "manager role" (or Administrator permission) can run
/addrole and /removerole.
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

from keep_alive import keep_alive

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
                color=discord.Color.blurple(),
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

    # ---- activity tracking (for /inactive) ----
    last_active = cfg.setdefault("last_active", {})
    now = datetime.now(timezone.utc)

    # Only write to disk if it's been a while since we last recorded this
    # person — avoids a disk write on every single message in a busy server.
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


async def log_action(
    guild: discord.Guild,
    title: str,
    color: discord.Color,
    member: discord.Member,
    moderator: discord.Member,
    fields: dict = None,
):
    """Post a structured, nicely formatted log embed to the configured log channel."""
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("log_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return

    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Member", value=member.mention, inline=True)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

    embed.set_footer(text=f"User ID: {member.id}")

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass


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
    (e.g. they have DMs closed) so the caller can let the moderator know."""
    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.description = f"This happened in **{guild.name}**."

    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

    try:
        await member.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


RANK_TIER_ICONS = ["🥇", "🥈", "🥉", "🔹", "🔸", "▪️", "▪️", "▪️"]


def build_roster_embed(guild: discord.Guild) -> discord.Embed:
    cfg = get_guild_cfg(guild.id)
    roster = cfg.get("roster", [])  # list of {"user_id": int, "rank_role_id": int}
    rank_role_ids = cfg.get("ranks", [])  # ordered list of role IDs, highest first

    embed = discord.Embed(title="📋 Server Roster", color=discord.Color.blurple())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    if not roster:
        embed.description = "The roster is currently empty."
        return embed

    def member_line(index, entry):
        member = guild.get_member(entry["user_id"])
        name = member.mention if member else f"<@{entry['user_id']}> (left server)"
        return f"`{index:>2}.` {name}"

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
        label = role.mention if role else "(deleted role)"
        icon = RANK_TIER_ICONS[position] if position < len(RANK_TIER_ICONS) else "▪️"
        value = "\n".join(member_line(i, e) for i, e in enumerate(members, start=1))
        embed.add_field(name=f"{icon} {label} — {len(members)}", value=value, inline=False)

    if unranked:
        value = "\n".join(member_line(i, e) for i, e in enumerate(unranked, start=1))
        embed.add_field(name=f"❔ Unranked — {len(unranked)}", value=value, inline=False)

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

    embed = discord.Embed(title=f"📈 {guild.name} Stats", color=discord.Color.blurple())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name="Total Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Humans", value=str(humans), inline=True)
    embed.add_field(name="Bots", value=str(bots), inline=True)
    embed.add_field(name="Roster Size", value=str(len(roster)), inline=True)
    embed.add_field(name="Server Boosts", value=str(guild.premium_subscription_count or 0), inline=True)
    embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)

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


def action_embed(title: str, description: str, color: discord.Color, member: discord.Member = None) -> discord.Embed:
    """A small, consistently-styled embed for command confirmation responses
    (as opposed to the log channel embeds, which are more detailed)."""
    embed = discord.Embed(title=title, description=description, color=color)
    if member is not None:
        embed.set_thumbnail(url=member.display_avatar.url)
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
@app_commands.describe(hours="Hours between rank changes for the same person (0 to disable)")
async def setcooldown(interaction: discord.Interaction, hours: int):
    if hours < 0:
        await interaction.response.send_message("❌ Hours can't be negative.", ephemeral=True)
        return

    cfg = get_guild_cfg(interaction.guild_id)
    cfg["cooldown_hours"] = hours
    save_config(config)

    if hours == 0:
        await interaction.response.send_message("✅ Promote/demote cooldown disabled.", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"✅ Members must now wait **{hours} hour(s)** between promotions/demotions.", ephemeral=True
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
        fields={"Role": role.mention, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "🟢 Role Given",
        f"Gave {role.mention} to {user.mention}.\n**Reason:** {reason}{note}",
        discord.Color.green(),
        member=user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        title="🟢 Role Added",
        color=discord.Color.green(),
        member=user,
        moderator=interaction.user,
        fields={"Role": role.mention, "Reason": reason},
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
        fields={"Role": role.mention, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "🔴 Role Removed",
        f"Removed {role.mention} from {user.mention}.\n**Reason:** {reason}{note}",
        discord.Color.red(),
        member=user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        title="🔴 Role Removed",
        color=discord.Color.red(),
        member=user,
        moderator=interaction.user,
        fields={"Role": role.mention, "Reason": reason},
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
        existing["rank_role_id"] = rank.id
        save_config(config)
        summary = f" ({', '.join(role_change_notes)})" if role_change_notes else ""
        dm_sent = await dm_notify(
            interaction.guild, user,
            title="📋 Your roster rank changed",
            color=discord.Color.blurple(),
            fields={"Previous Rank": old_label, "New Rank": rank.mention, "Reason": reason},
        )
        note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
        embed = action_embed(
            "📋 Rank Changed",
            f"Moved {user.mention} from {old_label} to {rank.mention}.\n**Reason:** {reason}{note}",
            discord.Color.blurple(),
            member=user,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            title="📋 Roster Rank Changed",
            color=discord.Color.blurple(),
            member=user,
            moderator=interaction.user,
            fields={"Previous Rank": old_label, "New Rank": rank.mention, "Reason": reason},
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
        color=discord.Color.blurple(),
        fields={"Rank": rank.mention, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    embed = action_embed(
        "📋 Added to Roster",
        f"Added {user.mention} to the roster and gave them {rank.mention}.\n**Reason:** {reason}{note}",
        discord.Color.blurple(),
        member=user,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        title="📋 Added to Roster",
        color=discord.Color.blurple(),
        member=user,
        moderator=interaction.user,
        fields={"Rank": rank.mention, "Reason": reason},
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
    )
    await interaction.edit_original_response(content=None, embed=embed, view=None)
    await log_action(
        interaction.guild,
        title="📋 Removed from Roster",
        color=discord.Color.orange(),
        member=user,
        moderator=interaction.user,
        fields={"Reason": reason},
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

    cooldown_hours = cfg.get("cooldown_hours", 0)
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
        fields={"Previous Rank": old_label, "New Rank": new_role.mention, "Reason": reason},
    )
    note = "\n\n*(couldn't DM them — their DMs may be closed)*" if not dm_sent else ""
    result_embed = action_embed(
        f"{dm_title.split(' ', 1)[0]} {verb}d",
        f"{verb}d {user.mention} from {old_label} to {new_role.mention}.\n**Reason:** {reason}{note}",
        dm_color,
        member=user,
    )
    if is_demote:
        await interaction.edit_original_response(content=None, embed=result_embed, view=None)
    else:
        await interaction.response.send_message(embed=result_embed, ephemeral=True)
    await log_action(
        interaction.guild,
        title=f"⬆️ {verb}d" if step < 0 else f"⬇️ {verb}d",
        color=discord.Color.gold() if step < 0 else discord.Color.dark_orange(),
        member=user,
        moderator=interaction.user,
        fields={"Previous Rank": old_label, "New Rank": new_role.mention, "Reason": reason},
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
    added, moved, skipped = 0, 0, 0

    for member in matching_members:
        existing = next((entry for entry in roster if entry["user_id"] == member.id), None)
        if existing is None:
            roster.append({"user_id": member.id, "rank_role_id": rank.id})
            record_history(interaction.guild_id, member.id, "Added to Roster", rank.mention, interaction.user.id, "Bulk import")
            added += 1
        elif existing.get("rank_role_id") != rank.id:
            old_role = interaction.guild.get_role(existing.get("rank_role_id"))
            old_label = old_role.mention if old_role else "an unknown rank"
            existing["rank_role_id"] = rank.id
            record_history(
                interaction.guild_id, member.id, "Rank Changed", f"{old_label} → {rank.mention}",
                interaction.user.id, "Bulk import",
            )
            moved += 1
        else:
            skipped += 1

    save_config(config)

    embed = discord.Embed(title="📋 Roster Import Complete", color=discord.Color.blurple())
    embed.description = f"Imported everyone with {rank.mention} onto the roster."
    embed.add_field(name="Added", value=str(added), inline=True)
    embed.add_field(name="Moved", value=str(moved), inline=True)
    embed.add_field(name="Already Correct", value=str(skipped), inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        title="📋 Roster Bulk Import",
        color=discord.Color.blurple(),
        member=interaction.user,
        moderator=interaction.user,
        fields={"Rank": rank.mention, "Added": str(added), "Moved": str(moved), "Already Correct": str(skipped)},
    )
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

    embed = discord.Embed(title="📊 Roster Stats", color=discord.Color.blurple())
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
        label = role.mention if role else "(deleted role)"
        icon = RANK_TIER_ICONS[position] if position < len(RANK_TIER_ICONS) else "▪️"
        embed.add_field(name=f"{icon} {label}", value=str(counts[rid]), inline=True)

    if unranked:
        embed.add_field(name="❔ Unranked", value=str(unranked), inline=True)

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

    entry = next((e for e in roster if e["user_id"] == user.id), None)

    embed = discord.Embed(color=discord.Color.blurple())
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_author(name=str(user), icon_url=user.display_avatar.url)

    if not entry:
        embed.description = f"{user.mention} isn't on the roster."
        await interaction.response.send_message(embed=embed)
        return

    role = interaction.guild.get_role(entry.get("rank_role_id"))
    embed.add_field(name="Current Rank", value=role.mention if role else "(deleted role)", inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="history", description="Show a member's rank/roster history.")
@app_commands.describe(user="The member to look up (defaults to you)")
async def history(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    cfg = get_guild_cfg(interaction.guild_id)
    user_history = cfg.get("history", {}).get(str(user.id), [])

    embed = discord.Embed(title=f"🕓 History for {user.display_name}", color=discord.Color.blurple())
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
        embed = discord.Embed(title=f"🏆 Tournament: {name}", color=discord.Color.blurple())

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
    embed = discord.Embed(title=f"🎮 Game Night: {data['game']}", color=discord.Color.green())
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

    embed = discord.Embed(title="🎮 Upcoming Game Nights", color=discord.Color.green())
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


# ---------- MVP voting ----------

def build_mvp_embed(guild: discord.Guild, poll: dict) -> discord.Embed:
    embed = discord.Embed(title=f"⭐ MVP Vote: {poll['title']}", color=discord.Color.gold())
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

    embed = discord.Embed(title="🔀 Cross-Posting Mirrors", color=discord.Color.blurple())
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
    keep_alive()
    bot.run(TOKEN)
