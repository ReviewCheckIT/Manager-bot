import os
import logging
import asyncio
import threading
import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rapidfuzz.fuzz import token_set_ratio 
from flask import Flask

# --- CONFIGURATION ---

TOKEN = os.environ.get("BOT_TOKEN", "")

# এডমিন আইডি হ্যান্ডলিং
admin_ids_str = os.environ.get("ADMIN_IDS", "7870088579,7259050773")
try:
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]
except:
    ADMIN_IDS = [7870088579, 7259050773] 

GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "-1002337825231")

# --- FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Skyzone IT Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION DATA ---
bot_config = {
    "video_link": "https://www.youtube.com/", 
    "video_text": "আমাদের গ্রুপে স্বাগতম! আপনি নতুন মেম্বার তাই আগে পিন করা ভিডিওটি সম্পূর্ণ দেখুন।",
    "terms_text": """
⚠️ আপনাকে এই শর্তগুলো দেওয়া হল, মেনে চলতে হবে ⚠️

1️⃣ সাবধান: যে অ্যাপের জন্য টেক্সট তৈরি করা হবে, সেই অ্যাপেই রিভিউ দিতে হবে। ওই টেক্সট দিয়ে অন্য কোনো অ্যাপে রিভিউ দেওয়া যাবে না।

2️⃣ একবার সাবমিট: আপনি যে অ্যাপে কাজ সাবমিট করবেন, একবার করে ফেললে দ্বিতীয়বার আর সেই কাজ সাবমিট করবেন না।

3️⃣ সময় মেনে চলা: অ্যাপস যে সময় দেওয়া থাকবে, সেই সময় থেকেই কাজ শুরু করবেন।

4️⃣ একটি ফোন, একটি জিমেইল: আপনি যে অ্যাপে একবার রিভিউ দিবেন, একটি ফোন ও একটি জিমেইল দিয়ে। ওই অ্যাপে যে ফোন দিয়ে রিভিউ দিয়েছেন, সেই ফোন দিয়ে আর রিভিউ দেওয়া যাবে না। ওই অ্যাপে

5️⃣ নতুন মানুষ আনা: মনে রাখবেন, আপনি যেভাবে এখানে এসেছেন, ঠিক সেইভাবেই অন্যদেরও নিয়ে আসবেন।

6️⃣ সঠিক গ্রুপ এড: আপনার থেকে বেশি বোঝে এমন কাউকে গ্রুপে এড করবেন না।

7️⃣ পেমেন্ট স্ক্রিনশট: পেমেন্ট পাওয়ার পর পেমেন্টের স্ক্রিনশট গ্রুপে পোস্ট করতে হবে।

8️⃣ ভদ্র আচরণ: সবার সাথে ভালো ব্যবহার করবেন এবং যাদের নিয়ে আসবেন, তাদের সাথেও ভদ্র আচরণ করবেন।

9️⃣ ২৪ ঘণ্টা নিয়ম: আপনি যাদের দিয়ে রিভিউ করাবেন, তাদেরকে ২৪ ঘণ্টা পর গ্রুপে এড করতে হবে।

🔟 সমস্যা সমাধান: কোনো সমস্যা হলে ভিডিও দেখে সমাধান করবেন।
___
সতর্কবার্তা:

❌ আপনার নেটওয়ার্কের ভেতরে যেগুলো ডিভাইস থাকবে সেগুলো থেকে রিভিউ দিতে পারবেন না

❌ নির্ধারিত সময়ের আগে মার্কেটিং করা

❌ আগে থেকেই ওয়ার্কার ঠিক করে রাখা

❌ সাবমিট অপশন চালু হতেই সঙ্গে সঙ্গে সাবমিট করে ফেলা

❌একই লোকেশন থেকে একাধিক রিভিউ দেওয়া যাবে না, ফ্যামিলি এবং নিজের ফোন থেকে রিভিউ দেওয়া যাবে না❌

ফলাফল:
🚫 আপনার অ্যাকাউন্ট ব্যান হবে 

🚫 ব্যালেন্স ফ্রিজ করা হবে 

🚫 আর কখনো কাজ করতে পারবেন না

👉 তাই সাবধান থাকবেন।
অ্যাপসে যে সময় দেওয়া থাকবে, সেই সময় থেকে মার্কেটিং শুরু করবেন।
তারপর কোনো ওয়ার্কার যদি নক করে, তখনই কাজ শুরু ও সাবমিট করবেন।
শুধু যে কাজ দেওয়া হবে সেটাই সাবমিট করতে হবে।

⚠️ আগেভাগে মার্কেটিং বা লোক তৈরি করলে আপনার অ্যাকাউন্টও ব্যান হয়ে যাবে, ব্যালেন্স জিরো হয়ে যাবে।

💖 আমরা আপনাদের সব সময় ভালো চাই।
💡 মনে রাখবেন, এখানে কেউ আপনার কাছে টাকা চাবে না।
🌟 ভালো থাকবেন।

সকল শর্ত মেনে চললে আমাকে রিপ্লাই দিন "ইনশাআল্লাহ আমি পারবো" এটা লিখে

**মানলে হুবহু রিপ্লাই দিন:** "**ইনশাআল্লাহ আমি পারবো**"
""",
    "final_phrase": "ইনশাআল্লাহ আমি পারবো",
    "form_link": "https://forms.gle/TYdZFiFEJcrDcD2r5", 
    "admin_username": "@AfMdshakil" 
}

