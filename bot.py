import os
import asyncio
import logging
import threading
import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Token configuration
BOT_TOKEN = "8927253241:AAFaQO_zQQU5XeXNGHeA8acoX2LEkhp3haI"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI(title="MGTHANTIT Premium Cloud Engine")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🌐 Cobalt Premium API Handler (Bypass Cloud Blocks)
async def fetch_cobalt_api(payload: dict):
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://cobalt.tools"
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Cobalt API Status Error: {response.status_code}")
        except Exception as e:
            logger.error(f"Cobalt Connection Error: {str(e)}")
    return None

# ----------------- WEB PORTAL ENDPOINT -----------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>MGTHANTIT Multi-Downloader Cloud Server Core is Active 24/7!</h1>"

# ----------------- TELEGRAM BOT LOGIC -----------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📺 YouTube Download"), KeyboardButton("🎵 TikTok Download")],
         [KeyboardButton("📘 Facebook Download"), KeyboardButton("🔍 Music Mode (သီချင်းရှာ)")]],
        resize_keyboard=True
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in context.user_data:
        context.user_data[user_id].clear()
        
    await update.message.reply_text(
        "🚀 **MGTHANTIT Premium Ultra Downloader Core (24/7 Service)**\n\n"
        "အောက်ပါ Menu ခလုတ်များကို အသုံးပြုနိုင်သလို၊ မိမိ ဒေါင်းလုဒ်ဆွဲလိုသော ဗီဒီယိုလင့်ခ် (Link) ကိုလည်း တိုက်ရိုက် ပို့ပေးနိုင်ပါတယ်ဗျာ။ 👇\n\n"
        "👨‍💻 *Dev By: KHAING MIN THANT*",
        reply_markup=get_main_keyboard()
    )

