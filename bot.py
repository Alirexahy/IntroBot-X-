import os
import html
import hashlib
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

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
INTRO_TOPIC_ID_RAW = os.getenv("INTRO_TOPIC_ID")

try:
    INTRO_TOPIC_ID = int(INTRO_TOPIC_ID_RAW) if INTRO_TOPIC_ID_RAW else None
except ValueError as exc:
    raise RuntimeError("INTRO_TOPIC_ID must be a numeric Telegram topic ID.") from exc

if INTRO_TOPIC_ID is not None and INTRO_TOPIC_ID <= 0:
    raise RuntimeError("INTRO_TOPIC_ID must be a positive integer.")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set.")

if not PUBLIC_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is not available.")

(
    NAME,
    NICKNAME,
    BIRTH_DATE,
    JOB,
    AREA,
    INTERESTS,
    REDLINE,
    PERSONALITY,
    GOAL,
    ABOUT,
    SKILLS,
    ACTIVITIES,
    CONFIRM,
) = range(13)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def profile_text(data, user=None):
    values = {
        key: html.escape(data[key])
        for key in (
            "name",
            "nickname",
            "birth_date",
            "age",
            "job",
            "area",
            "interests",
            "redline",
            "personality",
            "goal",
            "about",
            "skills",
            "activities",
        )
    }

    mention = ""
    if user:
        mention = (
            f"\n\n🆔 <b>آیدی عددی تلگرام:</b> <code>{user.id}</code>"
            f'\n👤 <b>پروفایل:</b> <a href="tg://user?id={user.id}">'
            f"{html.escape(user.full_name)}</a>"
        )

    return (
        "✨ <b>معارفه عضو خانواده ایکس</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"🪪 <b>نام:</b> {values['name']}\n"
        f"🏷 <b>نام یا لقب موردعلاقه:</b> {values['nickname']}\n"
        f"🎂 <b>تاریخ تولد:</b> {values['birth_date']}\n"
        f"🎈 <b>سن:</b> {values['age']} سال\n"
        f"💼 <b>شغل:</b> {values['job']}\n"
        f"📍 <b>محدوده سکونت در کرج:</b> {values['area']}\n\n"
        f"❤️ <b>علایق:</b> {values['interests']}\n"
        f"🚫 <b>خط قرمز:</b> {values['redline']}\n"
        f"🧭 <b>تیپ اجتماعی:</b> {values['personality']}\n\n"
        f"🎯 <b>هدف از حضور در گروه:</b>\n{values['goal']}\n\n"
        f"💬 <b>یک جمله درباره من:</b>\n{values['about']}\n\n"
        f"🛠 <b>مهارت یا تجربه قابل اشتراک:</b>\n{values['skills']}\n\n"
        f"🎉 <b>فعالیت‌های پیشنهادی برای گروه:</b>\n{values['activities']}"
        f"{mention}"
    )


async def intro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text("این دستور را داخل گروه ارسال کنید.")
        return

    if INTRO_TOPIC_ID is None:
        await update.message.reply_text(
            "❌ تاپیک انتشار معارفه هنوز تنظیم نشده است.\n\n"
            "دستور /topicid را داخل تاپیک موردنظر بزنید، سپس شناسه نمایش‌داده‌شده "
            "را در Render با نام INTRO_TOPIC_ID ثبت و سرویس را دوباره Deploy کنید."
        )
        return

    bot_username = context.bot.username
    deep_link = f"https://t.me/{bot_username}?start=g_{chat.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 ثبت معارفه", url=deep_link)]
    ])

    await update.message.reply_text(
        "👋 برای ثبت معارفه روی دکمه زیر بزنید.\n\n"
        "اطلاعات در خصوصی دریافت می‌شود و بعد از تأیید داخل تاپیک معارفه نمایش داده خواهد شد.",
        reply_markup=keyboard,
    )