# --- QUESTIONS DB ---
questions_db = [
    {"id": 1, "q": "1️⃣ আপনি কি ভিডিওটি সম্পূর্ণ মনোযোগ দিয়ে দেখেছেন?", "a": ["hea", "ji", "yes", "ha", "সম্পূর্ণ ভিডিও দেখছি", "জি", "ho", "dekhsi"], "threshold": 70},
    {"id": 2, "q": "2️⃣ ভিডিও দেখে আপনি কী বুঝেছেন?", "a": ["Kivabe app use Korte hobe", "ভিডিওটি দেখে বুঝতে পারছি আমি যেভাবে এখানে আইসি সেভাবেই অন্যদেরকে নিয়ে আসতে হবে", "পরবর্তী", "শিখতে পারলাম", "marketing korbo", "apps review"], "threshold": 50},
    {"id": 3, "q": "3️⃣ আপনি কোন ফোন থেকে রিভিউ দেবেন?", "a": ["ami nijer phn theke review dibo na", "অন্যদের ফোন থেকে", "worker er phone", "user er phone"], "threshold": 60},
    {"id": 4, "q": "4️⃣ আপনি মোট কয়টি রিভিউ দিতে পারবেন?", "a": ["joto golo limit thakbe", "5 tar moto", "unlimited", "jotogula lagbe"], "threshold": 50},
    {"id": 5, "q": "5️⃣ আপনার কি অভিজ্ঞতা আছে, নাকি একদম নতুন?", "a": ["noton", "new", "অভিজ্ঞতা আছে", "আমি একদম নতুন", "নতুন"], "threshold": 60},
    {"id": 6, "q": "6️⃣ আপনি কোন সময়ে কাজ করতে স্বাচ্ছন্দ্যবোধ করবেন?", "a": ["any time", "jekono somoy", "shokal", "rat", "all time"], "threshold": 40},
    {"id": 7, "q": "7️⃣ আপনি কি নিয়মিত কাজ করতে পারবেন?", "a": ["hea", "ji", "yes", "ইনশাআল্লাহ পারবো", "চেষ্টা করব", "পারবো"], "threshold": 70},
    {"id": 8, "q": "8️⃣ সব নিয়ম ও শর্ত মেনে কাজ করতে পারবেন?", "a": ["hea", "ji", "yes", "parbo", "ইনশাআল্লাহ"], "threshold": 70},
    {"id": 9, "q": "9️⃣ ভিডিওতে বলা হয়েছে — সর্বনিম্ন কত টাকা হলে উত্তোলন করা যাবে?", "a": ["50", "panchas", "৫০", "৫০ টাকা"], "threshold": 90},
    {"id": 10, "q": "🔟 আপনি কীভাবে মার্কেটিং করতে চান? (সংক্ষেপে)", "a": ["Facebook", "social media", "ফেসবুক মার্কেটিং"], "threshold": 50}
]

USER_DATA = {}
S_IDLE, S_READY_CHECK, S_INTERVIEW, S_WAITING_PHRASE, S_FORM_FILLED = range(5)

# --- HELPERS ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

def check_answer_ai(user_text, expected_answers, threshold):
    best_score = 0
    if not user_text: return False
    for ans in expected_answers:
        score = token_set_ratio(user_text.lower(), ans.lower())
        if score > best_score: best_score = score
    return best_score >= threshold

