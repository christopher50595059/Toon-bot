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
import csv
import html
import io
import json
import os
import secrets
import threading
from datetime import datetime, timezone

import requests
from flask import Flask, Response, redirect, request, session, url_for, render_template_string

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "").rstrip("/")  # e.g. https://your-app.onrender.com
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

DISCORD_API = "https://discord.com/api"

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
# Session cookies expire when the browser closes (not "permanent"/long-lived),
# so everyone has to log back in with Discord each time they open a new
# browser session, even if they were logged in before.
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_REFRESH_EACH_REQUEST"] = False

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
_untimeout = None
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
_send_dm = None
_set_rust_server = None
_set_rust_status_channel = None
_get_rust_status = None
_rust_command = None
_rust_get_players = None
_rust_kick_player = None
_rust_ban_player = None
_rust_get_banlist = None
_rust_unban_player = None
_set_backup_settings = None
_run_backup_now = None
_set_rust_alert_channel = None
_set_minecraft_alert_channel = None
_set_minecraft_server = None
_set_minecraft_status_channel = None
_get_minecraft_status = None
_minecraft_command = None
_relay_incoming_webhook = None
_tournament_create = None
_tournament_start = None
_tournament_report = None
_gamenight_create = None
_gamenight_cancel = None
_mvp_start = None
_mvp_end = None
_add_ticket_category = None
_remove_ticket_category = None
_set_ticket_questions = None
_get_ticket_messages = None
_send_ticket_message = None
_redeem_web_login_code = None
_minecraft_get_players = None
_minecraft_kick_player = None
_minecraft_ban_player = None
_minecraft_get_banlist = None
_minecraft_unban_player = None
_set_bot_status = None
_roster_add_all = None
_set_suggestions_channel = None
_suggestion_set_status = None
_giveaway_start = None
_giveaway_end = None
_put_on_cooldown = None
_remove_cooldown = None
_add_custom_command = None
_remove_custom_command = None
_refresh_roster = None
_automod_toggle = None
_automod_settings = None
_automod_add_word = None
_automod_remove_word = None
_set_ticket_autoclose = None
_set_reports_channel = None
_report_set_status = None
_fetch_discord_audit_log = None
_rust_set_wipe = None
_rust_set_popalert = None
_rust_set_joinleave_channel = None
_rust_set_bansync = None
_rust_set_rules = None
_rust_save = None
_rust_restart = None
_rust_announce = None
_rust_macro_add = None
_rust_macro_remove = None
_rust_macro_run = None
_rust_announcement_add = None
_rust_announcement_remove = None
_add_rank_bonus_role = None
_remove_rank_bonus_role = None
_set_whitelist_sync = None


# ---------- shared page chrome ----------

