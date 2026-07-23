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

import os
import secrets
import threading

import requests
from flask import Flask, redirect, request, session, url_for, render_template_string

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
</style>
"""


def render_page(title: str, body: str, show_logout: bool = True) -> str:
    logout_link = '<a href="/logout">Log out</a>' if show_logout and "user_id" in session else ""
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

    <div class="quicknav">
      <a href="#channels">📢 Channels</a>
      <a href="#roles">🎭 Roles</a>
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
    return render_page(f"{guild.name} — Dashboard", body)


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


# ---------- entrypoint ----------

def _run(port: int):
    app.run(host="0.0.0.0", port=port)


def start_web_app(bot, config, save_config, get_guild_cfg):
    """Call once from bot.py after the bot object exists. Runs Flask in a
    background thread so it doesn't block discord.py's event loop."""
    global _bot, _config, _save_config, _get_guild_cfg
    _bot = bot
    _config = config
    _save_config = save_config
    _get_guild_cfg = get_guild_cfg

    port = int(os.environ.get("PORT", 8080))
    thread = threading.Thread(target=_run, args=(port,), daemon=True)
    thread.start()