# --- HANDLERS ---

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id: continue
        # গ্রুপে ট্যাগ করে স্বাগতম জানানো
        welcome_msg = (
            f"স্বাগতম {member.mention_html()}! 🎉\n\n"
            f"{bot_config['video_text']}\n"
            f"👉 <a href='{bot_config['video_link']}'>ভিডিওটি দেখতে এখানে ক্লিক করুন</a>\n\n"
            f"ভিডিও দেখা শেষ হলে কাজ শুরু করতে আমার ইনবক্সে গিয়ে <b>'IT'</b> লিখে মেসেজ দিন।"
        )
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text.strip() if update.message.text else ""
    chat_type = update.effective_chat.type
    uid = user.id

    if not msg: return

    # গ্রুপ মেসেজ লজিক
    if chat_type != 'private':
        triggers = ["it", "আমি নতুন", "কাজ কি", "কি কাজ", "ami new"]
        if any(t in msg.lower() for t in triggers):
            await update.message.reply_text(f"{user.mention_html()}, কাজের বিস্তারিত ও ইন্টারভিউ দিতে ইনবক্সে এসে 'IT' লিখুন।", parse_mode=ParseMode.HTML)
        return

    # ইনবক্স ইন্টারভিউ লজিক
    if uid not in USER_DATA: USER_DATA[uid] = {"state": S_IDLE, "answers": [], "q_idx": 0}
    state = USER_DATA[uid]["state"]

    if msg.upper() == 'IT':
        USER_DATA[uid] = {"state": S_READY_CHECK, "answers": [], "q_idx": 0}
        await update.message.reply_text("আপনি কি ১০টি প্রশ্নের উত্তর দিতে প্রস্তুত? (Yes/প্রস্তুত)")
        return

    if state == S_READY_CHECK:
        if any(x in msg.lower() for x in ["yes", "ready", "ha", "ji"]):
            USER_DATA[uid]["state"] = S_INTERVIEW
            await update.message.reply_text(questions_db[0]["q"])
        return

    if state == S_INTERVIEW:
        idx = USER_DATA[uid]["q_idx"]
        current_q = questions_db[idx]
        if check_answer_ai(msg, current_q['a'], current_q['threshold']):
            USER_DATA[uid]["answers"].append({"q": current_q['q'], "a": msg})
            if idx + 1 < len(questions_db):
                USER_DATA[uid]["q_idx"] += 1
                await update.message.reply_text(f"✅ সঠিক।\n\n{questions_db[idx+1]['q']}")
            else:
                USER_DATA[uid]["state"] = S_WAITING_PHRASE
                await update.message.reply_text(bot_config["terms_text"], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ উত্তর সঠিক হয়নি। আবার চেষ্টা করুন।")
        return

    if state == S_WAITING_PHRASE:
        if token_set_ratio(msg.lower(), bot_config['final_phrase'].lower()) > 90:
            USER_DATA[uid]["state"] = S_FORM_FILLED
            await update.message.reply_text(f"অভিনন্দন! ফর্মটি পূরণ করুন: <a href='{bot_config['form_link']}'>Form Link</a>\n\nপূরণ শেষে এখানে লিখুন: <b>Form Done</b>", parse_mode=ParseMode.HTML)
        return

    if state == S_FORM_FILLED:
        if "done" in msg.lower():
            report = f"📄 **SKYZONE IT REPORT**\n👤 User: {user.mention_html()}\n🆔 ID: <code>{uid}</code>\n✅ Status: Passed"
            for aid in ADMIN_IDS:
                try: await context.bot.send_message(chat_id=aid, text=f"📩 **নতুন মেম্বার পাস করেছে!**\n\n{report}", parse_mode=ParseMode.HTML)
                except: pass
            await update.message.reply_text(report, parse_mode=ParseMode.HTML)
            await update.message.reply_text(f"স্লিপটি কপি করে এডমিনকে পাঠান: {bot_config['admin_username']}", parse_mode=ParseMode.HTML)
            USER_DATA[uid]["state"] = S_IDLE
        return

# --- ADMIN COMMANDS ---

async def set_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if context.args:
        bot_config['video_link'] = context.args[0]
        await update.message.reply_text(f"✅ আপডেট হয়েছে: {context.args[0]}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(f"📊 ইউজার সংখ্যা: {len(USER_DATA)}")

# --- MAIN ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("setvideo", set_video))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
