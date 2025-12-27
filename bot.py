import os
import logging
import asyncio
import threading
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rapidfuzz.fuzz import token_set_ratio
from flask import Flask

# --- CONFIGURATION ---
TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "7870088579,7259050773")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "-1002337825231")

try:
    ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip().isdigit()]
except:
    ADMIN_IDS = [7870088579, 7259050773]

# --- FLASK SERVER (Keep-Alive) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Skyzone IT Bot is Running and Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL VARIABLES & TEXTS ---
BOT_CONFIG = {
    "video_link": "https://www.youtube.com/",
    "video_text": "আমাদের গ্রুপে নতুন তাই ভিডিওটি সম্পূর্ণ দেখুন। ভিডিওটি দেখার শেষ হলে, এই বটটিতে গিয়ে 'IT' লিখে সকল প্রশ্নের উত্তর দিবেন।",
    "terms_text": """ ⚠️ **আপনাকে এই শর্তগুলো দেওয়া হল, মেনে চলতে হবে** ⚠️ 

1️⃣ সাবধান: যে অ্যাপের জন্য টেক্সট তৈরি করা হবে, সেই অ্যাপেই রিভিউ দিতে হবে। 
2️⃣ একবার সাবমিট: আপনি যে অ্যাপে কাজ সাবমিট করবেন, একবার করে ফেললে দ্বিতীয়বার আর সেই কাজ সাবমিট করবেন না। 
3️⃣ সময় মেনে চলা: অ্যাপস যে সময় দেওয়া থাকবে, সেই সময় থেকেই কাজ শুরু করবেন। 
4️⃣ একটি ফোন, একটি জিমেইল: আপনি যে অ্যাপে একবার রিভিউ দিবেন, একটি ফোন ও একটি জিমেইল দিয়ে। 
5️⃣ নতুন মানুষ আনা: মনে রাখবেন, আপনি যেভাবে এখানে এসেছে, ঠিক সেইভাবেই অন্যদেরও নিয়ে আসবেন। 
6️⃣ সঠিক গ্রুপ এড: আপনার থেকে বেশি বোঝে এমন কাউকে গ্রুপে এড করবেন না। 
7️⃣ পেমেন্ট স্ক্রিনশট: পেমেন্ট পাওয়ার পর পেমেন্টের স্ক্রিনশট গ্রুপে পোস্ট করতে হবে। 
8️⃣ ভদ্র আচরণ: সবার সাথে ভালো ব্যবহার করবেন। 
9️⃣ ২৪ ঘণ্টা নিয়ম: আপনি যাদের দিয়ে রিভিউ করাবেন, তাদেরকে ২৪ ঘণ্টা পর গ্রুপে এড করতে হবে। 
🔟 সমস্যা সমাধান: কোনো সমস্যা হলে ভিডিও দেখে সমাধান করবেন। 

**সতর্কবার্তা:** ❌ একই লোকেশন বা ফ্যামিলি ফোন থেকে রিভিউ দেওয়া যাবে না। 
❌ নির্ধারিত সময়ের আগে মার্কেটিং করা যাবে না। 

**ফলাফল:** 🚫 অ্যাকাউন্ট ব্যান ও ব্যালেন্স ফ্রিজ হবে। 

**সকল শর্ত মেনে চললে আমাকে রিপ্লাই দিন:** "**ইনশাআল্লাহ আমি পারবো**" 
— SKYZONE IT Admin™ """,
    "final_phrase": "ইনশাআল্লাহ আমি পারবো",
    "form_link": "https://forms.gle/TYdZFiFEJcrDcD2r5",
}

# নতুন ইউজারদের জন্য গ্রুপ কি-ওয়ার্ড
TRIGGER_KEYWORDS = [
    "আমি নতুন", "কিভাবে কাজ করতে হবে", "কাজ কি", "কি কাজ", 
    "আমি আপনাদের গ্রুপে নতুন", "আমাকে কাজ শিখিয়ে দিন", 
    "এডমিন আপনি আমাকে কাজ বুঝিয়ে দিন",
    "ami notun", "Ami new", "iT"
]

