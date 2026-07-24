"""
Web dashboard for the Discord bot.

Runs a Flask app alongside the bot (in a background thread) that:
  - Serves a "/" health-check route so Render's free tier / an uptime
    pinger keeps the service awake (same role keep_alive.py used to play).
  - Lets server admins log in with Discord ("Login with Discord" OAuth2,
    identify scope only) and view/edit the bot's settings for any server
    they administer, through a browser instead of slash commands.

This module doesn't talk to Discord's REST API for guild/channel/role
data — it reads directly from the running bot's cache (bot.get_guild(...))
since the dashboard runs in the same process. That keeps setup to just
one OAuth app (the bot's own) and avoids a second set of API calls.
"""

import asyncio
import json
import os
import secrets
import threading
from datetime import datetime

import requests
from flask import Flask, Response, redirect, request, session, url_for, render_template_string

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "").rstrip("/")  # e.g. https://your-app.onrender.com
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

DISCORD_API = "https://discord.com/api"

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Set by start_web_app() once the bot is ready to share its live state.
_bot = None
_config = None
_save_config = None
_get_guild_cfg = None
_give_role = None
_remove_role = None
_roster_add = None
_roster_remove = None
_promote = None
_demote = None
_kick = None
_ban = None
_timeout = None
_warn = None
_mass_add_role = None
_mass_remove_role = None
_mass_rename = None
_announce = None
_massannounce = None
_showcase_add = None
_showcase_remove = None
_open_ticket = None
_close_ticket = None
_set_ticket_channel = None


# ---------- shared page chrome ----------

BASE_STYLE = """
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    background:
      radial-gradient(circle at 15% -10%, rgba(88,101,242,0.20) 0%, transparent 45%),
      radial-gradient(circle at 90% 10%, rgba(155,107,255,0.16) 0%, transparent 40%),
      linear-gradient(160deg, #16121f 0%, #131320 40%, #101014 100%);
    background-attachment:fixed;
    color:#dbdee1; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    margin:0; padding:0 0 80px; line-height:1.4;
  }
  .wrap { max-width:800px; margin:0 auto; padding:36px 24px; }
  h1 {
    font-size:26px; margin:0 0 4px; font-weight:800; letter-spacing:-0.3px;
    background:linear-gradient(90deg,#7c9aff,#b18aff); -webkit-background-clip:text; background-clip:text; color:transparent;
  }
  h2 { font-size:15px; color:#f2f3f5; margin:0 0 18px; font-weight:700; display:flex; align-items:center; gap:8px; }
  .card {
    background:linear-gradient(160deg, rgba(88,101,242,0.08), rgba(43,45,49,0.9) 30%);
    border:1px solid #35363c; border-left:3px solid #5865f2; border-radius:12px;
    padding:22px 24px; margin-bottom:18px; box-shadow:0 4px 14px rgba(0,0,0,0.35);
  }
  .card#roles { border-left-color:#9b6bff; background:linear-gradient(160deg, rgba(155,107,255,0.09), rgba(43,45,49,0.9) 30%); }
  .card#ranks { border-left-color:#7c8cff; background:linear-gradient(160deg, rgba(124,140,255,0.09), rgba(43,45,49,0.9) 30%); }
  .card#other { border-left-color:#6ea8fe; background:linear-gradient(160deg, rgba(110,168,254,0.09), rgba(43,45,49,0.9) 30%); }
  a { color:#7c9aff; text-decoration:none; }
  a:hover { text-decoration:underline; color:#9db4ff; }
  .btn {
    display:inline-block; background:linear-gradient(135deg,#5865f2,#9b6bff); color:#fff; padding:11px 20px;
    border-radius:8px; border:none; font-size:14px; cursor:pointer; font-weight:600;
    transition:filter 0.15s ease, transform 0.15s ease;
  }
  .btn:hover { filter:brightness(1.12); text-decoration:none; }
  .btn-secondary { background:#3f4147; }
  .btn-secondary:hover { background:#54565c; filter:none; }
  .field { margin-bottom:18px; }
  .field:last-child { margin-bottom:0; }
  label { display:block; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; color:#949ba4;
          margin:0 0 6px; font-weight:700; }
  select, input[type=number], input[type=text] {
    width:100%; background:#1c1a26; border:1px solid #40415a; color:#f2f3f5;
    padding:10px 12px; border-radius:8px; font-size:14px; transition:border-color 0.15s ease, background 0.15s ease;
  }
  select {
    appearance:none; -webkit-appearance:none;
    background-image:url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a9b3ff' stroke-width='2'%3e%3cpath d='M6 9l6 6 6-6'/%3e%3c/svg%3e");
    background-repeat:no-repeat; background-position:right 10px center; background-size:18px; padding-right:36px;
  }
  select:hover, input:hover { border-color:#9b6bff; background:#231f30; }
  select:focus, input:focus { outline:none; border-color:#9b6bff; box-shadow:0 0 0 3px rgba(155,107,255,0.25); }
  .hint { color:#80848e; font-size:12px; margin-top:6px; }
  .flash { background:linear-gradient(135deg,#2d6a4f,#1f5a44); border:1px solid #40916c; color:#d8f3dc;
           padding:12px 16px; border-radius:8px; margin-bottom:18px; font-size:14px; font-weight:600; }
  .guild-list a {
    display:flex; align-items:center; gap:12px; background:linear-gradient(135deg, rgba(88,101,242,0.08), rgba(38,40,44,0.9));
    border:1px solid #35363c; padding:14px 16px; border-radius:10px; margin-bottom:8px; color:#dbdee1;
    transition:all 0.15s ease;
  }
  .guild-list a:hover { border-color:#9b6bff; box-shadow:0 0 0 1px #9b6bff; text-decoration:none; transform:translateX(2px); }
  .topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }
  .topbar a { color:#949ba4; font-size:13px; }
  .topbar a:hover { color:#dbdee1; }
  form { margin:0; }
  .quicknav { display:flex; gap:8px; margin:20px 0 24px; flex-wrap:wrap; }
  .quicknav a { background:#211d2e; border:1px solid #3a3550; padding:9px 16px; border-radius:20px;
                font-size:13px; font-weight:600; color:#dbdee1; transition:all 0.15s ease; }
  .quicknav a:hover { background:linear-gradient(135deg,#5865f2,#9b6bff); border-color:transparent; color:#fff; text-decoration:none; }
  .save-bar { position:sticky; bottom:20px; margin-top:12px; }
  .save-bar .btn { width:100%; padding:15px; font-size:15px; box-shadow:0 6px 24px rgba(124,90,255,0.35); }
  .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:520px) { .grid-2 { grid-template-columns:1fr; } }
  .log-wrap { max-height:640px; overflow-y:auto; border-radius:10px; border:1px solid #35363c; }
  table.log-table { width:100%; border-collapse:collapse; font-size:13px; }
  .log-table th { position:sticky; top:0; background:#1c1a26; text-align:left; padding:10px 12px;
                  font-size:11px; text-transform:uppercase; letter-spacing:0.4px; color:#949ba4; border-bottom:1px solid #35363c; }
  .log-table td { padding:10px 12px; border-bottom:1px solid #26282c; vertical-align:top; }
  .log-table tr:hover td { background:rgba(88,101,242,0.06); }
  .log-table tr:last-child td { border-bottom:none; }
  .pill { display:inline-block; background:#2a2740; border:1px solid #40415a; color:#c9c9ff;
          padding:2px 9px; border-radius:12px; font-size:12px; font-weight:600; }
  .filter-bar { display:flex; gap:10px; align-items:end; margin-bottom:18px; flex-wrap:wrap; }
  .filter-bar .field { margin-bottom:0; flex:1; min-width:200px; }
  .action-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:10px; }
  .action-tile {
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px;
    background:#1e1c29; border:1px solid #3a3550; border-radius:10px; padding:16px 10px;
    color:#dbdee1; font-weight:600; font-size:13px; text-align:center; transition:all 0.15s ease;
  }
  .action-tile span { font-size:22px; }
  .action-tile:hover { border-color:#9b6bff; background:#241f36; text-decoration:none; transform:translateY(-2px); }
  .page-layout { display:flex; gap:28px; align-items:flex-start; }
  .sidenav { width:190px; flex-shrink:0; position:sticky; top:24px; display:flex; flex-direction:column; gap:2px; }
  .sidenav a {
    display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:8px; color:#b5bac1;
    font-size:13px; font-weight:600; transition:all 0.12s ease;
  }
  .sidenav a:hover { background:#211d2e; color:#fff; text-decoration:none; }
  .sidenav a.active { background:linear-gradient(135deg,#5865f2,#9b6bff); color:#fff; }
  .sidenav .sidenav-label { font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:#6b6f76;
    font-weight:700; margin:14px 0 4px 12px; }
  .sidenav .sidenav-label:first-child { margin-top:0; }
  .main-col { flex:1; min-width:0; }
  @media (max-width:760px) {
    .page-layout { flex-direction:column; }
    .sidenav { width:100%; position:static; flex-direction:row; flex-wrap:wrap; }
    .sidenav .sidenav-label { display:none; }
  }
</style>
"""


