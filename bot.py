import os
import html
import hashlib
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
PUBLIC_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")

if not PUBLIC_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is not available.")

NAME, AGE, AREA, REDLINE, ABOUT, CONFIRM = range(6)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def profile_text(data, user=None):
    name = html.escape(data["name"])
    age = html.escape(data["age"])
    area = html.escape(data["area"])
    redline = html.escape(data["redline"])
    about = html.escape(data["about"])

    mention = ""
    if user:
        mention = (
            f'\n\n👤 <a href="tg://user?id={user.id}">'
            f'{html.escape(user.full_name)}</a>'
        )

    return (
        "✨ <b>معارفه عضو گروه</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"🪪 <b>نام:</b> {name}\n\n"
        f"🎂 <b>سن:</b> {age}\n\n"
        f"📍 <b>منطقه سکونت:</b> {area}\n\n"
        f"🚫 <b>خط قرمز من:</b> {redline}\n\n"
        f"💬 <b>یک جمله درباره من:</b>\n{about}"
        f"{mention}"
    )


async def intro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text("این دستور را داخل گروه ارسال کنید.")
        return

    bot_username = context.bot.username
    deep_link = f"https://t.me/{bot_username}?start=g_{chat.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 ثبت معارفه", url=deep_link)]
    ])

    await update.message.reply_text(
        "👋 برای ثبت معارفه روی دکمه زیر بزنید.\n\n"
        "اطلاعات در خصوصی دریافت می‌شود و بعد از تأیید داخل همین گروه نمایش داده خواهد شد.",
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "private":
        await update.message.reply_text("برای معارفه، داخل گروه دستور /intro را بزنید.")
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text(
            "سلام 👋\n\n"
            "برای ثبت معارفه ابتدا داخل گروه موردنظر /intro را بزنید "
            "و سپس روی دکمه «ثبت معارفه» بزنید."
        )
        return ConversationHandler.END

    payload = context.args[0]
    if not payload.startswith("g_"):
        await update.message.reply_text("لینک معارفه معتبر نیست.")
        return ConversationHandler.END

    try:
        group_id = int(payload[2:])
    except ValueError:
        await update.message.reply_text("شناسه گروه معتبر نیست.")
        return ConversationHandler.END

    user = update.effective_user

    try:
        member = await context.bot.get_chat_member(group_id, user.id)
        if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.BANNED}:
            await update.message.reply_text("❌ شما عضو این گروه نیستید.")
            return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "❌ امکان بررسی عضویت شما وجود ندارد.\n"
            "مطمئن شوید ربات داخل گروه حضور دارد و اجازه ارسال پیام دارد."
        )
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["group_id"] = group_id

    await update.message.reply_text(
        "عالی 👌\n\n1️⃣ <b>نام شما چیست؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 50:
        await update.message.reply_text("نام باید بین ۲ تا ۵۰ کاراکتر باشد.")
        return NAME

    context.user_data["name"] = value
    await update.message.reply_text(
        "2️⃣ <b>چند سالته؟</b>\n\nمثلاً: 28",
        parse_mode=ParseMode.HTML,
    )
    return AGE


def normalize_digits(value: str) -> str:
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return value.translate(table)


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    normalized = normalize_digits(value)

    if not normalized.isdigit():
        await update.message.reply_text("لطفاً سن را فقط به صورت عدد وارد کنید.")
        return AGE

    age = int(normalized)
    if not 10 <= age <= 100:
        await update.message.reply_text("لطفاً یک سن معتبر وارد کنید.")
        return AGE

    context.user_data["age"] = value
    await update.message.reply_text(
        "3️⃣ <b>منطقه سکونتت کجاست؟</b>\n\nمثلاً: غرب تهران",
        parse_mode=ParseMode.HTML,
    )
    return AREA


async def get_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 100:
        await update.message.reply_text("لطفاً منطقه سکونت را کوتاه و واضح وارد کنید.")
        return AREA

    context.user_data["area"] = value
    await update.message.reply_text(
        "4️⃣ <b>خط قرمز شما چیست؟</b>\n\nمثلاً: بی‌احترامی",
        parse_mode=ParseMode.HTML,
    )
    return REDLINE


async def get_redline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 300:
        await update.message.reply_text("متن باید بین ۲ تا ۳۰۰ کاراکتر باشد.")
        return REDLINE

    context.user_data["redline"] = value
    await update.message.reply_text(
        "5️⃣ <b>در یک جمله خودت را معرفی کن 🙂</b>",
        parse_mode=ParseMode.HTML,
    )
    return ABOUT


async def get_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 3 <= len(value) <= 500:
        await update.message.reply_text("جمله معرفی باید بین ۳ تا ۵۰۰ کاراکتر باشد.")
        return ABOUT

    context.user_data["about"] = value

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأیید و ارسال", callback_data="intro_confirm")],
        [
            InlineKeyboardButton("🔄 از اول", callback_data="intro_restart"),
            InlineKeyboardButton("❌ لغو", callback_data="intro_cancel"),
        ],
    ])

    await update.message.reply_text(
        "👀 <b>پیش‌نمایش معارفه:</b>\n\n"
        + profile_text(context.user_data, update.effective_user),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )
    return CONFIRM


async def confirm_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    group_id = context.user_data.get("group_id")

    required = {"name", "age", "area", "redline", "about"}
    if not group_id or not required.issubset(context.user_data):
        await query.edit_message_text(
            "❌ اطلاعات فرم منقضی شده است.\n"
            "لطفاً دوباره از داخل گروه /intro را بزنید."
        )
        return ConversationHandler.END

    try:
        member = await context.bot.get_chat_member(group_id, user.id)
        if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.BANNED}:
            await query.edit_message_text("❌ شما دیگر عضو گروه نیستید.")
            return ConversationHandler.END

        await context.bot.send_message(
            chat_id=group_id,
            text=profile_text(context.user_data, user),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.exception("Failed to publish introduction: %s", exc)
        await query.edit_message_text(
            "❌ ارسال معرفی به گروه انجام نشد.\n"
            "دسترسی ربات برای ارسال پیام داخل گروه را بررسی کنید."
        )
        return ConversationHandler.END

    await query.edit_message_text("✅ معارفه شما با موفقیت داخل گروه منتشر شد.")
    context.user_data.clear()
    return ConversationHandler.END


async def restart_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id = context.user_data.get("group_id")
    context.user_data.clear()
    if group_id:
        context.user_data["group_id"] = group_id

    await query.edit_message_text(
        "🔄 از اول شروع می‌کنیم.\n\n1️⃣ <b>نام شما چیست؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return NAME


async def cancel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ ثبت معارفه لغو شد.")
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ ثبت معارفه لغو شد.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)],
            REDLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_redline)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_about)],
            CONFIRM: [
                CallbackQueryHandler(confirm_intro, pattern="^intro_confirm$"),
                CallbackQueryHandler(restart_intro, pattern="^intro_restart$"),
                CallbackQueryHandler(cancel_button, pattern="^intro_cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("intro", intro_command), group=0)
    app.add_handler(conversation, group=1)

    webhook_secret = hashlib.sha256(BOT_TOKEN.encode()).hexdigest()

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="telegram",
        webhook_url=f"{PUBLIC_URL}/telegram",
        secret_token=webhook_secret,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
