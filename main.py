import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

from config import BOT_TOKEN, ADMIN_IDS, GAMES, DEFAULT_GAME, LOG_TAIL_LINES, LOG_STREAM_INTERVAL
import games as gm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_allowed(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main_menu_keyboard(game_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🟢 روشن", callback_data=f"start:{game_id}"),
            InlineKeyboardButton("🔴 خاموش", callback_data=f"stop:{game_id}"),
            InlineKeyboardButton("🔄 ریستارت", callback_data=f"restart:{game_id}"),
        ],
        [
            InlineKeyboardButton("📊 وضعیت", callback_data=f"status:{game_id}"),
            InlineKeyboardButton("📜 لاگ", callback_data=f"log:{game_id}"),
        ],
        [
            InlineKeyboardButton("💻 کنسول (دستور)", callback_data=f"console:{game_id}"),
        ],
    ]
    if len(GAMES) > 1:
        rows.append([InlineKeyboardButton("🎮 تعویض بازی", callback_data="switch_game")])
    return InlineKeyboardMarkup(rows)


def games_list_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(g["label"], callback_data=f"select_game:{gid}")] for gid, g in GAMES.items()]
    return InlineKeyboardMarkup(rows)


async def guard(update: Update) -> bool:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        if update.message:
            await update.message.reply_text("⛔️ دسترسی نداری.")
        elif update.callback_query:
            await update.callback_query.answer("⛔️ دسترسی نداری.", show_alert=True)
        return False
    return True


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    game_id = context.user_data.get("current_game", DEFAULT_GAME)
    await update.message.reply_text(
        f"🎮 پنل مدیریت سرور\nبازی فعلی: {GAMES[game_id]['label']}",
        reply_markup=main_menu_keyboard(game_id),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_allowed(query.from_user.id):
        await query.answer("⛔️ دسترسی نداری.", show_alert=True)
        return
    await query.answer()

    data = query.data

    if data == "switch_game":
        await query.edit_message_text("یه بازی انتخاب کن:", reply_markup=games_list_keyboard())
        return

    if data.startswith("select_game:"):
        game_id = data.split(":", 1)[1]
        context.user_data["current_game"] = game_id
        await query.edit_message_text(
            f"🎮 پنل مدیریت سرور\nبازی فعلی: {GAMES[game_id]['label']}",
            reply_markup=main_menu_keyboard(game_id),
        )
        return

    action, game_id = data.split(":", 1)

    if action in ("start", "stop", "restart"):
        await query.edit_message_text(f"⏳ در حال اجرای {action}...")
        result = await gm.service_action(game_id, action)
        await query.message.reply_text(result)
        await query.message.reply_text(
            f"🎮 پنل مدیریت سرور\nبازی فعلی: {GAMES[game_id]['label']}",
            reply_markup=main_menu_keyboard(game_id),
        )

    elif action == "status":
        result = await gm.service_status(game_id)
        await query.message.reply_text(result)

    elif action == "log":
        text = await gm.tail_log(game_id, LOG_TAIL_LINES)
        await query.message.reply_text(
            f"📜 آخرین خطوط لاگ:\n\n<pre>{escape_html(text)}</pre>", parse_mode="HTML"
        )

    elif action == "console":
        context.user_data["console_mode"] = game_id
        await query.message.reply_text(
            f"💻 حالت کنسول فعال شد برای {GAMES[game_id]['label']}.\n"
            f"هر پیامی بفرستی به‌عنوان دستور کنسول اجرا میشه (مثلاً say hi).\n"
            f"برای خروج از این حالت: /cancel"
        )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    context.user_data.pop("console_mode", None)
    await update.message.reply_text("❎ از حالت کنسول خارج شدی.")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    game_id = context.user_data.get("console_mode")
    if not game_id:
        return
    command = update.message.text.strip()
    await update.message.reply_text(f"⏳ در حال اجرا: {command}")
    result = await gm.run_console_command(game_id, command)
    await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")


async def logs_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    game_id = context.user_data.get("current_game", DEFAULT_GAME)
    chat_id = update.effective_chat.id
    job_name = f"logstream_{chat_id}"

    if context.job_queue.get_jobs_by_name(job_name):
        await update.message.reply_text("📡 استریم لاگ از قبل فعاله.")
        return

    initial_pos = await gm.get_log_size(game_id)
    context.job_queue.run_repeating(
        stream_log_job, interval=LOG_STREAM_INTERVAL, first=LOG_STREAM_INTERVAL,
        name=job_name, chat_id=chat_id,
        data={"game_id": game_id, "pos": initial_pos},
    )
    await update.message.reply_text("📡 استریم زنده‌ی لاگ فعال شد. برای خاموش کردن: /logs_off")


async def logs_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    chat_id = update.effective_chat.id
    job_name = f"logstream_{chat_id}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text("🛑 استریم لاگ خاموش شد." if jobs else "استریمی فعال نبود.")


async def stream_log_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    game_id = job.data["game_id"]
    pos = job.data["pos"]

    size = await gm.get_log_size(game_id)
    if size < pos:
        pos = 0  # لاگ rotate شده

    if size > pos:
        new_text = await gm.read_log_from(game_id, pos)
        job.data["pos"] = size
        new_text = new_text.strip()
        if new_text:
            chunk = new_text[-3500:]
            await context.bot.send_message(
                chat_id=job.chat_id,
                text=f"<pre>{escape_html(chunk)}</pre>",
                parse_mode="HTML",
            )


def run_health_server():
    """Render برای Web Service به یه پورت باز نیاز داره؛ این یه health-check ساده‌ست"""
    port = int(os.environ.get("PORT", "10000"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        def log_message(self, *args):
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


def main():
    if os.environ.get("PORT"):
        threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("logs_on", logs_on_cmd))
    app.add_handler(CommandHandler("logs_off", logs_off_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
