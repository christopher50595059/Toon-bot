"""
Discord Role Assignment Bot
----------------------------
Lets authorized staff assign/remove roles (staff positions, tiers, etc.)
with a simple slash command, and logs every action to a chosen channel.

Commands:
  /addrole user:<member> role:<role>      - give a role to a member
  /removerole user:<member> role:<role>   - remove a role from a member
  /setlogchannel channel:<channel>        - (admin only) set where actions are logged
  /setmanagerrole role:<role>             - (admin only) set which role is allowed to use /addrole & /removerole
  /rosteradd user:<member> rank:<role>    - add a member to the roster at a rank AND give them that role
  /rosterremove user:<member>             - remove a member from the roster
  /roster                                 - show the current roster, grouped by rank
  /setrosterchannel channel:<channel>     - (admin only) post a live roster embed that auto-updates in this channel
  /setranks rank1:<role> [rank2]...[rank8]  - (admin only) set the ordered rank roles (highest first)

Only server admins can run the "set" commands. Only members with the
configured "manager role" (or Administrator permission) can run
/addrole and /removerole.
"""

import json
import os
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


async def log_action(guild: discord.Guild, message: str, color: discord.Color):
    cfg = get_guild_cfg(guild.id)
    channel_id = cfg.get("log_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    embed = discord.Embed(description=message, color=color)
    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass


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


# ---------- role assignment commands ----------

@bot.tree.command(name="addrole", description="Give a role to a member (e.g. promote to staff or a tier).")
@app_commands.describe(user="The member to give the role to", role="The role to assign")
async def addrole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
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

    await user.add_roles(role, reason=f"Added by {interaction.user} via /addrole")
    await interaction.response.send_message(
        f"✅ Gave {role.mention} to {user.mention}.", ephemeral=True
    )
    await log_action(
        interaction.guild,
        f"🟢 {interaction.user.mention} gave {role.mention} to {user.mention}.",
        discord.Color.green(),
    )


@bot.tree.command(name="removerole", description="Remove a role from a member.")
@app_commands.describe(user="The member to remove the role from", role="The role to remove")
async def removerole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
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

    await user.remove_roles(role, reason=f"Removed by {interaction.user} via /removerole")
    await interaction.response.send_message(
        f"✅ Removed {role.mention} from {user.mention}.", ephemeral=True
    )
    await log_action(
        interaction.guild,
        f"🔴 {interaction.user.mention} removed {role.mention} from {user.mention}.",
        discord.Color.red(),
    )


# ---------- roster commands ----------

@bot.tree.command(name="rosteradd", description="Add a member to the roster at a rank and give them that role.")
@app_commands.describe(user="The member to add to the roster", rank="The rank role to place them at")
async def rosteradd(interaction: discord.Interaction, user: discord.Member, rank: discord.Role):
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
            await user.add_roles(rank, reason=f"Added by {interaction.user} via /rosteradd")
            role_change_notes.append(f"gave them {rank.mention}")

        if existing:
            old_rank_role = interaction.guild.get_role(existing.get("rank_role_id"))
            if old_rank_role and old_rank_role.id != rank.id and old_rank_role in user.roles:
                await user.remove_roles(old_rank_role, reason=f"Rank changed by {interaction.user} via /rosteradd")
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
        await interaction.response.send_message(
            f"✅ Moved {user.mention} from {old_label} to {rank.mention}{summary}.", ephemeral=True
        )
        await log_action(
            interaction.guild,
            f"📋 {interaction.user.mention} moved {user.mention} from {old_label} to {rank.mention}.",
            discord.Color.blurple(),
        )
        await refresh_roster_message(interaction.guild)
        return

    roster.append({"user_id": user.id, "rank_role_id": rank.id})
    save_config(config)

    await interaction.response.send_message(
        f"✅ Added {user.mention} to the roster and gave them {rank.mention}.", ephemeral=True
    )
    await log_action(
        interaction.guild,
        f"📋 {interaction.user.mention} added {user.mention} to the roster as {rank.mention}.",
        discord.Color.blurple(),
    )
    await refresh_roster_message(interaction.guild)


@bot.tree.command(name="rosterremove", description="Remove a member from the roster.")
@app_commands.describe(user="The member to remove from the roster")
async def rosterremove(interaction: discord.Interaction, user: discord.Member):
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", ephemeral=True
        )
        return

    cfg = get_guild_cfg(interaction.guild_id)
    roster = cfg.setdefault("roster", [])
    new_roster = [entry for entry in roster if entry["user_id"] != user.id]

    if len(new_roster) == len(roster):
        await interaction.response.send_message(
            f"ℹ️ {user.mention} isn't on the roster.", ephemeral=True
        )
        return

    cfg["roster"] = new_roster
    save_config(config)

    await interaction.response.send_message(
        f"✅ Removed {user.mention} from the roster.", ephemeral=True
    )
    await log_action(
        interaction.guild,
        f"📋 {interaction.user.mention} removed {user.mention} from the roster.",
        discord.Color.orange(),
    )
    await refresh_roster_message(interaction.guild)


@bot.tree.command(name="roster", description="Show the current roster.")
async def roster(interaction: discord.Interaction):
    embed = build_roster_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)


# ---------- error handling ----------

@setlogchannel.error
@setmanagerrole.error
@setrosterchannel.error
@setranks.error
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
