import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]

SSH_HOST = os.environ["SSH_HOST"]
SSH_PORT = int(os.environ.get("SSH_PORT", "22"))
SSH_USER = os.environ["SSH_USER"]
SSH_PRIVATE_KEY = os.environ["SSH_PRIVATE_KEY"]  # کل متن کلید خصوصی (نه مسیر فایل)

# مسیر پوشه‌ی agent روی VPS (فایل rcon_cli.py اونجاست)
AGENT_DIR = os.environ.get("AGENT_DIR", "/home/tri_ali/mc_panel_bot_agent")

GAMES = {
    "minecraft": {
        "label": "🧱 Minecraft",
        "service": "minecraft",
        "log_path": "/home/tri_ali/minecraft-server/logs/latest.log",
        "rcon_enabled": True,
    },
    # برای بازی بعدی فقط یه بلوک مثل این اضافه کن:
    # "valheim": {
    #     "label": "⚔️ Valheim",
    #     "service": "valheim",
    #     "log_path": "/home/tri_ali/valheim-server/logs/latest.log",
    #     "rcon_enabled": False,
    # },
}

DEFAULT_GAME = "minecraft"
LOG_TAIL_LINES = 15
LOG_STREAM_INTERVAL = 4
