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

# আপনি চ্যাটে যে তথ্য দিয়েছেন তা এখানে ডিফল্ট হিসেবে রাখা হয়েছে
# তবে Render-এ Environment Variable সেট করা সবথেকে নিরাপদ।

TOKEN = os.environ.get("BOT_TOKEN", "")

# এডমিন আইডি হ্যান্ডলিং (স্ট্রং করা হয়েছে)
admin_ids_str = os.environ.get("ADMIN_IDS", "7870088579,7259050773")
try:
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]
except:
    ADMIN_IDS = [7870088579, 7259050773] # Fallback if error

GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "-1002337825231")

# --- FLASK SERVER (To Keep Bot Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Skyzone IT Bot is Running and Active!"

def run_flask():
    # পোর্ট এনভায়রনমেন্ট থেকে নিবে অথবা 10000 ব্যবহার করবে
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False জরুরি
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# httpx এর লগ কমানো হলো
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- GLOBAL VARIABLES & TEXTS ---
bot_config = {
    "video_link": "https://www.youtube.com/", 
    "video_text": "আমাদের গ্রুপে নতুন তাই ভিডিওটি সম্পূর্ণ দেখুন। ভিডিওটি দেখার শেষ হলে, এই বটটিতে গিয়ে 'IT' লিখে সকল প্রশ্নের উত্তর দিবেন।",
    "terms_text": """
⚠️ **আপনাকে এই শর্তগুলো দেওয়া হল, মেনে চলতে হবে** ⚠️

1️⃣ সাবধান: যে অ্যাপের জন্য টেক্সট তৈরি করা হবে, সেই অ্যাপেই রিভিউ দিতে হবে।
2️⃣ একবার সাবমিট: আপনি যে অ্যাপে কাজ সাবমিট করবেন, একবার করে ফেললে দ্বিতীয়বার আর সেই কাজ সাবমিট করবেন না।
3️⃣ সময় মেনে চলা: অ্যাপস যে সময় দেওয়া থাকবে, সেই সময় থেকেই কাজ শুরু করবেন।
4️⃣ একটি ফোন, একটি জিমেইল: আপনি যে অ্যাপে একবার রিভিউ দিবেন, একটি ফোন ও একটি জিমেইল দিয়ে।
5️⃣ নতুন মানুষ আনা: মনে রাখবেন, আপনি যেভাবে এখানে এসেছেন, ঠিক সেইভাবেই অন্যদেরও নিয়ে আসবেন।
6️⃣ সঠিক গ্রুপ এড: আপনার থেকে বেশি বোঝে এমন কাউকে গ্রুপে এড করবেন না।
7️⃣ পেমেন্ট স্ক্রিনশট: পেমেন্ট পাওয়ার পর পেমেন্টের স্ক্রিনশট গ্রুপে পোস্ট করতে হবে।
8️⃣ ভদ্র আচরণ: সবার সাথে ভালো ব্যবহার করবেন।
9️⃣ ২৪ ঘণ্টা নিয়ম: আপনি যাদের দিয়ে রিভিউ করাবেন, তাদেরকে ২৪ ঘণ্টা পর গ্রুপে এড করতে হবে।
🔟 সমস্যা সমাধান: কোনো সমস্যা হলে ভিডিও দেখে সমাধান করবেন।

**সতর্কবার্তা:**
❌ একই লোকেশন বা ফ্যামিলি ফোন থেকে রিভিউ দেওয়া যাবে না।
❌ নির্ধারিত সময়ের আগে মার্কেটিং করা যাবে না।

**ফলাফল:**
🚫 অ্যাকাউন্ট ব্যান ও ব্যালেন্স ফ্রিজ হবে।

**সকল শর্ত মেনে চললে আমাকে রিপ্লাই দিন:** "**ইনশাআল্লাহ আমি পারবো**"
— SKYZONE IT Admin™
""",
    "final_phrase": "ইনশাআল্লাহ আমি পারবো",
    "form_link": "https://forms.gle/TYdZFiFEJcrDcD2r5", 
    "admin_username": "@AfMdshakil" 
}

