# Telegram Intro Bot

ربات ساده معارفه برای گروه تلگرام، آماده استقرار روی Render.

## متغیر محیطی لازم
- `BOT_TOKEN`: توکن دریافتی از BotFather
- `INTRO_TOPIC_ID`: شناسه عددی تاپیکی که معارفه‌ها باید داخل آن منتشر شوند

## پیدا کردن شناسه تاپیک
1. ربات را اجرا کنید؛ خالی بودن موقت `INTRO_TOPIC_ID` مانع اجرای ربات نمی‌شود.
2. وارد تاپیک موردنظر شوید و دستور `/topicid` را بزنید.
3. عدد نمایش‌داده‌شده را در Render با نام `INTRO_TOPIC_ID` ذخیره کنید.
4. سرویس را دوباره Deploy کنید.

## روند استفاده
1. ربات را به گروه اضافه کنید.
2. در گروه `/intro` بزنید.
3. کاربر روی «ثبت معارفه» می‌زند.
4. فرم در خصوصی ربات تکمیل می‌شود.
5. پس از تأیید، معرفی داخل تاپیک تنظیم‌شده ارسال می‌شود.

## Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Environment Variables: `BOT_TOKEN` و `INTRO_TOPIC_ID`
- سرویس باید Web Service باشد.