SIDENAV_SECTIONS = [
    ("General", [
        ("dashboard", "⚙️", "Settings"),
        ("roles_page", "🎭", "Roles"),
        ("roster_page", "📋", "Roster"),
        ("moderation_page", "🛡️", "Moderation"),
    ]),
    ("Bulk & Broadcast", [
        ("mass_page", "🧰", "Mass Actions"),
        ("announce_page", "📣", "Announcements"),
        ("showcase_page", "🎭", "Showcase"),
        ("crosspost_page", "🔀", "Cross-Posting"),
        ("greetings_page", "🔊", "VC Greetings"),
        ("tickets_page", "🎫", "Tickets"),
    ]),
    ("Insight", [
        ("logs_page", "🗂️", "Logs"),
        ("activity_page", "📈", "Activity"),
        ("backup_download", "💾", "Backup"),
    ]),
]


def render_page(title: str, body: str, show_logout: bool = True, guild_id: int = None) -> str:
    logout_link = '<a href="/logout">Log out</a>' if show_logout and "user_id" in session else ""

    if guild_id is None:
        return render_template_string(
            f"""
            <!doctype html><html><head><meta charset="utf-8">
            <title>{{{{ title }}}}</title>{BASE_STYLE}</head>
            <body><div class="wrap">
            <div class="topbar"><h1>🤖 Bot Dashboard</h1>{logout_link}</div>
            {{{{ body|safe }}}}
            </div></body></html>
            """,
            title=title,
            body=body,
        )

    current_endpoint = request.endpoint
    nav_html = ""
    for section_label, links in SIDENAV_SECTIONS:
        nav_html += f'<div class="sidenav-label">{section_label}</div>'
        for endpoint, icon, label in links:
            css_class = "active" if endpoint == current_endpoint else ""
            href = url_for(endpoint, guild_id=guild_id)
            nav_html += f'<a class="{css_class}" href="{href}">{icon} {label}</a>'

    return render_template_string(
        f"""
        <!doctype html><html><head><meta charset="utf-8">
        <title>{{{{ title }}}}</title>{BASE_STYLE}</head>
        <body><div class="wrap" style="max-width:1040px;">
        <div class="topbar"><h1>🤖 Bot Dashboard</h1>{logout_link}</div>
        <div class="page-layout">
          <div class="sidenav">{{{{ nav|safe }}}}</div>
          <div class="main-col">{{{{ body|safe }}}}</div>
        </div>
        </div></body></html>
        """,
        title=title,
        body=body,
        nav=nav_html,
    )


# ---------- health check (uptime pinger target) ----------

@app.route("/")
def home():
    if "user_id" not in session:
        return render_page("Dashboard", """
            <div class="card">
              <p>Manage this bot's settings from your browser.</p>
              <a class="btn" href="/login">Login with Discord</a>
            </div>
        """, show_logout=False)
    return redirect(url_for("guild_picker"))


# ---------- OAuth2 login ----------