FORM_NOTICE_TEXT = f"""
⚡ **Official Notice – SKYZONE IT** ⚡
✅ উত্তর ও শর্ত সঠিক হয়েছে।
📋 এখন নিচের ফর্মটি পূরণ করুন:
🔗 <a href='{bot_config["form_link"]}'>Form Link👈</a>

📸 ফর্ম সাবমিট করে স্ক্রিনশট দিন।

⚠️ **নিয়মাবলী:**
1. একই লোকেশন/ফ্যামিলি থেকে একাধিক রিভিউ ❌
2. ভুল তথ্য একাধিক ❌

📩 — Skyzone IT | Admin
"""

# --- QUESTIONS DB ---
questions_db = [
    {"id": 1, "q": "1️⃣ আপনি কি ভিডিওটি সম্পূর্ণ মনোযোগ দিয়ে দেখেছেন?", "a": ["hea", "ji", "yes", "ha",  "সম্পূর্ণ ভিডিও দেখছি", "দেখছি", "জি", "ho", "dekhsi"], "threshold": 70},
    {"id": 2, "q": "2️⃣ ভিডিও দেখে আপনি কী বুঝেছেন?", "a": ["Kivabe app use Korte hobe", "ভিডিওটি দেখে বুঝতে পারছি আমি যেভাবে এখানে আইসি সেভাবেই অন্যদেরকে নিয়ে আসতে হবে", "পরবর্তী", "ভিডিও দেখে সকল কিছু শিখতে পারলাম", "Facebook e post kore user k telegram e aina", "review apnder app e submit dite hobe", "marketing korbo", "apps review"], "threshold": 50},
    {"id": 3, "q": "3️⃣ আপনি কোন ফোন থেকে রিভিউ দেবেন? (নিজের/পরিবারের ফোন ও একই লোকেশন নিষিদ্ধ)", "a": ["ami nijer phn theke review dibo na", "অন্যদের ফোন থেকে", "মার্কেটিং করে অন্যদের ফোন থেকে রিভিউ দেওয়াতে হবে", "review amr worker dibe", "worker er phone", "onno manush diye", "user er phone"], "threshold": 60},
    {"id": 4, "q": "4️⃣ আপনি মোট কয়টি রিভিউ দিতে পারবেন?", "a": ["joto golo limit thakbe", "5 tar moto", "ফেসবুক এবং টেলিগ্রামের বিভিন্ন গ্রুপ থেকে মেম্বার খুজে তাদের ফোন থেকে রিভিউ দেওয়াবো, এবং তাদের রিভিৎ এপ্রুভ হলে তাদেরকে গ্রুপে এড করে দিবো।", "অ্যাপে যে লিমিট দেওয়া থাকবে ওই অনুযায়ী দিতে পারব", "অ্যাপের নির্দেশনা অনুযায়ী দিতে পারব", "unlimited", "jotogula lagbe"], "threshold": 50},
    {"id": 5, "q": "5️⃣ আপনার কি আগে থেকে কোনো অভিজ্ঞতা আছে, নাকি একদম নতুন?", "a": ["noton", "new", "অভিজ্ঞতা আছে", "আমি একদম নতুন", "নতুন", "অভিজ্ঞতা আছে", "experience nai", "agerr oviggota ace"], "threshold": 60},
    {"id": 6, "q": "6️⃣ আপনি দিনে কোন সময়ে কাজ করতে স্বাচ্ছন্দ্যবোধ করবেন?", "a": ["user jeita bolbe", "নির্দিষ্ট সময় নাই", "অ্যাপে যে সময় দেওয়া থাকবে ওই সময় থেকে", "আপনারা যে সময় দিবেন ওই সময় থেকে", "jekono somoy", "shokal", "bikal", "rat", "all time"], "threshold": 40},
    {"id": 7, "q": "7️⃣ আপনি কি এই কাজগুলোর দায়িত্ব নিয়ে নিয়মিত করতে পারবেন?", "a": ["hea", "ji", "yes", "ইনশাআল্লাহ পারবো", "চেষ্টা করব", "ইনশাআল্লাহ", "অবশ্যই", "জি", "parbo"], "threshold": 80},
    {"id": 8, "q": "8️⃣ আমাদের সব নিয়ম ও শর্ত মেনে কাজ করতে পারবেন তো?", "a": ["hea", "ji", "yes", "parbo", "ইনশাআল্লাহ", "সব শর্ত মানব", "চেষ্টা করব", "ইনশাআল্লাহ চেষ্টা করব", "InshaAllah"], "threshold": 80},
    {"id": 9, "q": "9️⃣ ভিডিওতে বলা হয়েছে — সর্বনিম্ন কত টাকা হলে উত্তোলন করা যাবে?", "a": ["50", "panchas", "৫০", "৫০ টাকা", "সর্বনিম্ন ৫০ টাকা", "ponchash"], "threshold": 90},
    {"id": 10, "q": "🔟 আপনি কীভাবে মার্কেটিং করতে চান? (সংক্ষেপে)", "a": ["Facebook e post kore", "ফেসবুক মার্কেটিং করে", "ফেসবুক মার্কেটিং করে বিভিন্ন গ্রুপে পোস্ট করে", "userder sathe contect kore", "social media", "marketing kore"], "threshold": 50}
]

