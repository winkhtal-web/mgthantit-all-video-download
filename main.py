import os
import sys
import asyncio
import logging
import threading
import yt_dlp
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import uvicorn

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# မိမိ Bot Token ကို ဤနေရာတွင် သေချာစွာ ထည့်သွင်းပါ
BOT_TOKEN = "8927253241:AAFaQO_zQQU5XeXNGHeA8acoX2LEkhp3haI"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI(title="MGTHANTIT Premium Downloader")

# CORS Setup (Website နှင့် API ချိတ်ဆက်နိုင်ရန်)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- WEB API ENDPOINTS -----------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>MGTHANTIT Downloader Server is Running!</h1>"

@app.get("/api/download")
async def web_download_api(url: str, quality: str, background_tasks: BackgroundTasks):
    logger.info(f"Web Request -> URL: {url}, Quality: {quality}")
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/web_%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_check_certificates': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    if quality == "mp3":
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    elif quality == "4k":
        ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]'
    elif quality == "1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
    elif quality == "720p":
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
    else:
        ydl_opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]'

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        filepath = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        if quality == "mp3" and not os.path.exists(filepath):
            filepath = os.path.splitext(filepath)[0] + ".m4a"
        elif not os.path.exists(filepath):
            filepath = os.path.splitext(filepath)[0] + ".mp4"

        def remove_file(path):
            if os.path.exists(path): os.remove(path)
            
        background_tasks.add_task(remove_file, filepath)
        return FileResponse(filepath, media_type='application/octet-stream', filename=os.path.basename(filepath))
    except Exception as e:
        logger.error(f"Web Download Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- TELEGRAM BOT LOGIC -----------------
def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📺 YouTube Download"), KeyboardButton("🎵 TikTok Download")],
         [KeyboardButton("📘 Facebook Download"), KeyboardButton("🔍 Music Mode (သီချင်းရှာ)")]],
        resize_keyboard=True
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in context.user_data: context.user_data[user_id].clear()
    
    await update.message.reply_text(
        "🚀 **MGTHANTIT Premium Downloader Bot မှ ကြိုဆိုပါတယ်!**\n\n"
        "စာရိုက်ဘေးက Menu ခလုတ်များကို သုံးနိုင်သလို၊ ဒေါင်းလုဒ်ဆွဲလိုသော လင့်ခ်ကိုလည်း တိုက်ရိုက် ပို့ပေးနိုင်ပါတယ်ဗျာ။ 👇\n\n"
        "👨‍💻 *Admin: By MGTHANT*",
        reply_markup=get_main_reply_keyboard()
    )

async def handle_bot_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user_id = str(update.effective_user.id)

    if user_input.startswith(("http://", "https://")):
        if user_id not in context.user_data: context.user_data[user_id] = {}
        context.user_data[user_id]['link'] = user_input
        
        keyboard = [
            [InlineKeyboardButton("🎵 High-Speed MP3 Audio", callback_data="yt_mp3")],
            [InlineKeyboardButton("💎 4K Ultra HD", callback_data="yt_4k"), InlineKeyboardButton("✨ 1080p Full HD", callback_data="yt_1080p")],
            [InlineKeyboardButton("📁 720p HD", callback_data="yt_720p"), InlineKeyboardButton("📁 360p Low", callback_data="yt_360p")]
        ]
        await update.message.reply_text(
            "✅ **လင့်ခ်လက်ခံရရှိပါပြီ!**\n\nဒေါင်းလုဒ်ဆွဲလိုသည့် Quality ကို ရွေးချယ်ပေးပါရန်။ 👇", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def bot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = str(update.effective_user.id)
    
    if user_id not in context.user_data or 'link' not in context.user_data[user_id]:
        await query.edit_message_text("❌ သက်တမ်းကုန်ဆုံးသွားပါပြီ။ လင့်ခ်ပြန်ပို့ပေးပါ။")
        return
        
    url = context.user_data[user_id]['link']
    await query.edit_message_text("📥 ဆာဗာတွင် ဖိုင်စတင်ဆွဲနေပါပြီ... ခေတ္တစောင့်ပါ။")
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/bot_%(id)s.%(ext)s',
        'quiet': True,
        'no_check_certificates': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    
    if data == "yt_mp3": ydl_opts['format'] = 'bestaudio[ext=m4a]/best'
    elif data == "yt_4k": ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best'
    elif data == "yt_1080p": ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best'
    elif data == "yt_720p": ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best'
    else: ydl_opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best'

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        filename = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        if data == "yt_mp3" and not os.path.exists(filename): 
            filename = os.path.splitext(filename)[0] + ".m4a"
        elif not os.path.exists(filename): 
            filename = os.path.splitext(filename)[0] + ".mp4"
            
        with open(filename, 'rb') as f:
            if data == "yt_mp3":
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="🎵 By MGTHANTIT")
            else:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption="🎬 By MGTHANTIT")
        
        await query.message.delete()
        if os.path.exists(filename): os.remove(filename)
    except Exception as e:
        logger.error(f"Bot Error: {str(e)}")
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ ဒေါင်းလုဒ်ဆွဲ၍ မရနိုင်ပါ။")

# Bot ကို သီးသန့် Thread ဖြင့် အားအပြည့် မောင်းနှင်ခြင်း
def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_message))
    bot_app.add_handler(CallbackQueryHandler(bot_callback))
    
    logger.info("Telegram Bot is starting up on dedicated thread...")
    bot_app.run_polling(close_loop=False)

@app.on_event("startup")
async def startup_event():
    # FastAPI တက်လာတာနဲ့ Bot ကို Thread ခွဲပြီး နောက်ကွယ်မှာ အလုပ်လုပ်စေခြင်း
    t = threading.Thread(target=start_bot_thread, daemon=True)
    t.start()