async def handle_bot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Menu Buttons Interactions
    if text == "📺 YouTube Download":
        await update.message.reply_text("ဒေါင်းလုဒ်ဆွဲလိုသော **YouTube ဗီဒီယို သို့မဟုတ် Shorts လင့်ခ်** ကို ပို့ပေးပါခင်ဗျာ။")
        return
    elif text == "🎵 TikTok Download":
        await update.message.reply_text("ဒေါင်းလုဒ်ဆွဲလိုသော **TikTok ဗီဒီယိုလင့်ခ်** ကို ပို့ပေးပါခင်ဗျာ။")
        return
    elif text == "📘 Facebook Download":
        await update.message.reply_text("ဒေါင်းလုဒ်ဆွဲလိုသော **Facebook Reel သို့မဟုတ် Video လင့်ခ်** ကို ပို့ပေးပါခင်ဗျာ။")
        return
    elif text == "🔍 Music Mode (သီချင်းရှာ)":
        await update.message.reply_text("ဒေါင်းလုဒ်ဆွဲလိုသော **YouTube Music သို့မဟုတ် သီချင်းလင့်ခ်** ကို ပို့ပေးပါခင်ဗျာ။ (Audio သီးသန့် ထုတ်ပေးမည်ဖြစ်သည်)")
        return

    # URL Processing
    if text.startswith(("http://", "https://")):
        context.user_data[user_id] = {"link": text}
        url = text.lower()
        
        # 1. TikTok Router
        if "tiktok.com" in url:
            keyboard = [
                [InlineKeyboardButton("🚫 No Watermark (စာတန်းမပါ)", callback_data="tt_nowm")],
                [InlineKeyboardButton("🏷 With Watermark (စာတန်းပါ)", callback_data="tt_wm")],
                [InlineKeyboardButton("🎵 Audio Only (သီချင်းသီးသန့်)", callback_data="audio")]
            ]
            await update.message.reply_text("✨ **TikTok ဗီဒီယို တွေ့ရှိပါသည်!**\nWatermark ပါ/မပါ ရွေးချယ်ပေးပါရန်👇", reply_markup=InlineKeyboardMarkup(keyboard))
            
        # 2. YouTube Router
        elif "youtube.com" in url or "youtu.be" in url:
            keyboard = [
                [InlineKeyboardButton("🎵 MP3 Audio High Quality", callback_data="audio")],
                [InlineKeyboardButton("💎 4K Ultra HD", callback_data="yt_2160"), InlineKeyboardButton("✨ 1080p Full HD", callback_data="yt_1080")],
                [InlineKeyboardButton("📁 720p HD Quality", callback_data="yt_720"), InlineKeyboardButton("📁 360p Low Quality", callback_data="yt_360")]
            ]
            await update.message.reply_text("📺 **YouTube ဗီဒီယို တွေ့ရှိပါသည်!**\nဒေါင်းလုဒ်ဆွဲလိုသည့် ဗီဒီယို အရည်အသွေး (Resolution) ကို ရွေးချယ်ပါ👇", reply_markup=InlineKeyboardMarkup(keyboard))
            
        # 3. Facebook Router
        elif "facebook.com" in url or "fb.watch" in url:
            keyboard = [
                [InlineKeyboardButton("✨ High HD Quality", callback_data="fb_hd")],
                [InlineKeyboardButton("📁 Standard SD Quality", callback_data="fb_sd")],
                [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio")]
            ]
            await update.message.reply_text("📘 **Facebook ဗီဒီယို တွေ့ရှိပါသည်!**\nအလိုရှိရာ အရည်အသွေးကို ရွေးချယ်ပါ👇", reply_markup=InlineKeyboardMarkup(keyboard))
            
        # 4. Generic/Other Links Router
        else:
            keyboard = [
                [InlineKeyboardButton("🎬 Download Video", callback_data="generic_video")],
                [InlineKeyboardButton("🎵 Download Audio", callback_data="audio")]
            ]
            await update.message.reply_text("🔗 **လင့်ခ် ရရှိပါသည်!**\nဒေါင်းလုဒ် ပုံစံကို ရွေးချယ်ပါ👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    action = query.data
    
    user_info = context.user_data.get(user_id)
    if not user_info or "link" not in user_info:
        await query.edit_message_text("❌ သက်တမ်းကုန်ဆုံးသွားပါပြီ။ လင့်ခ်ကို ပြန်လည် ပို့ပေးပါရန်။")
        return
        
    video_url = user_info["link"]
    await query.edit_message_text("⚡ Cloud Server တွင် ဖိုင်စတင်ပြင်ဆင်နေပါပြီ... ခေတ္တစောင့်ပါ။")

    # API Payload Configuration mapping
    payload = {"url": video_url}
    
    if action == "audio":
        payload["isAudioOnly"] = True
    elif action == "tt_nowm":
        payload["isNoTTWatermark"] = True
    elif action == "tt_wm":
        payload["isNoTTWatermark"] = False
    elif action == "yt_2160":
        payload["vQuality"] = "2160"
    elif action == "yt_1080":
        payload["vQuality"] = "1080"
    elif action == "yt_720":
        payload["vQuality"] = "720"
    elif action == "yt_360":
        payload["vQuality"] = "360"
    elif action == "fb_hd":
        payload["vQuality"] = "max"
    elif action == "fb_sd":
        payload["vQuality"] = "720"

    # Fetch stream from API
    result = await fetch_cobalt_api(payload)
    
    if result and result.get("status") in ["stream", "picker", "redirect"]:
        stream_link = result.get("url")
        await query.edit_message_text("📥 ဆာဗာမှ တယ်လီဂရမ်သို့ တိုက်ရိုက် ပို့ဆောင်နေပါပြီ... ⏳")
        
        try:
            if action == "audio":
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=stream_link, caption="🎵 Audio By MGTHANTIT Downloader")
            else:
                await context.bot.send_video(chat_id=query.message.chat_id, video=stream_link, caption="🎬 Video By MGTHANTIT Downloader")
            await query.message.delete()
        except Exception as telegram_error:
            logger.error(f"Telegram Send Error: {str(telegram_error)}")
            await query.edit_message_text(f"🔗 ဗီဒီယိုအရွယ်အစားကြီး၍ တိုက်ရိုက်ပို့မရပါ။ ဤလင့်ခ်မှတစ်ဆင့် ဒေါင်းလုဒ်ဆွဲပါ- [တိုက်ရိုက်လင့်ခ်]({stream_link})", parse_mode="Markdown")
    else:
        error_msg = result.get("text", "Unknown API error") if result else "Connection Failure"
        logger.error(f"Download Engine Failed: {error_msg}")
        await query.edit_message_text("❌ ဒေါင်းလုဒ်ဆွဲ၍ မရနိုင်ပါ။ လင့်ခ်မှားနေခြင်း သို့မဟုတ် ဆာဗာ သက်တမ်းကုန်ခြင်း ဖြစ်နိုင်ပါသည်။")

# Background thread to run Bot Polling smoothly
def run_bot_polling():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_message))
    bot_app.add_handler(CallbackQueryHandler(bot_callback))
    
    logger.info("Ultimate Bot Engine started polling.")
    bot_app.run_polling(close_loop=False)

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=run_bot_polling, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
