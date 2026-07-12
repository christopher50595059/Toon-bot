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

Only server admins can run the "set" commands. Only members with the
configured "manager role" (or Administrator permission) can run
/addrole and /removerole.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
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
intents.members = True  # required to look up / modify member roles

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}. Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Sync failed: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    cfg = get_guild_cfg(message.guild.id)
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


def build_roster_embed(guild: discord.Guild) -> discord.Embed:
    cfg = get_guild_cfg(guild.id)
    roster = cfg.get("roster", [])  # list of {"user_id": int, "rank_role_id": int}
    rank_role_ids = cfg.get("ranks", [])  # ordered list of role IDs, highest first

    embed = discord.Embed(title="📋 Roster", color=discord.Color.blurple())
    if not roster:
        embed.description = "The roster is currently empty."
        return embed

    def member_line(entry):
        member = guild.get_member(entry["user_id"])
        return member.mention if member else f"<@{entry['user_id']}> (left server)"

    # Group entries by rank role, preserving the configured rank order.
    grouped = {rid: [] for rid in rank_role_ids}
    unranked = []
    for entry in roster:
        rid = entry.get("rank_role_id")
        if rid in grouped:
            grouped[rid].append(entry)
        else:
            unranked.append(entry)

    for rid in rank_role_ids:
        members = grouped[rid]
        if not members:
            continue
        role = guild.get_role(rid)
        label = role.mention if role else "(deleted role)"
        value = "\n".join(f"• {member_line(e)}" for e in members)
        embed.add_field(name=f"{label} ({len(members)})", value=value, inline=False)

    if unranked:
        value = "\n".join(f"• {member_line(e)}" for e in unranked)
        embed.add_field(name=f"Unranked ({len(unranked)})", value=value, inline=False)

    embed.set_footer(text=f"{len(roster)} member(s) total")
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
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    await interaction.response.send_message(
        f"✅ Gave {role.mention} to {user.mention}. Reason: {reason}{note}", ephemeral=True
    )
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
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    await interaction.response.send_message(
        f"✅ Removed {role.mention} from {user.mention}. Reason: {reason}{note}", ephemeral=True
    )
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
        note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
        await interaction.response.send_message(
            f"✅ Moved {user.mention} from {old_label} to {rank.mention}{summary}. Reason: {reason}{note}", ephemeral=True
        )
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
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    await interaction.response.send_message(
        f"✅ Added {user.mention} to the roster and gave them {rank.mention}. Reason: {reason}{note}", ephemeral=True
    )
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
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    await interaction.edit_original_response(
        content=f"✅ Removed {user.mention} from the roster. Reason: {reason}{note}", view=None
    )
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
    note = "" if dm_sent else " (couldn't DM them — their DMs may be closed)"
    result_message = f"✅ {verb}d {user.mention} from {old_label} to {new_role.mention}. Reason: {reason}{note}"
    if is_demote:
        await interaction.edit_original_response(content=result_message, view=None)
    else:
        await interaction.response.send_message(result_message, ephemeral=True)
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

    summary = f"✅ Import complete for {rank.mention}: **{added}** added, **{moved}** moved, **{skipped}** already correct."
    await interaction.followup.send(summary, ephemeral=True)
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

    for rid in rank_role_ids:
        role = interaction.guild.get_role(rid)
        label = role.mention if role else "(deleted role)"
        embed.add_field(name=label, value=str(counts[rid]), inline=True)

    if unranked:
        embed.add_field(name="Unranked", value=str(unranked), inline=True)

    embed.set_footer(text=f"{len(roster)} member(s) total on the roster")
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


# ---------- error handling ----------

@setlogchannel.error
@setmanagerrole.error
@setrosterchannel.error
@setranks.error
@setcooldown.error
@setinactivitydays.error
@setstatschannel.error
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