USER_DATA = {} 
S_IDLE, S_READY_CHECK, S_INTERVIEW, S_WAITING_PHRASE, S_FORM_FILLED = range(5)

# --- HELPER FUNCTIONS ---

def is_admin(user_id):
    """চেক করে ইউজার এডমিন কিনা"""
    return user_id in ADMIN_IDS

def check_answer_ai(user_text, expected_answers, threshold):
    """rapidfuzz ব্যবহার করে উত্তর যাচাই করে।"""
    best_score = 0
    if not user_text: return False
    
    for ans in expected_answers:
        score = token_set_ratio(user_text.lower(), ans.lower())
        if score > best_score:
            best_score = score
    return best_score >= threshold

# --- STARTUP NOTIFICATION ---
async def post_init(application: Application):
    """বট চালু হলে গ্রুপে মেসেজ পাঠাবে"""
    logger.info("Bot is starting up...")
    try:
        # গ্রুপ চ্যাট আইডি যদি স্ট্রিং হয়, ইনটিজারে কনভার্ট করার চেষ্টা
        chat_id = int(GROUP_CHAT_ID)
        await application.bot.send_message(
            chat_id=chat_id,
            text="🟢 **Skyzone IT Bot is Online!**\nSystem is ready to take interviews.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info("Startup message sent to group.")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

# --- BOT HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type

    if chat_type in ['group', 'supergroup']:
        # গ্রুপে কেউ /start দিলে কিছু হবে না
        pass
    else:
        await update.message.reply_text(
            f"হ্যালো {user.first_name} 👋\n\nআপনি যদি কাজ শুরু করতে চান, তাহলে গ্রুপের পিন করা ভিডিওটি দেখুন এবং এখানে **'IT'** লিখে মেসেজ দিন।"
        )

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        welcome_text = f"স্বাগতম {member.mention_html()}! 🎉\n\n{bot_config['video_text']}\n\n👉 <a href='{bot_config['video_link']}'>ভিডিওটি দেখতে এখানে ক্লিক করুন</a>"
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text.strip() if update.message.text else ""
    chat_type = update.effective_chat.type
    user_id = user.id

    if not msg: return

    # গ্রুপ লজিক - কেউ গ্রুপে IT লিখলে তাকে ইনবক্সে যেতে বলবে
    if chat_type in ['group', 'supergroup']:
        if msg.upper() == "IT":
            await update.message.reply_text(f"{user.mention_html()}, কাজের জন্য আমাকে ইনবক্সে (Private Message) 'IT' লিখুন। এখানে নয়।", parse_mode=ParseMode.HTML)
        return

    # প্রাইভেট চ্যাট লজিক
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"state": S_IDLE, "answers": [], "q_index": 0}

    state = USER_DATA[user_id]["state"]

    # 1. কাজের শুরু (Trigger: IT)
    if msg.upper() == 'IT':
        if state == S_FORM_FILLED:
             await update.message.reply_text("আপনি ইতিমধ্যেই সকল ধাপ সম্পন্ন করেছেন। স্লিপ পেতে যেকোনো কিছু লিখে রিপ্লাই দিন, যেমন: 'Slip Din'.")
             return

        USER_DATA[user_id] = {"state": S_READY_CHECK, "answers": [], "q_index": 0}
        await update.message.reply_text("আপনি কি ১০টি প্রশ্নের উত্তর দিতে প্রস্তুত?\n(উত্তর দিন: Yes / Ready / প্রস্তুত)")
        return

    # 2. রেডি চেক
    if state == S_READY_CHECK:
        if any(word in msg.lower() for word in ['yes', 'ready', 'ha', 'hea', 'ji', 'prostut', 'start']):
            USER_DATA[user_id]["state"] = S_INTERVIEW
            USER_DATA[user_id]["q_index"] = 0
            q_data = questions_db[0]
            await update.message.reply_text(f"চমৎকার! শুরু করছি।\n\n{q_data['q']}")
        else:
            await update.message.reply_text("আপনি প্রস্তুত হলে 'Yes' বা 'Ready' লিখুন। অন্যথায় ভিডিওটি আবার দেখুন।")
        return

    # 3. ইন্টারভিউ চলাকালীন
    if state == S_INTERVIEW:
        idx = USER_DATA[user_id]["q_index"]
        if idx >= len(questions_db):
             USER_DATA[user_id]["state"] = S_WAITING_PHRASE
             await update.message.reply_text(f"আপনার প্রশ্ন শেষ।\n{bot_config['terms_text']}")
             return

        current_q = questions_db[idx]
        is_correct = check_answer_ai(msg, current_q['a'], current_q['threshold'])
        
        if is_correct:
            USER_DATA[user_id]["answers"].append({"q": current_q['q'], "a": msg})
            next_idx = idx + 1
            if next_idx < len(questions_db):
                USER_DATA[user_id]["q_index"] = next_idx
                await update.message.reply_text(f"✅ সঠিক উত্তর!\n\n{questions_db[next_idx]['q']}")
            else:
                USER_DATA[user_id]["state"] = S_WAITING_PHRASE
                await update.message.reply_text(f"অভিনন্দন! আপনি ১০টি প্রশ্নের সঠিক উত্তর দিয়েছেন। 🎉\n{bot_config['terms_text']}")
        else:
            await update.message.reply_text("❌ আপনার উত্তর সঠিক নয়। ভিডিওটি ভালো করে দেখে থাকলে আবার চেষ্টা করুন।\n(সঠিক উত্তর দিয়ে আবার মেসেজ দিন)")
        return

    # 4. শর্ত ও ফর্ম নোটিশ পর্যায়
    if state == S_WAITING_PHRASE:
        if token_set_ratio(msg.lower(), bot_config['final_phrase'].lower()) > 90:
            USER_DATA[user_id]["state"] = S_FORM_FILLED
            await update.message.reply_text(FORM_NOTICE_TEXT, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            await update.message.reply_text("ফর্ম পূরণ শেষে এখানে এসে লিখুন: **'Form Done'** বা **'Slip Din'**")
        else:
            await update.message.reply_text(f"বাক্যটি সঠিক হয়নি। হুবহু লিখুন:\n`{bot_config['final_phrase']}`", parse_mode=ParseMode.MARKDOWN)
        return

    # 5. স্লিপ জেনারেশন পর্যায় (✅ স্লিপ শুধুমাত্র এই শেষ স্টেজে দেওয়া হবে)
    if state == S_FORM_FILLED:
        if any(word in msg.lower() for word in ['form done', 'slip din', 'dan', 'din', 'dakhaw']):
            answers = USER_DATA[user_id]["answers"]
            
            # --- মেসেজ ১: স্লিপ তৈরি (এখানে স্লিপের কন্টেন্ট থাকবে) ---
            slip_text = f"📄 **SKYZONE IT - RECRUITMENT SLIP**\n"
            slip_text += f"User: {user.mention_html()} (ID: <code>{user_id}</code>)\n" 
            slip_text += f"Status: Passed ✅\n\n"
            for ans in answers:
                q_short = ans['q'].split(' ')[0] 
                slip_text += f"**{q_short}** {ans['a']}\n"
            
            await update.message.reply_text(slip_text, parse_mode=ParseMode.HTML) 

            # --- মেসেজ ২: এডমিনকে যোগাযোগের নির্দেশিকা (পরের মেসেজ) ---
            admin_instruction = f"""
✅ **অভিনন্দন!**

আপনার স্লিপটি কপি করুন এবং অ্যাপ ও কাজ নেওয়ার জন্য এখনই এডমিনকে পাঠান।

👉 এডমিন: <a href='https://t.me/{bot_config['admin_username'].lstrip('@')}'>{bot_config['admin_username']}</a>
"""
            await update.message.reply_text(admin_instruction, parse_mode=ParseMode.HTML) 

        else:
             await update.message.reply_text("ফর্ম পূরণ করে থাকলে স্লিপ পেতে যেকোনো কিছু লিখে রিপ্লাই দিন, যেমন: 'Slip Din'.")
        return

    if state == S_IDLE:
        await update.message.reply_text("আপনি যদি কাজ করতে চান, ভিডিওটি দেখে **'IT'** লিখুন। অন্য কোনো মেসেজ গ্রহণ করা হবে না।")

# --- ADMIN COMMANDS ---

async def set_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ আপনি এডমিন নন।")
        return
    
    if context.args:
        new_link = context.args[0]
        bot_config['video_link'] = new_link
        await update.message.reply_text(f"✅ ভিডিও লিংক আপডেট করা হয়েছে:\n{new_link}")
    else:
        await update.message.reply_text("ব্যবহারবিধি: `/setvideo https://youtu.be/xxxx`", parse_mode=ParseMode.MARKDOWN)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    total_users = len(USER_DATA)
    passed_users = sum(1 for u in USER_DATA.values() if u['state'] == S_FORM_FILLED)
    await update.message.reply_text(
        f"📊 **User Statistics:**\nTotal Interactions: {total_users}\nPassed Exam: {passed_users}", 
        parse_mode=ParseMode.MARKDOWN
    )

# --- MAIN FUNCTION ---
def main():
    if not TOKEN:
        logger.error("Error: BOT_TOKEN is missing.")
        return

    # Flask Thread (Daemon)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Telegram App with Timeout Settings (To prevent silent crashes)
    try:
        application = (
            Application.builder()
            .token(TOKEN)
            .post_init(post_init) # বট চালু হলে গ্রুপে মেসেজ যাবে
            .read_timeout(30) # নেটওয়ার্ক স্লো হলে অপেক্ষা করবে
            .write_timeout(30)
            .build()
        )
    except Exception as e:
        logger.error(f"Error initializing Application: {e}")
        return

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setvideo", set_video))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram Bot is starting polling...")
    
    # Polling with Error Handling
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES, 
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Critical Error in polling: {e}")

if __name__ == "__main__":
    main()
