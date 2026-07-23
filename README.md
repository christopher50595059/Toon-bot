# Discord Role Bot

A slash-command bot that lets your staff instantly assign or remove roles
(promote to staff, set a tier, etc.) and logs every change to a channel you choose.

## Commands

| Command | Who can use it | What it does |
|---|---|---|
| `/setlogchannel #channel` | Server admins | Sets where role changes get logged |
| `/setmanagerrole @role` | Server admins | Sets which role is allowed to use the commands below |
| `/addrole @user @role reason:...` | Admins + the manager role | Gives a role to a member |
| `/removerole @user @role reason:...` | Admins + the manager role | Removes a role from a member |
| `/setrosterchannel #channel` | Server admins | Posts a live roster embed that auto-updates in this channel |
| `/setranks rank1:@Owner rank2:@Manager ...` | Server admins | Sets the ordered rank roles (highest first) — picked from your server's real roles |
| `/rosteradd @user rank:@Staff reason:...` | Admins + the manager role | Adds a member to the roster at a rank **and gives them that Discord role**. If they're already on the roster, moves them and swaps the old rank role for the new one. |
| `/rosterremove @user reason:...` | Admins + the manager role | Removes a member from the roster — **asks you to confirm first** |
| `/promote @user reason:...` | Admins + the manager role | Moves a member up one rank (toward the top of your `/setranks` list) and swaps their role accordingly |
| `/demote @user reason:...` | Admins + the manager role | Moves a member down one rank (toward the bottom) and swaps their role accordingly — **asks you to confirm first** |
| `/rosterimport rank:@Staff` | Admins + the manager role | Bulk-adds everyone who already has the `@Staff` role onto the roster at that rank in one go |
| `/setcooldown hours:24 [@user]` | Server admins | Requires a wait between promotions/demotions — server-wide by default, or just for one person if you specify `user` (0 disables) |
| `/setinactivitydays days:14` | Server admins | Sets how many days of silence counts as "inactive" for `/inactive` (0 disables it) |
| `/inactive` | Anyone | Lists roster members who haven't sent a message in longer than the configured threshold |
| `/serverstats` | Anyone | Shows a one-off snapshot of server stats (members, roster size, boosts, etc.) |
| `/setstatschannel #channel` | Server admins | Posts a live server-stats embed that auto-updates in this channel |
| `/roster` | Anyone | Shows the current roster, grouped by rank |
| `/stats` | Anyone | Shows how many members are at each rank |
| `/rank [@user]` | Anyone | Shows a member's current rank (defaults to yourself) |
| `/history [@user]` | Anyone | Shows a member's rank/roster history — promotions, demotions, roster changes (defaults to yourself) |
| `/tournament_create name:...` | Admins + the manager role | Opens sign-ups for a single-elimination tournament (anyone can click Join) |
| `/tournament_start name:...` | Admins + the manager role | Locks sign-ups and generates the bracket |
| `/tournament_report name:... match:# winner:@user` | Admins + the manager role | Records who won a match, advancing the bracket |
| `/tournament_bracket name:...` | Anyone | Shows the current bracket |
| `/gamenight_create game:... date:YYYY-MM-DD time:HH:MM` | Admins + the manager role | Schedules a game night with RSVP buttons and an automatic reminder |
| `/gamenight_list` | Anyone | Shows upcoming game nights |
| `/gamenight_cancel id:#` | Admins + the manager role | Cancels a scheduled game night |
| `/mvp_start title:... user1:@... user2..user5` | Admins + the manager role | Opens MVP voting among up to 5 candidates |
| `/mvp_end` | Admins + the manager role | Closes voting and announces the winner |
| `/crosspost_add destination_channel_id:...` | Server admins | Mirrors messages sent in the current channel to a channel in **another server** the bot is also in |
| `/crosspost_remove` | Server admins | Stops mirroring the current channel |
| `/crosspost_list` | Server admins | Shows all cross-posting mirrors set up in this server |
| `/kick @user reason:...` | Admins + the manager role | Kicks a member — asks you to confirm first |
| `/ban @user reason:... [delete_days]` | Admins + the manager role | Bans a member — asks you to confirm first |
| `/timeout @user minutes:... reason:...` | Admins + the manager role | Temporarily mutes a member |
| `/warn @user reason:...` | Admins + the manager role | Logs a warning against a member |
| `/warnings [@user]` | Anyone | Shows a member's warning history (defaults to yourself) |
| `/purge amount:50` | Admins + the manager role | Bulk-deletes recent messages in the current channel |
| `/lock [reason]` | Admins + the manager role | Stops everyone from sending messages in the current channel |
| `/unlock` | Admins + the manager role | Re-allows sending messages in the current channel |
| `/slowmode seconds:10` | Admins + the manager role | Sets the current channel's slowmode delay |
| `/audit` | Admins + the manager role | Shows the last 20 rank/roster actions across everyone in the server |
| `/evaluate [@user]` | Anyone | Shows the message-activity leaderboard for the current week, or one person's count |
| `/setbirthday month:.. day:..` | Anyone | Sets your own birthday (no year needed) |
| `/removebirthday` | Anyone | Removes your saved birthday |
| `/mybirthday` | Anyone | Shows your currently saved birthday |
| `/setbirthdayrole [@role]` | Server admins | Role auto-given to members on their birthday (omit to disable) |
| `/setbirthdaychannel [#channel]` | Server admins | Channel for birthday shoutouts (omit to disable) |
| `/backup` | Server admins | Exports this server's bot config (ranks, settings, roster, history) as a downloadable file |
| `/announce #channel title:... message:... [ping_everyone]` | Admins + the manager role | Posts a formatted announcement embed to a channel, pinging @everyone by default |
| `/massannounce message:... [title] [ping_everyone]` | Admins + the manager role | Posts to every channel with "announcement" in its name AND speaks it aloud in every active voice channel — pings @everyone by default |
| `/massrename [prefix] [suffix] [role]` | Admins + the manager role | Adds a prefix/suffix to multiple members' nicknames at once — asks you to confirm first |
| `/massaddrole role:@... [filter_role]` | Admins + the manager role | Gives a role to multiple members at once — asks you to confirm first |
| `/massremoverole role:@... [filter_role]` | Admins + the manager role | Removes a role from multiple members at once — asks you to confirm first |
| `/afk [reason]` | Anyone | Marks you AFK; clears automatically the next time you send a message, and anyone who @mentions you gets a heads-up |
| `/setvcgreeting @user message:...` | Admins + the manager role | The bot speaks a custom message out loud whenever that person joins any voice channel |
| `/removevcgreeting @user` | Admins + the manager role | Stops greeting that person when they join a VC |
| `/showcase add role:@... description:...` | Admins + the manager role | Adds a self-assignable role to the showcase, with a description |
| `/showcase remove role:@...` | Admins + the manager role | Removes a role from the showcase |
| `/showcase setchannel #channel` | Admins + the manager role | Posts a live, self-assign role showcase in that channel |
| `/showcase list` | Anyone | Shows the current showcase |
| `/help` | Anyone | Shows every command this bot has, grouped by category |