async def topic_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == "private":
        await message.reply_text("این دستور را داخل تاپیک موردنظر در گروه ارسال کنید.")
        return

    topic_id = message.message_thread_id
    if topic_id is None:
        await message.reply_text(
            "این پیام داخل یک تاپیک ارسال نشده است.\n"
            "وارد تاپیک موردنظر شوید و همان‌جا /topicid را بزنید."
        )
        return

    await message.reply_text(
        "🧵 <b>شناسه این تاپیک:</b>\n"
        f"<code>{topic_id}</code>\n\n"
        "این عدد را در Render با نام INTRO_TOPIC_ID ثبت کنید.",
        parse_mode=ParseMode.HTML,
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
        "عالی 👌\n\n"
        "پاسخ‌های شما پس از تأیید داخل تاپیک معارفه منتشر می‌شوند؛ "
        "فقط اطلاعاتی را وارد کنید که با انتشار آن‌ها راحت هستید.\n\n"
        "1️⃣ <b>اسمت چیه؟</b>",
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
        "2️⃣ <b>دوست داری با چه اسم یا لقبی صدات کنیم؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return NICKNAME


async def get_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 1 <= len(value) <= 50:
        await update.message.reply_text("نام یا لقب باید حداکثر ۵۰ کاراکتر باشد.")
        return NICKNAME

    context.user_data["nickname"] = value
    await update.message.reply_text(
        "3️⃣ <b>تاریخ تولدت رو به‌صورت روز/ماه/سال وارد کن.</b>\n\n"
        "مثال: <code>۱۵/۰۷/۱۳۷۵</code>",
        parse_mode=ParseMode.HTML,
    )
    return BIRTH_DATE


def normalize_digits(value: str) -> str:
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return value.translate(table)


def normalize_birth_date(value: str):
    normalized = normalize_digits(value.strip()).replace("-", "/").replace(".", "/")
    parts = normalized.split("/")

    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None

    day, month, year = map(int, parts)
    if not 1300 <= year <= 1500 or not 1 <= month <= 12:
        return None

    if month <= 6:
        max_day = 31
    elif month <= 11:
        max_day = 30
    else:
        is_leap = year % 33 in {1, 5, 9, 13, 17, 22, 26, 30}
        max_day = 30 if is_leap else 29

    if not 1 <= day <= max_day:
        return None

    return f"{day:02d}/{month:02d}/{year:04d}"


def gregorian_to_jalali(year: int, month: int, day: int):
    month_offsets = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    if year > 1600:
        jalali_year = 979
        year -= 1600
    else:
        jalali_year = 0
        year -= 621

    adjusted_year = year + 1 if month > 2 else year
    days = (
        365 * year
        + (adjusted_year + 3) // 4
        - (adjusted_year + 99) // 100
        + (adjusted_year + 399) // 400
        - 80
        + day
        + month_offsets[month - 1]
    )

    jalali_year += 33 * (days // 12053)
    days %= 12053
    jalali_year += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jalali_year += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jalali_month = 1 + days // 31
        jalali_day = 1 + days % 31
    else:
        jalali_month = 7 + (days - 186) // 30
        jalali_day = 1 + (days - 186) % 30

    return jalali_year, jalali_month, jalali_day


def calculate_age(birth_date: str, today_jalali=None) -> int:
    birth_day, birth_month, birth_year = map(int, birth_date.split("/"))

    if today_jalali is None:
        now = datetime.now(ZoneInfo("Asia/Tehran"))
        today_jalali = gregorian_to_jalali(now.year, now.month, now.day)

    today_year, today_month, today_day = today_jalali
    birthday_passed = (today_month, today_day) >= (birth_month, birth_day)
    return today_year - birth_year - (0 if birthday_passed else 1)


async def get_birth_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    birth_date = normalize_birth_date(update.message.text)

    if birth_date is None:
        await update.message.reply_text(
            "لطفاً یک تاریخ شمسی معتبر با فرمت روز/ماه/سال وارد کنید.\n"
            "مثال: ۱۵/۰۷/۱۳۷۵"
        )
        return BIRTH_DATE

    age = calculate_age(birth_date)
    if not 0 <= age <= 120:
        await update.message.reply_text(
            "تاریخ تولد واردشده قابل قبول نیست. لطفاً تاریخ صحیح را وارد کنید."
        )
        return BIRTH_DATE

    context.user_data["birth_date"] = birth_date
    context.user_data["age"] = str(age)
    await update.message.reply_text(
        "4️⃣ <b>شغلت چیه؟</b>\n\n"
        "اگر دانشجو هستی، رشته‌ات رو هم می‌تونی بنویسی.",
        parse_mode=ParseMode.HTML,
    )
    return JOB


async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 100:
        await update.message.reply_text("لطفاً شغلت را کوتاه و واضح بنویس.")
        return JOB

    context.user_data["job"] = value
    await update.message.reply_text(
        "5️⃣ <b>در کدوم محدودهٔ کرج زندگی می‌کنی؟</b>",
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
        "6️⃣ <b>به چه چیزهایی علاقه داری؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return INTERESTS


async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 300:
        await update.message.reply_text("علایقت را در حداکثر ۳۰۰ کاراکتر بنویس.")
        return INTERESTS

    context.user_data["interests"] = value
    await update.message.reply_text(
        "7️⃣ <b>مهم‌ترین خط قرمزت در ارتباط با دیگران چیه؟</b>\n\n"
        "مثلاً: بی‌احترامی",
        parse_mode=ParseMode.HTML,
    )
    return REDLINE


async def get_redline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 300:
        await update.message.reply_text("متن باید بین ۲ تا ۳۰۰ کاراکتر باشد.")
        return REDLINE

    context.user_data["redline"] = value

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("درون‌گرا", callback_data="personality_introvert"),
            InlineKeyboardButton("برون‌گرا", callback_data="personality_extrovert"),
        ],
        [InlineKeyboardButton("میانه‌گرا", callback_data="personality_ambivert")],
    ])

    await update.message.reply_text(
        "8️⃣ <b>خودت رو بیشتر درون‌گرا، برون‌گرا یا میانه‌گرا می‌دونی؟</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return PERSONALITY


async def get_personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choices = {
        "personality_introvert": "درون‌گرا",
        "personality_extrovert": "برون‌گرا",
        "personality_ambivert": "میانه‌گرا",
    }
    personality = choices.get(query.data)
    if personality is None:
        return PERSONALITY

    context.user_data["personality"] = personality
    await query.edit_message_text(
        f"✅ انتخاب شما: <b>{personality}</b>\n\n"
        "9️⃣ <b>هدفت از حضور در خانوادهٔ ایکس چیه؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 3 <= len(value) <= 500:
        await update.message.reply_text("پاسخ باید بین ۳ تا ۵۰۰ کاراکتر باشد.")
        return GOAL

    context.user_data["goal"] = value
    await update.message.reply_text(
        "🔟 <b>در یک جمله خودت رو معرفی کن.</b>",
        parse_mode=ParseMode.HTML,
    )
    return ABOUT


async def get_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 3 <= len(value) <= 500:
        await update.message.reply_text("جمله معرفی باید بین ۳ تا ۵۰۰ کاراکتر باشد.")
        return ABOUT

    context.user_data["about"] = value
    await update.message.reply_text(
        "1️⃣1️⃣ <b>چه مهارت یا تجربه‌ای داری که دوست داری با اعضای گروه به اشتراک بذاری؟</b>\n\n"
        "اگر موردی نداری، بنویس «ندارم».",
        parse_mode=ParseMode.HTML,
    )
    return SKILLS


async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 300:
        await update.message.reply_text("پاسخ باید بین ۲ تا ۳۰۰ کاراکتر باشد.")
        return SKILLS

    context.user_data["skills"] = value
    await update.message.reply_text(
        "1️⃣2️⃣ <b>دوست داری چه فعالیت‌ها یا برنامه‌هایی در گروه برگزار بشه؟</b>",
        parse_mode=ParseMode.HTML,
    )
    return ACTIVITIES


async def get_activities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not 2 <= len(value) <= 300:
        await update.message.reply_text("پاسخ باید بین ۲ تا ۳۰۰ کاراکتر باشد.")
        return ACTIVITIES

    context.user_data["activities"] = value

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

    required = {
        "name",
        "nickname",
        "birth_date",
        "age",
        "job",
        "area",
        "interests",
        "redline",
        "personality",
        "goal",
        "about",
        "skills",
        "activities",
    }
    if not group_id or not required.issubset(context.user_data):
        await query.edit_message_text(
            "❌ اطلاعات فرم منقضی شده است.\n"
            "لطفاً دوباره از داخل گروه /intro را بزنید."
        )
        return ConversationHandler.END

    if INTRO_TOPIC_ID is None:
        await query.edit_message_text(
            "❌ تاپیک انتشار معارفه تنظیم نشده است.\n"
            "لطفاً از مدیر گروه بخواهید INTRO_TOPIC_ID را تنظیم کند."
        )
        return ConversationHandler.END

    try:
        member = await context.bot.get_chat_member(group_id, user.id)
        if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.BANNED}:
            await query.edit_message_text("❌ شما دیگر عضو گروه نیستید.")
            return ConversationHandler.END

        await context.bot.send_message(
            chat_id=group_id,
            message_thread_id=INTRO_TOPIC_ID,
            text=profile_text(context.user_data, user),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.exception("Failed to publish introduction: %s", exc)
        await query.edit_message_text(
            "❌ ارسال معرفی به تاپیک انجام نشد.\n"
            "شناسه تاپیک و دسترسی ربات برای ارسال پیام را بررسی کنید."
        )
        return ConversationHandler.END

    await query.edit_message_text("✅ معارفه شما با موفقیت داخل تاپیک منتشر شد.")
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
        "🔄 از اول شروع می‌کنیم.\n\n1️⃣ <b>اسمت چیه؟</b>",
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
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_date)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            REDLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_redline)],
            PERSONALITY: [
                CallbackQueryHandler(get_personality, pattern="^personality_")
            ],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_about)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
            ACTIVITIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_activities)],
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
    app.add_handler(CommandHandler("topicid", topic_id_command), group=0)
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