# --- QUESTIONS DB (হুবহু আগের উত্তরসহ) ---
QUESTIONS_DB = [
    {"id": 1, "q": "1️⃣ আপনি কি ভিডিওটি সম্পূর্ণ মনোযোগ দিয়ে দেখেছেন?", "a": ["hea", "ji", "yes", "ha", "সম্পূর্ণ ভিডিও দেখছি", "দেখছি", "জি", "ho", "dekhsi"], "threshold": 70},
    {"id": 2, "q": "2️⃣ ভিডিও দেখে আপনি কী বুঝেছেন?", "a": ["Kivabe app use Korte hobe", "ভিডিওটি দেখে বুঝতে পারছি আমি যেভাবে এখানে আইসি সেভাবেই অন্যদেরকে নিয়ে আসতে হবে", "পরবর্তী", "ভিডিও দেখে সকল কিছু শিখতে পারলাম", "Facebook e post kore user k telegram e aina", "review apnder app e submit dite hobe", "marketing korbo", "apps review"], "threshold": 50},
    {"id": 3, "q": "3️⃣ আপনি কোন ফোন থেকে রিভিউ দেবেন? (নিজের/পরিবারের ফোন ও একই লোকেশন নিষিদ্ধ)", "a": ["ami nijer phn theke review dibo na", "অন্যদের ফোন থেকে", "মার্কেটিং করে অন্যদের ফোন থেকে রিভিউ দেওয়াতে হবে", "review amr worker dibe", "worker er phone", "onno manush diye", "user er phone"], "threshold": 60},
    {"id": 4, "q": "4️⃣ আপনি মোট কয়টি রিভিউ দিতে পারবেন?", "a": ["joto golo limit thakbe", "5 tar moto", "অ্যাপে যে লিমিট দেওয়া থাকবে ওই অনুযায়ী দিতে পারব", "অ্যাপের নির্দেশনা অনুযায়ী দিতে পারব", "unlimited", "jotogula lagbe"], "threshold": 50},
    {"id": 5, "q": "5️⃣ আপনার কি আগে থেকে কোনো অভিজ্ঞতা আছে, নাকি একদম নতুন?", "a": ["noton", "new", "অভিজ্ঞতা আছে", "আমি একদম নতুন", "নতুন", "অভিজ্ঞতা আছে", "experience nai", "agerr oviggota ace"], "threshold": 60},
    {"id": 6, "q": "6️⃣ আপনি দিনে কোন সময়ে কাজ করতে স্বাচ্ছন্দ্যবোধ করবেন?", "a": ["user jeita bolbe", "নির্দিষ্ট সময় নাই", "অ্যাপে যে সময় দেওয়া থাকবে ওই সময় থেকে", "আপনারা যে সময় দিবেন ওই সময় থেকে", "jekono somoy", "shokal", "bikal", "rat", "all time"], "threshold": 40},
    {"id": 7, "q": "7️⃣ আপনি কি এই কাজগুলোর দায়িত্ব নিয়ে নিয়মিত করতে পারবেন?", "a": ["hea", "ji", "yes", "ইনশাআল্লাহ পারবো", "চেষ্টা করব", "ইনশাআল্লাহ", "অবশ্যই", "জি", "parbo"], "threshold": 80},
    {"id": 8, "q": "8️⃣ আমাদের সব নিয়ম ও শর্ত মেনে কাজ করতে পারবেন তো?", "a": ["hea", "ji", "yes", "parbo", "ইনশাআল্লাহ", "সব শর্ত মানব", "চেষ্টা করব", "ইনশাআল্লাহ চেষ্টা করব", "InshaAllah"], "threshold": 80},
    {"id": 9, "q": "9️⃣ ভিডিওতে বলা হয়েছে — সর্বনিম্ন কত টাকা হলে উত্তোলন করা যাবে?", "a": ["50", "panchas", "৫০", "৫০ টাকা", "সর্বনিম্ন ৫০ টাকা", "ponchash"], "threshold": 90},
    {"id": 10, "q": "🔟 আপনি কীভাবে মার্কেটিং করতে চান? (সংক্ষেপে)", "a": ["Facebook e post kore", "ফেসবুক মার্কেটিং করে", "ফেসবুক মার্কেটিং করে বিভিন্ন গ্রুপে পোস্ট করে", "ফেসবুক গ্রুপে পোস্ট করে", "userder sathe contect kore", "social media", "marketing kore"], "threshold": 50}
]

USER_DATA = {}
S_IDLE, S_READY_CHECK, S_INTERVIEW, S_WAITING_PHRASE, S_FORM_FILLED = range(5)

# --- HELPER FUNCTIONS ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

def check_answer_ai(user_text, expected_answers, threshold):
    best_score = 0
    if not user_text: return False
    for ans in expected_answers:
        score = token_set_ratio(user_text.lower(), ans.lower())
        if score > best_score: best_score = score
    return best_score >= threshold