## Setup

### 1. Create the bot in Discord
1. Go to https://discord.com/developers/applications → **New Application**.
2. Go to **Bot** → **Add Bot**.
3. Under **Privileged Gateway Intents**, enable both **Server Members Intent** (so the bot can look up members and change their roles) and **Message Content Intent** (needed only for cross-posting — the bot reads message text in channels you've set up a mirror for).
4. Click **Reset Token** and copy the token — you'll need it below.
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Manage Roles`, `Send Messages`, `Embed Links`, `Kick Members`, `Ban Members`, `Moderate Members`, `Manage Messages`, `Manage Channels`, `Connect`, `Speak`
   - Copy the generated URL and open it to invite the bot to your server.

**Important:** In your server's role list, drag the bot's own role **above** any role you want it to assign (Discord bots can only manage roles below their own).

### 2. (Optional) Set up the web dashboard
This lets admins log in with Discord and edit settings (channels, roles, ranks) from a browser instead of slash commands. Skip this whole section if you're happy with just slash commands — everything else works fine without it.

1. In the same Developer Portal application, go to **OAuth2 → General**.
2. Copy the **Client ID** shown there.
3. Click **Reset Secret** (or **Copy** if a secret already shows), and copy the **Client Secret**. Treat this like a password — anyone with it can impersonate your app's login.
4. Under **Redirects**, click **Add Redirect** and enter your Render URL followed by `/callback`, e.g. `https://toon-bot-ltn8.onrender.com/callback` — then **Save Changes**.
5. Add four environment variables (same place you added `DISCORD_TOKEN` — locally in `.env`, or on Render under Environment):
   - `DISCORD_CLIENT_ID` — from step 2
   - `DISCORD_CLIENT_SECRET` — from step 3
   - `DASHBOARD_URL` — your Render URL with **no trailing slash**, e.g. `https://toon-bot-ltn8.onrender.com`
   - `FLASK_SECRET_KEY` — any long random string you make up (used to secure login sessions — if you skip this, one gets generated automatically each time the bot restarts, which will log everyone out on every redeploy; setting your own keeps people logged in across restarts)

Once deployed, visit your Render URL in a browser and click **Login with Discord**. Anyone who's a server Administrator, or holds the role set via `/setmanagerrole`, will see that server in their list and can edit its settings.

### 3. Install and run
```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your bot token in place of "your-bot-token-here"
python bot.py
```

### 4. Configure it in your server
Once the bot is online and slash commands have synced (may take a minute the first time):
```
/setlogchannel #staff-logs
/setmanagerrole @Staff Manager
```
Now anyone with the `@Staff Manager` role (or Administrator) can run:
```
/addrole @SomeUser @Staff reason:Great tryout performance
/addrole @SomeUser @Tier 2 reason:Reached tier requirements
/removerole @SomeUser @Tier 1 reason:Moved to Tier 2
```

### Roster
First, set your ranks using your server's actual roles (highest to lowest):
```
/setranks rank1:@Owner rank2:@Manager rank3:@Staff rank4:@Trial Staff
```
Then set up the live roster channel:
```
/setrosterchannel #roster
```
This posts a live embed in that channel that automatically updates whenever the roster changes, grouped by rank role. From then on:
```
/rosteradd @SomeUser rank:@Staff reason:New hire
/rosterremove @SomeUser reason:Left the team
/promote @SomeUser reason:Great performance this month
/demote @SomeUser reason:Inactive for 30 days
/roster   (shows the roster on demand, anywhere)
```
Running `/rosteradd` on someone already on the roster moves them to the new rank, gives them the new rank's role, and removes their old rank role (so people only ever hold one rank role at a time). The `rank` field uses Discord's native role picker, so you can only choose roles you configured with `/setranks`.

`/promote` and `/demote` move someone one step up or down your `/setranks` list automatically — no need to specify which role, just the direction. They only work on people already on the roster (add them with `/rosteradd` first).

As with `/addrole`, make sure the bot's own role is positioned above any rank role in Server Settings > Roles, or it won't be able to assign it.

### DM notifications
Every action that affects a member — `/addrole`, `/removerole`, `/rosteradd`, `/rosterremove`, `/promote`, `/demote` — now sends them a DM letting them know what happened and why. If someone has DMs closed (Discord's default privacy setting for messages from server members), the DM silently fails and the moderator running the command sees a note in their response saying it couldn't be delivered — everything else about the command still goes through normally.

### Confirmation for risky actions
`/rosterremove` and `/demote` now show a Confirm/Cancel button before doing anything, so a mis-click doesn't demote or remove the wrong person. Only the person who ran the command can respond to the buttons, and it times out after 30 seconds with no changes made if left alone.

### Bulk importing an existing roster
If you already had staff roles set up before installing this bot, you don't have to add everyone one at a time. First set up your ranks with `/setranks`, then run:
```
/rosterimport rank:@Staff
/rosterimport rank:@Manager
/rosterimport rank:@Owner
```
Each run scans your whole server for members who currently hold that role and adds them to the roster at that rank — reporting how many were added, moved (if they were at a different rank), or already correct. Run it once per rank to fully populate the roster.

### Cooldown on promotions/demotions
```
/setcooldown hours:24
/setcooldown hours:72 user:@SomeUser
/setcooldown hours:0 user:@SomeUser
```
Once set, `/promote` and `/demote` will refuse to change someone's rank again until the cooldown has passed, showing how much time is left. This guards against accidental double-promotions or rapid back-and-forth changes.

Run it **without** `user` to set the default that applies to everyone. Run it **with** `user` to override that default for just one specific person (useful if, say, one person tends to get promoted/demoted more carefully and needs a longer wait, or someone needs an exception with a shorter one). A `0` in the per-user version removes their override and puts them back on the server default; a `0` without a user disables the cooldown entirely for everyone without an override. `/rosteradd` (manual rank picks) isn't affected by the cooldown either way.

### Inactivity tracking
```
/setinactivitydays days:14
```
The bot quietly tracks the last time each server member sent a message (no message content is read or stored — just the timestamp). Once a threshold is set, run:
```
/inactive
```
to see everyone on the roster who hasn't sent a message in that many days, including anyone who's never been seen talking at all. Nothing is automated — it's purely a report to help you spot people who might need a nudge or a rank review. Set the threshold to `0` to disable tracking.

### Live server stats
```
/setstatschannel #stats
```
Posts an embed showing total members, humans vs. bots, roster size, server boosts, and when the server was created — and keeps it updated automatically whenever someone joins, leaves, or the roster changes. No need to run anything else; it refreshes itself. If you just want a one-off snapshot without dedicating a channel to it, use `/serverstats` instead.

### Checking status
```
/stats           (counts per rank, e.g. Owner: 1, Staff: 4)
/rank @SomeUser   (shows their current rank)
/history @SomeUser (shows a timeline of promotions, demotions, and roster changes for them)
```
`/rank` and `/history` default to yourself if you don't specify a user. History is capped to the 10 most recent entries per person to keep the embed readable.

### Reasons
`/addrole`, `/removerole`, `/rosteradd`, `/rosterremove`, `/promote`, and `/demote` all require a `reason`. It shows up in the log channel embed and in Discord's built-in audit log for that role change, so there's always a record of why an action was taken.

### Tournaments
```
/tournament_create name:Summer Cup
```
Posts a sign-up embed with Join/Leave buttons — anyone can click to enter, no permission needed for that part. When you're ready to lock it in:
```
/tournament_start name:Summer Cup
```
This shuffles the sign-ups and generates a single-elimination bracket (odd numbers get a bye automatically). Report results as matches happen:
```
/tournament_report name:Summer Cup match:1 winner:@SomeUser
```
Once every match in a round has a winner, the next round is generated automatically; the last standing player is announced as champion. Check the bracket anytime with `/tournament_bracket name:Summer Cup` — anyone can run this one.

### Game nights
```
/gamenight_create game:Valorant date:2026-07-20 time:20:00
```
**Time is in UTC** — convert your local time before entering it (a search like "8pm EST to UTC" works well). This posts an embed with Going/Maybe/Can't Go buttons, and the bot automatically posts a reminder in the same channel — pinging everyone who RSVP'd "Going" — 15 minutes before it starts, as long as the bot stays running. `/gamenight_list` shows everything upcoming with the ID you'll need for `/gamenight_cancel id:<#>`.

### MVP voting
```
/mvp_start title:Scrim vs Team X user1:@Alex user2:@Sam user3:@Jordan
```
Posts a vote with a button per candidate (2–5 people) — anyone can click to vote, and can change their vote by clicking a different button. When you're ready to close it:
```
/mvp_end
```
This tallies the votes, announces the winner (or a tie if there is one), and removes the buttons from the original message. Only one MVP vote can be active per server at a time.

**Heads up on all three of these:** sign-up/RSVP/vote buttons only work while the bot process is actively running — if it restarts (e.g. a Render redeploy) while one is open, existing buttons on already-posted messages will stop responding. This doesn't affect anything else in the bot (roles, roster, etc.) — just re-run the create command if that happens to you mid-event.

### Cross-posting to another server
This mirrors messages from a channel in this server to a channel in a **different** server. It only works if the same bot is invited to both servers — invite it to the other server the same way you did this one (same OAuth2 URL from Setup, run again for the second server), using the same bot token.

To set it up:
1. In the **other server**, enable Developer Mode (User Settings → Advanced → Developer Mode), then right-click the destination channel and **Copy Channel ID**.
2. Back in **this server**, go to the channel you want to mirror **from** and run:
```
/crosspost_add destination_channel_id:123456789012345678
```
From then on, every message sent in that channel gets mirrored as an embed (showing who sent it and which server/channel it came from) into the destination channel. Images are shown inline; other attachments are linked. `/crosspost_list` shows everything currently mirrored, and `/crosspost_remove` (run in the source channel) turns it off.

Note: this only forwards one-way and doesn't sync edits or deletions — if the original message is edited or deleted afterward, the mirrored copy stays as-is.

### Moderation
```
/kick @SomeUser reason:Repeated rule violations
/ban @SomeUser reason:Spam bot delete_days:1
/timeout @SomeUser minutes:60 reason:Cooling off period
/warn @SomeUser reason:First warning for spam
/warnings @SomeUser
/purge amount:25
/lock reason:Heated argument, cooling down
/unlock
/slowmode seconds:10
```
`/kick` and `/ban` show a confirm/cancel prompt before doing anything, same as `/demote` and `/rosterremove`. The bot tries to DM the person first so they know why (kick/ban/timeout/warn all attempt this), but goes ahead with the action either way if their DMs are closed. `/kick` and `/ban` also won't work on someone whose highest role sits above the bot's own role in Server Settings — same rule as role assignment.

**Voice announcement on timeout:** if the person is currently in a voice channel when `/timeout` is run, the bot joins that channel and announces their name, the timeout duration, and the reason out loud (text-to-speech), then leaves. This needs the bot's `Connect` and `Speak` permissions (see Setup above) — if it can't join for any reason, the timeout itself still goes through normally, it just skips the announcement silently.

### Server-wide audit log
```
/audit
```
Shows the last 20 rank/roster actions across **everyone** in the server, not just one person — useful for a quick "what's happened lately" check without scrolling the log channel. This pulls from the same history data `/history` uses for individuals.

### Backups
```
/backup
```
Sends you a downloadable JSON file containing this server's full bot configuration — ranks, channels, roster, warnings, and history. Handy to keep on hand in case something gets misconfigured and you want to see exactly what was set.

### Announcements
```
/announce channel:#news title:Server Update message:We just added a new tournament system!
/announce channel:#news title:Update message:Small fix, nothing urgent ping_everyone:False
```
Posts a clean announcement embed to whatever channel you choose, with your name credited in the footer. **Pings @everyone by default** — set `ping_everyone:False` for quieter, non-urgent updates. Note: the bot needs the **Mention @everyone, @here, and All Roles** permission in that channel for the ping to actually notify people (it comes bundled with Administrator, so if you gave the bot that, you're already covered) — if it's missing, the announcement still posts, you'll just get a heads-up that nobody was pinged.

### Mass announce (text + voice)
```
/massannounce message:Servers restarting in 10 minutes, save your progress! title:Heads Up
```
Goes further than `/announce` — it posts the embed to **every text channel whose name contains "announcement"** (no setup needed, just name your channels normally, e.g. `#announcements`, `#server-announcements`), **pings @everyone** in each of them by default (same `ping_everyone:False` option available here too), and **speaks the message out loud** in every voice channel that currently has at least one person in it, one channel at a time. Runs in the background so the command responds instantly instead of making you wait for every voice channel to finish. Needs the bot's `Connect` and `Speak` permissions to reach voice channels (see Setup above) — if it can't join a particular VC, it just skips that one and keeps going.

### Mass rename
```
/massrename prefix:[Staff] role:@Staff
/massrename suffix: | Verified
/massrename prefix:🎮 suffix:🎮
```
Adds a prefix and/or suffix to multiple members' nicknames at once. Leave `role` off to target every eligible member in the server, or set it to only rename members holding a specific role. Shows a confirmation prompt with the exact count and pattern before touching anyone.

Safety notes:
- The server owner and anyone whose highest role sits above the bot's own are automatically skipped (Discord won't let the bot rename them anyway).
- Bots are skipped.
- Discord caps nicknames at 32 characters — anything longer gets truncated.
- There's no automatic undo — if you want to reverse it, you'd run `/massrename` again with the opposite pattern, or fix names individually.

### Mass role add/remove
```
/massaddrole role:@Verified
/massaddrole role:@Event2026 filter_role:@Staff
/massremoverole role:@Trial Staff
/massremoverole role:@Old Tier filter_role:@New Tier
```
`/massaddrole` gives a role to everyone who doesn't already have it — or, if you set `filter_role`, only to members who currently hold that other role (useful for "give everyone with Staff the new Event role" type situations). `/massremoverole` works the same way in reverse — it targets everyone who currently has the role, optionally narrowed further by `filter_role` (handy for cleanup, like stripping an old rank role only from people who've already been moved to a new one). Both show a confirmation with the exact member count before doing anything, and report how many succeeded/failed afterward.

### AFK
```
/afk
/afk reason:Grabbing food, back in 20
```
Marks you AFK — anyone who @mentions you afterward gets an automatic heads-up in the same channel showing your reason and how long you've been away. The moment you send any message again, your AFK status clears automatically and the bot lets the channel know you're back.

### VC greetings
```
/setvcgreeting user:@Jerry message:The legend has arrived!
/removevcgreeting user:@Jerry
```
Once set, the bot automatically joins whatever voice channel that person joins and speaks the message out loud, then leaves — no command needs to be run each time, it just happens. If two greeted people join voice channels close together, the greetings play one after another rather than overlapping. Needs the bot's `Connect` and `Speak` permissions in that channel (already covered if you gave the bot Administrator).

### Message activity (weekly)
```
/evaluate
/evaluate user:@SomeUser
```
The bot quietly counts how many messages each person sends (no content is read or stored, just a running count per person). `/evaluate` with no user shows a top-10 leaderboard for the current tracking period; with a user, it shows just their count. The period automatically resets every 7 days — if you have a log channel set with `/setlogchannel`, the bot also auto-posts the full leaderboard there right before each weekly reset, so you get a standing record even if nobody checks manually.

### Birthdays
```
/setbirthday month:7 day:18
/mybirthday
/removebirthday
```
Anyone can set their own birthday — just month and day, no year needed (kept private in that sense). Two optional admin setup steps make it actually do something on the day:
```
/setbirthdayrole role:@Birthday
/setbirthdaychannel channel:#general
```
`/setbirthdayrole` automatically gives that role to anyone whose birthday it is, and takes it back off them once the day passes — checked every hour, so it's resilient to the bot restarting at odd times (a Render redeploy won't cause it to miss the day). `/setbirthdaychannel` posts a shoutout message in that channel for each birthday. Either one is optional and works independently — set just the role, just the channel, or both.

