# Endless Path - Minecraft Telegram Panel Bot

بات تلگرام برای مدیریت سرور ماین‌کرفت روی VPS (روشن/خاموش/ریستارت/وضعیت/لاگ زنده/کنسول دستور)
از طریق SSH به VPS وصل میشه، پس روی سرویس‌هایی مثل Render قابل اجراست حتی اگه خود VPS به تلگرام دسترسی نداشته باشه.

## متغیرهای محیطی لازم

- `BOT_TOKEN` — توکن بات از BotFather
- `ADMIN_IDS` — آیدی عددی تلگرام (با کاما جدا شده برای چند نفر)
- `SSH_HOST` — آی‌پی VPS
- `SSH_PORT` — پیش‌فرض 22
- `SSH_USER` — یوزر SSH روی VPS
- `SSH_PRIVATE_KEY` — کل متن کلید خصوصی SSH
- `AGENT_DIR` — مسیر پوشه‌ی agent روی VPS (پیش‌فرض `/home/tri_ali/mc_panel_bot_agent`)

## اجرا

```bash
pip install -r requirements.txt
python main.py
```

## پیش‌نیاز روی VPS

- سرویس systemd به اسم `minecraft` برای اجرای سرور
- دسترسی sudo بدون پسورد برای `systemctl start/stop/restart minecraft`
- پوشه‌ی agent (`rcon.py` + `rcon_cli.py`) برای اجرای دستورات RCON محلی