@app.route("/login")
def login():
    if not DISCORD_CLIENT_ID or not DASHBOARD_URL:
        return "Dashboard isn't configured yet — missing DISCORD_CLIENT_ID or DASHBOARD_URL.", 500
    redirect_uri = f"{DASHBOARD_URL}/callback"
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "identify",
    }
    query = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
    return redirect(f"{DISCORD_API}/oauth2/authorize?{query}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("home"))

    redirect_uri = f"{DASHBOARD_URL}/callback"
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        token_resp = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers=headers, timeout=10)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        user_resp = requests.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_resp.raise_for_status()
        user = user_resp.json()
    except requests.RequestException:
        return "Login failed — couldn't reach Discord. Try again.", 502

    session["user_id"] = int(user["id"])
    session["username"] = user.get("username", "there")
    return redirect(url_for("guild_picker"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


def _admin_guilds_for(user_id: int):
    """Every guild the bot is in where this user is an Administrator or holds the manager role."""
    results = []
    for guild in _bot.guilds:
        member = guild.get_member(user_id)
        if member is None:
            continue
        cfg = _get_guild_cfg(guild.id)
        manager_role_id = cfg.get("manager_role_id")
        is_manager = manager_role_id and any(r.id == manager_role_id for r in member.roles)
        if member.guild_permissions.administrator or is_manager:
            results.append(guild)
    return results


@app.route("/guilds")
def guild_picker():
    if "user_id" not in session:
        return redirect(url_for("login"))

    guilds = _admin_guilds_for(session["user_id"])
    if not guilds:
        body = """
            <div class="card">
              <p>Hi! I couldn't find any servers where you're an admin or have the manager role, and where this bot is present.</p>
              <p class="hint">If you just set this up, make sure you're using the same Discord account you use in that server.</p>
            </div>
        """
        return render_page("No servers", body)

    items = ""
    for g in guilds:
        icon_html = (
            f'<img src="{g.icon.url}" style="width:32px;height:32px;border-radius:8px;">'
            if g.icon else
            '<div style="width:32px;height:32px;border-radius:8px;background:#5865f2;display:flex;'
            'align-items:center;justify-content:center;font-weight:700;">' + g.name[0].upper() + '</div>'
        )
        items += f"""
        <a href="/dashboard/{g.id}" style="display:flex;align-items:center;gap:12px;">
          {icon_html}
          <div>
            <div style="font-weight:600;">{g.name}</div>
            <div class="hint" style="margin-top:0;">{g.member_count} member(s)</div>
          </div>
        </a>
        """
    body = f"""
        <p>Pick a server to manage:</p>
        <div class="guild-list">{items}</div>
    """
    return render_page("Your servers", body)


# ---------- dashboard ----------

def _check_access(guild_id: int):
    """Returns (guild, member) if the logged-in user can manage this guild, else (None, None)."""
    if "user_id" not in session:
        return None, None
    guild = _bot.get_guild(guild_id)
    if guild is None:
        return None, None
    member = guild.get_member(session["user_id"])
    if member is None:
        return None, None
    cfg = _get_guild_cfg(guild.id)
    manager_role_id = cfg.get("manager_role_id")
    is_manager = manager_role_id and any(r.id == manager_role_id for r in member.roles)
    if not (member.guild_permissions.administrator or is_manager):
        return None, None
    return guild, member


def _channel_options(guild, selected_id, channel_type="text"):
    channels = guild.text_channels if channel_type == "text" else guild.voice_channels
    opts = ['<option value="">— none —</option>']
    for c in channels:
        sel = "selected" if selected_id == c.id else ""
        opts.append(f'<option value="{c.id}" {sel}>#{c.name}</option>')
    return "".join(opts)


def _role_options(guild, selected_id, allow_none=True):
    opts = ['<option value="">— none —</option>'] if allow_none else ['<option value="">— pick a role —</option>']
    for r in sorted(guild.roles, key=lambda r: r.position, reverse=True):
        if r.is_default():
            continue
        sel = "selected" if selected_id == r.id else ""
        opts.append(f'<option value="{r.id}" {sel}>@{r.name}</option>')
    return "".join(opts)


def _member_options(guild):
    opts = ['<option value="">— pick a member —</option>']
    members = sorted((m for m in guild.members if not m.bot), key=lambda m: m.display_name.lower())
    for m in members:
        opts.append(f'<option value="{m.id}">{m.display_name} ({m})</option>')
    return "".join(opts)


def _rank_options(guild, cfg):
    """Only the roles configured via /setranks, highest first — used for roster forms."""
    rank_ids = cfg.get("ranks", [])
    opts = ['<option value="">— pick a rank —</option>']
    for rid in rank_ids:
        role = guild.get_role(rid)
        if role:
            opts.append(f'<option value="{role.id}">@{role.name}</option>')
    return "".join(opts)


def _run_async(coro, timeout=15):
    """Bridge a Flask request (running in its own thread) into the bot's
    asyncio event loop (running in the main thread), and wait for the result."""
    future = asyncio.run_coroutine_threadsafe(coro, _bot.loop)
    try:
        return future.result(timeout=timeout)
    except Exception as e:
        return f"❌ Something went wrong: {e}"


@app.route("/dashboard/<int:guild_id>", methods=["GET"])
def dashboard(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    flash = request.args.get("saved")
    flash_html = '<div class="flash">✅ Settings saved.</div>' if flash else ""

    ranks = cfg.get("ranks", [])
    rank_fields = ""
    for i in range(8):
        selected = ranks[i] if i < len(ranks) else None
        rank_fields += f"""
            <div class="field">
              <label>Rank {i + 1} {'(highest)' if i == 0 else ''}</label>
              <select name="rank{i}">{_role_options(guild, selected)}</select>
            </div>
        """

    guild_icon_html = (
        f'<img src="{guild.icon.url}" style="width:32px;height:32px;border-radius:8px;vertical-align:middle;margin-right:10px;">'
        if guild.icon else ""
    )

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/guilds">&larr; All servers</a></div>
    <h1 style="margin-top:18px;">{guild_icon_html}{guild.name}</h1>
    {flash_html}

    <div class="card">
      <h2>⚡ Actions</h2>
      <div class="action-grid">
        <a class="action-tile" href="/dashboard/{guild_id}/roles"><span>🎭</span>Roles</a>
        <a class="action-tile" href="/dashboard/{guild_id}/roster"><span>📋</span>Roster</a>
        <a class="action-tile" href="/dashboard/{guild_id}/moderation"><span>🛡️</span>Moderation</a>
        <a class="action-tile" href="/dashboard/{guild_id}/mass"><span>🧰</span>Mass Actions</a>
        <a class="action-tile" href="/dashboard/{guild_id}/announce"><span>📣</span>Announcements</a>
        <a class="action-tile" href="/dashboard/{guild_id}/showcase"><span>🎭</span>Showcase</a>
        <a class="action-tile" href="/dashboard/{guild_id}/crosspost"><span>🔀</span>Cross-Posting</a>
        <a class="action-tile" href="/dashboard/{guild_id}/greetings"><span>🔊</span>VC Greetings</a>
        <a class="action-tile" href="/dashboard/{guild_id}/tickets"><span>🎫</span>Tickets</a>
        <a class="action-tile" href="/dashboard/{guild_id}/logs"><span>🗂️</span>Logs</a>
        <a class="action-tile" href="/dashboard/{guild_id}/activity"><span>📈</span>Activity</a>
        <a class="action-tile" href="/dashboard/{guild_id}/backup"><span>💾</span>Download Backup</a>
      </div>
    </div>

    <div class="quicknav">
      <a href="#channels">📢 Channels</a>
      <a href="#roles">🎭 Settings</a>
      <a href="#ranks">📋 Ranks</a>
      <a href="#other">⚙️ Other</a>
    </div>

    <form method="post" action="/dashboard/{guild_id}/save">

      <div class="card" id="channels">
        <h2>📢 Channels</h2>
        <div class="grid-2">
          <div class="field">
            <label>Log channel</label>
            <select name="log_channel">{_channel_options(guild, cfg.get('log_channel_id'))}</select>
            <div class="hint">Role/roster actions get posted here.</div>
          </div>
          <div class="field">
            <label>Live roster channel</label>
            <select name="roster_channel">{_channel_options(guild, cfg.get('roster_channel_id'))}</select>
          </div>
          <div class="field">
            <label>Live stats channel</label>
            <select name="stats_channel">{_channel_options(guild, cfg.get('stats_channel_id'))}</select>
          </div>
          <div class="field">
            <label>Birthday shoutout channel</label>
            <select name="birthday_channel">{_channel_options(guild, cfg.get('birthday_channel_id'))}</select>
          </div>
          <div class="field">
            <label>Role showcase channel</label>
            <select name="showcase_channel">{_channel_options(guild, cfg.get('showcase_channel_id'))}</select>
          </div>
        </div>
      </div>

      <div class="card" id="roles">
        <h2>🎭 Roles</h2>
        <div class="grid-2">
          <div class="field">
            <label>Manager role (can use staff commands)</label>
            <select name="manager_role">{_role_options(guild, cfg.get('manager_role_id'))}</select>
          </div>
          <div class="field">
            <label>Birthday role</label>
            <select name="birthday_role">{_role_options(guild, cfg.get('birthday_role_id'))}</select>
          </div>
        </div>
      </div>

      <div class="card" id="ranks">
        <h2>📋 Ranks (highest to lowest)</h2>
        <div class="grid-2">
          {rank_fields}
        </div>
        <div class="hint">Leave lower ones on "none" if you have fewer than 8 ranks.</div>
      </div>

      <div class="card" id="other">
        <h2>⚙️ Other settings</h2>
        <div class="grid-2">
          <div class="field">
            <label>Promotion/demotion cooldown (hours, 0 = off)</label>
            <input type="number" name="cooldown_hours" min="0" value="{cfg.get('cooldown_hours', 0)}">
          </div>
          <div class="field">
            <label>Inactivity threshold (days, 0 = off)</label>
            <input type="number" name="inactivity_days" min="0" value="{cfg.get('inactivity_days', 0)}">
          </div>
        </div>
      </div>

      <div class="save-bar">
        <button class="btn" type="submit">Save changes</button>
      </div>
    </form>
    """
    return render_page(f"{guild.name} — Dashboard", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/save", methods=["POST"])
def dashboard_save(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    f = request.form

    def set_or_clear(key, form_key, cast=int):
        raw = f.get(form_key, "")
        if raw:
            cfg[key] = cast(raw)
        else:
            cfg.pop(key, None)

    set_or_clear("log_channel_id", "log_channel")
    set_or_clear("roster_channel_id", "roster_channel")
    set_or_clear("stats_channel_id", "stats_channel")
    set_or_clear("birthday_channel_id", "birthday_channel")
    set_or_clear("showcase_channel_id", "showcase_channel")
    set_or_clear("manager_role_id", "manager_role")
    set_or_clear("birthday_role_id", "birthday_role")

    ranks = []
    for i in range(8):
        raw = f.get(f"rank{i}", "")
        if raw:
            ranks.append(int(raw))
    cfg["ranks"] = ranks

    try:
        cfg["cooldown_hours"] = max(0, int(f.get("cooldown_hours", 0)))
    except ValueError:
        pass
    try:
        cfg["inactivity_days"] = max(0, int(f.get("inactivity_days", 0)))
    except ValueError:
        pass

    _save_config(_config)
    return redirect(url_for("dashboard", guild_id=guild_id, saved=1))


# ---------- role actions (give/remove) ----------

@app.route("/dashboard/<int:guild_id>/roles")
def roles_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    member_opts = _member_options(guild)
    role_opts = _role_options(guild, None, allow_none=False)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎭 Give / Remove Roles</h1>
    {result_html}

    <div class="card">
      <h2>🟢 Give a role</h2>
      <form method="post" action="/dashboard/{guild_id}/roles/give">
        <div class="grid-2">
          <div class="field">
            <label>Member</label>
            <select name="user_id" required>{member_opts}</select>
          </div>
          <div class="field">
            <label>Role</label>
            <select name="role_id" required>{role_opts}</select>
          </div>
        </div>
        <div class="field">
          <label>Reason</label>
          <input type="text" name="reason" placeholder="Why you're giving this role" required>
        </div>
        <button class="btn" type="submit">Give Role</button>
      </form>
    </div>

    <div class="card">
      <h2>🔴 Remove a role</h2>
      <form method="post" action="/dashboard/{guild_id}/roles/remove">
        <div class="grid-2">
          <div class="field">
            <label>Member</label>
            <select name="user_id" required>{member_opts}</select>
          </div>
          <div class="field">
            <label>Role</label>
            <select name="role_id" required>{role_opts}</select>
          </div>
        </div>
        <div class="field">
          <label>Reason</label>
          <input type="text" name="reason" placeholder="Why you're removing this role" required>
        </div>
        <button class="btn btn-secondary" type="submit">Remove Role</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Roles", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/roles/give", methods=["POST"])
def roles_give(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    try:
        user_id = int(request.form["user_id"])
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roles_page", guild_id=guild_id, result="❌ Pick a member and a role."))

    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_give_role(guild_id, user_id, role_id, reason, session["user_id"]))
    return redirect(url_for("roles_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/roles/remove", methods=["POST"])
def roles_remove(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    try:
        user_id = int(request.form["user_id"])
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roles_page", guild_id=guild_id, result="❌ Pick a member and a role."))

    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_remove_role(guild_id, user_id, role_id, reason, session["user_id"]))
    return redirect(url_for("roles_page", guild_id=guild_id, result=result))


# ---------- roster actions (add/remove/promote/demote) ----------

@app.route("/dashboard/<int:guild_id>/roster")
def roster_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    member_opts = _member_options(guild)
    rank_opts = _rank_options(guild, cfg)
    no_ranks_hint = "" if cfg.get("ranks") else '<div class="hint">No ranks configured yet — set them up in this server\'s settings first.</div>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📋 Roster Actions</h1>
    {result_html}

    <div class="card">
      <h2>📋 Add / move on roster</h2>
      {no_ranks_hint}
      <form method="post" action="/dashboard/{guild_id}/roster/add">
        <div class="grid-2">
          <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
          <div class="field"><label>Rank</label><select name="rank_id" required>{rank_opts}</select></div>
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Add / Move</button>
      </form>
    </div>

    <div class="card">
      <h2>⬆️ Promote</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/promote">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Promote</button>
      </form>
    </div>

    <div class="card">
      <h2>⬇️ Demote</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/demote">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Demote</button>
      </form>
    </div>

    <div class="card">
      <h2>🗑️ Remove from roster</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/remove">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Remove</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Roster", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/roster/add", methods=["POST"])
def roster_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
        rank_id = int(request.form["rank_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick a member and a rank."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_roster_add(guild_id, user_id, rank_id, reason, session["user_id"]))
    return redirect(url_for("roster_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/roster/remove", methods=["POST"])
def roster_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_roster_remove(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("roster_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/roster/promote", methods=["POST"])
def roster_promote_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_promote(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("roster_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/roster/demote", methods=["POST"])
def roster_demote_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_demote(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("roster_page", guild_id=guild_id, result=result))


# ---------- moderation actions (kick/ban/timeout/warn) ----------

@app.route("/dashboard/<int:guild_id>/moderation")
def moderation_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""
    member_opts = _member_options(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🛡️ Moderation</h1>
    {result_html}

    <div class="card">
      <h2>⚠️ Warn</h2>
      <form method="post" action="/dashboard/{guild_id}/moderation/warn">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Warn</button>
      </form>
    </div>

    <div class="card">
      <h2>🔇 Timeout</h2>
      <form method="post" action="/dashboard/{guild_id}/moderation/timeout">
        <div class="grid-2">
          <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
          <div class="field"><label>Minutes</label><input type="number" name="minutes" min="1" max="40320" value="60" required></div>
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Time Out</button>
      </form>
    </div>

    <div class="card">
      <h2>👢 Kick</h2>
      <form method="post" action="/dashboard/{guild_id}/moderation/kick">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Kick</button>
      </form>
    </div>

    <div class="card">
      <h2>🔨 Ban</h2>
      <form method="post" action="/dashboard/{guild_id}/moderation/ban">
        <div class="grid-2">
          <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
          <div class="field"><label>Delete message history (days, 0-7)</label><input type="number" name="delete_days" min="0" max="7" value="0"></div>
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Ban</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Moderation", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/moderation/kick", methods=["POST"])
def moderation_kick(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_kick(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("moderation_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/moderation/ban", methods=["POST"])
def moderation_ban(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick a member."))
    try:
        delete_days = int(request.form.get("delete_days", 0))
    except ValueError:
        delete_days = 0
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_ban(guild_id, user_id, reason, delete_days, session["user_id"]))
    return redirect(url_for("moderation_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/moderation/timeout", methods=["POST"])
def moderation_timeout(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
        minutes = int(request.form["minutes"])
    except (KeyError, ValueError):
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick a member and a valid duration."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_timeout(guild_id, user_id, minutes, reason, session["user_id"]))
    return redirect(url_for("moderation_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/moderation/warn", methods=["POST"])
def moderation_warn(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_warn(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("moderation_page", guild_id=guild_id, result=result))


# ---------- logs / movements ----------

def _format_ts(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, TypeError):
        return iso_str or "—"


@app.route("/dashboard/<int:guild_id>/logs")
def logs_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    history = cfg.get("history", {})
    warnings = cfg.get("warnings", {})

    filter_user_id = request.args.get("user", "").strip()

    all_entries = []
    for uid_str, entries in history.items():
        if filter_user_id and uid_str != filter_user_id:
            continue
        for e in entries:
            all_entries.append((int(uid_str), e))
    all_entries.sort(key=lambda pair: pair[1].get("timestamp", ""), reverse=True)

    limit = 300 if filter_user_id else 100
    shown = all_entries[:limit]

    def action_color(action):
        a = action.lower()
        if "promot" in a: return "#f5c15c"
        if "demot" in a: return "#ff9f5a"
        if "remov" in a: return "#ff6b6b"
        if "add" in a: return "#5ee0a0"
        return "#a9b3ff"

    rows = ""
    if not shown:
        rows = '<tr><td colspan="5" class="hint" style="padding:20px;">No recorded activity yet.</td></tr>'
    for uid, e in shown:
        m = guild.get_member(uid)
        name = m.display_name if m else f"Unknown ({uid})"
        mod = guild.get_member(e.get("moderator_id"))
        mod_name = mod.display_name if mod else f"Unknown ({e.get('moderator_id')})"
        action = e.get("action", "—")
        detail = e.get("detail", "") or ""
        reason = e.get("reason") or ""
        color = action_color(action)
        rows += f"""
        <tr>
          <td>{name}</td>
          <td><span class="pill" style="background:{color}22; border-color:{color}55; color:{color};">{action}</span></td>
          <td>{detail}</td>
          <td>{mod_name}</td>
          <td>{reason}</td>
          <td class="hint" style="white-space:nowrap;">{_format_ts(e.get("timestamp"))}</td>
        </tr>
        """

    # Warnings block only shown when filtered to one person.
    warnings_html = ""
    if filter_user_id:
        user_warnings = warnings.get(filter_user_id, [])
        if user_warnings:
            w_rows = ""
            for w in reversed(user_warnings):
                mod = guild.get_member(w.get("moderator_id"))
                mod_name = mod.display_name if mod else f"Unknown ({w.get('moderator_id')})"
                w_rows += f"""
                <tr>
                  <td>{w.get('reason','')}</td>
                  <td>{mod_name}</td>
                  <td class="hint" style="white-space:nowrap;">{_format_ts(w.get('timestamp'))}</td>
                </tr>
                """
            warnings_html = f"""
            <div class="card">
              <h2>⚠️ Warnings ({len(user_warnings)})</h2>
              <div class="log-wrap"><table class="log-table">
                <tr><th>Reason</th><th>Moderator</th><th>When</th></tr>
                {w_rows}
              </table></div>
            </div>
            """

    member_opts = '<option value="">— everyone —</option>' + _member_options(guild).split("</option>", 1)[1]
    # Re-mark the currently selected filter, if any.
    if filter_user_id:
        member_opts = member_opts.replace(f'value="{filter_user_id}"', f'value="{filter_user_id}" selected')

    filter_label = ""
    if filter_user_id:
        fm = guild.get_member(int(filter_user_id))
        filter_label = f' — {fm.display_name}' if fm else ""

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🗂️ Logs & Movements{filter_label}</h1>
    <div class="hint" style="margin-bottom:18px;">
      {"Showing this member's full history (up to 300 entries)." if filter_user_id else f"Showing the {len(shown)} most recent action(s) across everyone."}
    </div>

    <form method="get" class="filter-bar">
      <div class="field">
        <label>Filter to one member</label>
        <select name="user" onchange="this.form.submit()">{member_opts}</select>
      </div>
    </form>

    {warnings_html}

    <div class="card">
      <h2>📋 Rank / Roster History</h2>
      <div class="log-wrap">
        <table class="log-table">
          <tr><th>Member</th><th>Action</th><th>Detail</th><th>By</th><th>Reason</th><th>When</th></tr>
          {rows}
        </table>
      </div>
    </div>
    """
    return render_page(f"{guild.name} — Logs", body, guild_id=guild_id)


# ---------- mass actions ----------

@app.route("/dashboard/<int:guild_id>/mass")
def mass_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""
    role_opts = _role_options(guild, None, allow_none=False)
    role_opts_optional = _role_options(guild, None, allow_none=True)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🧰 Mass Actions</h1>
    {result_html}

    <div class="card">
      <h2>🟢 Give a role to many members</h2>
      <form method="post" action="/dashboard/{guild_id}/mass/addrole">
        <div class="grid-2">
          <div class="field"><label>Role to give</label><select name="role_id" required>{role_opts}</select></div>
          <div class="field"><label>Only members who have this role (optional)</label><select name="filter_role_id">{role_opts_optional}</select></div>
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Give to All Matching</button>
      </form>
    </div>

    <div class="card">
      <h2>🔴 Remove a role from many members</h2>
      <form method="post" action="/dashboard/{guild_id}/mass/removerole">
        <div class="grid-2">
          <div class="field"><label>Role to remove</label><select name="role_id" required>{role_opts}</select></div>
          <div class="field"><label>Only members who also have this role (optional)</label><select name="filter_role_id">{role_opts_optional}</select></div>
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Remove from All Matching</button>
      </form>
    </div>

    <div class="card">
      <h2>✏️ Mass rename</h2>
      <form method="post" action="/dashboard/{guild_id}/mass/rename">
        <div class="grid-2">
          <div class="field"><label>Prefix (optional)</label><input type="text" name="prefix" placeholder="[Staff] "></div>
          <div class="field"><label>Suffix (optional)</label><input type="text" name="suffix" placeholder=" | Verified"></div>
        </div>
        <div class="field"><label>Only members with this role (optional)</label><select name="filter_role_id">{role_opts_optional}</select></div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Rename All Matching</button>
      </form>
      <div class="hint">The server owner and anyone above the bot's own role are automatically skipped.</div>
    </div>
    """
    return render_page(f"{guild.name} — Mass Actions", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/mass/addrole", methods=["POST"])
def mass_addrole_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("mass_page", guild_id=guild_id, result="❌ Pick a role."))
    filter_role_id = int(request.form["filter_role_id"]) if request.form.get("filter_role_id") else None
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_mass_add_role(guild_id, role_id, filter_role_id, reason, session["user_id"]), timeout=60)
    return redirect(url_for("mass_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/mass/removerole", methods=["POST"])
def mass_removerole_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("mass_page", guild_id=guild_id, result="❌ Pick a role."))
    filter_role_id = int(request.form["filter_role_id"]) if request.form.get("filter_role_id") else None
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_mass_remove_role(guild_id, role_id, filter_role_id, reason, session["user_id"]), timeout=60)
    return redirect(url_for("mass_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/mass/rename", methods=["POST"])
def mass_rename_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    prefix = request.form.get("prefix", "").strip()
    suffix = request.form.get("suffix", "").strip()
    if not prefix and not suffix:
        return redirect(url_for("mass_page", guild_id=guild_id, result="❌ Provide at least a prefix or a suffix."))
    filter_role_id = int(request.form["filter_role_id"]) if request.form.get("filter_role_id") else None
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_mass_rename(guild_id, prefix, suffix, filter_role_id, reason, session["user_id"]), timeout=60)
    return redirect(url_for("mass_page", guild_id=guild_id, result=result))


# ---------- announcements ----------

@app.route("/dashboard/<int:guild_id>/announce")
def announce_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""
    channel_opts = _channel_options(guild, None)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📣 Announcements</h1>
    {result_html}

    <div class="card">
      <h2>📢 Post to one channel</h2>
      <form method="post" action="/dashboard/{guild_id}/announce/single">
        <div class="field"><label>Channel</label><select name="channel_id" required>{channel_opts}</select></div>
        <div class="field"><label>Title</label><input type="text" name="title" value="Announcement" required></div>
        <div class="field"><label>Message</label><input type="text" name="message" placeholder="What's the announcement?" required></div>
        <div class="field"><label style="display:flex;align-items:center;gap:8px;text-transform:none;font-size:14px;">
          <input type="checkbox" name="ping_everyone" value="1" checked style="width:auto;"> Ping @everyone
        </label></div>
        <button class="btn" type="submit">Post</button>
      </form>
    </div>

    <div class="card">
      <h2>📢 Broadcast everywhere (text + voice)</h2>
      <div class="hint" style="margin-bottom:12px;">Posts to every channel with "announcement" in its name, and speaks the message aloud in every voice channel that currently has people in it.</div>
      <form method="post" action="/dashboard/{guild_id}/announce/broadcast">
        <div class="field"><label>Title</label><input type="text" name="title" value="Announcement" required></div>
        <div class="field"><label>Message</label><input type="text" name="message" placeholder="What's the announcement?" required></div>
        <div class="field"><label style="display:flex;align-items:center;gap:8px;text-transform:none;font-size:14px;">
          <input type="checkbox" name="ping_everyone" value="1" checked style="width:auto;"> Ping @everyone
        </label></div>
        <button class="btn btn-secondary" type="submit">Broadcast</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Announcements", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/announce/single", methods=["POST"])
def announce_single_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("announce_page", guild_id=guild_id, result="❌ Pick a channel."))
    title = request.form.get("title", "").strip() or "Announcement"
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("announce_page", guild_id=guild_id, result="❌ Write a message."))
    ping_everyone = request.form.get("ping_everyone") == "1"
    result = _run_async(_announce(guild_id, channel_id, title, message, ping_everyone, session["user_id"]))
    return redirect(url_for("announce_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/announce/broadcast", methods=["POST"])
def announce_broadcast_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    title = request.form.get("title", "").strip() or "Announcement"
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("announce_page", guild_id=guild_id, result="❌ Write a message."))
    ping_everyone = request.form.get("ping_everyone") == "1"
    result = _run_async(_massannounce(guild_id, title, message, ping_everyone, session["user_id"]), timeout=60)
    return redirect(url_for("announce_page", guild_id=guild_id, result=result))


# ---------- role showcase ----------

@app.route("/dashboard/<int:guild_id>/showcase")
def showcase_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    entries = cfg.get("showcase_roles", [])
    current_rows = ""
    if entries:
        for e in entries:
            role = guild.get_role(e["role_id"])
            name = f"@{role.name}" if role else f"(deleted role {e['role_id']})"
            current_rows += f"""
            <tr>
              <td>{name}</td>
              <td>{e.get('description','')}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/showcase/remove" style="margin:0;">
                  <input type="hidden" name="role_id" value="{e['role_id']}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        current_rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No roles in the showcase yet.</td></tr>'

    role_opts = _role_options(guild, None, allow_none=False)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎭 Role Showcase</h1>
    {result_html}

    <div class="card">
      <h2>Current showcase ({len(entries)}/25)</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Role</th><th>Description</th><th></th></tr>
        {current_rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Add or update a role</h2>
      <form method="post" action="/dashboard/{guild_id}/showcase/add">
        <div class="field"><label>Role</label><select name="role_id" required>{role_opts}</select></div>
        <div class="field"><label>Description</label><input type="text" name="description" placeholder="What this role is for / how to earn it" required></div>
        <button class="btn" type="submit">Add / Update</button>
      </form>
      <div class="hint">Set a showcase channel from the main settings page for members to see this with clickable "get role" buttons.</div>
    </div>
    """
    return render_page(f"{guild.name} — Showcase", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/showcase/add", methods=["POST"])
def showcase_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("showcase_page", guild_id=guild_id, result="❌ Pick a role."))
    description = request.form.get("description", "").strip()
    if not description:
        return redirect(url_for("showcase_page", guild_id=guild_id, result="❌ Write a description."))
    result = _run_async(_showcase_add(guild_id, role_id, description, session["user_id"]))
    return redirect(url_for("showcase_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/showcase/remove", methods=["POST"])
def showcase_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("showcase_page", guild_id=guild_id, result="❌ Pick a role."))
    result = _run_async(_showcase_remove(guild_id, role_id, session["user_id"]))
    return redirect(url_for("showcase_page", guild_id=guild_id, result=result))


# ---------- cross-posting (pure config, no Discord action needed to set up) ----------

@app.route("/dashboard/<int:guild_id>/crosspost")
def crosspost_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    crossposts = cfg.get("crossposts", {})
    rows = ""
    if crossposts:
        for source_id, dest_id in crossposts.items():
            source_channel = guild.get_channel(int(source_id))
            dest_channel = _bot.get_channel(dest_id)
            source_label = f"#{source_channel.name}" if source_channel else f"(deleted channel {source_id})"
            dest_label = f"#{dest_channel.name} in {dest_channel.guild.name}" if dest_channel else f"(unreachable channel {dest_id})"
            rows += f"""
            <tr>
              <td>{source_label}</td>
              <td>→ {dest_label}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/crosspost/remove" style="margin:0;">
                  <input type="hidden" name="source_id" value="{source_id}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No mirrors set up yet.</td></tr>'

    channel_opts = _channel_options(guild, None)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔀 Cross-Posting</h1>
    {result_html}

    <div class="card">
      <h2>Current mirrors</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>From</th><th>To</th><th></th></tr>
        {rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Add a mirror</h2>
      <form method="post" action="/dashboard/{guild_id}/crosspost/add">
        <div class="field"><label>Source channel (in this server)</label><select name="source_channel_id" required>{channel_opts}</select></div>
        <div class="field">
          <label>Destination channel ID (in another server, bot must be there too)</label>
          <input type="text" name="dest_channel_id" placeholder="123456789012345678" required>
        </div>
        <button class="btn" type="submit">Add Mirror</button>
      </form>
      <div class="hint">To get a channel ID: enable Developer Mode in Discord (User Settings → Advanced), then right-click the destination channel → Copy Channel ID.</div>
    </div>
    """
    return render_page(f"{guild.name} — Cross-Posting", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/crosspost/add", methods=["POST"])
def crosspost_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        source_channel_id = int(request.form["source_channel_id"])
        dest_channel_id = int(request.form["dest_channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("crosspost_page", guild_id=guild_id, result="❌ Fill in both fields with valid values."))

    dest_channel = _bot.get_channel(dest_channel_id)
    if dest_channel is None:
        return redirect(url_for(
            "crosspost_page", guild_id=guild_id,
            result="❌ I can't see that channel. Make sure the bot is invited to that server and has access to it.",
        ))

    cfg = _get_guild_cfg(guild_id)
    crossposts = cfg.setdefault("crossposts", {})
    crossposts[str(source_channel_id)] = dest_channel_id
    _save_config(_config)
    return redirect(url_for("crosspost_page", guild_id=guild_id, result=f"✅ Mirror added: #{guild.get_channel(source_channel_id).name} → #{dest_channel.name}"))


@app.route("/dashboard/<int:guild_id>/crosspost/remove", methods=["POST"])
def crosspost_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    source_id = request.form.get("source_id", "")
    cfg = _get_guild_cfg(guild_id)
    crossposts = cfg.setdefault("crossposts", {})
    if source_id in crossposts:
        crossposts.pop(source_id)
        _save_config(_config)
        return redirect(url_for("crosspost_page", guild_id=guild_id, result="✅ Mirror removed."))
    return redirect(url_for("crosspost_page", guild_id=guild_id, result="ℹ️ That mirror wasn't found."))


# ---------- VC greetings (pure config, no Discord action needed to set up) ----------

@app.route("/dashboard/<int:guild_id>/greetings")
def greetings_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    greetings = cfg.get("vc_greetings", {})
    rows = ""
    if greetings:
        for uid_str, message in greetings.items():
            m = guild.get_member(int(uid_str))
            name = m.display_name if m else f"Unknown ({uid_str})"
            rows += f"""
            <tr>
              <td>{name}</td>
              <td>{message}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/greetings/remove" style="margin:0;">
                  <input type="hidden" name="user_id" value="{uid_str}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No VC greetings set up yet.</td></tr>'

    member_opts = _member_options(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔊 VC Greetings</h1>
    {result_html}

    <div class="card">
      <h2>Current greetings</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Member</th><th>Message</th><th></th></tr>
        {rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Add / update a greeting</h2>
      <form method="post" action="/dashboard/{guild_id}/greetings/add">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <div class="field"><label>What the bot should say when they join a VC</label><input type="text" name="message" placeholder="The legend has arrived!" required></div>
        <button class="btn" type="submit">Save Greeting</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — VC Greetings", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/greetings/add", methods=["POST"])
def greetings_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("greetings_page", guild_id=guild_id, result="❌ Pick a member."))
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("greetings_page", guild_id=guild_id, result="❌ Write a greeting message."))

    cfg = _get_guild_cfg(guild_id)
    greetings = cfg.setdefault("vc_greetings", {})
    greetings[str(user_id)] = message
    _save_config(_config)
    target = guild.get_member(user_id)
    name = target.display_name if target else str(user_id)
    return redirect(url_for("greetings_page", guild_id=guild_id, result=f"✅ Greeting saved for {name}."))


@app.route("/dashboard/<int:guild_id>/greetings/remove", methods=["POST"])
def greetings_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_id = request.form.get("user_id", "")
    cfg = _get_guild_cfg(guild_id)
    greetings = cfg.setdefault("vc_greetings", {})
    if user_id in greetings:
        greetings.pop(user_id)
        _save_config(_config)
        return redirect(url_for("greetings_page", guild_id=guild_id, result="✅ Greeting removed."))
    return redirect(url_for("greetings_page", guild_id=guild_id, result="ℹ️ That greeting wasn't found."))


# ---------- message activity (read-only) ----------

@app.route("/dashboard/<int:guild_id>/activity")
def activity_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    counts = cfg.get("message_counts", {})
    since_str = cfg.get("message_count_since")
    since_label = _format_ts(since_str) if since_str else "—"

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:50]
    rows = ""
    if ranked:
        for i, (uid, count) in enumerate(ranked, start=1):
            m = guild.get_member(int(uid))
            name = m.display_name if m else f"Unknown ({uid})"
            rows += f"<tr><td>#{i}</td><td>{name}</td><td>{count}</td></tr>"
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No messages recorded yet this period.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📈 Message Activity</h1>
    <div class="hint" style="margin-bottom:18px;">Counting since {since_label} — resets automatically every 7 days.</div>

    <div class="card">
      <h2>Top {len(ranked)}</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Rank</th><th>Member</th><th>Messages</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Activity", body, guild_id=guild_id)


# ---------- tickets ----------

@app.route("/dashboard/<int:guild_id>/tickets")
def tickets_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    tickets = cfg.get("tickets", {})
    all_tickets = sorted(tickets.values(), key=lambda t: t.get("id", 0), reverse=True)

    rows = ""
    if all_tickets:
        for t in all_tickets:
            owner = guild.get_member(t["user_id"])
            owner_name = owner.display_name if owner else f"Unknown ({t['user_id']})"
            status = t.get("status", "open")
            status_color = "#5ee0a0" if status == "open" else "#80848e"
            status_pill = f'<span class="pill" style="background:{status_color}22; border-color:{status_color}55; color:{status_color};">{status}</span>'

            action_cell = ""
            if status == "open":
                channel = guild.get_channel(t.get("channel_id"))
                link = f'<a href="https://discord.com/channels/{guild_id}/{t["channel_id"]}" target="_blank">Open in Discord</a>' if channel else ""
                action_cell = f"""
                {link}
                <form method="post" action="/dashboard/{guild_id}/tickets/close" style="display:inline; margin-left:8px;">
                  <input type="hidden" name="ticket_id" value="{t['id']}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Close</button>
                </form>
                """
            else:
                closer = guild.get_member(t.get("closed_by"))
                closer_name = closer.display_name if closer else "—"
                action_cell = f'<span class="hint">Closed by {closer_name}</span>'

            rows += f"""
            <tr>
              <td>#{t['id']}</td>
              <td>{owner_name}</td>
              <td>{status_pill}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(t.get('created_at'))}</td>
              <td>{action_cell}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="5" class="hint" style="padding:16px;">No tickets yet.</td></tr>'

    member_opts = _member_options(guild)
    channel_opts = _channel_options(guild, cfg.get("ticket_channel_id"))

    body = f"""
    <h1>🎫 Tickets</h1>
    {result_html}

    <div class="card">
      <h2>📌 Ticket panel channel</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a button in this channel that lets any member open their own ticket instantly.</div>
      <form method="post" action="/dashboard/{guild_id}/tickets/setchannel">
        <div class="field"><label>Channel</label><select name="channel_id" required>{channel_opts}</select></div>
        <button class="btn" type="submit">Post Ticket Panel</button>
      </form>
    </div>

    <div class="card">
      <h2>➕ Open a ticket for someone</h2>
      <div class="hint" style="margin-bottom:12px;">Members can also open their own with /ticket in Discord, or a button if you've set one up with /setticketchannel.</div>
      <form method="post" action="/dashboard/{guild_id}/tickets/open">
        <div class="field"><label>Member</label><select name="user_id" required>{member_opts}</select></div>
        <button class="btn" type="submit">Open Ticket</button>
      </form>
    </div>

    <div class="card">
      <h2>All tickets</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>#</th><th>Member</th><th>Status</th><th>Opened</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Tickets", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/tickets/open", methods=["POST"])
def tickets_open_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Pick a member."))
    result = _run_async(_open_ticket(guild_id, user_id))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/close", methods=["POST"])
def tickets_close_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        ticket_id = int(request.form["ticket_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Invalid ticket."))
    result = _run_async(_close_ticket(guild_id, ticket_id, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/setchannel", methods=["POST"])
def tickets_setchannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Pick a channel."))
    result = _run_async(_set_ticket_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


# ---------- backup download ----------

@app.route("/dashboard/<int:guild_id>/backup")
def backup_download(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    data = json.dumps(cfg, indent=2)
    return Response(
        data, mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=backup-{guild_id}.json"},
    )


# ---------- entrypoint ----------

def _run(port: int):
    app.run(host="0.0.0.0", port=port)


def start_web_app(
    bot, config, save_config, get_guild_cfg,
    give_role, remove_role,
    roster_add, roster_remove, promote, demote,
    kick, ban, timeout, warn,
    mass_add_role, mass_remove_role, mass_rename,
    announce, massannounce,
    showcase_add, showcase_remove,
    open_ticket, close_ticket, set_ticket_channel,
):
    """Call once from bot.py after the bot object exists. Runs Flask in a
    background thread so it doesn't block discord.py's event loop."""
    global _bot, _config, _save_config, _get_guild_cfg, _give_role, _remove_role
    global _roster_add, _roster_remove, _promote, _demote, _kick, _ban, _timeout, _warn
    global _mass_add_role, _mass_remove_role, _mass_rename, _announce, _massannounce
    global _showcase_add, _showcase_remove, _open_ticket, _close_ticket, _set_ticket_channel
    _bot = bot
    _config = config
    _save_config = save_config
    _get_guild_cfg = get_guild_cfg
    _give_role = give_role
    _remove_role = remove_role
    _roster_add = roster_add
    _roster_remove = roster_remove
    _promote = promote
    _demote = demote
    _kick = kick
    _ban = ban
    _timeout = timeout
    _warn = warn
    _mass_add_role = mass_add_role
    _mass_remove_role = mass_remove_role
    _mass_rename = mass_rename
    _announce = announce
    _massannounce = massannounce
    _showcase_add = showcase_add
    _showcase_remove = showcase_remove
    _open_ticket = open_ticket
    _close_ticket = close_ticket
    _set_ticket_channel = set_ticket_channel

    port = int(os.environ.get("PORT", 8080))
    thread = threading.Thread(target=_run, args=(port,), daemon=True)
    thread.start()