### Web dashboard
If you completed the OAuth setup above, visiting your bot's URL in a browser gives you a login-protected settings page — an alternative to typing slash commands for the settings that benefit most from a visual picker:

- Log channel, live roster channel, live stats channel, birthday shoutout channel, role showcase channel
- Manager role, birthday role
- The full rank order (all 8 slots, picked from real roles in your server)
- Cooldown hours and inactivity threshold

Click **Login with Discord**, and you'll land on a list of every server where you're either an Administrator or hold the role set via `/setmanagerrole` (and where the bot is present). Pick one, edit whatever you want, and hit **Save changes** — it writes to the exact same config the bot already uses, so changes take effect immediately, no restart needed. This doesn't replace the slash commands — things like roster membership, warnings, and history still go through Discord — it's specifically for the "which channel/role should X use" type settings.

Nothing here needs a database: the dashboard reads and writes the bot's existing `guild_config.json` directly, since it runs in the same process.

### Role showcase (self-assignable roles)
```
/showcase add role:@Valorant description:Get pinged for Valorant scrims and game nights
/showcase add role:@Minecraft description:Access to the Minecraft server + channels
/showcase setchannel channel:#roles
```
Builds a live, self-updating embed listing every showcased role with its description and current member count — each with its own button underneath. Anyone in the server can click a role's button to instantly give themselves that role, or click again to remove it — no staff involvement needed. Great for game tags, notification pings, or any role people should be able to opt into freely.

`/showcase remove role:@...` takes a role back out of the showcase (existing members keep the role, it just stops being offered). `/showcase list` shows the current lineup without needing the live channel. Discord caps this at 25 roles per showcase message. As with any role the bot manages, make sure the bot's own role sits above whatever you showcase in Server Settings > Roles.

## Notes
- Role changes are stored in `guild_config.json`, created automatically next to `bot.py`.
- For 24/7 uptime you'll want to host this somewhere (a small VPS, Railway, Render, etc.) rather than running it on your own machine.
- If a command doesn't appear in Discord right away, it can take up to an hour for global slash commands to propagate on first sync — restarting the bot after inviting it usually speeds this up.