BASE_STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: dark;
    --accent: #3b82f6;
    --accent-hover: #60a5fa;
    --accent-soft: rgba(59,130,246,0.18);
    --bg: #05070d;
    --surface: #142240;
    --surface-hover: #1c2f52;
    --border: rgba(96,150,255,0.16);
    --border-hover: rgba(96,150,255,0.32);
    --text: #eef2fb;
    --text-dim: #94a1c2;
    --text-faint: #626c8c;
    --success: #22c55e;
    --danger: #f87171;
    --warning: #f5b942;
    --radius: 10px;
  }
  * { box-sizing: border-box; }
  html { scrollbar-color: #2f56a8 #060810; scrollbar-width: thin; }
  ::-webkit-scrollbar { width:10px; height:10px; }
  ::-webkit-scrollbar-track { background:#060810; }
  ::-webkit-scrollbar-thumb { background:#2f56a8; border-radius:6px; }
  ::-webkit-scrollbar-thumb:hover { background:#3d69c9; }

  @keyframes fadeInUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

  body {
    background:
      radial-gradient(ellipse 950px 600px at 10% 0%, rgba(59,130,246,0.34) 0%, transparent 60%),
      radial-gradient(ellipse 800px 600px at 95% 6%, rgba(37,99,235,0.28) 0%, transparent 58%),
      radial-gradient(ellipse 900px 700px at 50% 38%, rgba(29,78,216,0.18) 0%, transparent 62%),
      radial-gradient(ellipse 800px 650px at 4% 68%, rgba(30,64,175,0.22) 0%, transparent 58%),
      radial-gradient(ellipse 850px 650px at 100% 82%, rgba(37,99,235,0.20) 0%, transparent 58%),
      linear-gradient(180deg, #0a0f1e 0%, #080c18 35%, #070b16 65%, #060a14 100%);
    color:var(--text); font-family:'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size:14.5px; font-weight:400; margin:0; padding:0 0 80px; line-height:1.5; min-height:100vh;
  }

  .wrap { max-width:1200px; margin:0 auto; padding:28px 24px; }
  h1 {
    font-size:22px; margin:0 0 3px; font-weight:700; letter-spacing:-0.3px; color:var(--text);
    animation:fadeInUp 0.3s ease;
  }
  h2 {
    font-size:14px; color:var(--text); margin:0 0 14px; font-weight:600;
    display:flex; align-items:center; gap:8px; letter-spacing:-0.1px;
  }
  .card {
    background:linear-gradient(160deg, #142240 0%, #0a0e1a 100%);
    border:1px solid var(--border); border-radius:var(--radius);
    padding:20px 22px; margin-bottom:14px;
    box-shadow:0 1px 3px rgba(0,0,0,0.4);
    transition:border-color 0.15s ease; animation:fadeInUp 0.25s ease backwards;
  }
  .card:hover { border-color:var(--border-hover); }
  a { color:var(--accent-hover); text-decoration:none; }
  a:hover { text-decoration:underline; color:#60a5fa; }
  .btn {
    display:inline-block; background:linear-gradient(135deg, #4f95ff, #2563eb);
    color:#fff; padding:9px 18px; border-radius:8px;
    border:none; font-family:inherit; font-size:13.5px; font-weight:600; letter-spacing:0;
    cursor:pointer; transition:filter 0.15s ease, transform 0.1s ease;
    box-shadow:0 2px 14px rgba(59,130,246,0.45);
  }
  .btn:hover { filter:brightness(1.12); text-decoration:none; }
  .btn:active { transform:translateY(1px); }
  .btn-secondary { background:linear-gradient(135deg, #1c2333, #12151f); color:var(--text); box-shadow:none; }
  .btn-secondary:hover { background:linear-gradient(135deg, #232b3f, #171b28); filter:none; }
  .field { margin-bottom:12px; }
  .field:last-child { margin-bottom:0; }
  label { display:block; font-size:12px; color:var(--text-dim); margin:0 0 5px; font-weight:500; }
  select, input[type=number], input[type=text], input[type=date], input[type=time], input[type=file] {
    width:100%; background:#0e1016; border:1px solid var(--border); color:var(--text);
    padding:9px 11px; border-radius:8px; font-family:inherit; font-size:14px; font-weight:400;
    transition:border-color 0.15s ease, box-shadow 0.15s ease;
  }
  select {
    appearance:none; -webkit-appearance:none;
    background-image:url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239497a6' stroke-width='2'%3e%3cpath d='M6 9l6 6 6-6'/%3e%3c/svg%3e");
    background-repeat:no-repeat; background-position:right 10px center; background-size:18px; padding-right:36px;
  }
  select:hover, input:hover { border-color:var(--border-hover); }
  select:focus, input:focus { outline:none; border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft); }
  ::placeholder { color:var(--text-faint); }
  .hint { color:var(--text-dim); font-size:12.5px; margin-top:4px; }
  .flash {
    background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.35);
    color:#86e6a8; padding:10px 14px; margin-bottom:14px; font-size:13.5px; font-weight:500;
    border-radius:8px;
  }
  .guild-list a {
    display:flex; align-items:center; gap:12px;
    background:linear-gradient(160deg, #142240 0%, #0a0e1a 100%); border:1px solid var(--border); border-radius:var(--radius);
    padding:12px 14px; margin-bottom:8px; color:var(--text);
    transition:all 0.15s ease;
  }
  .guild-list a:hover { border-color:var(--border-hover); background:linear-gradient(160deg, #1c2f52 0%, #0c1120 100%); text-decoration:none; }
  .topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
  .topbar a { color:var(--text-dim); font-size:13px; }
  .topbar a:hover { color:var(--text); }
  form { margin:0; }
  .quicknav { display:flex; gap:6px; margin:12px 0 16px; flex-wrap:wrap; }
  .quicknav a {
    background:var(--surface); border:1px solid var(--border); padding:7px 14px; border-radius:7px;
    font-size:12.5px; font-weight:500; color:var(--text); transition:all 0.15s ease;
  }
  .quicknav a:hover { background:linear-gradient(135deg, #4f95ff, #2563eb); border-color:transparent; color:#fff; text-decoration:none; }
  .save-bar { position:sticky; bottom:14px; margin-top:8px; }
  .save-bar .btn { width:100%; padding:13px; font-size:14px; box-shadow:0 4px 20px rgba(37,99,235,0.4); }
  .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  @media (max-width:520px) { .grid-2 { grid-template-columns:1fr; } }
  .card-row { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px; align-items:start; }
  .card-row .card { margin-bottom:0; }
  .log-wrap { max-height:520px; overflow-y:auto; border:1px solid var(--border); border-radius:8px; background:#060810; }
  table.log-table { width:100%; border-collapse:collapse; font-size:13px; }
  .log-table th {
    position:sticky; top:0; background:#0e1424; text-align:left; padding:9px 12px;
    font-size:11px; text-transform:uppercase; letter-spacing:0.5px; font-weight:600;
    color:var(--text-dim); border-bottom:1px solid var(--border);
  }
  .log-table td { padding:9px 12px; border-bottom:1px solid var(--border); vertical-align:top; }
  .log-table tr:hover td { background:rgba(37,99,235,0.05); }
  .log-table tr:last-child td { border-bottom:none; }
  .pill {
    display:inline-block; background:var(--accent-soft); border:1px solid rgba(37,99,235,0.35); color:#93c5fd;
    padding:2px 10px; font-size:11.5px; font-weight:600; border-radius:20px;
  }
  .filter-bar { display:flex; gap:10px; align-items:end; margin-bottom:18px; flex-wrap:wrap; }
  .filter-bar .field { margin-bottom:0; flex:1; min-width:200px; }
  .action-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(140px, 1fr)); gap:10px; }
  .action-tile {
    display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px;
    background:linear-gradient(160deg, #142240 0%, #0a0e1a 100%); border:1px solid var(--border); border-radius:var(--radius); padding:18px 10px;
    color:var(--text); font-weight:600; font-size:12.5px; text-align:center;
    transition:all 0.15s ease;
  }
  .action-tile span { font-size:22px; }
  .action-tile:hover { border-color:var(--accent); background:linear-gradient(160deg, #1c2f52 0%, #0c1120 100%); text-decoration:none; transform:translateY(-2px); }
  .stats-strip { display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:12px; margin:18px 0 24px; }
  .stat-tile {
    background:linear-gradient(160deg, #142240 0%, #0a0e1a 100%); border:1px solid var(--border); border-radius:var(--radius); padding:16px; text-align:center;
    transition:border-color 0.15s ease; animation:fadeInUp 0.3s ease backwards;
  }
  .stat-tile:hover { border-color:var(--border-hover); }
  .stat-tile .icon { font-size:18px; margin-bottom:4px; opacity:0.9; }
  .stat-tile .num { font-size:24px; font-weight:700; color:#5fa4ff; }
  .stat-tile .label { font-size:11px; letter-spacing:0.3px; color:var(--text-dim); margin-top:4px; font-weight:500; }
  .stat-tile.violet .num { color:#a78bfa; }
  .stat-tile.magenta .num { color:#f472b6; }
  .stat-tile.gold .num { color:var(--warning); }
  .stat-tile.grey .num { color:var(--text-dim); }
  .page-layout { display:flex; gap:28px; align-items:flex-start; }
  .sidenav { width:190px; flex-shrink:0; position:sticky; top:24px; display:flex; flex-direction:column; gap:1px; }
  .sidenav a {
    display:flex; align-items:center; gap:10px; padding:8px 12px; color:var(--text-dim);
    font-size:13px; font-weight:500; border-radius:7px; transition:all 0.12s ease;
  }
  .sidenav a:hover { background:var(--surface); color:var(--text); text-decoration:none; }
  .sidenav a.active { background:linear-gradient(90deg, rgba(59,130,246,0.32), rgba(59,130,246,0.06)); color:#a3c9ff; font-weight:600; }
  .sidenav .sidenav-label {
    font-size:10.5px; text-transform:uppercase; letter-spacing:0.8px;
    color:var(--text-faint); font-weight:600; margin:16px 0 4px 12px;
  }
  .sidenav .sidenav-label:first-child { margin-top:0; }
  .main-col { flex:1; min-width:0; }
  @media (max-width:760px) {
    .page-layout { flex-direction:column; }
    .sidenav { width:100%; position:static; flex-direction:row; flex-wrap:wrap; }
    .sidenav .sidenav-label { display:none; }
  }
  .search-wrap { position:relative; }
  .search-dropdown-floating {
    display:none; position:absolute; z-index:5000;
    max-height:280px; overflow-y:auto; border-radius:8px;
    background:#191c25; border:1px solid var(--border-hover); box-shadow:0 8px 24px rgba(0,0,0,0.5);
  }
  .search-option {
    padding:9px 14px; font-size:13.5px; font-weight:400; color:var(--text);
    cursor:pointer; border-bottom:1px solid var(--border); transition:background 0.1s ease;
  }
  .search-option:last-child { border-bottom:none; }
  .search-option:hover { background:var(--accent-soft); color:#fff; }
  .chips-box { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
  .chip {
    display:inline-flex; align-items:center; gap:6px; background:var(--accent-soft);
    border:1px solid rgba(59,130,246,0.35); color:#93c5fd; padding:4px 6px 4px 12px;
    border-radius:20px; font-size:12.5px; font-weight:500;
  }
  .chip-remove {
    background:none; border:none; color:#93c5fd; cursor:pointer; font-size:16px; line-height:1;
    padding:0 4px; border-radius:50%; transition:background 0.1s ease;
  }
  .chip-remove:hover { background:rgba(248,113,113,0.25); color:#f87171; }
</style>
"""


SIDENAV_SECTIONS = [
    ("General", [
        ("dashboard", "⚙️", "Settings"),
        ("setup_wizard_page", "🧭", "Setup Wizard"),
        ("lookup_page", "🔎", "Member Lookup"),
        ("roles_page", "🎭", "Roles"),
        ("roster_page", "📋", "Roster"),
    ]),
    ("Moderation", [
        ("moderation_page", "🛡️", "Moderation"),
        ("automod_page", "🚨", "Auto-Moderation"),
        ("warnings_page", "⚠️", "Warnings"),
        ("reports_page", "🚩", "Reports"),
    ]),
    ("Game Servers", [
        ("game_servers_page", "🕹️", "Overview"),
        ("rust_page", "🦀", "Rust: Overview"),
        ("rust_players_page", "🎮", "Rust: Players"),
        ("rust_bans_page", "🚫", "Rust: Bans"),
        ("rust_macros_page", "⚡", "Rust: Macros"),
        ("minecraft_page", "⛏️", "Minecraft: Overview"),
        ("minecraft_players_page", "🎮", "Minecraft: Players"),
        ("minecraft_bans_page", "🚫", "Minecraft: Bans"),
        ("whitelist_sync_page", "🔗", "Whitelist Sync"),
    ]),
    ("Community", [
        ("tournaments_page", "🏆", "Tournaments"),
        ("gamenights_page", "🎮", "Game Nights"),
        ("mvp_page", "⭐", "MVP Voting"),
        ("suggestions_page", "💡", "Suggestions"),
        ("giveaways_page", "🎉", "Giveaways"),
        ("trivia_page", "🧠", "Trivia Leaderboard"),
        ("rank_bonus_roles_page", "🎁", "Rank Bonus Roles"),
        ("custom_commands_page", "💬", "Custom Commands"),
    ]),
    ("Bulk & Broadcast", [
        ("mass_page", "🧰", "Mass Actions"),
        ("announce_page", "📣", "Announcements"),
        ("showcase_page", "🎭", "Showcase"),
        ("crosspost_page", "🔀", "Cross-Posting"),
        ("greetings_page", "🔊", "VC Greetings"),
        ("tickets_page", "🎫", "Tickets"),
        ("dm_page", "✉️", "Direct Message"),
        ("webhooks_page", "🔌", "Webhooks"),
    ]),
    ("Insight & Logs", [
        ("logs_page", "🗂️", "Logs"),
        ("activity_log_page", "🖱️", "Dashboard Activity"),
        ("discord_audit_log_page", "🗂️", "Discord Audit Log"),
        ("login_history_page", "🔑", "Login History"),
        ("activity_page", "📈", "Message Activity"),
        ("voice_activity_page", "🎙️", "Voice Activity"),
        ("growth_page", "📊", "Growth Analytics"),
    ]),
    ("System", [
        ("afk_page", "💤", "AFK Status"),
        ("backup_download", "💾", "Backup"),
        ("backups_page", "🗄️", "Auto Backups"),
    ]),
]


SEARCH_JS = """
<script>
  let SEARCH_MAPS = {};
  let _activeSearchInput = null;
  let _dropdownEl = null;

  function getDropdownEl() {
    if (!_dropdownEl) {
      _dropdownEl = document.createElement('div');
      _dropdownEl.className = 'search-dropdown-floating';
      document.body.appendChild(_dropdownEl);
    }
    return _dropdownEl;
  }

  function onSearchFocus(inputEl) {
    renderSearchOptions(inputEl, inputEl.value);
  }
  function onSearchInput(inputEl) {
    renderSearchOptions(inputEl, inputEl.value);
  }
  function renderSearchOptions(inputEl, query) {
    _activeSearchInput = inputEl;
    const map = SEARCH_MAPS[inputEl.dataset.map] || {};
    const q = query.toLowerCase();
    const keys = Object.keys(map).filter(k => k.toLowerCase().includes(q)).slice(0, 60);
    const dropdown = getDropdownEl();
    dropdown.innerHTML = '';
    if (keys.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'search-option';
      empty.style.opacity = '0.5';
      empty.style.cursor = 'default';
      empty.textContent = 'No matches';
      dropdown.appendChild(empty);
    } else {
      keys.forEach(function(k) {
        const opt = document.createElement('div');
        opt.className = 'search-option';
        opt.textContent = k;
        opt.addEventListener('mousedown', function(e) {
          e.preventDefault();
          selectSearchOption(k);
        });
        dropdown.appendChild(opt);
      });
    }
    const rect = inputEl.getBoundingClientRect();
    dropdown.style.left = (rect.left + window.scrollX) + 'px';
    dropdown.style.top = (rect.bottom + window.scrollY + 4) + 'px';
    dropdown.style.width = rect.width + 'px';
    dropdown.style.display = 'block';
  }
  function selectSearchOption(label) {
    if (!_activeSearchInput) return;
    const map = SEARCH_MAPS[_activeSearchInput.dataset.map] || {};
    const id = map[label] || '';

    if (_activeSearchInput.dataset.multi === 'true') {
      const chipsBox = _activeSearchInput.closest('.field').querySelector('.chips-box');
      if (!chipsBox || !id) { getDropdownEl().style.display = 'none'; return; }
      if (chipsBox.querySelector('input[value="' + id + '"]')) {
        _activeSearchInput.value = '';
        getDropdownEl().style.display = 'none';
        return; // already added
      }
      const fieldName = chipsBox.dataset.fieldName;
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = '<input type="hidden" name="' + fieldName + '" value="' + id + '">' +
        '<span>' + label + '</span><button type="button" class="chip-remove">&times;</button>';
      chip.querySelector('.chip-remove').addEventListener('click', function() { chip.remove(); });
      chipsBox.appendChild(chip);
      _activeSearchInput.value = '';
      getDropdownEl().style.display = 'none';
      return;
    }

    const field = _activeSearchInput.closest('.field');
    const hidden = field.querySelector('input[type=hidden]');
    _activeSearchInput.value = label;
    hidden.value = id;
    getDropdownEl().style.display = 'none';
  }
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-wrap') && !e.target.closest('.search-dropdown-floating')) {
      if (_dropdownEl) _dropdownEl.style.display = 'none';
    }
  });
  window.addEventListener('scroll', function() {
    if (_dropdownEl && _dropdownEl.style.display === 'block' && _activeSearchInput) {
      renderSearchOptions(_activeSearchInput, _activeSearchInput.value);
    }
  }, true);

  function filterTable(inputEl, tableId) {
    const q = inputEl.value.toLowerCase();
    const table = document.getElementById(tableId);
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr, tr');
    rows.forEach(function(row) {
      if (row.querySelector('th')) return; // skip header row
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(q) ? '' : 'none';
    });
  }

  // ---- AJAX form submission: swap page content without a full reload ----
  function _showLoadingBar() {
    let bar = document.getElementById('_ajaxBar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = '_ajaxBar';
      bar.style.cssText = 'position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent,#6366f1);z-index:99999;transition:width 0.25s ease;';
      document.body.appendChild(bar);
    }
    bar.style.width = '0%';
    requestAnimationFrame(function() { bar.style.width = '75%'; });
  }
  function _hideLoadingBar() {
    const bar = document.getElementById('_ajaxBar');
    if (!bar) return;
    bar.style.width = '100%';
    setTimeout(function() { bar.style.width = '0%'; }, 250);
  }
  function _reExecuteScripts(container) {
    container.querySelectorAll('script').forEach(function(oldScript) {
      const newScript = document.createElement('script');
      for (const attr of oldScript.attributes) newScript.setAttribute(attr.name, attr.value);
      newScript.textContent = oldScript.textContent;
      oldScript.parentNode.replaceChild(newScript, oldScript);
    });
  }
  function _swapPageContent(html, newUrl) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const newWrap = doc.querySelector('.wrap');
    const curWrap = document.querySelector('.wrap');
    if (!newWrap || !curWrap) { window.location.href = newUrl; return; }
    curWrap.innerHTML = newWrap.innerHTML;
    document.title = doc.title;
    if (newUrl) history.pushState({ajax: true}, '', newUrl);
    _reExecuteScripts(curWrap);
    _hideLoadingBar();
  }
  async function navigateAjax(url) {
    _showLoadingBar();
    try {
      const resp = await fetch(url, {method: 'GET', credentials: 'same-origin'});
      if (!resp.ok) throw new Error('status ' + resp.status);
      const html = await resp.text();
      _swapPageContent(html, resp.url);
    } catch (err) {
      window.location.href = url; // fall back to a normal page load
    }
  }
  async function submitFormAjax(form) {
    const method = (form.getAttribute('method') || 'GET').toUpperCase();
    const action = form.getAttribute('action') || window.location.href;
    _showLoadingBar();
    try {
      let resp;
      if (method === 'GET') {
        const params = new URLSearchParams(new FormData(form));
        const sep = action.includes('?') ? '&' : '?';
        resp = await fetch(action + sep + params.toString(), {method: 'GET', credentials: 'same-origin'});
      } else {
        resp = await fetch(action, {method: 'POST', body: new FormData(form), credentials: 'same-origin'});
      }
      if (!resp.ok) throw new Error('status ' + resp.status);
      const html = await resp.text();
      _swapPageContent(html, resp.url);
    } catch (err) {
      _hideLoadingBar();
      HTMLFormElement.prototype.submit.call(form); // fall back to a normal page load
    }
  }
  document.addEventListener('click', function(e) {
    const link = e.target.closest('.sidenav a, .action-tile, .quicknav a');
    if (!link || !link.href) return;
    if (link.hasAttribute('data-no-ajax') || link.target === '_blank') return;
    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin) return; // never intercept external links
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return; // same-page anchor jump
    e.preventDefault();
    navigateAjax(link.href);
  });
  document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.hasAttribute('data-no-ajax')) return;
    e.preventDefault();
    submitFormAjax(form);
  });
  window.addEventListener('popstate', function() { window.location.reload(); });
</script>
"""


def render_page(title: str, body: str, show_logout: bool = True, guild_id: int = None) -> str:
    logout_link = '<a href="/logout">Log out</a>' if show_logout and "user_id" in session else ""

    if guild_id is None:
        return render_template_string(
            f"""
            <!doctype html><html><head><meta charset="utf-8">
            <title>{{{{ title }}}}</title>{BASE_STYLE}{SEARCH_JS}</head>
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

    _guild, _member, _level = _get_access_level(guild_id)
    viewer_banner = (
        '<div class="flash" style="background:rgba(139,150,179,0.12); border-color:rgba(139,150,179,0.35); color:#c3c9db;">'
        '👁️ You have view-only access here — you can look around, but any changes you submit won\'t be saved.</div>'
        if _level == "viewer" else ""
    )

    return render_template_string(
        f"""
        <!doctype html><html><head><meta charset="utf-8">
        <title>{{{{ title }}}}</title>{BASE_STYLE}{SEARCH_JS}</head>
        <body><div class="wrap" style="max-width:1040px;">
        <div class="topbar"><h1>🤖 Bot Dashboard</h1>{logout_link}</div>
        <div class="page-layout">
          <div class="sidenav">{{{{ nav|safe }}}}</div>
          <div class="main-col">{viewer_banner}{{{{ body|safe }}}}</div>
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
            <div class="card" style="text-align:center; padding:48px 32px;">
              <div style="font-size:48px; margin-bottom:8px;">🤖</div>
              <h1 style="font-size:28px; margin-bottom:10px;">Bot Control Deck</h1>
              <p class="hint" style="font-size:14px; margin-bottom:24px;">Manage roles, moderation, tickets, integrations, and more — all from your browser.</p>
              <a class="btn" href="/login" style="padding:13px 32px; font-size:14px;">🔐 Login with Discord</a>
              <div class="hint" style="margin-top:18px;"><a href="/login/code">Having trouble? Use a login code instead →</a></div>
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


# ---------- code-based login (fallback when Discord OAuth doesn't work) ----------

@app.route("/login/code")
def login_code_page():
    error = request.args.get("error", "")
    error_html = f'<div class="flash" style="background:linear-gradient(135deg,rgba(255,80,80,0.15),rgba(40,20,20,0.9)); border-color:rgba(255,80,80,0.4); color:#ffc8c8;">{error}</div>' if error else ""
    return render_page("Login with code", f"""
        <div class="card" style="text-align:center; padding:40px 32px;">
          <div style="font-size:40px; margin-bottom:8px;">🔑</div>
          <h1 style="font-size:24px; margin-bottom:10px;">Login with a code</h1>
          <p class="hint" style="font-size:14px; margin-bottom:20px;">
            In Discord, run <code>/weblogin</code> in any server the bot is in. It'll reply with a 6-character
            one-time code, valid for 10 minutes. Enter it below.
          </p>
          {error_html}
          <form method="post" action="/login/code" style="max-width:280px; margin:0 auto;">
            <div class="field"><input type="text" name="code" placeholder="ABC123" maxlength="6" autocomplete="off" style="text-align:center; text-transform:uppercase; font-size:20px; letter-spacing:4px;" required></div>
            <button class="btn" type="submit" style="width:100%;">Log In</button>
          </form>
          <div class="hint" style="margin-top:18px;"><a href="/login">← Back to Discord login</a></div>
        </div>
    """, show_logout=False)


@app.route("/login/code", methods=["POST"])
def login_code_submit():
    code = request.form.get("code", "").strip()
    if not code:
        return redirect(url_for("login_code_page", error="Enter a code."))

    user_id = _redeem_web_login_code(code)
    if user_id is None:
        return redirect(url_for("login_code_page", error="That code is invalid or has expired — run /weblogin again for a new one."))

    user = _bot.get_user(user_id)
    session["user_id"] = user_id
    session["username"] = user.name if user else "there"

    for guild in _admin_guilds_for(user_id):
        cfg = _get_guild_cfg(guild.id)
        logins = cfg.setdefault("dashboard_logins", [])
        logins.append({
            "user_id": user_id,
            "username": session["username"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        cfg["dashboard_logins"] = logins[-100:]
    _save_config(_config)

    return redirect(url_for("guild_picker"))


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

    for guild in _admin_guilds_for(session["user_id"]):
        cfg = _get_guild_cfg(guild.id)
        logins = cfg.setdefault("dashboard_logins", [])
        logins.append({
            "user_id": session["user_id"],
            "username": session["username"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        cfg["dashboard_logins"] = logins[-100:]  # keep it capped
    _save_config(_config)

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
            f'<img src="{g.icon.url}" style="width:44px;height:44px;border-radius:10px;">'
            if g.icon else
            '<div style="width:44px;height:44px;border-radius:10px;background:var(--accent);display:flex;'
            'align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#04050a;">' + g.name[0].upper() + '</div>'
        )
        items += f"""
        <a href="/dashboard/{g.id}" style="display:flex;align-items:center;gap:14px;">
          {icon_html}
          <div>
            <div style="font-weight:700; font-size:15px;">{g.name}</div>
            <div class="hint" style="margin-top:2px;">👥 {g.member_count} member(s)</div>
          </div>
        </a>
        """
    body = f"""
        <h1 style="margin-bottom:4px;">🗂️ Your Servers</h1>
        <p class="hint" style="margin-bottom:18px;">Pick a server to manage.</p>
        <div class="guild-list">{items}</div>
    """
    return render_page("Your servers", body)


# ---------- dashboard ----------

def _get_access_level(guild_id: int):
    """Returns (guild, member, level) where level is 'admin', 'manager', 'viewer',
    or None. No side effects (no logging) — safe to call more than once per request."""
    if "user_id" not in session:
        return None, None, None
    guild = _bot.get_guild(guild_id)
    if guild is None:
        return None, None, None
    member = guild.get_member(session["user_id"])
    if member is None:
        return None, None, None
    cfg = _get_guild_cfg(guild.id)
    if member.guild_permissions.administrator:
        return guild, member, "admin"
    manager_role_id = cfg.get("manager_role_id")
    if manager_role_id and any(r.id == manager_role_id for r in member.roles):
        return guild, member, "manager"
    ban_role_threshold_id = cfg.get("ban_role_threshold_id")
    if ban_role_threshold_id:
        threshold_role = guild.get_role(ban_role_threshold_id)
        if threshold_role and member.top_role >= threshold_role:
            return guild, member, "manager"  # same access level as manager — see /setbanrole
    viewer_threshold_id = cfg.get("viewer_rank_threshold_id")
    if viewer_threshold_id:
        ranks = cfg.get("ranks", [])
        if viewer_threshold_id in ranks:
            idx = ranks.index(viewer_threshold_id)
            eligible_rank_ids = set(ranks[idx:])  # that rank and every rank below it
            if any(r.id in eligible_rank_ids for r in member.roles):
                return guild, member, "viewer"
    return guild, member, None


def _check_access(guild_id: int):
    """Returns (guild, member) if the logged-in user can access this guild's
    dashboard at all — any tier, admin/manager/viewer — else (None, None).
    Also logs POST actions to the dashboard activity log (viewers never reach
    this as POST since a separate before_request hook blocks them earlier)."""
    guild, member, level = _get_access_level(guild_id)
    if level is None:
        return None, None
    cfg = _get_guild_cfg(guild.id)

    if request.method == "POST":
        log = cfg.setdefault("dashboard_activity_log", [])
        log.append({
            "actor_id": member.id,
            "path": request.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        cfg["dashboard_activity_log"] = log[-200:]  # keep it capped
        _save_config(_config)

    return guild, member


@app.before_request
def _enforce_viewer_readonly():
    """Viewers can open every page (handled normally by _check_access), but
    can't submit any form. Checked here once, centrally, instead of adding a
    guard to every individual POST route."""
    if request.method != "POST" or not request.path.startswith("/dashboard/"):
        return None
    parts = request.path.split("/")
    try:
        guild_id = int(parts[2])
    except (IndexError, ValueError):
        return None
    guild, member, level = _get_access_level(guild_id)
    if level == "viewer":
        return "❌ Your access to this dashboard is view-only — ask an admin for edit access to make changes.", 403


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


def _member_search_assets(guild):
    """Include ONCE per page (anywhere in the body). Feeds SEARCH_MAPS.member
    for any _member_search_field() on the same page."""
    mapping = {}
    members = sorted((m for m in guild.members if not m.bot), key=lambda m: m.display_name.lower())
    for m in members:
        mapping[f"{m.display_name} ({m})"] = str(m.id)
    return f"<script>SEARCH_MAPS.member = {json.dumps(mapping)};</script>"


def _member_search_field(label="Member", field_name="user_id"):
    """A type-to-search member picker with a custom, fully-styled dropdown.
    Pair with one _member_search_assets() call anywhere earlier in the page."""
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="member" placeholder="Type or click to browse..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <input type="hidden" name="{field_name}">
    </div>
    """


def _member_multi_search_field(label="Members", field_name="user_ids"):
    """A type-to-search picker that lets you select MULTIPLE members, shown
    as removable chips. Each selected member becomes its own hidden input
    sharing {field_name}, so the route reads them with request.form.getlist().
    Pair with one _member_search_assets() call anywhere earlier in the page."""
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="member" data-multi="true" placeholder="Type to search, click to add..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <div class="chips-box" data-field-name="{field_name}"></div>
    </div>
    """


def _unique_labels(items, name_fn, id_fn, prefix):
    """Build a {label: id} map where duplicate names get a short ID suffix
    appended so they don't silently collide/overwrite each other."""
    names = [name_fn(item) for item in items]
    counts = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1

    mapping = {}
    for item in items:
        name = name_fn(item)
        item_id = id_fn(item)
        label = f"{prefix}{name}"
        if counts[name] > 1:
            label = f"{prefix}{name} (…{str(item_id)[-4:]})"
        mapping[label] = str(item_id)
    return mapping


def _role_search_assets(guild):
    """Include ONCE per page. Feeds SEARCH_MAPS.role for any _role_search_field()."""
    roles = [r for r in sorted(guild.roles, key=lambda r: r.position, reverse=True) if not r.is_default()]
    mapping = _unique_labels(roles, lambda r: r.name, lambda r: r.id, "@")
    return f"<script>SEARCH_MAPS.role = {json.dumps(mapping)};</script>"


def _role_search_field(label="Role", field_name="role_id", guild=None, current_id=None):
    """A type-to-search role picker. Pass guild+current_id to pre-fill an
    existing selection (e.g. on the settings page)."""
    current_label = ""
    current_value = ""
    if guild is not None and current_id:
        role = guild.get_role(current_id)
        if role:
            dupes = sum(1 for r in guild.roles if r.name == role.name)
            current_label = f"@{role.name}" if dupes <= 1 else f"@{role.name} (…{str(current_id)[-4:]})"
            current_value = str(current_id)
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="role" value="{current_label}" placeholder="Type or click to browse..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <input type="hidden" name="{field_name}" value="{current_value}">
    </div>
    """


def _channel_search_assets(guild, channel_type="text"):
    """Include ONCE per page. Feeds SEARCH_MAPS.channel for any _channel_search_field()."""
    channels = guild.text_channels if channel_type == "text" else guild.voice_channels
    mapping = _unique_labels(channels, lambda c: c.name, lambda c: c.id, "#")
    return f"<script>SEARCH_MAPS.channel = {json.dumps(mapping)};</script>"


def _channel_search_field(label="Channel", field_name="channel_id", guild=None, current_id=None):
    """A type-to-search channel picker. Pair with one _channel_search_assets()
    call anywhere earlier in the same page's body."""
    current_label = ""
    current_value = ""
    if guild is not None and current_id:
        channel = guild.get_channel(current_id)
        if channel:
            dupes = sum(1 for c in guild.text_channels if c.name == channel.name)
            current_label = f"#{channel.name}" if dupes <= 1 else f"#{channel.name} (…{str(current_id)[-4:]})"
            current_value = str(current_id)
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="channel" value="{current_label}" placeholder="Type or click to browse..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <input type="hidden" name="{field_name}" value="{current_value}">
    </div>
    """


def _category_search_assets(guild):
    """Include ONCE per page. Feeds SEARCH_MAPS.category for any _category_search_field()."""
    mapping = _unique_labels(guild.categories, lambda c: c.name, lambda c: c.id, "📁 ")
    return f"<script>SEARCH_MAPS.category = {json.dumps(mapping)};</script>"


def _category_search_field(label="Category", field_name="category_id"):
    """A type-to-search Discord category picker."""
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="category" placeholder="Type or click to browse..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <input type="hidden" name="{field_name}">
    </div>
    """


def _rank_options(guild, cfg):
    """Only the roles configured via /setranks, highest first — used for roster forms."""
    rank_ids = cfg.get("ranks", [])
    opts = ['<option value="">— pick a rank —</option>']
    for rid in rank_ids:
        role = guild.get_role(rid)
        if role:
            opts.append(f'<option value="{role.id}">@{role.name}</option>')
    return "".join(opts)


def _rank_search_assets(guild, cfg):
    """Include ONCE per page. Feeds SEARCH_MAPS.rank — limited to configured
    ranks only (not every role in the server)."""
    rank_ids = cfg.get("ranks", [])
    roles = [guild.get_role(rid) for rid in rank_ids]
    roles = [r for r in roles if r is not None]
    mapping = _unique_labels(roles, lambda r: r.name, lambda r: r.id, "@")
    return f"<script>SEARCH_MAPS.rank = {json.dumps(mapping)};</script>"


def _rank_search_field(label="Rank", field_name="rank_id", guild=None, current_id=None):
    """Pass guild+current_id to pre-fill an existing selection (e.g. on the settings page)."""
    current_label = ""
    current_value = ""
    if guild is not None and current_id:
        role = guild.get_role(current_id)
        if role:
            current_label = f"@{role.name}"
            current_value = str(current_id)
    return f"""
    <div class="field">
      <label>{label}</label>
      <div class="search-wrap">
        <input type="text" data-map="rank" value="{current_label}" placeholder="Type or click to browse..." autocomplete="off"
               oninput="onSearchInput(this)" onfocus="onSearchFocus(this)">
      </div>
      <input type="hidden" name="{field_name}" value="{current_value}">
    </div>
    """


def _run_async(coro, timeout=15):
    """Bridge a Flask request (running in its own thread) into the bot's
    asyncio event loop (running in the main thread), and wait for the result."""
    future = asyncio.run_coroutine_threadsafe(coro, _bot.loop)
    try:
        return future.result(timeout=timeout)
    except Exception as e:
        return f"❌ Something went wrong: {e}"


def _fire_and_forget(coro):
    """For background tasks the request doesn't wait on (e.g. bulk actions
    that could take minutes). Unlike a bare asyncio.run_coroutine_threadsafe,
    this makes sure an unexpected exception gets printed instead of vanishing
    with zero trace — since nothing else is watching this task complete."""
    future = asyncio.run_coroutine_threadsafe(coro, _bot.loop)

    def _log_if_failed(f):
        try:
            f.result()
        except Exception as e:
            print(f"⚠️ Background task failed: {e}")

    future.add_done_callback(_log_if_failed)


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
    for i in range(16):
        selected = ranks[i] if i < len(ranks) else None
        rank_fields += _role_search_field(f"Rank {i + 1} {'(highest)' if i == 0 else ''}", f"rank{i}", guild, selected)

    guild_icon_html = (
        f'<img src="{guild.icon.url}" style="width:32px;height:32px;border-radius:8px;vertical-align:middle;margin-right:10px;">'
        if guild.icon else ""
    )
    role_assets = _role_search_assets(guild)
    channel_assets = _channel_search_assets(guild)
    rank_picker_assets = _rank_search_assets(guild, cfg)

    roster_size = len(cfg.get("roster", []))
    open_tickets = sum(1 for t in cfg.get("tickets", {}).values() if t.get("status") == "open")
    total_warnings = sum(len(w) for w in cfg.get("warnings", {}).values())
    afk_count = len(cfg.get("afk", {}))

    stats_html = f"""
    <div class="stats-strip">
      <div class="stat-tile"><div class="icon">👥</div><div class="num">{guild.member_count}</div><div class="label">Members</div></div>
      <div class="stat-tile violet"><div class="icon">📋</div><div class="num">{roster_size}</div><div class="label">On Roster</div></div>
      <div class="stat-tile magenta"><div class="icon">🎫</div><div class="num">{open_tickets}</div><div class="label">Open Tickets</div></div>
      <div class="stat-tile gold"><div class="icon">⚠️</div><div class="num">{total_warnings}</div><div class="label">Warnings</div></div>
      <div class="stat-tile grey"><div class="icon">💤</div><div class="num">{afk_count}</div><div class="label">Currently AFK</div></div>
    </div>
    """

    recent_actions = list(reversed(cfg.get("dashboard_activity_log", [])))[:5]
    if recent_actions:
        recent_rows = ""
        for entry in recent_actions:
            actor = guild.get_member(entry.get("actor_id"))
            actor_name = actor.display_name if actor else f"Unknown ({entry.get('actor_id')})"
            recent_rows += f"""
            <tr>
              <td>{actor_name}</td>
              <td class="hint">{html.escape(entry.get('path', ''))}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(entry.get('timestamp'))}</td>
            </tr>
            """
        recent_activity_html = f"""
        <div class="card">
          <h2>🕒 Recent Activity</h2>
          <div class="log-wrap" style="max-height:220px;"><table class="log-table">
            <tr><th>Staff Member</th><th>Action</th><th>When</th></tr>
            {recent_rows}
          </table></div>
          <div class="hint" style="margin-top:8px;"><a href="/dashboard/{guild_id}/activitylog">View full activity log →</a></div>
        </div>
        """
    else:
        recent_activity_html = ""

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/guilds">&larr; All servers</a></div>
    <h1 style="margin-top:18px;">{guild_icon_html}{guild.name}</h1>
    {stats_html}
    <div class="hint" style="margin-bottom:12px;">📡 Public status page (no login, safe to share with members): <a href="/status/{guild_id}" target="_blank">{DASHBOARD_URL}/status/{guild_id}</a></div>
    {flash_html}
    {recent_activity_html}
    {role_assets}
    {channel_assets}
    {rank_picker_assets}

    <div class="card">
      <h2>⚡ Actions</h2>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">General</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/setup"><span>🧭</span>Setup Wizard</a>
        <a class="action-tile" href="/dashboard/{guild_id}/lookup"><span>🔎</span>Member Lookup</a>
        <a class="action-tile" href="/dashboard/{guild_id}/roles"><span>🎭</span>Roles</a>
        <a class="action-tile" href="/dashboard/{guild_id}/roster"><span>📋</span>Roster</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">Moderation</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/moderation"><span>🛡️</span>Moderation</a>
        <a class="action-tile" href="/dashboard/{guild_id}/automod"><span>🚨</span>Auto-Moderation</a>
        <a class="action-tile" href="/dashboard/{guild_id}/warnings"><span>⚠️</span>Warnings</a>
        <a class="action-tile" href="/dashboard/{guild_id}/reports"><span>🚩</span>Reports</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">Game Servers</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/gameservers"><span>🕹️</span>Overview</a>
        <a class="action-tile" href="/dashboard/{guild_id}/rust"><span>🦀</span>Rust Server</a>
        <a class="action-tile" href="/dashboard/{guild_id}/rust/players"><span>🎮</span>Rust Players</a>
        <a class="action-tile" href="/dashboard/{guild_id}/rust/bans"><span>🚫</span>Rust Bans</a>
        <a class="action-tile" href="/dashboard/{guild_id}/rust/macros"><span>⚡</span>Rust Macros</a>
        <a class="action-tile" href="/dashboard/{guild_id}/minecraft"><span>⛏️</span>Minecraft Server</a>
        <a class="action-tile" href="/dashboard/{guild_id}/minecraft/players"><span>🎮</span>Minecraft Players</a>
        <a class="action-tile" href="/dashboard/{guild_id}/minecraft/bans"><span>🚫</span>Minecraft Bans</a>
        <a class="action-tile" href="/dashboard/{guild_id}/whitelistsync"><span>🔗</span>Whitelist Sync</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">Community</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/tournaments"><span>🏆</span>Tournaments</a>
        <a class="action-tile" href="/dashboard/{guild_id}/gamenights"><span>🎮</span>Game Nights</a>
        <a class="action-tile" href="/dashboard/{guild_id}/mvp"><span>⭐</span>MVP Voting</a>
        <a class="action-tile" href="/dashboard/{guild_id}/suggestions"><span>💡</span>Suggestions</a>
        <a class="action-tile" href="/dashboard/{guild_id}/giveaways"><span>🎉</span>Giveaways</a>
        <a class="action-tile" href="/dashboard/{guild_id}/trivia"><span>🧠</span>Trivia</a>
        <a class="action-tile" href="/dashboard/{guild_id}/rankbonusroles"><span>🎁</span>Rank Bonus Roles</a>
        <a class="action-tile" href="/dashboard/{guild_id}/customcommands"><span>💬</span>Custom Commands</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">Bulk & Broadcast</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/mass"><span>🧰</span>Mass Actions</a>
        <a class="action-tile" href="/dashboard/{guild_id}/announce"><span>📣</span>Announcements</a>
        <a class="action-tile" href="/dashboard/{guild_id}/showcase"><span>🎭</span>Showcase</a>
        <a class="action-tile" href="/dashboard/{guild_id}/crosspost"><span>🔀</span>Cross-Posting</a>
        <a class="action-tile" href="/dashboard/{guild_id}/greetings"><span>🔊</span>VC Greetings</a>
        <a class="action-tile" href="/dashboard/{guild_id}/tickets"><span>🎫</span>Tickets</a>
        <a class="action-tile" href="/dashboard/{guild_id}/dm"><span>✉️</span>Direct Message</a>
        <a class="action-tile" href="/dashboard/{guild_id}/webhooks"><span>🔌</span>Webhooks</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">Insight & Logs</div>
      <div class="action-grid" style="margin-bottom:20px;">
        <a class="action-tile" href="/dashboard/{guild_id}/logs"><span>🗂️</span>Logs</a>
        <a class="action-tile" href="/dashboard/{guild_id}/activitylog"><span>🖱️</span>Dashboard Activity</a>
        <a class="action-tile" href="/dashboard/{guild_id}/discordauditlog"><span>🗂️</span>Discord Audit Log</a>
        <a class="action-tile" href="/dashboard/{guild_id}/loginhistory"><span>🔑</span>Login History</a>
        <a class="action-tile" href="/dashboard/{guild_id}/activity"><span>📈</span>Message Activity</a>
        <a class="action-tile" href="/dashboard/{guild_id}/voiceactivity"><span>🎙️</span>Voice Activity</a>
        <a class="action-tile" href="/dashboard/{guild_id}/growth"><span>📊</span>Growth Analytics</a>
      </div>

      <div class="hint" style="font-weight:600; text-transform:uppercase; letter-spacing:0.5px; font-size:11px; margin:0 0 8px;">System</div>
      <div class="action-grid">
        <a class="action-tile" href="/dashboard/{guild_id}/afk"><span>💤</span>AFK Status</a>
        <a class="action-tile" href="/dashboard/{guild_id}/backup"><span>💾</span>Download Backup</a>
        <a class="action-tile" href="/dashboard/{guild_id}/backups"><span>🗄️</span>Auto Backups</a>
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
          {_channel_search_field("Log channel", "log_channel", guild, cfg.get('log_channel_id'))}
          {_channel_search_field("Live roster channel", "roster_channel", guild, cfg.get('roster_channel_id'))}
          {_channel_search_field("Live stats channel", "stats_channel", guild, cfg.get('stats_channel_id'))}
          {_channel_search_field("Birthday shoutout channel", "birthday_channel", guild, cfg.get('birthday_channel_id'))}
          {_channel_search_field("Role showcase channel", "showcase_channel", guild, cfg.get('showcase_channel_id'))}
        </div>
        <div class="hint">Log channel: role/roster actions get posted here.</div>
      </div>

      <div class="card" id="roles">
        <h2>🎭 Roles</h2>
        <div class="grid-2">
          {_role_search_field("Manager role (can use staff commands)", "manager_role", guild, cfg.get('manager_role_id'))}
          {_role_search_field("Birthday role", "birthday_role", guild, cfg.get('birthday_role_id'))}
          {_role_search_field("Who can run /weblogin (blank = everyone)", "weblogin_role", guild, cfg.get('weblogin_role_id'))}
          {_role_search_field("Promotion cooldown role (blocks promote/demote while worn)", "promotion_cooldown_role", guild, cfg.get('promotion_cooldown_role_id'))}
          {_rank_search_field("View-only dashboard access threshold (this rank and everything below it)", "viewer_rank_threshold", guild, cfg.get('viewer_rank_threshold_id'))}
          {_role_search_field("Who can use /ban — this role or higher in Server Settings (Discord + web)", "ban_role_threshold", guild, cfg.get('ban_role_threshold_id'))}
        </div>
      </div>

      <div class="card" id="ranks">
        <h2>📋 Ranks (highest to lowest)</h2>
        <div class="grid-2">
          {rank_fields}
        </div>
        <div class="hint">Leave lower ones on "none" if you have fewer than 16 ranks.</div>
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
    set_or_clear("weblogin_role_id", "weblogin_role")
    set_or_clear("promotion_cooldown_role_id", "promotion_cooldown_role")
    set_or_clear("viewer_rank_threshold_id", "viewer_rank_threshold")
    set_or_clear("ban_role_threshold_id", "ban_role_threshold")

    ranks = []
    for i in range(16):
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


# ---------- setup wizard ----------

@app.route("/dashboard/<int:guild_id>/setup")
def setup_wizard_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    role_assets = _role_search_assets(guild)
    channel_assets = _channel_search_assets(guild)

    body = f"""
    <h1>🧭 Setup Wizard</h1>
    <div class="hint" style="margin-bottom:18px;">
      A quick walkthrough of the essentials — the dashboard has a lot of pages, but these are the settings
      that make the roster and moderation tools actually work. Fill in what applies and save; you can always
      change any of this later on the main Settings page or the more specific pages in the sidebar.
    </div>
    {result_html}
    {role_assets}
    {channel_assets}

    <form method="post" action="/dashboard/{guild_id}/setup/save">
      <div class="card">
        <h2>1️⃣ Log Channel</h2>
        <div class="hint" style="margin-bottom:12px;">Where moderation actions and role/roster changes get logged.</div>
        {_channel_search_field("Log channel", "log_channel", guild, cfg.get('log_channel_id'))}
      </div>

      <div class="card">
        <h2>2️⃣ Manager Role</h2>
        <div class="hint" style="margin-bottom:12px;">Who besides Administrators can use staff commands (roster, moderation, etc.) on this bot.</div>
        {_role_search_field("Manager role", "manager_role", guild, cfg.get('manager_role_id'))}
      </div>

      <div class="card">
        <h2>3️⃣ Top Rank</h2>
        <div class="hint" style="margin-bottom:12px;">Your highest roster rank — you can add the rest (up to 16 total) later on the main Settings page.</div>
        {_role_search_field("Rank 1 (highest)", "rank1", guild, (cfg.get('ranks') or [None])[0])}
      </div>

      <div class="card">
        <h2>4️⃣ Roster Channel</h2>
        <div class="hint" style="margin-bottom:12px;">Where the live, auto-updating roster embed gets posted.</div>
        {_channel_search_field("Roster channel", "roster_channel", guild, cfg.get('roster_channel_id'))}
      </div>

      <div class="card">
        <h2>5️⃣ Ticket Panel Channel</h2>
        <div class="hint" style="margin-bottom:12px;">Where the "Open Ticket" button gets posted for members to reach staff. Optional.</div>
        {_channel_search_field("Ticket channel", "ticket_channel", guild, cfg.get('ticket_channel_id'))}
      </div>

      <div class="save-bar">
        <button class="btn" type="submit">Save & Finish Setup</button>
      </div>
    </form>
    """
    return render_page(f"{guild.name} — Setup Wizard", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/setup/save", methods=["POST"])
def setup_wizard_save(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    f = request.form

    # Scoped on purpose — only touches these specific keys, so re-running the
    # wizard (or skipping fields) never wipes out unrelated settings elsewhere.
    def set_or_clear(key, form_key):
        raw = f.get(form_key, "")
        if raw:
            try:
                cfg[key] = int(raw)
            except ValueError:
                pass
        else:
            cfg.pop(key, None)

    set_or_clear("log_channel_id", "log_channel")
    set_or_clear("manager_role_id", "manager_role")
    set_or_clear("roster_channel_id", "roster_channel")
    set_or_clear("ticket_channel_id", "ticket_channel")

    rank1_raw = f.get("rank1", "")
    if rank1_raw:
        try:
            rank1_id = int(rank1_raw)
            ranks = cfg.get("ranks", [])
            if not ranks:
                ranks = [rank1_id]
            else:
                ranks[0] = rank1_id
            cfg["ranks"] = ranks
        except ValueError:
            pass

    _save_config(_config)

    # Posting the ticket panel and roster embed are real Discord actions
    # (not just config), so run those through the normal async bridges.
    if f.get("ticket_channel"):
        _run_async(_set_ticket_channel(guild_id, cfg.get("ticket_channel_id"), session["user_id"]))
    if f.get("roster_channel"):
        _run_async(_refresh_roster(guild_id, session["user_id"]))

    return redirect(url_for("setup_wizard_page", guild_id=guild_id, result="✅ Setup saved! Head to the main Settings page anytime to fine-tune everything else."))


# ---------- role actions (give/remove) ----------

@app.route("/dashboard/<int:guild_id>/roles")
def roles_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    member_assets = _member_search_assets(guild)
    role_assets = _role_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎭 Give / Remove Roles</h1>
    {result_html}
    {member_assets}
    {role_assets}

    <div class="card">
      <h2>🟢 Give a role</h2>
      <form method="post" action="/dashboard/{guild_id}/roles/give">
        <div class="grid-2">
          {_member_multi_search_field()}
          {_role_search_field()}
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
          {_member_search_field()}
          {_role_search_field()}
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

    user_ids = request.form.getlist("user_ids")
    try:
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roles_page", guild_id=guild_id, result="❌ Pick a role."))
    if not user_ids:
        return redirect(url_for("roles_page", guild_id=guild_id, result="❌ Pick at least one member."))

    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_give_role(guild_id, int(raw_id), role_id, reason, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("roles_page", guild_id=guild_id, result=" / ".join(results)))


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
    member_assets = _member_search_assets(guild)
    rank_assets = _rank_search_assets(guild, cfg)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📋 Roster Actions</h1>
    <div class="hint" style="margin-bottom:18px;">
      <a href="/dashboard/{guild_id}/export/roster.csv">⬇️ Download roster as CSV</a>
    </div>
    <form method="post" action="/dashboard/{guild_id}/roster/refresh" style="margin-bottom:18px;">
      <button class="btn btn-secondary" type="submit">🔄 Force Refresh Roster & Stats Embeds</button>
    </form>
    {result_html}
    {member_assets}
    {rank_assets}

    <div class="card">
      <h2>📋 Add / move on roster</h2>
      {no_ranks_hint}
      <form method="post" action="/dashboard/{guild_id}/roster/add">
        <div class="grid-2">
          {_member_search_field()}
          {_rank_search_field()}
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Add / Move</button>
      </form>
    </div>

    <div class="card">
      <h2>👥 Put everyone on the roster</h2>
      <div class="hint" style="margin-bottom:12px;">Adds EVERY server member to the roster at once, at the rank you pick — also grants them that role if they don't already have it. Big action, applies to the whole server.</div>
      <form method="post" action="/dashboard/{guild_id}/roster/addall">
        {_rank_search_field("Rank", "rank_id")}
        <button class="btn btn-secondary" type="submit">Put Everyone On Roster</button>
      </form>
    </div>

    <div class="card-row">
      <div class="card">
        <h2>⏳ Put on Cooldown</h2>
        <div class="hint" style="margin-bottom:12px;">Gives selected members the promotion cooldown role, blocking them from being promoted/demoted until it's removed. Set the role first on the main Settings page.</div>
        <form method="post" action="/dashboard/{guild_id}/roster/cooldown/add">
          {_member_multi_search_field()}
          <button class="btn btn-secondary" type="submit">Put on Cooldown</button>
        </form>
      </div>

      <div class="card">
        <h2>✅ Remove Cooldown</h2>
        <div class="hint" style="margin-bottom:12px;">Removes the cooldown role from selected members, letting them be promoted/demoted again.</div>
        <form method="post" action="/dashboard/{guild_id}/roster/cooldown/remove">
          {_member_multi_search_field()}
          <button class="btn" type="submit">Remove Cooldown</button>
        </form>
      </div>
    </div>

    <div class="card">
      <h2>⬆️ Promote</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/promote">
        {_member_multi_search_field()}
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Promote</button>
      </form>
    </div>

    <div class="card">
      <h2>⬇️ Demote</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/demote">
        {_member_multi_search_field()}
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn btn-secondary" type="submit">Demote</button>
      </form>
    </div>

    <div class="card">
      <h2>🗑️ Remove from roster</h2>
      <form method="post" action="/dashboard/{guild_id}/roster/remove">
        {_member_search_field()}
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


@app.route("/dashboard/<int:guild_id>/roster/addall", methods=["POST"])
def roster_addall_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        rank_id = int(request.form["rank_id"])
    except (KeyError, ValueError):
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick a rank."))
    # This can take a while for large servers (one Discord API call per
    # member) — don't block the HTTP request waiting for it, just kick it
    # off in the background and let the user check back shortly.
    _fire_and_forget(_roster_add_all(guild_id, rank_id, session["user_id"]))
    return redirect(url_for(
        "roster_page", guild_id=guild_id,
        result="⏳ Started in the background — Discord rate-limits bulk role changes to roughly 1 member per 10 seconds, so this can take a while for large servers (e.g. ~1-3 hours for 500-1000+ members). Check your log channel for progress updates every 50 members.",
    ))


@app.route("/dashboard/<int:guild_id>/roster/refresh", methods=["POST"])
def roster_refresh_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_refresh_roster(guild_id, session["user_id"]))
    return redirect(url_for("roster_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/roster/cooldown/add", methods=["POST"])
def roster_cooldown_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick at least one member."))
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_put_on_cooldown(guild_id, int(raw_id), session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("roster_page", guild_id=guild_id, result=" / ".join(results)))


@app.route("/dashboard/<int:guild_id>/roster/cooldown/remove", methods=["POST"])
def roster_cooldown_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick at least one member."))
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_remove_cooldown(guild_id, int(raw_id), session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("roster_page", guild_id=guild_id, result=" / ".join(results)))


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
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick at least one member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_promote(guild_id, int(raw_id), reason, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("roster_page", guild_id=guild_id, result=" / ".join(results)))


@app.route("/dashboard/<int:guild_id>/roster/demote", methods=["POST"])
def roster_demote_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("roster_page", guild_id=guild_id, result="❌ Pick at least one member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_demote(guild_id, int(raw_id), reason, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("roster_page", guild_id=guild_id, result=" / ".join(results)))


# ---------- moderation actions (kick/ban/timeout/warn) ----------

@app.route("/dashboard/<int:guild_id>/moderation")
def moderation_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""
    member_assets = _member_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🛡️ Moderation</h1>
    {result_html}
    {member_assets}

    <div class="card-row">
      <div class="card">
        <h2>⚠️ Warn</h2>
        <form method="post" action="/dashboard/{guild_id}/moderation/warn">
          {_member_multi_search_field()}
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
          <button class="btn" type="submit">Warn</button>
        </form>
      </div>

      <div class="card">
        <h2>🔇 Timeout</h2>
        <form method="post" action="/dashboard/{guild_id}/moderation/timeout">
          {_member_search_field()}
          <div class="field"><label>Minutes</label><input type="number" name="minutes" min="1" max="40320" value="60" required></div>
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
          <button class="btn" type="submit">Time Out</button>
        </form>
      </div>

      <div class="card">
        <h2>🔊 Remove Timeout</h2>
        <form method="post" action="/dashboard/{guild_id}/moderation/untimeout">
          {_member_search_field()}
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" value="No reason given"></div>
          <button class="btn btn-secondary" type="submit">Remove Timeout</button>
        </form>
      </div>

      <div class="card">
        <h2>👢 Kick</h2>
        <form method="post" action="/dashboard/{guild_id}/moderation/kick">
          {_member_multi_search_field()}
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
          <button class="btn btn-secondary" type="submit">Kick</button>
        </form>
      </div>

      <div class="card">
        <h2>🔨 Ban</h2>
        <form method="post" action="/dashboard/{guild_id}/moderation/ban">
          {_member_multi_search_field()}
          <div class="field"><label>Delete message history (days, 0-7)</label><input type="number" name="delete_days" min="0" max="7" value="0"></div>
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
          <button class="btn btn-secondary" type="submit">Ban</button>
        </form>
      </div>
    </div>
    """
    return render_page(f"{guild.name} — Moderation", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/moderation/kick", methods=["POST"])
def moderation_kick(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick at least one member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_kick(guild_id, int(raw_id), reason, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("moderation_page", guild_id=guild_id, result=" / ".join(results)))


@app.route("/dashboard/<int:guild_id>/moderation/ban", methods=["POST"])
def moderation_ban(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick at least one member."))
    try:
        delete_days = int(request.form.get("delete_days", 0))
    except ValueError:
        delete_days = 0
    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_ban(guild_id, int(raw_id), reason, delete_days, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("moderation_page", guild_id=guild_id, result=" / ".join(results)))


# ---------- auto-moderation ----------

@app.route("/dashboard/<int:guild_id>/automod")
def automod_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    enabled = cfg.get("automod_enabled", False)
    block_invites = cfg.get("automod_block_invites", True)
    block_spam = cfg.get("automod_block_spam", True)
    action = cfg.get("automod_action", "delete_only")
    role_assets = _role_search_assets(guild)

    words = cfg.get("automod_banned_words", [])
    word_rows = ""
    if words:
        for w in words:
            safe_w = html.escape(w)
            word_rows += f"""
            <tr>
              <td><code>{safe_w}</code></td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/automod/removeword" style="margin:0;">
                  <input type="hidden" name="word" value="{safe_w}">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        word_rows = '<tr><td colspan="2" class="hint" style="padding:16px;">No blocked words yet.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🚨 Auto-Moderation</h1>
    {result_html}
    {role_assets}

    <div class="card">
      <h2>{'🟢 Currently ON' if enabled else '🔴 Currently OFF'}</h2>
      <form method="post" action="/dashboard/{guild_id}/automod/toggle">
        <input type="hidden" name="enabled" value="{'false' if enabled else 'true'}">
        <button class="btn{' btn-secondary' if enabled else ''}" type="submit">{"Turn Off" if enabled else "Turn On"}</button>
      </form>
    </div>

    <div class="card">
      <h2>⚙️ Settings</h2>
      <form method="post" action="/dashboard/{guild_id}/automod/settings">
        <div class="grid-2">
          <div class="field">
            <label>Block Discord invite links</label>
            <select name="block_invites"><option value="true" {"selected" if block_invites else ""}>Yes</option><option value="false" {"selected" if not block_invites else ""}>No</option></select>
          </div>
          <div class="field">
            <label>Block repeated-message spam</label>
            <select name="block_spam"><option value="true" {"selected" if block_spam else ""}>Yes</option><option value="false" {"selected" if not block_spam else ""}>No</option></select>
          </div>
        </div>
        <div class="field">
          <label>Action (in addition to deleting the message)</label>
          <select name="action">
            <option value="delete_only" {"selected" if action == "delete_only" else ""}>Delete only</option>
            <option value="delete_and_warn" {"selected" if action == "delete_and_warn" else ""}>Delete + warn</option>
            <option value="delete_and_timeout" {"selected" if action == "delete_and_timeout" else ""}>Delete + 10 minute timeout</option>
          </select>
        </div>
        {_role_search_field("Exempt role (staff, etc. — blank = none)", "exempt_role", guild, cfg.get('automod_exempt_role_id'))}
        <button class="btn" type="submit">Save Settings</button>
      </form>
    </div>

    <div class="card">
      <h2>🚫 Blocked Words</h2>
      <form method="post" action="/dashboard/{guild_id}/automod/addword" style="margin-bottom:14px;">
        <div class="field"><input type="text" name="word" placeholder="Add a word to block" required></div>
        <button class="btn btn-secondary" type="submit">Add Word</button>
      </form>
      {_table_search_box("automod-words-table")}
      <div class="log-wrap"><table class="log-table" id="automod-words-table">
        <tr><th>Word</th><th></th></tr>
        {word_rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Auto-Moderation", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/automod/toggle", methods=["POST"])
def automod_toggle_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    enabled = request.form.get("enabled", "false") == "true"
    result = _run_async(_automod_toggle(guild_id, enabled, session["user_id"]))
    return redirect(url_for("automod_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/automod/settings", methods=["POST"])
def automod_settings_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    block_invites = request.form.get("block_invites", "true") == "true"
    block_spam = request.form.get("block_spam", "true") == "true"
    action = request.form.get("action", "delete_only")
    raw_role = request.form.get("exempt_role", "")
    exempt_role_id = int(raw_role) if raw_role else None
    result = _run_async(_automod_settings(guild_id, block_invites, block_spam, action, exempt_role_id, session["user_id"]))
    return redirect(url_for("automod_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/automod/addword", methods=["POST"])
def automod_addword_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    word = request.form.get("word", "").strip()
    if not word:
        return redirect(url_for("automod_page", guild_id=guild_id, result="❌ Enter a word."))
    result = _run_async(_automod_add_word(guild_id, word, session["user_id"]))
    return redirect(url_for("automod_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/automod/removeword", methods=["POST"])
def automod_removeword_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    word = request.form.get("word", "").strip()
    if not word:
        return redirect(url_for("automod_page", guild_id=guild_id, result="❌ Missing word."))
    result = _run_async(_automod_remove_word(guild_id, word, session["user_id"]))
    return redirect(url_for("automod_page", guild_id=guild_id, result=result))


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


@app.route("/dashboard/<int:guild_id>/moderation/untimeout", methods=["POST"])
def moderation_untimeout(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick a member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    result = _run_async(_untimeout(guild_id, user_id, reason, session["user_id"]))
    return redirect(url_for("moderation_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/moderation/warn", methods=["POST"])
def moderation_warn(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_ids = request.form.getlist("user_ids")
    if not user_ids:
        return redirect(url_for("moderation_page", guild_id=guild_id, result="❌ Pick at least one member."))
    reason = request.form.get("reason", "").strip() or "No reason given"
    results = []
    for raw_id in user_ids:
        try:
            results.append(_run_async(_warn(guild_id, int(raw_id), reason, session["user_id"])))
        except ValueError:
            continue
    return redirect(url_for("moderation_page", guild_id=guild_id, result=" / ".join(results)))


# ---------- logs / movements ----------

def _format_ts(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, TypeError):
        return iso_str or "—"


def _table_search_box(table_id, placeholder="Type to filter..."):
    return f'<input type="text" oninput="filterTable(this, \'{table_id}\')" placeholder="{placeholder}" style="margin-bottom:10px;">'


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
        <select name="user" onchange="submitFormAjax(this.form)">{member_opts}</select>
      </div>
    </form>

    {warnings_html}

    <div class="card">
      <h2>📋 Rank / Roster History</h2>
      {_table_search_box("logs-table")}
      <div class="log-wrap">
        <table class="log-table" id="logs-table">
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
    role_assets = _role_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🧰 Mass Actions</h1>
    {result_html}
    {role_assets}

    <div class="card">
      <h2>🟢 Give a role to many members</h2>
      <form method="post" action="/dashboard/{guild_id}/mass/addrole">
        <div class="grid-2">
          {_role_search_field("Role to give", "role_id")}
          {_role_search_field("Only members who have this role (optional)", "filter_role_id")}
        </div>
        <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        <button class="btn" type="submit">Give to All Matching</button>
      </form>
    </div>

    <div class="card">
      <h2>🔴 Remove a role from many members</h2>
      <form method="post" action="/dashboard/{guild_id}/mass/removerole">
        <div class="grid-2">
          {_role_search_field("Role to remove", "role_id")}
          {_role_search_field("Only members who also have this role (optional)", "filter_role_id")}
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
        {_role_search_field("Only members with this role (optional)", "filter_role_id")}
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
    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📣 Announcements</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>📢 Post to one channel</h2>
      <form method="post" action="/dashboard/{guild_id}/announce/single">
        {_channel_search_field()}
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

    role_assets = _role_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎭 Role Showcase</h1>
    {result_html}
    {role_assets}

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
        {_role_search_field()}
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

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔀 Cross-Posting</h1>
    {result_html}
    {channel_assets}

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
        {_channel_search_field("Source channel (in this server)", "source_channel_id")}
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

    member_assets = _member_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔊 VC Greetings</h1>
    {result_html}
    {member_assets}

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
        {_member_search_field()}
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
    <div class="hint" style="margin-bottom:18px;">Counting since {since_label} — resets automatically every 7 days. &middot; <a href="/dashboard/{guild_id}/export/activity.csv">⬇️ Download as CSV</a></div>

    <div class="card">
      <h2>Top {len(ranked)}</h2>
      {_table_search_box("activity-table")}
      <div class="log-wrap"><table class="log-table" id="activity-table">
        <tr><th>Rank</th><th>Member</th><th>Messages</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Activity", body, guild_id=guild_id)


def _build_growth_chart_svg(history):
    """Renders a simple line chart as raw SVG — no JS charting library needed,
    consistent with the rest of this dashboard."""
    width, height = 780, 280
    pad_left, pad_right, pad_top, pad_bottom = 50, 20, 20, 30

    counts = [h["count"] for h in history]
    min_count, max_count = min(counts), max(counts)
    if min_count == max_count:
        min_count -= 1
        max_count += 1
    span = max_count - min_count

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    n = len(history)

    def x_at(i):
        return pad_left + (i / (n - 1) * plot_w if n > 1 else plot_w / 2)

    def y_at(count):
        return pad_top + plot_h - ((count - min_count) / span * plot_h)

    points = [(x_at(i), y_at(h["count"])) for i, h in enumerate(history)]
    line_path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area_path = line_path + f" L {points[-1][0]:.1f},{pad_top + plot_h} L {points[0][0]:.1f},{pad_top + plot_h} Z"

    # Y-axis gridlines/labels — 4 evenly spaced steps
    gridlines = ""
    for step in range(5):
        val = min_count + span * step / 4
        y = y_at(val)
        gridlines += f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
        gridlines += f'<text x="{pad_left - 8}" y="{y:.1f}" text-anchor="end" dominant-baseline="middle" font-size="11" fill="#8b96b3">{int(val)}</text>'

    # X-axis labels — first, middle, last date only, to avoid clutter
    label_indices = sorted(set([0, n // 2, n - 1])) if n > 1 else [0]
    x_labels = ""
    for i in label_indices:
        x_labels += f'<text x="{x_at(i):.1f}" y="{height - pad_bottom + 18}" text-anchor="middle" font-size="11" fill="#8b96b3">{history[i]["date"]}</text>'

    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#3b82f6"/>' for x, y in points) if n <= 60 else ""

    return f"""
    <svg viewBox="0 0 {width} {height}" style="width:100%; height:auto;">
      <defs>
        <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
        </linearGradient>
      </defs>
      {gridlines}
      <path d="{area_path}" fill="url(#growthFill)"/>
      <path d="{line_path}" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
      {dots}
      {x_labels}
    </svg>
    """


@app.route("/dashboard/<int:guild_id>/growth")
def growth_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    history = cfg.get("member_count_history", [])

    if len(history) < 2:
        chart_html = f'<div class="hint" style="padding:24px 0;">Not enough data yet — this records one snapshot per day, so check back after a couple of days. Currently {len(history)} data point(s) recorded.</div>'
        change_html = ""
    else:
        chart_html = _build_growth_chart_svg(history)
        first, last = history[0]["count"], history[-1]["count"]
        delta = last - first
        sign = "+" if delta >= 0 else ""
        change_html = f"""
        <div class="stats-strip" style="margin-top:0;">
          <div class="stat-tile"><div class="icon">👥</div><div class="num">{last}</div><div class="label">Current</div></div>
          <div class="stat-tile{'' if delta >= 0 else ' magenta'}"><div class="icon">{'📈' if delta >= 0 else '📉'}</div><div class="num">{sign}{delta}</div><div class="label">Since {history[0]['date']}</div></div>
          <div class="stat-tile grey"><div class="icon">🗓️</div><div class="num">{len(history)}</div><div class="label">Days Tracked</div></div>
        </div>
        """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">📊 Growth Analytics</h1>
    <div class="hint" style="margin-bottom:18px;">One member-count snapshot recorded per day, keeping roughly the last 6 months.</div>

    {change_html}

    <div class="card">
      <h2>Member Count Over Time</h2>
      {chart_html}
    </div>
    """
    return render_page(f"{guild.name} — Growth Analytics", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/trivia")
def trivia_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    scores = cfg.get("trivia_scores", {})

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:50]
    rows = ""
    if ranked:
        for i, (uid, score) in enumerate(ranked, start=1):
            m = guild.get_member(int(uid))
            name = m.display_name if m else f"Unknown ({uid})"
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            rows += f"<tr><td>{medal}</td><td>{name}</td><td>{score}</td></tr>"
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No trivia games played yet — run /trivia in Discord to start!</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🧠 Trivia Leaderboard</h1>
    <div class="hint" style="margin-bottom:18px;">Run <code>/trivia</code> in Discord to play — first correct answer wins a point.</div>

    <div class="card">
      <h2>Top {len(ranked)}</h2>
      {_table_search_box("trivia-table")}
      <div class="log-wrap"><table class="log-table" id="trivia-table">
        <tr><th>Rank</th><th>Member</th><th>Points</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Trivia Leaderboard", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/voiceactivity")
def voice_activity_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    minutes_map = cfg.get("voice_minutes", {})
    since_str = cfg.get("voice_minutes_since")
    since_label = _format_ts(since_str) if since_str else "—"

    ranked = sorted(minutes_map.items(), key=lambda kv: kv[1], reverse=True)[:50]
    rows = ""
    if ranked:
        for i, (uid, mins) in enumerate(ranked, start=1):
            m = guild.get_member(int(uid))
            name = m.display_name if m else f"Unknown ({uid})"
            hours, remainder_mins = divmod(int(mins), 60)
            duration = f"{hours}h {remainder_mins}m" if hours else f"{remainder_mins}m"
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
            rows += f"<tr><td>{medal}</td><td>{name}</td><td>{duration}</td></tr>"
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No voice activity recorded yet this period.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎙️ Voice Activity</h1>
    <div class="hint" style="margin-bottom:18px;">Counting time spent in voice channels since {since_label} — resets automatically every 7 days.</div>

    <div class="card">
      <h2>Top {len(ranked)}</h2>
      {_table_search_box("voice-activity-table")}
      <div class="log-wrap"><table class="log-table" id="voice-activity-table">
        <tr><th>Rank</th><th>Member</th><th>Time</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Voice Activity", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/customcommands")
def custom_commands_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    custom_commands = cfg.get("custom_commands", {})
    rows = ""
    if custom_commands:
        for trigger, response in custom_commands.items():
            safe_trigger = html.escape(trigger)
            rows += f"""
            <tr>
              <td><code>{safe_trigger}</code></td>
              <td>{html.escape(response)}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/customcommands/remove" style="margin:0;">
                  <input type="hidden" name="trigger" value="{safe_trigger}">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No custom commands yet.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">💬 Custom Commands</h1>
    <div class="hint" style="margin-bottom:18px;">When a member's message matches a trigger word exactly (not case-sensitive), the bot replies automatically.</div>
    {result_html}

    <div class="card">
      <h2>➕ Add a custom command</h2>
      <form method="post" action="/dashboard/{guild_id}/customcommands/add">
        <div class="field"><label>Trigger word/phrase</label><input type="text" name="trigger" placeholder="!rules" required></div>
        <div class="field"><label>Response</label><input type="text" name="response" placeholder="Check out #rules for the full list!" required></div>
        <button class="btn" type="submit">Add</button>
      </form>
    </div>

    <div class="card">
      <h2>All custom commands</h2>
      {_table_search_box("customcommands-table")}
      <div class="log-wrap"><table class="log-table" id="customcommands-table">
        <tr><th>Trigger</th><th>Response</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Custom Commands", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/customcommands/add", methods=["POST"])
def custom_commands_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    trigger = request.form.get("trigger", "").strip()
    response = request.form.get("response", "").strip()
    if not trigger or not response:
        return redirect(url_for("custom_commands_page", guild_id=guild_id, result="❌ Fill in both fields."))
    result = _run_async(_add_custom_command(guild_id, trigger, response, session["user_id"]))
    return redirect(url_for("custom_commands_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/customcommands/remove", methods=["POST"])
def custom_commands_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    trigger = request.form.get("trigger", "").strip()
    if not trigger:
        return redirect(url_for("custom_commands_page", guild_id=guild_id, result="❌ Missing trigger."))
    result = _run_async(_remove_custom_command(guild_id, trigger, session["user_id"]))
    return redirect(url_for("custom_commands_page", guild_id=guild_id, result=result))


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
                <a href="/dashboard/{guild_id}/tickets/{t['id']}">Reply</a>
                {" &middot; " + link if link else ""}
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
              <td>{t.get('type_name') or '—'}</td>
              <td>{status_pill}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(t.get('created_at'))}</td>
              <td>{action_cell}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="6" class="hint" style="padding:16px;">No tickets yet.</td></tr>'

    member_assets = _member_search_assets(guild)
    channel_assets = _channel_search_assets(guild)
    category_assets = _category_search_assets(guild)

    ticket_types = cfg.get("ticket_types", {})
    type_rows = ""
    if ticket_types:
        for type_id, t in ticket_types.items():
            category = guild.get_channel(t.get("category_id"))
            questions = t.get("questions", [])
            questions_text = "|".join(questions)
            q_summary = f"{len(questions)} question(s)" if questions else "no questions"
            type_rows += f"""
            <tr>
              <td>{t['name']}</td>
              <td>{category.name if category else '(deleted category)'}</td>
              <td>{q_summary}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/tickets/removecategory" style="margin:0;">
                  <input type="hidden" name="type_id" value="{type_id}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Remove</button>
                </form>
              </td>
            </tr>
            <tr>
              <td colspan="4" style="padding-top:0;">
                <form method="post" action="/dashboard/{guild_id}/tickets/setquestions" style="display:flex; gap:8px; align-items:flex-end;">
                  <input type="hidden" name="type_id" value="{type_id}">
                  <div class="field" style="flex:1; margin-bottom:0;">
                    <label>Intake questions for {t['name']} (one per line, max 5, leave blank for none)</label>
                    <input type="text" name="questions" value="{questions_text.replace('"', '&quot;')}" placeholder="e.g. What's your in-game name?|What happened?">
                  </div>
                  <button class="btn btn-secondary" type="submit" style="padding:10px 14px; font-size:12px;">Save Questions</button>
                </form>
              </td>
            </tr>
            """
    else:
        type_rows = '<tr><td colspan="4" class="hint" style="padding:16px;">No ticket types yet — the panel just shows a plain "Open Ticket" button until you add some.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎫 Tickets</h1>
    {result_html}
    {member_assets}
    {channel_assets}
    {category_assets}

    <div class="card">
      <h2>📌 Ticket panel channel</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a button (or a type dropdown, if you've added categories below) in this channel that lets any member open their own ticket instantly.</div>
      <form method="post" action="/dashboard/{guild_id}/tickets/setchannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("ticket_channel_id"))}
        <button class="btn" type="submit">Post Ticket Panel</button>
      </form>
    </div>

    <div class="card">
      <h2>⏰ Auto-Reminder / Auto-Close</h2>
      <div class="hint" style="margin-bottom:12px;">Nudges (then closes) tickets that go quiet too long, so nothing sits open forever unnoticed. {"<br>Currently <strong>ON</strong>." if cfg.get("ticket_autoclose_enabled") else "<br>Currently <strong>OFF</strong>."}</div>
      <form method="post" action="/dashboard/{guild_id}/tickets/autoclose">
        <div class="grid-2">
          <div class="field"><label>Remind after (hours)</label><input type="number" name="reminder_hours" min="1" value="{cfg.get('ticket_reminder_hours', 24)}" required></div>
          <div class="field"><label>Auto-close after (hours)</label><input type="number" name="close_hours" min="2" value="{cfg.get('ticket_autoclose_hours', 48)}" required></div>
        </div>
        <input type="hidden" name="enabled" value="{'false' if cfg.get('ticket_autoclose_enabled') else 'true'}">
        <button class="btn" type="submit">{"Save & Turn Off" if cfg.get("ticket_autoclose_enabled") else "Save & Turn On"}</button>
      </form>
    </div>

    <div class="card">
      <h2>🗂️ Ticket categories</h2>
      <div class="hint" style="margin-bottom:12px;">Add multiple ticket types (e.g. "Support", "Report Player", "Appeal") — each routes to its own Discord category. Members pick one from a dropdown when opening a ticket. Add intake questions below each type and members fill out a short form before their channel is created.</div>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Type</th><th>Category</th><th>Questions</th><th></th></tr>
        {type_rows}
      </table></div>
      <form method="post" action="/dashboard/{guild_id}/tickets/addcategory" style="margin-top:14px;">
        <div class="field"><label>Type name</label><input type="text" name="name" placeholder="Report a Player" required></div>
        {_category_search_field()}
        <div class="field"><label>Intake questions (optional, separate with | , max 5)</label><input type="text" name="questions" placeholder="What's your in-game name?|Who are you reporting?|What happened?"></div>
        <button class="btn" type="submit">Add Category</button>
      </form>
    </div>

    <div class="card">
      <h2>➕ Open a ticket for someone</h2>
      <div class="hint" style="margin-bottom:12px;">Members can also open their own with /ticket in Discord, or a button if you've set one up with /setticketchannel.</div>
      <form method="post" action="/dashboard/{guild_id}/tickets/open">
        {_member_search_field()}
        <button class="btn" type="submit">Open Ticket</button>
      </form>
    </div>

    <div class="card">
      <h2>All tickets</h2>
      {_table_search_box("all-tickets-table")}
      <div class="log-wrap"><table class="log-table" id="all-tickets-table">
        <tr><th>#</th><th>Member</th><th>Type</th><th>Status</th><th>Opened</th><th></th></tr>
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


@app.route("/dashboard/<int:guild_id>/tickets/autoclose", methods=["POST"])
def tickets_autoclose_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    enabled = request.form.get("enabled", "false") == "true"
    try:
        reminder_hours = int(request.form["reminder_hours"])
        close_hours = int(request.form["close_hours"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Enter valid hour values."))
    result = _run_async(_set_ticket_autoclose(guild_id, enabled, reminder_hours, close_hours, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/addcategory", methods=["POST"])
def tickets_addcategory_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    try:
        category_id = int(request.form["category_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Pick a category."))
    if not name:
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Enter a type name."))
    questions = [q.strip() for q in request.form.get("questions", "").split("|") if q.strip()][:5]
    result = _run_async(_add_ticket_category(guild_id, name, category_id, questions, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/removecategory", methods=["POST"])
def tickets_removecategory_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        type_id = int(request.form["type_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Invalid ticket type."))
    result = _run_async(_remove_ticket_category(guild_id, type_id, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/setquestions", methods=["POST"])
def tickets_setquestions_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        type_id = int(request.form["type_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Invalid ticket type."))
    questions = [q.strip() for q in request.form.get("questions", "").split("|") if q.strip()][:5]
    result = _run_async(_set_ticket_questions(guild_id, type_id, questions, session["user_id"]))
    return redirect(url_for("tickets_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tickets/<int:ticket_id>")
def ticket_detail_page(guild_id, ticket_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    ticket = cfg.get("tickets", {}).get(str(ticket_id))
    if ticket is None:
        return redirect(url_for("tickets_page", guild_id=guild_id, result="❌ Ticket not found."))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    owner = guild.get_member(ticket["user_id"])
    owner_name = owner.display_name if owner else f"Unknown ({ticket['user_id']})"
    status = ticket.get("status", "open")
    type_name = ticket.get("type_name")

    messages = _run_async(_get_ticket_messages(guild_id, ticket_id))
    msg_html = ""
    if messages:
        for m in messages:
            color = "#a78bfa" if m["is_bot"] else "#6366f1"
            safe_author = html.escape(m["author"])
            safe_content = html.escape(m["content"]).replace("\n", "<br>")
            msg_html += f"""
            <div style="padding:10px 14px; border-bottom:1px solid rgba(255,255,255,0.05);">
              <div style="font-size:12px; margin-bottom:4px;">
                <span style="color:{color}; font-weight:700;">{safe_author}</span>
                <span class="hint" style="margin-left:8px;">{_format_ts(m['timestamp'])}</span>
              </div>
              <div style="font-size:14px; line-height:1.5;">{safe_content}</div>
            </div>
            """
    else:
        msg_html = '<div class="hint" style="padding:16px;">No messages yet, or I couldn\'t read this channel\'s history.</div>'

    reply_form = ""
    if status == "open":
        reply_form = f"""
        <div class="card">
          <h2>💬 Send a reply</h2>
          <form method="post" action="/dashboard/{guild_id}/tickets/{ticket_id}/send">
            <div class="field"><input type="text" name="message" placeholder="Type a message to send in this ticket..." required></div>
            <button class="btn" type="submit">Send</button>
          </form>
        </div>
        """
    else:
        reply_form = '<div class="hint">This ticket is closed — replies are disabled.</div>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}/tickets">&larr; All tickets</a></div>
    <h1 style="margin-top:18px;">🎫 Ticket #{ticket_id}{f' — {type_name}' if type_name else ''}</h1>
    <div class="hint" style="margin-bottom:18px;">Opened by {owner_name} &middot; Status: {status}</div>
    {result_html}

    <div class="card" style="padding:0;">
      <div style="max-height:520px; overflow-y:auto;">
        {msg_html}
      </div>
    </div>

    {reply_form}
    """
    return render_page(f"{guild.name} — Ticket #{ticket_id}", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/tickets/<int:ticket_id>/send", methods=["POST"])
def ticket_send_route(guild_id, ticket_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("ticket_detail_page", guild_id=guild_id, ticket_id=ticket_id, result="❌ Write a message."))
    result = _run_async(_send_ticket_message(guild_id, ticket_id, session["user_id"], message))
    return redirect(url_for("ticket_detail_page", guild_id=guild_id, ticket_id=ticket_id, result=result))


# ---------- warnings management ----------

@app.route("/dashboard/<int:guild_id>/warnings")
def warnings_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    all_warnings = cfg.get("warnings", {})
    rows = ""
    any_warnings = False
    for uid_str, entries in all_warnings.items():
        if not entries:
            continue
        any_warnings = True
        m = guild.get_member(int(uid_str))
        name = m.display_name if m else f"Unknown ({uid_str})"
        for i, w in enumerate(entries):
            mod = guild.get_member(w.get("moderator_id"))
            mod_name = mod.display_name if mod else "—"
            rows += f"""
            <tr>
              <td>{name}</td>
              <td>{w.get('reason','')}</td>
              <td>{mod_name}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(w.get('timestamp'))}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/warnings/clear" style="margin:0;">
                  <input type="hidden" name="user_id" value="{uid_str}">
                  <input type="hidden" name="index" value="{i}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Clear</button>
                </form>
              </td>
            </tr>
            """
    if not any_warnings:
        rows = '<tr><td colspan="5" class="hint" style="padding:16px;">No warnings recorded.</td></tr>'

    member_assets = _member_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">⚠️ Warnings</h1>
    <div class="hint" style="margin-bottom:18px;"><a href="/dashboard/{guild_id}/export/warnings.csv">⬇️ Download warnings as CSV</a></div>
    {result_html}
    {member_assets}

    <div class="card">
      <h2>All warnings</h2>
      {_table_search_box("warnings-table")}
      <div class="log-wrap"><table class="log-table" id="warnings-table">
        <tr><th>Member</th><th>Reason</th><th>By</th><th>When</th><th></th></tr>
        {rows}
      </table></div>
    </div>

    <div class="card">
      <h2>🗑️ Clear all warnings for a member</h2>
      <form method="post" action="/dashboard/{guild_id}/warnings/clearall">
        {_member_search_field()}
        <button class="btn btn-secondary" type="submit">Clear All Warnings</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Warnings", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/warnings/clear", methods=["POST"])
def warnings_clear_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_id = request.form.get("user_id", "")
    try:
        index = int(request.form["index"])
    except (KeyError, ValueError):
        return redirect(url_for("warnings_page", guild_id=guild_id, result="❌ Invalid warning."))

    cfg = _get_guild_cfg(guild_id)
    warnings = cfg.get("warnings", {})
    user_warnings = warnings.get(user_id, [])
    if 0 <= index < len(user_warnings):
        user_warnings.pop(index)
        _save_config(_config)
        return redirect(url_for("warnings_page", guild_id=guild_id, result="✅ Warning cleared."))
    return redirect(url_for("warnings_page", guild_id=guild_id, result="ℹ️ That warning wasn't found."))


@app.route("/dashboard/<int:guild_id>/warnings/clearall", methods=["POST"])
def warnings_clearall_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("warnings_page", guild_id=guild_id, result="❌ Pick a member."))

    cfg = _get_guild_cfg(guild_id)
    warnings = cfg.get("warnings", {})
    if str(user_id) in warnings and warnings[str(user_id)]:
        count = len(warnings[str(user_id)])
        warnings[str(user_id)] = []
        _save_config(_config)
        m = guild.get_member(user_id)
        name = m.display_name if m else str(user_id)
        return redirect(url_for("warnings_page", guild_id=guild_id, result=f"✅ Cleared {count} warning(s) for {name}."))
    return redirect(url_for("warnings_page", guild_id=guild_id, result="ℹ️ That member has no warnings."))


# ---------- member reports ----------

@app.route("/dashboard/<int:guild_id>/reports")
def reports_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    reports = sorted(cfg.get("reports", {}).values(), key=lambda r: r.get("id", 0), reverse=True)
    rows = ""
    if reports:
        for r in reports:
            reporter = guild.get_member(r.get("reporter_id"))
            reported = guild.get_member(r.get("reported_user_id"))
            reporter_name = reporter.display_name if reporter else f"Unknown ({r.get('reporter_id')})"
            reported_name = reported.display_name if reported else f"Unknown ({r.get('reported_user_id')})"
            status = r.get("status", "open")
            color = {"open": "#f5b942", "resolved": "#22c55e", "dismissed": "#8b96b3"}.get(status, "#8b96b3")
            pill = f'<span class="pill" style="background:{color}22; border-color:{color}55; color:{color};">{status}</span>'
            actions = ""
            if status == "open":
                actions = f"""
                <form method="post" action="/dashboard/{guild_id}/reports/{r['id']}/status" style="display:inline;">
                  <input type="hidden" name="status" value="resolved">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Resolve</button>
                </form>
                <form method="post" action="/dashboard/{guild_id}/reports/{r['id']}/status" style="display:inline;">
                  <input type="hidden" name="status" value="dismissed">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Dismiss</button>
                </form>
                """
            rows += f"""
            <tr>
              <td>#{r['id']}</td>
              <td>{reported_name}</td>
              <td>{reporter_name}</td>
              <td>{html.escape(r.get('reason', ''))}</td>
              <td>{pill}</td>
              <td style="white-space:nowrap;">{actions}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="6" class="hint" style="padding:16px;">No reports yet.</td></tr>'

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <h1>🚩 Member Reports</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>📌 Reports Channel</h2>
      <div class="hint" style="margin-bottom:12px;">Where /report submissions get sent — keep this staff-only.</div>
      <form method="post" action="/dashboard/{guild_id}/reports/channel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("reports_channel_id"))}
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>All reports</h2>
      {_table_search_box("reports-table")}
      <div class="log-wrap"><table class="log-table" id="reports-table">
        <tr><th>#</th><th>Reported</th><th>Reported by</th><th>Reason</th><th>Status</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Reports", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/reports/channel", methods=["POST"])
def reports_channel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_reports_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("reports_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/reports/<int:report_id>/status", methods=["POST"])
def reports_status_route(guild_id, report_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    status = request.form.get("status", "")
    if status not in ("resolved", "dismissed"):
        return redirect(url_for("reports_page", guild_id=guild_id, result="❌ Invalid status."))
    result = _run_async(_report_set_status(guild_id, report_id, status, session["user_id"]))
    return redirect(url_for("reports_page", guild_id=guild_id, result=result))


# ---------- AFK status ----------

@app.route("/dashboard/<int:guild_id>/afk")
def afk_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    afk_users = cfg.get("afk", {})
    rows = ""
    if afk_users:
        for uid_str, entry in afk_users.items():
            m = guild.get_member(int(uid_str))
            name = m.display_name if m else f"Unknown ({uid_str})"
            reason = entry.get("reason", "AFK") if isinstance(entry, dict) else str(entry)
            since = entry.get("since") if isinstance(entry, dict) else None
            rows += f"""
            <tr>
              <td>{name}</td>
              <td>{reason}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(since)}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/afk/clear" style="margin:0;">
                  <input type="hidden" name="user_id" value="{uid_str}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Clear</button>
                </form>
              </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="4" class="hint" style="padding:16px;">Nobody is currently AFK.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">💤 AFK Status</h1>
    {result_html}

    <div class="card">
      <h2>Currently AFK</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Member</th><th>Reason</th><th>Since</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — AFK Status", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/afk/clear", methods=["POST"])
def afk_clear_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    user_id = request.form.get("user_id", "")
    cfg = _get_guild_cfg(guild_id)
    afk_users = cfg.get("afk", {})
    if user_id in afk_users:
        afk_users.pop(user_id)
        _save_config(_config)
        return redirect(url_for("afk_page", guild_id=guild_id, result="✅ AFK status cleared."))
    return redirect(url_for("afk_page", guild_id=guild_id, result="ℹ️ That member isn't AFK."))


# ---------- direct message tool ----------

@app.route("/dashboard/<int:guild_id>/dm")
def dm_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""
    member_assets = _member_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">✉️ Direct Message</h1>
    <div class="hint" style="margin-bottom:18px;">Send a DM to any member on behalf of staff — a quick way to reach out without leaving the dashboard.</div>
    {result_html}
    {member_assets}

    <div class="card">
      <form method="post" action="/dashboard/{guild_id}/dm/send">
        {_member_search_field()}
        <div class="field"><label>Message</label><input type="text" name="message" placeholder="What do you want to say?" required></div>
        <button class="btn" type="submit">Send Message</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Direct Message", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/dm/send", methods=["POST"])
def dm_send_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        user_id = int(request.form["user_id"])
    except (KeyError, ValueError):
        return redirect(url_for("dm_page", guild_id=guild_id, result="❌ Pick a member."))
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("dm_page", guild_id=guild_id, result="❌ Write a message."))
    result = _run_async(_send_dm(guild_id, user_id, message, session["user_id"]))
    return redirect(url_for("dm_page", guild_id=guild_id, result=result))


# ---------- Game Servers hub ----------

@app.route("/dashboard/<int:guild_id>/gameservers")
def game_servers_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    # ---- Rust card ----
    if cfg.get("rust_host"):
        rust_status = _run_async(_get_rust_status(guild_id))
        if rust_status.get("error"):
            rust_body = f'<div class="hint" style="color:#ff8080;">⚠️ {rust_status["error"]}</div>'
        else:
            info = rust_status["info"]
            rcon_line = ""
            if rust_status.get("rcon_configured"):
                rcon_line = '<div class="field"><label>RCON</label><div>🟢 Connected</div></div>' if rust_status.get("rcon_connected") else '<div class="field"><label>RCON</label><div>🔴 Not connected</div></div>'
            rust_body = f"""
            <div class="grid-2">
              <div class="field"><label>Map</label><div>{info['map']}</div></div>
              <div class="field"><label>Players</label><div>{info['players']} / {info['max_players']}</div></div>
              {rcon_line}
            </div>
            """
        rust_card = f"""
        <div class="card">
          <h2>🦀 Rust — {cfg.get('rust_host')}</h2>
          {rust_body}
          <div class="hint" style="margin-top:12px; display:flex; gap:14px;">
            <a href="/dashboard/{guild_id}/rust">Overview</a>
            <a href="/dashboard/{guild_id}/rust/players">Players</a>
            <a href="/dashboard/{guild_id}/rust/bans">Bans</a>
          </div>
        </div>
        """
    else:
        rust_card = f"""
        <div class="card">
          <h2>🦀 Rust</h2>
          <div class="hint">Not connected yet. <a href="/dashboard/{guild_id}/rust">Set it up →</a></div>
        </div>
        """

    # ---- Minecraft card ----
    if cfg.get("mc_host"):
        mc_status = _run_async(_get_minecraft_status(guild_id))
        if mc_status.get("error"):
            mc_body = f'<div class="hint" style="color:#ff8080;">⚠️ {mc_status["error"]}</div>'
        else:
            info = mc_status["info"]
            rcon_line = '<div class="field"><label>RCON</label><div>🟢 Configured</div></div>' if mc_status.get("rcon_configured") else ""
            mc_body = f"""
            <div class="grid-2">
              <div class="field"><label>Players</label><div>{info['online']} / {info['max']}</div></div>
              <div class="field"><label>Version</label><div>{info['version']}</div></div>
              {rcon_line}
            </div>
            """
        mc_card = f"""
        <div class="card">
          <h2>⛏️ Minecraft — {cfg.get('mc_host')}</h2>
          {mc_body}
          <div class="hint" style="margin-top:12px; display:flex; gap:14px;">
            <a href="/dashboard/{guild_id}/minecraft">Overview</a>
            <a href="/dashboard/{guild_id}/minecraft/players">Players</a>
            <a href="/dashboard/{guild_id}/minecraft/bans">Bans</a>
          </div>
        </div>
        """
    else:
        mc_card = f"""
        <div class="card">
          <h2>⛏️ Minecraft</h2>
          <div class="hint">Not connected yet. <a href="/dashboard/{guild_id}/minecraft">Set it up →</a></div>
        </div>
        """

    body = f"""
    <h1>🕹️ Game Servers</h1>
    <div class="hint" style="margin-bottom:18px;">Live status for both integrations in one place.</div>
    {result_html}

    <div class="card-row">
      {rust_card}
      {mc_card}
    </div>

    <div class="card">
      <h2>🔄 Rotating Bot Status</h2>
      <div class="hint" style="margin-bottom:12px;">
        Shows a live, auto-updating status under the bot's name in Discord's member list — cycling through member count
        and Rust/Minecraft player counts if connected. Refreshes every 45 seconds.
        {"<br>Currently <strong>ON</strong> for this server." if cfg.get("bot_status_enabled") else "<br>Currently <strong>OFF</strong> for this server."}
      </div>
      <form method="post" action="/dashboard/{guild_id}/gameservers/botstatus">
        <input type="hidden" name="enabled" value="{'false' if cfg.get('bot_status_enabled') else 'true'}">
        <button class="btn" type="submit">
          {"Turn Off" if cfg.get("bot_status_enabled") else "Turn On"}
        </button>
      </form>
    </div>

    <div class="hint" style="margin-top:14px;">📡 Public status page (no login, safe to share with members): <a href="/status/{guild_id}" target="_blank">{DASHBOARD_URL}/status/{guild_id}</a></div>
    """
    return render_page(f"{guild.name} — Game Servers", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/gameservers/botstatus", methods=["POST"])
def game_servers_botstatus_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    enabled = request.form.get("enabled", "false") == "true"
    result = _run_async(_set_bot_status(guild_id, enabled, session["user_id"]))
    return redirect(url_for("game_servers_page", guild_id=guild_id, result=result))


# ---------- Rust server integration ----------

@app.route("/dashboard/<int:guild_id>/rust")
def rust_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    status = _run_async(_get_rust_status(guild_id))
    if status.get("error"):
        status_html = f'<div class="hint" style="color:#ff8080;">⚠️ {status["error"]}</div>'
    else:
        info = status["info"]
        rcon_line = ""
        if status.get("rcon_configured"):
            rcon_line = (
                '<div class="field"><label>RCON</label><div>🟢 Connected</div></div>'
                if status.get("rcon_connected") else
                '<div class="field"><label>RCON</label><div>🔴 Not connected</div></div>'
            )
        status_html = f"""
        <div class="grid-2">
          <div class="field"><label>Server Name</label><div>{info['name']}</div></div>
          <div class="field"><label>Map</label><div>{info['map']}</div></div>
          <div class="field"><label>Players</label><div>{info['players']} / {info['max_players']}</div></div>
          {rcon_line}
        </div>
        """

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🦀 Rust Server</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>📡 Live Status</h2>
      {status_html}
    </div>

    <div class="card">
      <h2>🔗 Connection</h2>
      <div class="hint" style="margin-bottom:12px;">Query port is needed for live status (no password required). RCON port + password are optional — only needed for the chat bridge and running commands.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/connect">
        <div class="grid-2">
          <div class="field"><label>Host / IP</label><input type="text" name="host" value="{cfg.get('rust_host', '')}" placeholder="123.45.67.89" required></div>
          <div class="field"><label>Query Port</label><input type="number" name="query_port" value="{cfg.get('rust_query_port', '')}" placeholder="28015" required></div>
        </div>
        <div class="grid-2">
          <div class="field"><label>RCON Port (optional)</label><input type="number" name="rcon_port" value="{cfg.get('rust_rcon_port', '')}" placeholder="28016"></div>
          <div class="field"><label>RCON Password (optional)</label><input type="password" name="rcon_password" placeholder="Leave blank to keep unchanged"></div>
        </div>
        <div class="field"><label>Connect Port (for the one-click Connect button — blank = same as Query Port)</label><input type="number" name="connect_port" value="{cfg.get('rust_connect_port', '')}" placeholder="28015"></div>
        <button class="btn" type="submit">Save & Connect</button>
      </form>
    </div>

    <div class="card">
      <h2>💬 Chat Bridge</h2>
      <div class="hint" style="margin-bottom:12px;">Requires RCON to be connected. Messages sent in this channel get relayed in-game, and in-game chat gets posted here.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/chatchannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("rust_chat_channel_id"))}
        <button class="btn" type="submit">Set Chat Channel</button>
      </form>
    </div>

    <div class="card">
      <h2>📌 Status Channel</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a live-updating status embed, refreshed automatically every 2 minutes.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/statuschannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("rust_status_channel_id"))}
        <button class="btn" type="submit">Set Status Channel</button>
      </form>
    </div>

    <div class="card">
      <h2>🚨 Downtime Alerts</h2>
      <div class="hint" style="margin-bottom:12px;">Posts here whenever the server goes offline or comes back — separate from the status channel above, so alerts can go somewhere staff-only if you want.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/alertchannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("rust_alert_channel_id"))}
        <button class="btn" type="submit">Set Alert Channel</button>
      </form>
    </div>

    <div class="card">
      <h2>⌨️ RCON Console</h2>
      <div class="hint" style="margin-bottom:12px;">Run a raw command on the server. Requires RCON to be connected.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/command">
        <div class="field"><label>Command</label><input type="text" name="cmd" placeholder="serverinfo" required></div>
        <button class="btn btn-secondary" type="submit">Run</button>
      </form>
    </div>

    <div class="card-row">
      <div class="card">
        <h2>💾 Quick Save</h2>
        <div class="hint" style="margin-bottom:12px;">Trigger an immediate server save.</div>
        <form method="post" action="/dashboard/{guild_id}/rust/save">
          <button class="btn btn-secondary" type="submit">Save Now</button>
        </form>
      </div>

      <div class="card">
        <h2>🔄 Restart</h2>
        <div class="hint" style="margin-bottom:12px;">Schedules a restart with a countdown warning to players.</div>
        <form method="post" action="/dashboard/{guild_id}/rust/restart">
          <div class="field"><label>Seconds</label><input type="number" name="seconds" value="60" min="10" required></div>
          <button class="btn btn-secondary" type="submit">Restart Server</button>
        </form>
      </div>

      <div class="card">
        <h2>📢 Broadcast</h2>
        <div class="hint" style="margin-bottom:12px;">Send a one-off message to everyone in-game.</div>
        <form method="post" action="/dashboard/{guild_id}/rust/announce">
          <div class="field"><label>Message</label><input type="text" name="message" placeholder="Server restarting soon!" required></div>
          <button class="btn btn-secondary" type="submit">Broadcast</button>
        </form>
      </div>
    </div>

    <div class="card">
      <h2>🔧 Wipe Schedule</h2>
      <div class="hint" style="margin-bottom:12px;">Auto-announces a countdown at 24h, 12h, and 1h before wipe.
        {"<br>Currently scheduled." if cfg.get("rust_wipe_day") is not None else "<br>Not scheduled."}</div>
      <form method="post" action="/dashboard/{guild_id}/rust/wipe">
        <div class="grid-2">
          <div class="field">
            <label>Day (UTC)</label>
            <select name="day">
              <option value="">— Disabled —</option>
              {"".join(f'<option value="{i}" {"selected" if cfg.get("rust_wipe_day") == i else ""}>{d}</option>' for i, d in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]))}
            </select>
          </div>
          <div class="field"><label>Hour (0-23 UTC)</label><input type="number" name="hour" min="0" max="23" value="{cfg.get('rust_wipe_hour', '')}"></div>
        </div>
        {_channel_search_field("Announcement channel", "channel_id", guild, cfg.get("rust_wipe_channel_id"))}
        <button class="btn" type="submit">Save Wipe Schedule</button>
      </form>
    </div>

    <div class="card">
      <h2>📊 Population Alerts</h2>
      <div class="hint" style="margin-bottom:12px;">Pings a role when the server hits a player threshold (defaults to full).
        {"<br>Currently ON." if cfg.get("rust_pop_alert_role_id") else "<br>Currently OFF."}</div>
      <form method="post" action="/dashboard/{guild_id}/rust/popalert">
        {_role_search_field("Role to ping", "role_id", guild, cfg.get("rust_pop_alert_role_id"))}
        {_channel_search_field("Alert channel", "channel_id", guild, cfg.get("rust_pop_alert_channel_id"))}
        <div class="field"><label>Threshold (blank = server's max player count)</label><input type="number" name="threshold" value="{cfg.get('rust_pop_threshold', '')}"></div>
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>🟢🔴 Join/Leave Announcements</h2>
      <div class="hint" style="margin-bottom:12px;">Posts when someone connects or disconnects. Best-effort message parsing — wording varies slightly by server version.
        {"<br>Currently ON." if cfg.get("rust_joinleave_channel_id") else "<br>Currently OFF."}</div>
      <form method="post" action="/dashboard/{guild_id}/rust/joinleave">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("rust_joinleave_channel_id"))}
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>🔨 Ban Sync</h2>
      <div class="hint" style="margin-bottom:12px;">Auto-bans on Rust too whenever someone is Discord-banned (requires a linked SteamID via /linksteam).
        {"<br>Currently ON." if cfg.get("rust_ban_sync_enabled") else "<br>Currently OFF."}</div>
      <form method="post" action="/dashboard/{guild_id}/rust/bansync">
        <input type="hidden" name="enabled" value="{'false' if cfg.get('rust_ban_sync_enabled') else 'true'}">
        <div class="field"><label>Command template (optional)</label><input type="text" name="command_template" placeholder='ban {{steamid}} "{{reason}}"' value="{cfg.get('rust_ban_sync_command_template', '')}"></div>
        <button class="btn" type="submit">{"Turn Off" if cfg.get("rust_ban_sync_enabled") else "Turn On"}</button>
      </form>
    </div>

    <div class="card">
      <h2>📋 Server Info / Rules</h2>
      <div class="hint" style="margin-bottom:12px;">Shown to members via /rust info, alongside a Connect button and your wipe schedule.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/rules">
        <div class="field"><label>Rules / info text</label><textarea name="text" rows="5" style="width:100%; background:#0e1016; border:1px solid var(--border); color:var(--text); padding:9px 11px; border-radius:8px; font-family:inherit; font-size:14px;">{html.escape(cfg.get('rust_rules_text', ''))}</textarea></div>
        <button class="btn" type="submit">Save</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Rust Server", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/rust/connect", methods=["POST"])
def rust_connect_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    host = request.form.get("host", "").strip()
    try:
        query_port = int(request.form["query_port"])
    except (KeyError, ValueError):
        return redirect(url_for("rust_page", guild_id=guild_id, result="❌ Enter a valid query port."))
    if not host:
        return redirect(url_for("rust_page", guild_id=guild_id, result="❌ Enter a host/IP."))

    rcon_port = None
    rcon_password = request.form.get("rcon_password", "").strip() or None
    if request.form.get("rcon_port"):
        try:
            rcon_port = int(request.form["rcon_port"])
        except ValueError:
            rcon_port = None

    # If they left the password blank but a port is set, reuse the saved password (don't wipe it).
    cfg = _get_guild_cfg(guild_id)
    if rcon_port and not rcon_password:
        rcon_password = cfg.get("rust_rcon_password")

    connect_port = None
    if request.form.get("connect_port"):
        try:
            connect_port = int(request.form["connect_port"])
        except ValueError:
            connect_port = None

    result = _run_async(_set_rust_server(guild_id, host, query_port, rcon_port, rcon_password, session["user_id"], connect_port))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/chatchannel", methods=["POST"])
def rust_chatchannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    cfg = _get_guild_cfg(guild_id)
    if not raw:
        cfg.pop("rust_chat_channel_id", None)
        _save_config(_config)
        return redirect(url_for("rust_page", guild_id=guild_id, result="✅ Chat bridge disabled."))
    try:
        channel_id = int(raw)
    except ValueError:
        return redirect(url_for("rust_page", guild_id=guild_id, result="❌ Pick a channel."))
    cfg["rust_chat_channel_id"] = channel_id
    _save_config(_config)
    channel = guild.get_channel(channel_id)
    name = f"#{channel.name}" if channel else "that channel"
    return redirect(url_for("rust_page", guild_id=guild_id, result=f"✅ Chat bridge set to {name}."))


@app.route("/dashboard/<int:guild_id>/rust/statuschannel", methods=["POST"])
def rust_statuschannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_rust_status_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/alertchannel", methods=["POST"])
def rust_alertchannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_rust_alert_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/command", methods=["POST"])
def rust_command_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cmd = request.form.get("cmd", "").strip()
    if not cmd:
        return redirect(url_for("rust_page", guild_id=guild_id, result="❌ Enter a command."))
    result = _run_async(_rust_command(guild_id, cmd, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=f"📟 {result}"))


@app.route("/dashboard/<int:guild_id>/rust/save", methods=["POST"])
def rust_save_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_rust_save(guild_id, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/restart", methods=["POST"])
def rust_restart_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        seconds = int(request.form.get("seconds", 60))
    except ValueError:
        seconds = 60
    result = _run_async(_rust_restart(guild_id, seconds, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/announce", methods=["POST"])
def rust_announce_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("rust_page", guild_id=guild_id, result="❌ Enter a message."))
    result = _run_async(_rust_announce(guild_id, message, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/wipe", methods=["POST"])
def rust_wipe_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw_day = request.form.get("day", "")
    day = int(raw_day) if raw_day != "" else None
    raw_hour = request.form.get("hour", "")
    hour = int(raw_hour) if raw_hour != "" else None
    raw_channel = request.form.get("channel_id", "")
    channel_id = int(raw_channel) if raw_channel else None
    result = _run_async(_rust_set_wipe(guild_id, day, hour, channel_id, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/popalert", methods=["POST"])
def rust_popalert_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw_role = request.form.get("role_id", "")
    role_id = int(raw_role) if raw_role else None
    raw_channel = request.form.get("channel_id", "")
    channel_id = int(raw_channel) if raw_channel else None
    raw_threshold = request.form.get("threshold", "")
    threshold = int(raw_threshold) if raw_threshold else None
    result = _run_async(_rust_set_popalert(guild_id, role_id, channel_id, threshold, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/joinleave", methods=["POST"])
def rust_joinleave_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_rust_set_joinleave_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/bansync", methods=["POST"])
def rust_bansync_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    enabled = request.form.get("enabled", "false") == "true"
    command_template = request.form.get("command_template", "").strip() or None
    result = _run_async(_rust_set_bansync(guild_id, enabled, command_template, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/rules", methods=["POST"])
def rust_rules_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    text = request.form.get("text", "").strip()
    result = _run_async(_rust_set_rules(guild_id, text, session["user_id"]))
    return redirect(url_for("rust_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/players")
def rust_players_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    data = _run_async(_rust_get_players(guild_id))
    if data.get("error"):
        players_html = f'<div class="hint" style="color:#ff8080; padding:12px;">⚠️ {data["error"]}</div>'
    else:
        players = data.get("players", [])
        if not players:
            players_html = '<div class="hint" style="padding:12px;">Nobody online right now.</div>'
        else:
            rows = ""
            for p in players:
                steam_id = str(p.get("SteamID", ""))
                name = html.escape(str(p.get("DisplayName", "Unknown")))
                ping = p.get("Ping", "—")
                connected = p.get("ConnectedSeconds", 0)
                mins = connected // 60 if isinstance(connected, int) else "—"
                rows += f"""
                <tr>
                  <td>{name}</td>
                  <td class="hint">{steam_id}</td>
                  <td>{ping}</td>
                  <td>{mins}m</td>
                  <td style="white-space:nowrap;">
                    <form method="post" action="/dashboard/{guild_id}/rust/players/kick" style="display:inline;">
                      <input type="hidden" name="steam_id" value="{steam_id}">
                      <input type="hidden" name="player_name" value="{name}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Kick</button>
                    </form>
                    <form method="post" action="/dashboard/{guild_id}/rust/players/ban" style="display:inline;">
                      <input type="hidden" name="steam_id" value="{steam_id}">
                      <input type="hidden" name="player_name" value="{name}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Ban</button>
                    </form>
                  </td>
                </tr>
                """
            players_html = f"""
            <div class="log-wrap"><table class="log-table">
              <tr><th>Name</th><th>SteamID</th><th>Ping</th><th>Time</th><th></th></tr>
              {rows}
            </table></div>
            """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}/rust">&larr; Rust Overview</a></div>
    <h1 style="margin-top:18px;">🎮 Rust Players</h1>
    {result_html}

    <div class="card-row">
      <div class="card">
        <h2>📣 Announce</h2>
        <form method="post" action="/dashboard/{guild_id}/rust/quick/announce">
          <div class="field"><input type="text" name="message" placeholder="Message to broadcast in-game" required></div>
          <button class="btn" type="submit">Send</button>
        </form>
      </div>
      <div class="card">
        <h2>💾 Save & Time</h2>
        <form method="post" action="/dashboard/{guild_id}/rust/quick/save" style="margin-bottom:10px;">
          <button class="btn btn-secondary" type="submit">Force Save</button>
        </form>
        <form method="post" action="/dashboard/{guild_id}/rust/quick/settime" style="display:flex; gap:8px; align-items:flex-end;">
          <div class="field" style="flex:1; margin-bottom:0;"><label>Time of day (0-24)</label><input type="number" name="hour" min="0" max="24" step="0.5" placeholder="12" required></div>
          <button class="btn btn-secondary" type="submit" style="padding:8px 14px;">Set</button>
        </form>
      </div>
    </div>

    <div class="card">
      <h2>Online now ({data.get("players", []).__len__() if not data.get("error") else "?"})</h2>
      {players_html}
    </div>
    """
    return render_page(f"{guild.name} — Rust Players", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/rust/players/kick", methods=["POST"])
def rust_players_kick_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    steam_id = request.form.get("steam_id", "").strip()
    name = request.form.get("player_name", steam_id)
    if not steam_id:
        return redirect(url_for("rust_players_page", guild_id=guild_id, result="❌ Missing SteamID."))
    result = _run_async(_rust_kick_player(guild_id, steam_id, f"Kicked by staff via dashboard ({name})", session["user_id"]))
    return redirect(url_for("rust_players_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/players/ban", methods=["POST"])
def rust_players_ban_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    steam_id = request.form.get("steam_id", "").strip()
    name = request.form.get("player_name", steam_id)
    if not steam_id:
        return redirect(url_for("rust_players_page", guild_id=guild_id, result="❌ Missing SteamID."))
    result = _run_async(_rust_ban_player(guild_id, steam_id, f"Banned by staff via dashboard ({name})", session["user_id"]))
    return redirect(url_for("rust_players_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/quick/announce", methods=["POST"])
def rust_quick_announce_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("rust_players_page", guild_id=guild_id, result="❌ Write a message."))
    safe = message.replace('"', "'")
    result = _run_async(_rust_command(guild_id, f'say "{safe}"', session["user_id"]))
    return redirect(url_for("rust_players_page", guild_id=guild_id, result=f"📣 Announced. {result}"))


@app.route("/dashboard/<int:guild_id>/rust/quick/save", methods=["POST"])
def rust_quick_save_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_rust_command(guild_id, "server.save", session["user_id"]))
    return redirect(url_for("rust_players_page", guild_id=guild_id, result=f"💾 {result}"))


@app.route("/dashboard/<int:guild_id>/rust/quick/settime", methods=["POST"])
def rust_quick_settime_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    hour = request.form.get("hour", "").strip()
    try:
        float(hour)
    except ValueError:
        return redirect(url_for("rust_players_page", guild_id=guild_id, result="❌ Enter a valid hour (0-24)."))
    result = _run_async(_rust_command(guild_id, f"env.time {hour}", session["user_id"]))
    return redirect(url_for("rust_players_page", guild_id=guild_id, result=f"🕐 {result}"))


@app.route("/dashboard/<int:guild_id>/rust/bans")
def rust_bans_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    data = _run_async(_rust_get_banlist(guild_id))
    if data.get("error"):
        bans_html = f'<div class="hint" style="color:#ff8080; padding:12px;">⚠️ {data["error"]}</div>'
    else:
        bans = data.get("bans", [])
        if not bans:
            bans_html = '<div class="hint" style="padding:12px;">No bans on record (or none could be parsed — try the raw command on the Overview page if this looks wrong).</div>'
        else:
            rows = ""
            for b in bans:
                rows += f"""
                <tr>
                  <td>{html.escape(b.get('name',''))}</td>
                  <td class="hint">{b.get('steam_id','')}</td>
                  <td>{html.escape(b.get('reason',''))}</td>
                  <td>
                    <form method="post" action="/dashboard/{guild_id}/rust/bans/unban" style="margin:0;">
                      <input type="hidden" name="steam_id" value="{b.get('steam_id','')}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Unban</button>
                    </form>
                  </td>
                </tr>
                """
            bans_html = f"""
            {_table_search_box("rust-bans-table")}
            <div class="log-wrap"><table class="log-table" id="rust-bans-table">
              <tr><th>Name</th><th>SteamID</th><th>Reason</th><th></th></tr>
              {rows}
            </table></div>
            """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}/rust">&larr; Rust Overview</a></div>
    <h1 style="margin-top:18px;">🚫 Rust Bans</h1>
    {result_html}

    <div class="card">
      <h2>➕ Ban by SteamID</h2>
      <div class="hint" style="margin-bottom:12px;">For banning someone who isn't currently online. For online players, use the Players page instead.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/bans/add">
        <div class="grid-2">
          <div class="field"><label>SteamID</label><input type="text" name="steam_id" placeholder="76561198000000000" required></div>
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        </div>
        <button class="btn btn-secondary" type="submit">Ban</button>
      </form>
    </div>

    <div class="card">
      <h2>Current bans</h2>
      {bans_html}
    </div>
    """
    return render_page(f"{guild.name} — Rust Bans", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/rust/bans/add", methods=["POST"])
def rust_bans_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    steam_id = request.form.get("steam_id", "").strip()
    reason = request.form.get("reason", "").strip()
    if not steam_id or not reason:
        return redirect(url_for("rust_bans_page", guild_id=guild_id, result="❌ Fill in both fields."))
    result = _run_async(_rust_ban_player(guild_id, steam_id, reason, session["user_id"]))
    return redirect(url_for("rust_bans_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/bans/unban", methods=["POST"])
def rust_bans_unban_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    steam_id = request.form.get("steam_id", "").strip()
    if not steam_id:
        return redirect(url_for("rust_bans_page", guild_id=guild_id, result="❌ Missing SteamID."))
    result = _run_async(_rust_unban_player(guild_id, steam_id, session["user_id"]))
    return redirect(url_for("rust_bans_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/macros")
def rust_macros_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    macros = cfg.get("rust_macros", {})
    macro_rows = ""
    if macros:
        for name, command in macros.items():
            safe_name = html.escape(name)
            macro_rows += f"""
            <tr>
              <td>{safe_name}</td>
              <td class="hint">{html.escape(command)}</td>
              <td style="white-space:nowrap;">
                <form method="post" action="/dashboard/{guild_id}/rust/macros/run" style="display:inline;">
                  <input type="hidden" name="name" value="{safe_name}">
                  <input type="text" name="player" placeholder="SteamID (if needed)" style="width:140px; display:inline-block;">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Run</button>
                </form>
                <form method="post" action="/dashboard/{guild_id}/rust/macros/remove" style="display:inline;">
                  <input type="hidden" name="name" value="{safe_name}">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        macro_rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No macros saved yet.</td></tr>'

    announcements = cfg.get("rust_recurring_announcements", [])
    announcement_rows = ""
    if announcements:
        for i, a in enumerate(announcements, start=1):
            announcement_rows += f"""
            <tr>
              <td>{i}</td>
              <td>{html.escape(a.get('message', ''))}</td>
              <td>{a.get('interval_minutes', '')} min</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/rust/macros/announcements/remove" style="margin:0;">
                  <input type="hidden" name="index" value="{i}">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    else:
        announcement_rows = '<tr><td colspan="4" class="hint" style="padding:16px;">No recurring announcements yet.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">⚡ Rust Macros & Announcements</h1>
    {result_html}

    <div class="card">
      <h2>➕ Save a macro</h2>
      <div class="hint" style="margin-bottom:12px;">Use <code>{{player}}</code> anywhere you want a SteamID substituted in when the macro runs.</div>
      <form method="post" action="/dashboard/{guild_id}/rust/macros/add">
        <div class="grid-2">
          <div class="field"><label>Name</label><input type="text" name="name" placeholder="starterkit" required></div>
          <div class="field"><label>RCON command</label><input type="text" name="command" placeholder="inventory.give {{player}} rifle.ak 1" required></div>
        </div>
        <button class="btn" type="submit">Save Macro</button>
      </form>
    </div>

    <div class="card">
      <h2>Saved macros</h2>
      {_table_search_box("rust-macros-table")}
      <div class="log-wrap"><table class="log-table" id="rust-macros-table">
        <tr><th>Name</th><th>Command</th><th></th></tr>
        {macro_rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Add a recurring announcement</h2>
      <form method="post" action="/dashboard/{guild_id}/rust/macros/announcements/add">
        <div class="field"><label>Message</label><input type="text" name="message" placeholder="Vote for the server at..." required></div>
        <div class="field"><label>Repeat every (minutes, min 5)</label><input type="number" name="interval_minutes" min="5" value="60" required></div>
        <button class="btn" type="submit">Add</button>
      </form>
    </div>

    <div class="card">
      <h2>Recurring announcements</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>#</th><th>Message</th><th>Interval</th><th></th></tr>
        {announcement_rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Rust Macros", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/rust/macros/add", methods=["POST"])
def rust_macros_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    command = request.form.get("command", "").strip()
    if not name or not command:
        return redirect(url_for("rust_macros_page", guild_id=guild_id, result="❌ Fill in both fields."))
    result = _run_async(_rust_macro_add(guild_id, name, command, session["user_id"]))
    return redirect(url_for("rust_macros_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/macros/remove", methods=["POST"])
def rust_macros_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("rust_macros_page", guild_id=guild_id, result="❌ Missing macro name."))
    result = _run_async(_rust_macro_remove(guild_id, name, session["user_id"]))
    return redirect(url_for("rust_macros_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/macros/run", methods=["POST"])
def rust_macros_run_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    player = request.form.get("player", "").strip() or None
    if not name:
        return redirect(url_for("rust_macros_page", guild_id=guild_id, result="❌ Missing macro name."))
    result = _run_async(_rust_macro_run(guild_id, name, player, session["user_id"]))
    return redirect(url_for("rust_macros_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/macros/announcements/add", methods=["POST"])
def rust_announcements_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    message = request.form.get("message", "").strip()
    try:
        interval_minutes = int(request.form.get("interval_minutes", 60))
    except ValueError:
        interval_minutes = 60
    if not message:
        return redirect(url_for("rust_macros_page", guild_id=guild_id, result="❌ Enter a message."))
    result = _run_async(_rust_announcement_add(guild_id, message, interval_minutes, session["user_id"]))
    return redirect(url_for("rust_macros_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rust/macros/announcements/remove", methods=["POST"])
def rust_announcements_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        index = int(request.form.get("index", 0))
    except ValueError:
        index = 0
    result = _run_async(_rust_announcement_remove(guild_id, index, session["user_id"]))
    return redirect(url_for("rust_macros_page", guild_id=guild_id, result=result))


# ---------- whitelist sync ----------

@app.route("/dashboard/<int:guild_id>/whitelistsync")
def whitelist_sync_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    rank_assets = _rank_search_assets(guild, cfg)
    threshold_rank_id = cfg.get("whitelist_sync_rank_id")
    threshold_role = guild.get_role(threshold_rank_id) if threshold_rank_id else None

    linked_steam = cfg.get("linked_steam_ids", {})
    linked_mc = cfg.get("linked_minecraft_names", {})
    linked_rows = ""
    all_linked_ids = set(linked_steam.keys()) | set(linked_mc.keys())
    if all_linked_ids:
        for uid in all_linked_ids:
            m = guild.get_member(int(uid))
            name = m.display_name if m else f"Unknown ({uid})"
            linked_rows += f"<tr><td>{name}</td><td>{linked_steam.get(uid, '—')}</td><td>{html.escape(linked_mc.get(uid, '—'))}</td></tr>"
    else:
        linked_rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No members have linked an account yet (/linksteam or /linkminecraft).</td></tr>'

    body = f"""
    <h1>🎮 Whitelist Auto-Sync</h1>
    <div class="hint" style="margin-bottom:18px;">Reaching a chosen rank automatically whitelists that member on Rust and/or Minecraft, if they've linked their account.</div>
    {result_html}
    {rank_assets}

    <div class="card">
      <h2>⚙️ Settings</h2>
      <div class="hint" style="margin-bottom:12px;">Current threshold: {threshold_role.mention if threshold_role else "not set"}</div>
      <form method="post" action="/dashboard/{guild_id}/whitelistsync/save">
        {_rank_search_field("Rank threshold (this rank or higher triggers whitelisting)", "rank_id")}
        <div class="field"><label>Rust RCON command template (use {{steamid}} as a placeholder)</label><input type="text" name="rust_command_template" placeholder='whitelist add {{steamid}}' value="{html.escape(cfg.get('whitelist_rust_command_template', ''))}"></div>
        <div class="field">
          <label>Minecraft whitelist</label>
          <select name="minecraft_enabled">
            <option value="true" {"selected" if cfg.get("whitelist_minecraft_enabled") else ""}>On</option>
            <option value="false" {"selected" if not cfg.get("whitelist_minecraft_enabled") else ""}>Off</option>
          </select>
        </div>
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>Linked accounts</h2>
      {_table_search_box("linked-accounts-table")}
      <div class="log-wrap"><table class="log-table" id="linked-accounts-table">
        <tr><th>Member</th><th>SteamID</th><th>Minecraft Username</th></tr>
        {linked_rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Whitelist Sync", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/whitelistsync/save", methods=["POST"])
def whitelist_sync_save_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw_rank = request.form.get("rank_id", "")
    rank_id = int(raw_rank) if raw_rank else None
    rust_command_template = request.form.get("rust_command_template", "").strip() or None
    minecraft_enabled = request.form.get("minecraft_enabled") == "true"
    result = _run_async(_set_whitelist_sync(guild_id, rank_id, rust_command_template, minecraft_enabled, session["user_id"]))
    return redirect(url_for("whitelist_sync_page", guild_id=guild_id, result=result))


# ---------- rank bonus roles ----------

@app.route("/dashboard/<int:guild_id>/rankbonusroles")
def rank_bonus_roles_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    rank_assets = _rank_search_assets(guild, cfg)
    role_assets = _role_search_assets(guild)

    bonus_map = cfg.get("rank_bonus_roles", {})
    ranks = cfg.get("ranks", [])
    rows = ""
    for rid in ranks:
        bonus_list = bonus_map.get(str(rid), [])
        if not bonus_list:
            continue
        rank_role = guild.get_role(rid)
        rank_label = rank_role.name if rank_role else f"(deleted rank {rid})"
        for bonus_id in bonus_list:
            bonus_role = guild.get_role(bonus_id)
            bonus_label = bonus_role.name if bonus_role else f"(deleted role {bonus_id})"
            rows += f"""
            <tr>
              <td>{html.escape(rank_label)}</td>
              <td>{html.escape(bonus_label)}</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/rankbonusroles/remove" style="margin:0;">
                  <input type="hidden" name="rank_id" value="{rid}">
                  <input type="hidden" name="bonus_role_id" value="{bonus_id}">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Remove</button>
                </form>
              </td>
            </tr>
            """
    if not rows:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No bonus roles configured yet.</td></tr>'

    body = f"""
    <h1>🎁 Rank Bonus Roles</h1>
    <div class="hint" style="margin-bottom:18px;">When someone reaches a rank, automatically grant them extra roles too — additive only, doesn't remove anything on demotion.</div>
    {result_html}
    {rank_assets}
    {role_assets}

    <div class="card">
      <h2>➕ Add a bonus role</h2>
      <form method="post" action="/dashboard/{guild_id}/rankbonusroles/add">
        <div class="grid-2">
          {_rank_search_field("Rank")}
          {_role_search_field("Bonus role to grant")}
        </div>
        <button class="btn" type="submit">Add</button>
      </form>
    </div>

    <div class="card">
      <h2>Current bonus roles</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Rank</th><th>Bonus Role</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Rank Bonus Roles", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/rankbonusroles/add", methods=["POST"])
def rank_bonus_roles_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        rank_id = int(request.form["rank_id"])
        role_id = int(request.form["role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("rank_bonus_roles_page", guild_id=guild_id, result="❌ Pick a rank and a role."))
    result = _run_async(_add_rank_bonus_role(guild_id, rank_id, role_id, session["user_id"]))
    return redirect(url_for("rank_bonus_roles_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/rankbonusroles/remove", methods=["POST"])
def rank_bonus_roles_remove_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        rank_id = int(request.form["rank_id"])
        bonus_role_id = int(request.form["bonus_role_id"])
    except (KeyError, ValueError):
        return redirect(url_for("rank_bonus_roles_page", guild_id=guild_id, result="❌ Invalid request."))
    result = _run_async(_remove_rank_bonus_role(guild_id, rank_id, bonus_role_id, session["user_id"]))
    return redirect(url_for("rank_bonus_roles_page", guild_id=guild_id, result=result))


# ---------- Minecraft server integration ----------

@app.route("/dashboard/<int:guild_id>/minecraft")
def minecraft_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    status = _run_async(_get_minecraft_status(guild_id))
    if status.get("error"):
        status_html = f'<div class="hint" style="color:#ff8080;">⚠️ {status["error"]}</div>'
    else:
        info = status["info"]
        rcon_line = '<div class="field"><label>RCON</label><div>🟢 Configured</div></div>' if status.get("rcon_configured") else ""
        status_html = f"""
        <div class="grid-2">
          <div class="field"><label>MOTD</label><div>{info['motd']}</div></div>
          <div class="field"><label>Players</label><div>{info['online']} / {info['max']}</div></div>
          <div class="field"><label>Version</label><div>{info['version']}</div></div>
          {rcon_line}
        </div>
        """

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">⛏️ Minecraft Server</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>📡 Live Status</h2>
      {status_html}
    </div>

    <div class="card">
      <h2>🔗 Connection</h2>
      <div class="hint" style="margin-bottom:12px;">Status works out of the box on any vanilla Java Edition server. RCON needs enable-rcon=true set in server.properties.</div>
      <form method="post" action="/dashboard/{guild_id}/minecraft/connect">
        <div class="grid-2">
          <div class="field"><label>Host / IP</label><input type="text" name="host" value="{cfg.get('mc_host', '')}" placeholder="123.45.67.89" required></div>
          <div class="field"><label>Port</label><input type="number" name="port" value="{cfg.get('mc_port', 25565)}" placeholder="25565" required></div>
        </div>
        <div class="grid-2">
          <div class="field"><label>RCON Port (optional)</label><input type="number" name="rcon_port" value="{cfg.get('mc_rcon_port', '')}" placeholder="25575"></div>
          <div class="field"><label>RCON Password (optional)</label><input type="password" name="rcon_password" placeholder="Leave blank to keep unchanged"></div>
        </div>
        <button class="btn" type="submit">Save & Connect</button>
      </form>
    </div>

    <div class="card">
      <h2>📌 Status Channel</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a live-updating status embed, refreshed automatically every 2 minutes.</div>
      <form method="post" action="/dashboard/{guild_id}/minecraft/statuschannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("mc_status_channel_id"))}
        <button class="btn" type="submit">Set Status Channel</button>
      </form>
    </div>

    <div class="card">
      <h2>🚨 Downtime Alerts</h2>
      <div class="hint" style="margin-bottom:12px;">Posts here whenever the server goes offline or comes back — separate from the status channel above.</div>
      <form method="post" action="/dashboard/{guild_id}/minecraft/alertchannel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("mc_alert_channel_id"))}
        <button class="btn" type="submit">Set Alert Channel</button>
      </form>
    </div>

    <div class="card">
      <h2>⌨️ RCON Console</h2>
      <div class="hint" style="margin-bottom:12px;">Run a raw command on the server (without the leading /). Requires RCON to be set up.</div>
      <form method="post" action="/dashboard/{guild_id}/minecraft/command">
        <div class="field"><label>Command</label><input type="text" name="cmd" placeholder="list" required></div>
        <button class="btn btn-secondary" type="submit">Run</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Minecraft Server", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/minecraft/connect", methods=["POST"])
def minecraft_connect_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    host = request.form.get("host", "").strip()
    try:
        port = int(request.form["port"])
    except (KeyError, ValueError):
        return redirect(url_for("minecraft_page", guild_id=guild_id, result="❌ Enter a valid port."))
    if not host:
        return redirect(url_for("minecraft_page", guild_id=guild_id, result="❌ Enter a host/IP."))

    rcon_port = None
    rcon_password = request.form.get("rcon_password", "").strip() or None
    if request.form.get("rcon_port"):
        try:
            rcon_port = int(request.form["rcon_port"])
        except ValueError:
            rcon_port = None

    cfg = _get_guild_cfg(guild_id)
    if rcon_port and not rcon_password:
        rcon_password = cfg.get("mc_rcon_password")

    result = _run_async(_set_minecraft_server(guild_id, host, port, rcon_port, rcon_password, session["user_id"]))
    return redirect(url_for("minecraft_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/statuschannel", methods=["POST"])
def minecraft_statuschannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_minecraft_status_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("minecraft_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/alertchannel", methods=["POST"])
def minecraft_alertchannel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_minecraft_alert_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("minecraft_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/command", methods=["POST"])
def minecraft_command_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cmd = request.form.get("cmd", "").strip()
    if not cmd:
        return redirect(url_for("minecraft_page", guild_id=guild_id, result="❌ Enter a command."))
    result = _run_async(_minecraft_command(guild_id, cmd, session["user_id"]))
    return redirect(url_for("minecraft_page", guild_id=guild_id, result=f"📟 {result}"))


@app.route("/dashboard/<int:guild_id>/minecraft/players")
def minecraft_players_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    data = _run_async(_minecraft_get_players(guild_id))
    if data.get("error"):
        players_html = f'<div class="hint" style="color:#ff8080; padding:12px;">⚠️ {data["error"]}</div>'
    else:
        players = data.get("players", [])
        if not players:
            players_html = '<div class="hint" style="padding:12px;">Nobody online right now.</div>'
        else:
            rows = ""
            for name in players:
                safe_name = html.escape(name)
                rows += f"""
                <tr>
                  <td>{safe_name}</td>
                  <td style="white-space:nowrap;">
                    <form method="post" action="/dashboard/{guild_id}/minecraft/players/kick" style="display:inline;">
                      <input type="hidden" name="player_name" value="{safe_name}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Kick</button>
                    </form>
                    <form method="post" action="/dashboard/{guild_id}/minecraft/players/ban" style="display:inline;">
                      <input type="hidden" name="player_name" value="{safe_name}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Ban</button>
                    </form>
                  </td>
                </tr>
                """
            players_html = f"""
            <div class="log-wrap"><table class="log-table">
              <tr><th>Name</th><th></th></tr>
              {rows}
            </table></div>
            """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}/minecraft">&larr; Minecraft Overview</a></div>
    <h1 style="margin-top:18px;">🎮 Minecraft Players</h1>
    {result_html}

    <div class="card">
      <h2>Online now ({len(data.get("players", [])) if not data.get("error") else "?"})</h2>
      {players_html}
    </div>
    """
    return render_page(f"{guild.name} — Minecraft Players", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/minecraft/players/kick", methods=["POST"])
def minecraft_players_kick_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    player_name = request.form.get("player_name", "").strip()
    if not player_name:
        return redirect(url_for("minecraft_players_page", guild_id=guild_id, result="❌ Missing player name."))
    result = _run_async(_minecraft_kick_player(guild_id, player_name, "Kicked by staff via dashboard", session["user_id"]))
    return redirect(url_for("minecraft_players_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/players/ban", methods=["POST"])
def minecraft_players_ban_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    player_name = request.form.get("player_name", "").strip()
    if not player_name:
        return redirect(url_for("minecraft_players_page", guild_id=guild_id, result="❌ Missing player name."))
    result = _run_async(_minecraft_ban_player(guild_id, player_name, "Banned by staff via dashboard", session["user_id"]))
    return redirect(url_for("minecraft_players_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/bans")
def minecraft_bans_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    data = _run_async(_minecraft_get_banlist(guild_id))
    if data.get("error"):
        bans_html = f'<div class="hint" style="color:#ff8080; padding:12px;">⚠️ {data["error"]}</div>'
    else:
        bans = data.get("bans", [])
        if not bans:
            bans_html = '<div class="hint" style="padding:12px;">No bans on record (or none could be parsed — try the raw command on the Overview page if this looks wrong).</div>'
        else:
            rows = ""
            for b in bans:
                safe_name = html.escape(b.get("name", ""))
                rows += f"""
                <tr>
                  <td>{safe_name}</td>
                  <td>{html.escape(b.get('reason',''))}</td>
                  <td>
                    <form method="post" action="/dashboard/{guild_id}/minecraft/bans/unban" style="margin:0;">
                      <input type="hidden" name="player_name" value="{safe_name}">
                      <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Unban</button>
                    </form>
                  </td>
                </tr>
                """
            bans_html = f"""
            <div class="log-wrap"><table class="log-table">
              <tr><th>Name</th><th>Reason</th><th></th></tr>
              {rows}
            </table></div>
            """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}/minecraft">&larr; Minecraft Overview</a></div>
    <h1 style="margin-top:18px;">🚫 Minecraft Bans</h1>
    {result_html}

    <div class="card">
      <h2>➕ Ban by player name</h2>
      <div class="hint" style="margin-bottom:12px;">For banning someone who isn't currently online. For online players, use the Players page instead.</div>
      <form method="post" action="/dashboard/{guild_id}/minecraft/bans/add">
        <div class="grid-2">
          <div class="field"><label>Player name</label><input type="text" name="player_name" placeholder="Steve" required></div>
          <div class="field"><label>Reason</label><input type="text" name="reason" placeholder="Why" required></div>
        </div>
        <button class="btn btn-secondary" type="submit">Ban</button>
      </form>
    </div>

    <div class="card">
      <h2>Current bans</h2>
      {bans_html}
    </div>
    """
    return render_page(f"{guild.name} — Minecraft Bans", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/minecraft/bans/add", methods=["POST"])
def minecraft_bans_add_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    player_name = request.form.get("player_name", "").strip()
    reason = request.form.get("reason", "").strip()
    if not player_name or not reason:
        return redirect(url_for("minecraft_bans_page", guild_id=guild_id, result="❌ Fill in both fields."))
    result = _run_async(_minecraft_ban_player(guild_id, player_name, reason, session["user_id"]))
    return redirect(url_for("minecraft_bans_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/minecraft/bans/unban", methods=["POST"])
def minecraft_bans_unban_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    player_name = request.form.get("player_name", "").strip()
    if not player_name:
        return redirect(url_for("minecraft_bans_page", guild_id=guild_id, result="❌ Missing player name."))
    result = _run_async(_minecraft_unban_player(guild_id, player_name, session["user_id"]))
    return redirect(url_for("minecraft_bans_page", guild_id=guild_id, result=result))


# ---------- generic incoming webhooks ----------

@app.route("/dashboard/<int:guild_id>/webhooks")
def webhooks_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    token = cfg.get("webhook_token")
    if token:
        webhook_url = f"{DASHBOARD_URL}/webhook/{guild_id}/{token}"
        url_html = f"""
        <div class="field">
          <label>Your webhook URL</label>
          <input type="text" value="{webhook_url}" readonly onclick="this.select()">
        </div>
        <div class="hint">POST JSON to this URL from any external service (GitHub, UptimeRobot, Zapier, IFTTT, etc.). It looks for a "title" and "text"/"message" field — anything else gets posted as raw JSON.</div>
        """
    else:
        url_html = '<div class="hint">No webhook URL generated yet — click below to create one.</div>'

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔌 Incoming Webhooks</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>Your webhook</h2>
      {url_html}
      <form method="post" action="/dashboard/{guild_id}/webhooks/regenerate" style="margin-top:14px;">
        <button class="btn btn-secondary" type="submit">{"Regenerate URL" if token else "Generate Webhook URL"}</button>
      </form>
    </div>

    <div class="card">
      <h2>📌 Target channel</h2>
      <form method="post" action="/dashboard/{guild_id}/webhooks/channel">
        {_channel_search_field("Channel", "channel_id", guild, cfg.get("webhook_channel_id"))}
        <button class="btn" type="submit">Set Channel</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Webhooks", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/webhooks/regenerate", methods=["POST"])
def webhooks_regenerate_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cfg = _get_guild_cfg(guild_id)
    cfg["webhook_token"] = secrets.token_urlsafe(24)
    _save_config(_config)
    return redirect(url_for("webhooks_page", guild_id=guild_id, result="✅ New webhook URL generated — update it wherever the old one was used."))


@app.route("/dashboard/<int:guild_id>/webhooks/channel", methods=["POST"])
def webhooks_channel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    cfg = _get_guild_cfg(guild_id)
    if not raw:
        cfg.pop("webhook_channel_id", None)
        _save_config(_config)
        return redirect(url_for("webhooks_page", guild_id=guild_id, result="✅ Webhook posting disabled."))
    try:
        channel_id = int(raw)
    except ValueError:
        return redirect(url_for("webhooks_page", guild_id=guild_id, result="❌ Pick a channel."))
    cfg["webhook_channel_id"] = channel_id
    _save_config(_config)
    channel = guild.get_channel(channel_id)
    name = f"#{channel.name}" if channel else "that channel"
    return redirect(url_for("webhooks_page", guild_id=guild_id, result=f"✅ Webhooks will now post to {name}."))


@app.route("/webhook/<int:guild_id>/<token>", methods=["POST"])
def incoming_webhook(guild_id, token):
    """Public endpoint — no login required, external services post here directly.
    Protected only by the random token in the URL."""
    cfg = _get_guild_cfg(guild_id)
    stored_token = cfg.get("webhook_token")
    if not stored_token or token != stored_token:
        return {"error": "invalid token"}, 403

    payload = request.get_json(silent=True) or {"text": request.get_data(as_text=True)}
    ok = _run_async(_relay_incoming_webhook(guild_id, payload))
    if ok:
        return {"status": "ok"}, 200
    return {"error": "no channel configured or send failed"}, 400


@app.route("/status/<int:guild_id>")
def public_status_page(guild_id):
    """Public endpoint — no login required. Shows bot + game server status
    only; nothing sensitive (no channels, no member data, no settings)."""
    guild = _bot.get_guild(guild_id)
    if guild is None:
        return render_page("Status", '<div class="card"><h2>Server not found</h2></div>', show_logout=False)

    cfg = _get_guild_cfg(guild_id)
    bot_online = _bot.is_ready()
    bot_pill = '<span class="pill" style="background:#5ee0a022; border-color:#5ee0a055; color:#5ee0a0;">🟢 Online</span>' if bot_online else '<span class="pill" style="background:#ff808022; border-color:#ff808055; color:#ff8080;">🔴 Offline</span>'

    sections = f"""
    <div class="card">
      <h2>🤖 Bot</h2>
      <div>{bot_pill}</div>
    </div>
    """

    if cfg.get("rust_host"):
        rust_status = _run_async(_get_rust_status(guild_id))
        if rust_status.get("error"):
            rust_html = f'<div class="hint" style="color:#ff8080;">⚠️ {rust_status["error"]}</div>'
        else:
            info = rust_status["info"]
            rust_html = f"""
            <div class="grid-2">
              <div class="field"><label>Map</label><div>{info['map']}</div></div>
              <div class="field"><label>Players</label><div>{info['players']} / {info['max_players']}</div></div>
            </div>
            """
    else:
        rust_html = '<div class="hint">Not set up yet.</div>'
    sections += f"""
    <div class="card">
      <h2>🦀 Rust Server</h2>
      {rust_html}
    </div>
    """

    if cfg.get("mc_host"):
        mc_status = _run_async(_get_minecraft_status(guild_id))
        if mc_status.get("error"):
            mc_html = f'<div class="hint" style="color:#ff8080;">⚠️ {mc_status["error"]}</div>'
        else:
            info = mc_status["info"]
            mc_html = f"""
            <div class="grid-2">
              <div class="field"><label>Players</label><div>{info['online']} / {info['max']}</div></div>
              <div class="field"><label>Version</label><div>{info['version']}</div></div>
            </div>
            """
    else:
        mc_html = '<div class="hint">Not set up yet.</div>'
    sections += f"""
    <div class="card">
      <h2>⛏️ Minecraft Server</h2>
      {mc_html}
    </div>
    """

    body = f"""
    <h1>📡 {guild.name} — Status</h1>
    <div class="hint" style="margin-bottom:18px;">Live status, no login required.</div>
    {sections}
    """
    return render_page(f"{guild.name} — Status", body, show_logout=False)


# ---------- tournaments ----------

@app.route("/dashboard/<int:guild_id>/tournaments")
def tournaments_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    tournaments = cfg.get("tournaments", {})
    rows = ""
    if tournaments:
        for name, data in tournaments.items():
            status = data.get("status", "signup")
            status_color = {"signup": "#5ee0a0", "in_progress": "#f5c15c", "complete": "#80848e"}.get(status, "#80848e")
            status_pill = f'<span class="pill" style="background:{status_color}22; border-color:{status_color}55; color:{status_color};">{status}</span>'
            extra = ""
            if status == "complete":
                champ = guild.get_member(data.get("champion"))
                extra = f" — 🏆 {champ.display_name if champ else 'Unknown'}"
            rows += f"<tr><td>{name}</td><td>{status_pill}{extra}</td><td>{len(data.get('players', []))}</td></tr>"
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No tournaments yet.</td></tr>'

    member_assets = _member_search_assets(guild)
    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🏆 Tournaments</h1>
    {result_html}
    {member_assets}
    {channel_assets}

    <div class="card">
      <h2>Current tournaments</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>Name</th><th>Status</th><th>Players</th></tr>
        {rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Create a tournament</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a sign-up embed with Join/Leave buttons.</div>
      <form method="post" action="/dashboard/{guild_id}/tournaments/create">
        <div class="field"><label>Tournament name</label><input type="text" name="name" placeholder="Summer Scrims" required></div>
        {_channel_search_field()}
        <button class="btn" type="submit">Create</button>
      </form>
    </div>

    <div class="card">
      <h2>▶️ Start a tournament</h2>
      <div class="hint" style="margin-bottom:12px;">Locks sign-ups and generates the first round.</div>
      <form method="post" action="/dashboard/{guild_id}/tournaments/start">
        <div class="field"><label>Tournament name</label><input type="text" name="name" required></div>
        <button class="btn" type="submit">Start</button>
      </form>
    </div>

    <div class="card">
      <h2>🏅 Report a match result</h2>
      <form method="post" action="/dashboard/{guild_id}/tournaments/report">
        <div class="grid-2">
          <div class="field"><label>Tournament name</label><input type="text" name="name" required></div>
          <div class="field"><label>Match number</label><input type="number" name="match" min="1" required></div>
        </div>
        {_member_search_field("Winner", "winner_id")}
        <button class="btn btn-secondary" type="submit">Report Result</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Tournaments", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/tournaments/create", methods=["POST"])
def tournaments_create_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    try:
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tournaments_page", guild_id=guild_id, result="❌ Fill in a name and pick a channel."))
    if not name:
        return redirect(url_for("tournaments_page", guild_id=guild_id, result="❌ Enter a tournament name."))
    result = _run_async(_tournament_create(guild_id, name, channel_id, session["user_id"]))
    return redirect(url_for("tournaments_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tournaments/start", methods=["POST"])
def tournaments_start_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    if not name:
        return redirect(url_for("tournaments_page", guild_id=guild_id, result="❌ Enter a tournament name."))
    result = _run_async(_tournament_start(guild_id, name, session["user_id"]))
    return redirect(url_for("tournaments_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/tournaments/report", methods=["POST"])
def tournaments_report_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    name = request.form.get("name", "").strip()
    try:
        match = int(request.form["match"])
        winner_id = int(request.form["winner_id"])
    except (KeyError, ValueError):
        return redirect(url_for("tournaments_page", guild_id=guild_id, result="❌ Fill in all fields correctly."))
    if not name:
        return redirect(url_for("tournaments_page", guild_id=guild_id, result="❌ Enter a tournament name."))
    result = _run_async(_tournament_report(guild_id, name, match, winner_id, session["user_id"]))
    return redirect(url_for("tournaments_page", guild_id=guild_id, result=result))


# ---------- game nights ----------

@app.route("/dashboard/<int:guild_id>/gamenights")
def gamenights_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    gamenights = cfg.get("gamenights", {})
    now = datetime.now(timezone.utc)
    upcoming = sorted(
        (d for d in gamenights.values() if datetime.fromisoformat(d["when"]) > now),
        key=lambda d: d["when"],
    )
    rows = ""
    if upcoming:
        for d in upcoming:
            rows += f"""
            <tr>
              <td>#{d['id']}</td>
              <td>{d['game']}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(d['when'])}</td>
              <td>{len(d['going'])} going</td>
              <td>
                <form method="post" action="/dashboard/{guild_id}/gamenights/cancel" style="margin:0;">
                  <input type="hidden" name="gamenight_id" value="{d['id']}">
                  <button class="btn btn-secondary" type="submit" style="padding:6px 12px; font-size:12px;">Cancel</button>
                </form>
              </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="5" class="hint" style="padding:16px;">Nothing scheduled right now.</td></tr>'

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🎮 Game Nights</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>Upcoming</h2>
      <div class="log-wrap"><table class="log-table">
        <tr><th>#</th><th>Game</th><th>When</th><th>RSVPs</th><th></th></tr>
        {rows}
      </table></div>
    </div>

    <div class="card">
      <h2>➕ Schedule a game night</h2>
      <div class="hint" style="margin-bottom:12px;">Posts an RSVP embed with Going/Maybe/Can't Go buttons. Time is in UTC.</div>
      <form method="post" action="/dashboard/{guild_id}/gamenights/create">
        <div class="field"><label>Game</label><input type="text" name="game" placeholder="Valorant" required></div>
        <div class="grid-2">
          <div class="field"><label>Date</label><input type="date" name="date" required></div>
          <div class="field"><label>Time (UTC, 24-hour)</label><input type="time" name="time" required></div>
        </div>
        {_channel_search_field()}
        <button class="btn" type="submit">Schedule</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Game Nights", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/gamenights/create", methods=["POST"])
def gamenights_create_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    game = request.form.get("game", "").strip()
    date = request.form.get("date", "").strip()
    time_str = request.form.get("time", "").strip()
    try:
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("gamenights_page", guild_id=guild_id, result="❌ Pick a channel."))
    if not game or not date or not time_str:
        return redirect(url_for("gamenights_page", guild_id=guild_id, result="❌ Fill in the game, date, and time."))

    when_iso = f"{date}T{time_str}:00+00:00"
    result = _run_async(_gamenight_create(guild_id, game, when_iso, channel_id, session["user_id"]))
    return redirect(url_for("gamenights_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/gamenights/cancel", methods=["POST"])
def gamenights_cancel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    try:
        gamenight_id = int(request.form["gamenight_id"])
    except (KeyError, ValueError):
        return redirect(url_for("gamenights_page", guild_id=guild_id, result="❌ Invalid game night."))
    result = _run_async(_gamenight_cancel(guild_id, gamenight_id, session["user_id"]))
    return redirect(url_for("gamenights_page", guild_id=guild_id, result=result))


# ---------- MVP voting ----------

@app.route("/dashboard/<int:guild_id>/mvp")
def mvp_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    poll = cfg.get("mvp_poll")
    if poll:
        tally = {}
        for cid in poll["votes"].values():
            tally[cid] = tally.get(cid, 0) + 1
        rows = ""
        for cid in poll["candidates"]:
            m = guild.get_member(cid)
            name = m.display_name if m else f"Unknown ({cid})"
            rows += f"<tr><td>{name}</td><td>{tally.get(cid, 0)} vote(s)</td></tr>"
        active_html = f"""
        <div class="card">
          <h2>⭐ Active vote: {poll['title']}</h2>
          <div class="log-wrap"><table class="log-table">
            <tr><th>Candidate</th><th>Votes</th></tr>
            {rows}
          </table></div>
          <form method="post" action="/dashboard/{guild_id}/mvp/end" style="margin-top:14px;">
            <button class="btn btn-secondary" type="submit">End Vote & Announce Winner</button>
          </form>
        </div>
        """
    else:
        active_html = '<div class="card"><h2>No active vote</h2><div class="hint">Start one below.</div></div>'

    member_assets = _member_search_assets(guild)
    channel_assets = _channel_search_assets(guild)

    new_vote_html = ""
    if not poll:
        new_vote_html = f"""
        <div class="card">
          <h2>➕ Start an MVP vote</h2>
          <div class="hint" style="margin-bottom:12px;">Pick up to 5 candidates. Posts a vote embed with a button per candidate.</div>
          <form method="post" action="/dashboard/{guild_id}/mvp/start">
            <div class="field"><label>Title</label><input type="text" name="title" placeholder="Scrim vs Team X" required></div>
            {_member_search_field("Candidate 1", "user1")}
            {_member_search_field("Candidate 2 (optional)", "user2")}
            {_member_search_field("Candidate 3 (optional)", "user3")}
            {_member_search_field("Candidate 4 (optional)", "user4")}
            {_member_search_field("Candidate 5 (optional)", "user5")}
            {_channel_search_field()}
            <button class="btn" type="submit">Start Vote</button>
          </form>
        </div>
        """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">⭐ MVP Voting</h1>
    {result_html}
    {member_assets}
    {channel_assets}
    {active_html}
    {new_vote_html}
    """
    return render_page(f"{guild.name} — MVP Voting", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/mvp/start", methods=["POST"])
def mvp_start_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    title = request.form.get("title", "").strip()
    try:
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("mvp_page", guild_id=guild_id, result="❌ Pick a channel."))
    if not title:
        return redirect(url_for("mvp_page", guild_id=guild_id, result="❌ Enter a title."))

    candidate_ids = []
    for field in ("user1", "user2", "user3", "user4", "user5"):
        raw = request.form.get(field, "")
        if raw:
            try:
                candidate_ids.append(int(raw))
            except ValueError:
                pass

    result = _run_async(_mvp_start(guild_id, title, candidate_ids, channel_id, session["user_id"]))
    return redirect(url_for("mvp_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/mvp/end", methods=["POST"])
def mvp_end_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_mvp_end(guild_id, session["user_id"]))
    return redirect(url_for("mvp_page", guild_id=guild_id, result=result))


# ---------- suggestions ----------

@app.route("/dashboard/<int:guild_id>/suggestions")
def suggestions_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    suggestions = sorted(cfg.get("suggestions", {}).values(), key=lambda s: s.get("id", 0), reverse=True)
    rows = ""
    if suggestions:
        for s in suggestions:
            author = guild.get_member(s.get("user_id"))
            author_name = author.display_name if author else f"Unknown ({s.get('user_id')})"
            status = s.get("status", "pending")
            color = {"pending": "#3b82f6", "approved": "#22c55e", "denied": "#f87171"}.get(status, "#8b96b3")
            pill = f'<span class="pill" style="background:{color}22; border-color:{color}55; color:{color};">{status}</span>'
            actions = ""
            if status == "pending":
                actions = f"""
                <form method="post" action="/dashboard/{guild_id}/suggestions/{s['id']}/status" style="display:inline;">
                  <input type="hidden" name="status" value="approved">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Approve</button>
                </form>
                <form method="post" action="/dashboard/{guild_id}/suggestions/{s['id']}/status" style="display:inline;">
                  <input type="hidden" name="status" value="denied">
                  <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">Deny</button>
                </form>
                """
            rows += f"""
            <tr>
              <td>#{s['id']}</td>
              <td>{html.escape(s.get('message', ''))}</td>
              <td>{author_name}</td>
              <td>👍 {len(s.get('upvotes', []))} 👎 {len(s.get('downvotes', []))}</td>
              <td>{pill}</td>
              <td style="white-space:nowrap;">{actions}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="6" class="hint" style="padding:16px;">No suggestions yet.</td></tr>'

    channel_assets = _channel_search_assets(guild)
    channel_id = cfg.get("suggestions_channel_id")

    body = f"""
    <h1>💡 Suggestions</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>📌 Suggestions Channel</h2>
      <div class="hint" style="margin-bottom:12px;">Where /suggest posts new suggestions for voting.</div>
      <form method="post" action="/dashboard/{guild_id}/suggestions/channel">
        {_channel_search_field("Channel", "channel_id", guild, channel_id)}
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>All suggestions</h2>
      {_table_search_box("suggestions-table")}
      <div class="log-wrap"><table class="log-table" id="suggestions-table">
        <tr><th>#</th><th>Suggestion</th><th>By</th><th>Votes</th><th>Status</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Suggestions", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/suggestions/channel", methods=["POST"])
def suggestions_channel_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw = request.form.get("channel_id", "")
    channel_id = int(raw) if raw else None
    result = _run_async(_set_suggestions_channel(guild_id, channel_id, session["user_id"]))
    return redirect(url_for("suggestions_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/suggestions/<int:suggestion_id>/status", methods=["POST"])
def suggestions_status_route(guild_id, suggestion_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    status = request.form.get("status", "")
    if status not in ("approved", "denied"):
        return redirect(url_for("suggestions_page", guild_id=guild_id, result="❌ Invalid status."))
    result = _run_async(_suggestion_set_status(guild_id, suggestion_id, status, session["user_id"]))
    return redirect(url_for("suggestions_page", guild_id=guild_id, result=result))


# ---------- giveaways ----------

@app.route("/dashboard/<int:guild_id>/giveaways")
def giveaways_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    giveaways = sorted(cfg.get("giveaways", {}).values(), key=lambda g: g.get("id", 0), reverse=True)
    rows = ""
    if giveaways:
        for g in giveaways:
            ended = g.get("ended", False)
            pill = '<span class="pill" style="background:#8b96b322; border-color:#8b96b355; color:#8b96b3;">ended</span>' if ended else '<span class="pill">active</span>'
            winners_text = ", ".join(f"<@{w}>" for w in g.get("winners", [])) if ended and g.get("winners") else "—"
            action = "" if ended else f"""
            <form method="post" action="/dashboard/{guild_id}/giveaways/{g['id']}/end" style="margin:0;">
              <button class="btn btn-secondary" type="submit" style="padding:5px 10px; font-size:11px;">End Now</button>
            </form>
            """
            rows += f"""
            <tr>
              <td>#{g['id']}</td>
              <td>{html.escape(g.get('prize', ''))}</td>
              <td>{len(g.get('entrants', []))}</td>
              <td>{g.get('winner_count', 1)}</td>
              <td class="hint">{winners_text}</td>
              <td>{pill}</td>
              <td>{action}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="7" class="hint" style="padding:16px;">No giveaways yet.</td></tr>'

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <h1>🎉 Giveaways</h1>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>➕ Start a giveaway</h2>
      <form method="post" action="/dashboard/{guild_id}/giveaways/start">
        <div class="field"><label>Prize</label><input type="text" name="prize" placeholder="Discord Nitro" required></div>
        <div class="grid-2">
          <div class="field"><label>Duration (minutes)</label><input type="number" name="duration_minutes" min="1" value="60" required></div>
          <div class="field"><label>Number of winners</label><input type="number" name="winner_count" min="1" value="1" required></div>
        </div>
        {_channel_search_field()}
        <button class="btn" type="submit">Start Giveaway</button>
      </form>
    </div>

    <div class="card">
      <h2>All giveaways</h2>
      {_table_search_box("giveaways-table")}
      <div class="log-wrap"><table class="log-table" id="giveaways-table">
        <tr><th>#</th><th>Prize</th><th>Entrants</th><th>Winners</th><th>Won by</th><th>Status</th><th></th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Giveaways", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/giveaways/start", methods=["POST"])
def giveaways_start_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    prize = request.form.get("prize", "").strip()
    try:
        duration_minutes = int(request.form["duration_minutes"])
        winner_count = int(request.form["winner_count"])
        channel_id = int(request.form["channel_id"])
    except (KeyError, ValueError):
        return redirect(url_for("giveaways_page", guild_id=guild_id, result="❌ Fill in all fields correctly."))
    if not prize:
        return redirect(url_for("giveaways_page", guild_id=guild_id, result="❌ Enter a prize."))
    result = _run_async(_giveaway_start(guild_id, prize, duration_minutes, winner_count, channel_id, session["user_id"]))
    return redirect(url_for("giveaways_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/giveaways/<int:giveaway_id>/end", methods=["POST"])
def giveaways_end_route(guild_id, giveaway_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_giveaway_end(guild_id, giveaway_id, session["user_id"]))
    return redirect(url_for("giveaways_page", guild_id=guild_id, result=result))


# ---------- member lookup ----------

@app.route("/dashboard/<int:guild_id>/lookup")
def lookup_page(guild_id):
    guild, access_member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    member_assets = _member_search_assets(guild)

    raw_user_id = request.args.get("user_id", "")
    body_extra = ""

    if raw_user_id:
        try:
            user_id = int(raw_user_id)
        except ValueError:
            user_id = None

        target = guild.get_member(user_id) if user_id else None
        name = target.display_name if target else f"Unknown ({raw_user_id})"
        tag = str(target) if target else ""

        # ---- roster / rank ----
        roster_entry = next((r for r in cfg.get("roster", []) if r["user_id"] == user_id), None)
        rank_role = guild.get_role(roster_entry["rank_role_id"]) if roster_entry else None
        joined = _format_ts(target.joined_at.isoformat()) if target and target.joined_at else "—"

        # ---- birthday / AFK ----
        birthday = cfg.get("birthdays", {}).get(str(user_id), "Not set")
        afk_entry = cfg.get("afk", {}).get(str(user_id))
        afk_status = "😴 Currently AFK" + (f" — {afk_entry.get('reason','')}" if isinstance(afk_entry, dict) else "") if afk_entry else "Not AFK"

        # ---- activity ----
        msg_count = cfg.get("message_counts", {}).get(str(user_id), 0)

        # ---- warnings ----
        warnings = cfg.get("warnings", {}).get(str(user_id), [])
        warning_rows = ""
        for w in reversed(warnings):
            mod = guild.get_member(w.get("moderator_id"))
            warning_rows += f"<tr><td>{w.get('reason','')}</td><td>{mod.display_name if mod else '—'}</td><td class='hint'>{_format_ts(w.get('timestamp'))}</td></tr>"
        if not warning_rows:
            warning_rows = '<tr><td colspan="3" class="hint" style="padding:12px;">No warnings.</td></tr>'

        # ---- history ----
        history = cfg.get("history", {}).get(str(user_id), [])
        history_rows = ""
        for h in reversed(history[-25:]):
            mod = guild.get_member(h.get("moderator_id"))
            history_rows += f"<tr><td>{h.get('action','')}</td><td>{h.get('detail','')}</td><td>{mod.display_name if mod else '—'}</td><td class='hint'>{_format_ts(h.get('timestamp'))}</td></tr>"
        if not history_rows:
            history_rows = '<tr><td colspan="4" class="hint" style="padding:12px;">No history.</td></tr>'

        # ---- name history ----
        name_history = cfg.get("name_history", {}).get(str(user_id), [])
        name_history_rows = ""
        for entry in reversed(name_history[-15:]):
            icon = "🏷️" if entry.get("kind") == "nickname" else "👤"
            name_history_rows += f"<tr><td>{icon} {entry.get('kind','')}</td><td>{html.escape(entry.get('old',''))}</td><td>{html.escape(entry.get('new',''))}</td><td class='hint'>{_format_ts(entry.get('timestamp'))}</td></tr>"
        if not name_history_rows:
            name_history_rows = '<tr><td colspan="4" class="hint" style="padding:12px;">No recorded name changes.</td></tr>'

        # ---- tickets ----
        tickets = [t for t in cfg.get("tickets", {}).values() if t.get("user_id") == user_id]
        tickets.sort(key=lambda t: t.get("id", 0), reverse=True)
        ticket_rows = ""
        for t in tickets:
            status = t.get("status", "open")
            color = "#5ee0a0" if status == "open" else "#80848e"
            pill = f'<span class="pill" style="background:{color}22; border-color:{color}55; color:{color};">{status}</span>'
            link = f'<a href="/dashboard/{guild_id}/tickets/{t["id"]}">#{t["id"]}</a>' if status == "open" else f"#{t['id']}"
            ticket_rows += f"<tr><td>{link}</td><td>{t.get('type_name') or '—'}</td><td>{pill}</td><td class='hint'>{_format_ts(t.get('created_at'))}</td></tr>"
        if not ticket_rows:
            ticket_rows = '<tr><td colspan="4" class="hint" style="padding:12px;">No tickets.</td></tr>'

        body_extra = f"""
        <div class="card">
          <h2>👤 {name} {f'<span class="hint" style="font-weight:400;">({tag})</span>' if tag else ''}</h2>
          <div class="grid-2">
            <div class="field"><label>Rank</label><div>{('@' + rank_role.name) if rank_role else '— Not on roster —'}</div></div>
            <div class="field"><label>Joined server</label><div>{joined}</div></div>
            <div class="field"><label>Birthday</label><div>{birthday}</div></div>
            <div class="field"><label>AFK status</label><div>{afk_status}</div></div>
            <div class="field"><label>Messages this week</label><div>{msg_count}</div></div>
            <div class="field"><label>Total warnings</label><div>{len(warnings)}</div></div>
          </div>
        </div>

        <div class="card">
          <h2>⚠️ Warnings</h2>
          <div class="log-wrap"><table class="log-table">
            <tr><th>Reason</th><th>By</th><th>When</th></tr>
            {warning_rows}
          </table></div>
        </div>

        <div class="card">
          <h2>🗂️ Rank / Roster History</h2>
          <div class="log-wrap"><table class="log-table">
            <tr><th>Action</th><th>Detail</th><th>By</th><th>When</th></tr>
            {history_rows}
          </table></div>
        </div>

        <div class="card">
          <h2>📝 Name History</h2>
          <div class="log-wrap"><table class="log-table">
            <tr><th>Type</th><th>Old</th><th>New</th><th>When</th></tr>
            {name_history_rows}
          </table></div>
        </div>

        <div class="card">
          <h2>🎫 Tickets</h2>
          <div class="log-wrap"><table class="log-table">
            <tr><th>#</th><th>Type</th><th>Status</th><th>Opened</th></tr>
            {ticket_rows}
          </table></div>
        </div>
        """

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔎 Member Lookup</h1>
    <div class="hint" style="margin-bottom:18px;">Everything the bot knows about one person, in one place.</div>
    {member_assets}

    <div class="card">
      <form method="get">
        {_member_search_field("Search a member", "user_id")}
        <button class="btn" type="submit">Look Up</button>
      </form>
    </div>

    {body_extra}
    """
    return render_page(f"{guild.name} — Member Lookup", body, guild_id=guild_id)


# ---------- CSV exports ----------

def _csv_response(filename, header, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/dashboard/<int:guild_id>/export/roster.csv")
def export_roster_csv(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cfg = _get_guild_cfg(guild_id)

    rows = []
    for entry in cfg.get("roster", []):
        m = guild.get_member(entry["user_id"])
        role = guild.get_role(entry.get("rank_role_id"))
        rows.append([
            entry["user_id"],
            m.display_name if m else "(left server)",
            str(m) if m else "",
            role.name if role else "",
            entry.get("last_rank_change", ""),
        ])
    return _csv_response(f"roster-{guild_id}.csv", ["User ID", "Display Name", "Username", "Rank", "Last Rank Change"], rows)


@app.route("/dashboard/<int:guild_id>/export/warnings.csv")
def export_warnings_csv(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cfg = _get_guild_cfg(guild_id)

    rows = []
    for uid_str, entries in cfg.get("warnings", {}).items():
        m = guild.get_member(int(uid_str))
        name = m.display_name if m else f"Unknown ({uid_str})"
        for w in entries:
            mod = guild.get_member(w.get("moderator_id"))
            rows.append([uid_str, name, w.get("reason", ""), mod.display_name if mod else "", w.get("timestamp", "")])
    return _csv_response(f"warnings-{guild_id}.csv", ["User ID", "Display Name", "Reason", "Moderator", "Timestamp"], rows)


@app.route("/dashboard/<int:guild_id>/export/activity.csv")
def export_activity_csv(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    cfg = _get_guild_cfg(guild_id)

    rows = []
    for uid_str, count in sorted(cfg.get("message_counts", {}).items(), key=lambda kv: kv[1], reverse=True):
        m = guild.get_member(int(uid_str))
        name = m.display_name if m else f"Unknown ({uid_str})"
        rows.append([uid_str, name, count])
    return _csv_response(f"activity-{guild_id}.csv", ["User ID", "Display Name", "Messages"], rows)


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


@app.route("/dashboard/<int:guild_id>/backups")
def backups_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    result = request.args.get("result", "")
    result_html = f'<div class="flash">{result}</div>' if result else ""

    channel_id = cfg.get("backup_channel_id")
    interval_days = cfg.get("backup_interval_days")
    last_backup = cfg.get("last_backup_at")

    status_html = ""
    if channel_id and interval_days:
        channel = guild.get_channel(channel_id)
        last_label = _format_ts(last_backup) if last_backup else "Never yet"
        status_html = f"""
        <div class="grid-2">
          <div class="field"><label>Posting to</label><div>{'#' + channel.name if channel else '(deleted channel)'}</div></div>
          <div class="field"><label>Every</label><div>{interval_days} day(s)</div></div>
          <div class="field"><label>Last backup</label><div>{last_label}</div></div>
        </div>
        """
    else:
        status_html = '<div class="hint">Not set up yet — automatic backups are off.</div>'

    channel_assets = _channel_search_assets(guild)

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🗄️ Automatic Backups</h1>
    <div class="hint" style="margin-bottom:18px;">Posts a fresh config backup file to a channel on a schedule, so you never have to remember to click download.</div>
    {result_html}
    {channel_assets}

    <div class="card">
      <h2>Current status</h2>
      {status_html}
    </div>

    <div class="card">
      <h2>⚙️ Settings</h2>
      <form method="post" action="/dashboard/{guild_id}/backups/settings">
        <div class="grid-2">
          {_channel_search_field("Channel (leave blank to disable)", "channel_id", guild, channel_id)}
          <div class="field"><label>Interval (days)</label><input type="number" name="interval_days" min="1" value="{interval_days or 7}"></div>
        </div>
        <button class="btn" type="submit">Save</button>
      </form>
    </div>

    <div class="card">
      <h2>▶️ Run Now</h2>
      <div class="hint" style="margin-bottom:12px;">Posts a backup immediately, without waiting for the schedule. Requires the channel above to be set first.</div>
      <form method="post" action="/dashboard/{guild_id}/backups/run">
        <button class="btn btn-secondary" type="submit">Run Backup Now</button>
      </form>
    </div>

    <div class="card">
      <h2>♻️ Restore from Backup</h2>
      <div class="hint" style="margin-bottom:12px;">Upload a previously downloaded backup .json file to instantly restore this server's settings — ranks, channels, roster, tickets, everything. This completely replaces the current settings, so double check you have the right file first.</div>
      <form method="post" action="/dashboard/{guild_id}/backups/restore" enctype="multipart/form-data">
        <div class="field"><input type="file" name="backup_file" accept=".json" required></div>
        <button class="btn btn-secondary" type="submit">Restore</button>
      </form>
    </div>
    """
    return render_page(f"{guild.name} — Auto Backups", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/backups/settings", methods=["POST"])
def backups_settings_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    raw_channel = request.form.get("channel_id", "")
    channel_id = int(raw_channel) if raw_channel else None
    try:
        interval_days = int(request.form.get("interval_days", 7))
    except ValueError:
        interval_days = 7
    result = _run_async(_set_backup_settings(guild_id, channel_id, interval_days, session["user_id"]))
    return redirect(url_for("backups_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/backups/run", methods=["POST"])
def backups_run_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))
    result = _run_async(_run_backup_now(guild_id, session["user_id"]))
    return redirect(url_for("backups_page", guild_id=guild_id, result=result))


@app.route("/dashboard/<int:guild_id>/backups/restore", methods=["POST"])
def backups_restore_route(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    uploaded = request.files.get("backup_file")
    if not uploaded or not uploaded.filename:
        return redirect(url_for("backups_page", guild_id=guild_id, result="❌ Choose a backup file first."))

    try:
        raw = uploaded.read().decode("utf-8")
        restored_cfg = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return redirect(url_for("backups_page", guild_id=guild_id, result="❌ That file isn't valid JSON — make sure it's an unmodified backup file."))

    if not isinstance(restored_cfg, dict):
        return redirect(url_for("backups_page", guild_id=guild_id, result="❌ That file doesn't look like a valid backup (expected a JSON object)."))

    _config[str(guild_id)] = restored_cfg
    _save_config(_config)
    return redirect(url_for(
        "backups_page", guild_id=guild_id,
        result="✅ Settings restored from backup. Note: live embeds (roster, stats, showcase, ticket panel) may need to be re-posted if their channel settings changed.",
    ))


# ---------- dashboard activity log ----------

@app.route("/dashboard/<int:guild_id>/activitylog")
def activity_log_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    log = list(reversed(cfg.get("dashboard_activity_log", [])))

    rows = ""
    if log:
        for entry in log[:200]:
            actor = guild.get_member(entry.get("actor_id"))
            actor_name = actor.display_name if actor else f"Unknown ({entry.get('actor_id')})"
            rows += f"""
            <tr>
              <td>{actor_name}</td>
              <td class="hint">{html.escape(entry.get('path', ''))}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(entry.get('timestamp'))}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="3" class="hint" style="padding:16px;">No dashboard activity recorded yet — this fills in as staff use the dashboard.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🖱️ Dashboard Activity</h1>
    <div class="hint" style="margin-bottom:18px;">Every settings change or action taken from this dashboard, by whom, and when. Keeps the most recent 200.</div>

    <div class="card">
      {_table_search_box("dashboard-activity-table")}
      <div class="log-wrap"><table class="log-table" id="dashboard-activity-table">
        <tr><th>Staff Member</th><th>Action</th><th>When</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Dashboard Activity", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/discordauditlog")
def discord_audit_log_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    result = _run_async(_fetch_discord_audit_log(guild_id, 100))
    if result.get("error"):
        rows_html = f'<div class="hint" style="color:#ff8080; padding:16px;">⚠️ {result["error"]}</div>'
        table_html = ""
    else:
        entries = result.get("entries", [])
        if entries:
            rows = ""
            for e in entries:
                rows += f"""
                <tr>
                  <td>{html.escape(e['action'])}</td>
                  <td>{html.escape(e['target'])}</td>
                  <td>{html.escape(e['moderator'])}</td>
                  <td class="hint">{html.escape(e.get('reason', '') or '—')}</td>
                  <td class="hint">{_format_ts(e['timestamp'])}</td>
                </tr>
                """
            rows_html = ""
            table_html = f"""
            {_table_search_box("discord-audit-table")}
            <div class="log-wrap"><table class="log-table" id="discord-audit-table">
              <tr><th>Action</th><th>Target</th><th>Moderator</th><th>Reason</th><th>When</th></tr>
              {rows}
            </table></div>
            """
        else:
            rows_html = '<div class="hint" style="padding:16px;">No recent audit log entries.</div>'
            table_html = ""

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🗂️ Discord Audit Log</h1>
    <div class="hint" style="margin-bottom:18px;">Discord's own native audit log — bans, kicks, channel/role changes, and more. Not limited to actions taken through this bot.</div>

    <div class="card">
      <h2>Recent activity</h2>
      {rows_html}
      {table_html}
    </div>
    """
    return render_page(f"{guild.name} — Discord Audit Log", body, guild_id=guild_id)


@app.route("/dashboard/<int:guild_id>/loginhistory")
def login_history_page(guild_id):
    guild, member = _check_access(guild_id)
    if guild is None:
        return redirect(url_for("guild_picker"))

    cfg = _get_guild_cfg(guild_id)
    logins = list(reversed(cfg.get("dashboard_logins", [])))

    rows = ""
    if logins:
        for entry in logins[:100]:
            actor = guild.get_member(entry.get("user_id"))
            name = actor.display_name if actor else html.escape(entry.get("username", "Unknown"))
            rows += f"""
            <tr>
              <td>{name}</td>
              <td class="hint" style="white-space:nowrap;">{_format_ts(entry.get('timestamp'))}</td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="2" class="hint" style="padding:16px;">No logins recorded yet.</td></tr>'

    body = f"""
    <div class="topbar" style="margin-bottom:0;"><a href="/dashboard/{guild_id}">&larr; {guild.name} settings</a></div>
    <h1 style="margin-top:18px;">🔑 Login History</h1>
    <div class="hint" style="margin-bottom:18px;">Everyone who has logged into this server's dashboard, and when. Keeps the most recent 100.</div>

    <div class="card">
      {_table_search_box("login-history-table")}
      <div class="log-wrap"><table class="log-table" id="login-history-table">
        <tr><th>Staff Member</th><th>Logged In</th></tr>
        {rows}
      </table></div>
    </div>
    """
    return render_page(f"{guild.name} — Login History", body, guild_id=guild_id)


# ---------- entrypoint ----------

def _run(port: int):
    app.run(host="0.0.0.0", port=port)


def start_web_app(
    bot, config, save_config, get_guild_cfg,
    give_role, remove_role,
    roster_add, roster_remove, promote, demote,
    kick, ban, timeout, untimeout, warn,
    mass_add_role, mass_remove_role, mass_rename,
    announce, massannounce,
    showcase_add, showcase_remove,
    open_ticket, close_ticket, set_ticket_channel,
    send_dm,
    set_rust_server, set_rust_status_channel, get_rust_status, rust_command,
    rust_get_players, rust_kick_player, rust_ban_player, rust_get_banlist, rust_unban_player,
    set_rust_alert_channel,
    set_minecraft_server, set_minecraft_status_channel, get_minecraft_status, minecraft_command,
    set_minecraft_alert_channel,
    relay_incoming_webhook,
    tournament_create, tournament_start, tournament_report,
    gamenight_create, gamenight_cancel,
    mvp_start, mvp_end,
    add_ticket_category, remove_ticket_category, set_ticket_questions,
    get_ticket_messages, send_ticket_message,
    set_backup_settings, run_backup_now,
    redeem_web_login_code,
    minecraft_get_players, minecraft_kick_player, minecraft_ban_player, minecraft_get_banlist, minecraft_unban_player,
    set_bot_status,
    roster_add_all,
    set_suggestions_channel, suggestion_set_status,
    giveaway_start, giveaway_end,
    put_on_cooldown, remove_cooldown,
    add_custom_command, remove_custom_command,
    refresh_roster,
    automod_toggle, automod_settings, automod_add_word, automod_remove_word,
    set_ticket_autoclose,
    set_reports_channel, report_set_status,
    fetch_discord_audit_log,
    rust_set_wipe, rust_set_popalert, rust_set_joinleave_channel, rust_set_bansync,
    rust_set_rules, rust_save, rust_restart, rust_announce,
    rust_macro_add, rust_macro_remove, rust_macro_run,
    rust_announcement_add, rust_announcement_remove,
    add_rank_bonus_role, remove_rank_bonus_role,
    set_whitelist_sync,
):
    """Call once from bot.py after the bot object exists. Runs Flask in a
    background thread so it doesn't block discord.py's event loop."""
    global _bot, _config, _save_config, _get_guild_cfg, _give_role, _remove_role
    global _roster_add, _roster_remove, _promote, _demote, _kick, _ban, _timeout, _untimeout, _warn
    global _mass_add_role, _mass_remove_role, _mass_rename, _announce, _massannounce
    global _showcase_add, _showcase_remove, _open_ticket, _close_ticket, _set_ticket_channel
    global _send_dm
    global _set_rust_server, _set_rust_status_channel, _get_rust_status, _rust_command, _set_rust_alert_channel
    global _rust_get_players, _rust_kick_player, _rust_ban_player, _rust_get_banlist, _rust_unban_player
    global _set_minecraft_server, _set_minecraft_status_channel, _get_minecraft_status, _minecraft_command, _set_minecraft_alert_channel
    global _relay_incoming_webhook
    global _tournament_create, _tournament_start, _tournament_report
    global _gamenight_create, _gamenight_cancel
    global _mvp_start, _mvp_end
    global _add_ticket_category, _remove_ticket_category, _set_ticket_questions
    global _get_ticket_messages, _send_ticket_message
    global _redeem_web_login_code
    global _minecraft_get_players, _minecraft_kick_player, _minecraft_ban_player, _minecraft_get_banlist, _minecraft_unban_player
    global _set_bot_status
    global _roster_add_all
    global _set_suggestions_channel, _suggestion_set_status
    global _giveaway_start, _giveaway_end
    global _put_on_cooldown, _remove_cooldown
    global _add_custom_command, _remove_custom_command
    global _refresh_roster
    global _automod_toggle, _automod_settings, _automod_add_word, _automod_remove_word
    global _set_ticket_autoclose
    global _set_reports_channel, _report_set_status
    global _fetch_discord_audit_log
    global _rust_set_wipe, _rust_set_popalert, _rust_set_joinleave_channel, _rust_set_bansync
    global _rust_set_rules, _rust_save, _rust_restart, _rust_announce
    global _rust_macro_add, _rust_macro_remove, _rust_macro_run
    global _rust_announcement_add, _rust_announcement_remove
    global _add_rank_bonus_role, _remove_rank_bonus_role
    global _set_whitelist_sync
    global _set_backup_settings, _run_backup_now
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
    _untimeout = untimeout
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
    _send_dm = send_dm
    _set_rust_server = set_rust_server
    _set_rust_status_channel = set_rust_status_channel
    _get_rust_status = get_rust_status
    _rust_command = rust_command
    _set_rust_alert_channel = set_rust_alert_channel
    _rust_get_players = rust_get_players
    _rust_kick_player = rust_kick_player
    _rust_ban_player = rust_ban_player
    _rust_get_banlist = rust_get_banlist
    _rust_unban_player = rust_unban_player
    _set_minecraft_server = set_minecraft_server
    _set_minecraft_status_channel = set_minecraft_status_channel
    _get_minecraft_status = get_minecraft_status
    _minecraft_command = minecraft_command
    _set_minecraft_alert_channel = set_minecraft_alert_channel
    _relay_incoming_webhook = relay_incoming_webhook
    _tournament_create = tournament_create
    _tournament_start = tournament_start
    _tournament_report = tournament_report
    _gamenight_create = gamenight_create
    _gamenight_cancel = gamenight_cancel
    _mvp_start = mvp_start
    _mvp_end = mvp_end
    _add_ticket_category = add_ticket_category
    _remove_ticket_category = remove_ticket_category
    _set_ticket_questions = set_ticket_questions
    _get_ticket_messages = get_ticket_messages
    _send_ticket_message = send_ticket_message
    _redeem_web_login_code = redeem_web_login_code
    _minecraft_get_players = minecraft_get_players
    _minecraft_kick_player = minecraft_kick_player
    _minecraft_ban_player = minecraft_ban_player
    _minecraft_get_banlist = minecraft_get_banlist
    _minecraft_unban_player = minecraft_unban_player
    _set_bot_status = set_bot_status
    _roster_add_all = roster_add_all
    _set_suggestions_channel = set_suggestions_channel
    _suggestion_set_status = suggestion_set_status
    _giveaway_start = giveaway_start
    _giveaway_end = giveaway_end
    _put_on_cooldown = put_on_cooldown
    _remove_cooldown = remove_cooldown
    _add_custom_command = add_custom_command
    _remove_custom_command = remove_custom_command
    _refresh_roster = refresh_roster
    _automod_toggle = automod_toggle
    _automod_settings = automod_settings
    _automod_add_word = automod_add_word
    _automod_remove_word = automod_remove_word
    _set_ticket_autoclose = set_ticket_autoclose
    _set_reports_channel = set_reports_channel
    _report_set_status = report_set_status
    _fetch_discord_audit_log = fetch_discord_audit_log
    _rust_set_wipe = rust_set_wipe
    _rust_set_popalert = rust_set_popalert
    _rust_set_joinleave_channel = rust_set_joinleave_channel
    _rust_set_bansync = rust_set_bansync
    _rust_set_rules = rust_set_rules
    _rust_save = rust_save
    _rust_restart = rust_restart
    _rust_announce = rust_announce
    _rust_macro_add = rust_macro_add
    _rust_macro_remove = rust_macro_remove
    _rust_macro_run = rust_macro_run
    _rust_announcement_add = rust_announcement_add
    _rust_announcement_remove = rust_announcement_remove
    _add_rank_bonus_role = add_rank_bonus_role
    _remove_rank_bonus_role = remove_rank_bonus_role
    _set_whitelist_sync = set_whitelist_sync
    _set_backup_settings = set_backup_settings
    _run_backup_now = run_backup_now

    port = int(os.environ.get("PORT", 8080))
    thread = threading.Thread(target=_run, args=(port,), daemon=True)
    thread.start()
