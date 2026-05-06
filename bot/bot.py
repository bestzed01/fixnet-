import os, logging, requests
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes
from telegram.ext import MessageHandler, filters


load_dotenv()
BOT_TOKEN    = os.getenv("BOT_TOKEN")
BACKEND_URL  = os.getenv("BACKEND_URL", "http://backend:8000")
MINI_APP_URL = os.getenv("MINI_APP_URL")   # https://xxxx.ngrok.app/app

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def is_expired(iso):
    try: return datetime.utcnow() > datetime.fromisoformat(iso)
    except: return True

def main_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🌐 Открыть приложение", web_app=WebAppInfo(url=MINI_APP_URL))
    ],[
        InlineKeyboardButton("⭐ Оплатить 150 звёзд", callback_data="pay")
    ]])

def pay_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐ Оплатить 150 звёзд", callback_data="pay")
    ],[
        InlineKeyboardButton("🌐 Открыть приложение", web_app=WebAppInfo(url=MINI_APP_URL))
    ]])

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    args = ctx.args

    # Came from Mini App pay button — always send invoice
    if args and args[0] == 'pay':
        await ctx.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title="FixNet — 1 месяц",
            description="Безлимитный доступ на 1 месяц. Все сайты, без ограничений.",
            payload=f"sub_{u.id}",
            currency="XTR",
            prices=[LabeledPrice("1 месяц", 150)],
        )
        return

    try:
        r = requests.get(f"{BACKEND_URL}/user/{u.id}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if is_expired(data.get("expires_at","")):
                await update.message.reply_text(
                    "⏰ *Ваш бесплатный период закончился*\n\n"
                    "Продолжите за 150 звёзд в месяц \\(≈ 150₽\\)",
                    parse_mode="MarkdownV2", reply_markup=pay_keyboard()
                )
            else:
                await update.message.reply_text(
                    "👋 С возвращением\\!\n\nОткройте приложение, чтобы получить вашу ссылку подключения\\.",
                    parse_mode="MarkdownV2", reply_markup=main_keyboard()
                )
            return
    except: pass

    await update.message.reply_text(
        "🛡 *Добро пожаловать в FixNet*\n\n"
        "Открывай YouTube, Instagram и любые сайты — быстро и безопасно\\.\n\n"
        "🎁 *Первые 24 часа — бесплатно*\n"
        "Потом всего 150 звёзд в месяц\\.",
        parse_mode="MarkdownV2",
        reply_markup=main_keyboard()
    )

async def pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await ctx.bot.send_invoice(
        chat_id=q.message.chat_id,
        title="FixNet — 1 месяц",
        description="Безлимитный доступ на 1 месяц. Все сайты, без ограничений.",
        payload=f"sub_{q.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice("1 месяц", 150)],
    )

async def precheckout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def payment_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    uid = update.effective_user.id
    try:
        requests.post(f"{BACKEND_URL}/payment/confirm",
                      json={"telegram_id": uid, "stars_amount": payment.total_amount},
                      timeout=10)
    except Exception as e:
        log.error(f"payment confirm error: {e}")
    await update.message.reply_text(
        "🎉 *Оплата прошла\\!*\n\nДоступ продлён на 1 месяц\\. Приятного использования\\! 🚀",
        parse_mode="MarkdownV2", reply_markup=main_keyboard()
    )

async def handle_webapp_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = update.message.web_app_data.data
    if data == 'pay':
        await ctx.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title="FixNet — 1 месяц",
            description="Безлимитный доступ на 1 месяц. Все сайты, без ограничений.",
            payload=f"sub_{update.effective_user.id}",
            currency="XTR",
            prices=[LabeledPrice("1 месяц", 150)],
        )

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pay, pattern="^pay$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_done))
    log.info("FixNet bot running")
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.run_polling()
