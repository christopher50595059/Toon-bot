# Discord Role Bot

A slash-command bot that lets your staff instantly assign or remove roles
(promote to staff, set a tier, etc.) and logs every change to a channel you choose.

## Commands

| Command | Who can use it | What it does |
|---|---|---|
| `/setlogchannel #channel` | Server admins | Sets where role changes get logged |
| `/setmanagerrole @role` | Server admins | Sets which role is allowed to use `/addrole` and `/removerole` |
| `/addrole @user @role` | Admins + the manager role | Gives a role to a member |
| `/removerole @user @role` | Admins + the manager role | Removes a role from a member |

## Setup

### 1. Create the bot in Discord
1. Go to https://discord.com/developers/applications → **New Application**.
2. Go to **Bot** → **Add Bot**.
3. Under **Privileged Gateway Intents**, enable **Server Members Intent** (required so the bot can look up members and change their roles).
4. Click **Reset Token** and copy the token — you'll need it below.
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Manage Roles`, `Send Messages`, `Embed Links`
   - Copy the generated URL and open it to invite the bot to your server.

**Important:** In your server's role list, drag the bot's own role **above** any role you want it to assign (Discord bots can only manage roles below their own).

### 2. Install and run
```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your bot token in place of "your-bot-token-here"
python bot.py
```

### 3. Configure it in your server
Once the bot is online and slash commands have synced (may take a minute the first time):
```
/setlogchannel #staff-logs
/setmanagerrole @Staff Manager
```
Now anyone with the `@Staff Manager` role (or Administrator) can run:
```
/addrole @SomeUser @Staff
/addrole @SomeUser @Tier 2
/removerole @SomeUser @Tier 1
```

## Notes
- Role changes are stored in `guild_config.json`, created automatically next to `bot.py`.
- For 24/7 uptime you'll want to host this somewhere (a small VPS, Railway, Render, etc.) rather than running it on your own machine.
- If a command doesn't appear in Discord right away, it can take up to an hour for global slash commands to propagate on first sync — restarting the bot after inviting it usually speeds this up.
