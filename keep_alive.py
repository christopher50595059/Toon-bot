"""
Keep-alive web server for Render's free tier.

Render's free Web Services spin down after 15 minutes with no incoming
HTTP traffic. Discord bots don't serve HTTP on their own, so this runs
a tiny web server alongside the bot in a background thread. Point a
free uptime pinger (e.g. UptimeRobot) at this server's URL every 5
minutes and Render will never see 15 minutes of silence.
"""

import os
import threading

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive."


def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
