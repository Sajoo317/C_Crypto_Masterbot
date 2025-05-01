import logging
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dummy user database
users = {}

# --- Helper: Get current crypto price from CoinGecko ---
async def get_price(symbol: str) -> float:
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data.get(symbol.lower(), {}).get('usd')

# --- Background Task: Monitor Alerts ---
async def monitor_alerts(application):
    while True:
        for user_id, data in users.items():
            for symbol, target_price in list(data.get('alerts', [])):
                try:
                    current_price = await get_price(symbol)
                    if current_price and current_price >= target_price:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=f"🚨 {symbol.upper()} has reached ${current_price} (target: ${target_price})"
                        )
                        data['alerts'].remove((symbol, target_price))
                except Exception as e:
                    logger.error(f"Error checking {symbol} for user {user_id}: {e}")
        await asyncio.sleep(60)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {'alerts': []}
    await update.message.reply_text(
        "Welcome to *C_Crypto_Masterbot*!\n\n"
        "Use /alert <symbol> <price> to set a free price alert.\n"
        "You can also chat with me and ask crypto questions!\n\n"
        "💖 If you liked the bot, consider donating at least $1 to support its growth.\n"
        "USDT (TRC20): TPkpS5feBawGeiBkbrjLWZKW6uQNFEYokG",
        parse_mode='Markdown'
    )

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].lower()
        price = float(context.args[1])
        user_id = update.effective_user.id
        users[user_id]['alerts'].append((symbol, price))
        await update.message.reply_text(f"Alert set for {symbol.upper()} at ${price}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /alert <symbol> <price>")

# --- Main ---
async def main():
    app = ApplicationBuilder().token("7420592292:AAFDWMCeK1EEdsjLclro-3XD7i_4Qd49dls").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alert", alert))

    # Start background task after app is running
    async def startup():
        asyncio.create_task(monitor_alerts(app))

    app.post_init = startup
    print("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

