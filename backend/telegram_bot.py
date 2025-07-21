from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

from shared.config import WEB_APP_URL

web_app = WebAppInfo(url=WEB_APP_URL)

# Command to show web app button
async def open_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶️ Play", web_app=web_app)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 Ready to play:", reply_markup=reply_markup)

# Handle web app data
async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.web_app_data:
        import json
        data = json.loads(update.message.web_app_data.data)
        action = data.get("action")
        code = data.get("code")

        if action == "host_game":
            context.bot_data[code] = {
                "host": update.effective_user.id,
                "players": [update.effective_user.username]
            }
            await update.message.reply_text(f"🧑 You hosted a game with code: {code}")
        elif action == "join_game":
            game = context.bot_data.get(code)
            if not game:
                await update.message.reply_text("❌ Game code not found.")
            else:
                game["players"].append(update.effective_user.username)
                await update.message.reply_text(f"✅ Joined game {code}. Players: {', '.join(game['players'])}")

# Start the bot
# import os
# BOT_TOKEN = os.getenv("8068386210:AAEiyCP3-0PVksVkX8fgomIj5JiwVuAqAbY")  

app = ApplicationBuilder().token("8068386210:AAEiyCP3-0PVksVkX8fgomIj5JiwVuAqAbY").build()
app.add_handler(CommandHandler("game", open_webapp))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))
app.run_polling()