# --- BOT HANDLERS ---
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id: continue
        welcome = f"স্বাগতম {member.mention_html()}! 🎉\n\n{BOT_CONFIG['video_text']}\n\n👉 <a href='{BOT_CONFIG['video_link']}'>ভিডিওটি দেখতে এখানে ক্লিক করুন</a>"
        await update.message.reply_text(welcome, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text.strip() if update.message.text else ""
    chat_type = update.effective_chat.type
    user_id = user.id

    # ১. গ্রুপ চ্যাট লজিক (নতুন ইউজারদের জন্য)
    if chat_type in ['group', 'supergroup']:
        # এডমিন মেসেজ করলে বট ডিস্টার্ব করবে না
        if is_admin(user_id): return
        
        # নির্দিষ্ট কি-ওয়ার্ড বা 'IT' লিখলে রেসপন্স করবে
        match = any(token_set_ratio(msg.lower(), key.lower()) > 85 for key in TRIGGER_KEYWORDS)
        if match or msg.upper() == "IT":
            await update.message.reply_text(f"{user.mention_html()}, আপনি ভিডিওটি দেখে আমাকে ইনবক্স করুন। ইনবক্সে 'IT' লিখুন।", parse_mode=ParseMode.HTML)
            try:
                await context.bot.send_message(chat_id=user_id, text=f"হ্যালো! আপনি গ্রুপে কাজ জানতে চেয়েছেন। দয়া করে এই ভিডিওটি দেখুন: {BOT_CONFIG['video_link']}\nভিডিও দেখা শেষ হলে এখানে 'IT' লিখে মেসেজ দিন।")
            except: pass
        return

    # ২. প্রাইভেট চ্যাট লজিক
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"state": S_IDLE, "answers": [], "q_index": 0}
    
    state = USER_DATA[user_id]["state"]

    if msg.upper() == 'IT':
        USER_DATA[user_id] = {"state": S_READY_CHECK, "answers": [], "q_index": 0}
        await update.message.reply_text("আপনি কি ১০টি প্রশ্নের উত্তর দিতে প্রস্তুত? (Ready/Yes লিখুন)")
        return

    if state == S_READY_CHECK:
        if any(w in msg.lower() for w in ['yes', 'ready', 'ha', 'ji', 'start']):
            USER_DATA[user_id]["state"] = S_INTERVIEW
            await update.message.reply_text(f"শুরু করছি।\n\n{QUESTIONS_DB[0]['q']}")
        return

    if state == S_INTERVIEW:
        idx = USER_DATA[user_id]["q_index"]
        current_q = QUESTIONS_DB[idx]
        if check_answer_ai(msg, current_q['a'], current_q['threshold']):
            USER_DATA[user_id]["answers"].append({"q": current_q['q'], "a": msg})
            next_idx = idx + 1
            if next_idx < len(QUESTIONS_DB):
                USER_DATA[user_id]["q_index"] = next_idx
                await update.message.reply_text(f"✅ সঠিক উত্তর!\n\n{QUESTIONS_DB[next_idx]['q']}")
            else:
                USER_DATA[user_id]["state"] = S_WAITING_PHRASE
                await update.message.reply_text(BOT_CONFIG['terms_text'], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ আপনার উত্তর সঠিক নয়। ভিডিওটি ভালো করে দেখে থাকলে আবার চেষ্টা করুন।")
        return

    if state == S_WAITING_PHRASE:
        if token_set_ratio(msg.lower(), BOT_CONFIG['final_phrase'].lower()) > 90:
            USER_DATA[user_id]["state"] = S_FORM_FILLED
            notice = f"✅ উত্তর ও শর্ত সঠিক হয়েছে।\n📋 এখন নিচের ফর্মটি পূরণ করুন:\n🔗 <a href='{BOT_CONFIG['form_link']}'>Form Link👈</a>\n📸 ফর্ম সাবমিট করে এখানে এসে 'Slip' লিখুন।"
            await update.message.reply_text(notice, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return

    if state == S_FORM_FILLED:
        if any(w in msg.lower() for w in ['slip', 'done', 'din', 'form done']):
            admin_list_str = ", ".join([str(aid) for aid in ADMIN_IDS])
            slip_text = f"📄 **SKYZONE IT - RECRUITMENT SLIP**\n"
            slip_text += f"User: {user.mention_html()} (ID: <code>{user_id}</code>)\n"
            slip_text += f"Status: Passed ✅\n\n"
            for ans in USER_DATA[user_id]["answers"]:
                q_num = ans['q'].split(' ')[0]
                slip_text += f"**{q_num}** {ans['a']}\n"
            slip_text += f"\n--------------------------\n👑 Admin IDs: {admin_list_str}\n"
            
            # ইউজারকে স্লিপ পাঠানো
            await update.message.reply_text(slip_text, parse_mode=ParseMode.HTML)
            
            # এডমিনদের কাছে স্লিপ পাঠানো (Mandatory)
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=f"📥 **New User Slip Received:**\n\n{slip_text}", parse_mode=ParseMode.HTML)
                except: pass
        return

def main():
    if not TOKEN: return
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
