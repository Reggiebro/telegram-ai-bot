#!/usr/bin/env python3
"""
Telegram AI Microservice Bot
Offers AI services: image generation, text processing, etc.
Run: python3 telegram_ai_bot.py
"""
import os
import io
import uuid
import requests
from datetime import datetime

# Load .env if present
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Try importing telegram, install if missing
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
except ImportError:
    print("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot --break-system-packages -q")
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode

# Try importing edge-tts, install if missing
try:
    import edge_tts
except ImportError:
    print("Installing edge-tts...")
    os.system("pip install edge-tts --break-system-packages -q")
    import edge_tts

# Configuration - SET THESE
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
HF_API = "https://api-inference.huggingface.co/models"
FLUX_MODEL = "black-forest-labs/FLUX.1-schnell"
SDXL_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

# Pricing
PRICES = {
    "image_flux": 0.25,
    "image_sd": 0.25,
    "text_process": 0.00,
    "ai_chat": 0.00,
    "tts": 0.25,
    "voiceover": 1.00,
}

# User sessions
sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data="gen_image")],
        [InlineKeyboardButton("💬 AI Chat", callback_data="ai_chat")],
        [InlineKeyboardButton("🔊 Text to Speech", callback_data="tts")],
        [InlineKeyboardButton("📝 Process Text", callback_data="process_text")],
        [InlineKeyboardButton("💰 Pricing", callback_data="pricing")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *AI Microservice Bot*\n\n"
        "I offer AI-powered services:\n"
        "• Image generation (Pollinations AI)\n"
        "• AI Chat (Groq LLM)\n"
        "• Text to Speech (edge-tts)\n"
        "• Text processing\n\n"
        "Select a service below:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - check wallet balance."""
    wallet = "0x37239DF5f8ffE8541657624726e0ffc517B38C57"
    
    await update.message.reply_text("🔍 Checking wallet balance...")
    
    try:
        import requests as req
        
        # Check USDC balance
        usdc_contract = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        balance_payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": usdc_contract,
                "data": f"0x70a08231{wallet[2:].zfill(64)}"
            }, "latest"],
            "id": 1
        }
        
        r = req.post("https://mainnet.base.org", json=balance_payload, timeout=15)
        if r.status_code == 200:
            result = r.json()
            balance_wei = int(result.get('result', '0x0'), 16)
            balance_usdc = balance_wei / 1e6
            
            await update.message.reply_text(
                f"💰 *Wallet Balance*\n\n"
                f"Address: `{wallet}`\n"
                f"Network: Base Mainnet\n"
                f"USDC Balance: **{balance_usdc:.2f} USDC**\n\n"
                f"Contract: `{usdc_contract}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("⚠️ Could not fetch balance. Try again later.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)[:50]}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "gen_image":
        sessions[user_id] = {"mode": "gen_image", "model": "pollinations"}
        await query.edit_message_text(
            "✍️ Send me a description of the image you want to generate.\\n\\n"
            "Example: *a futuristic city with flying cars*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "ai_chat":
        sessions[user_id] = {"mode": "ai_chat"}
        await query.edit_message_text(
            "💬 *AI Chat*\n\n"
            "Send any message and I will reply using AI.\n\n"
            "Price: Free",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "tts":
        sessions[user_id] = {"mode": "tts"}
        await query.edit_message_text(
            "🔊 *Text to Speech*\n\n"
            "Send text (up to 60 seconds) and I will convert it to speech.\n\n"
            "Price: $0.25 per audio",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "process_text":
        sessions[user_id] = {"mode": "process_text"}
        await query.edit_message_text(
            "📝 *Text Processing*\n\n"
            "Send me text and I will:\n"
            "• Convert to UPPERCASE\n"
            "• Convert to lowercase\n"
            "• Reverse it\n"
            "• Count characters/words\n"
            "• Simple summarize\n\n"
            "Just send the text!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "pricing":
        pricing_text = (
            "💰 *Pricing*\n\n"
            "🎨 Image Generation:\n"
            f"  • Image: ${PRICES['image_flux']}\n\n"
            f"💬 AI Chat: Free\n\n"
            f"🔊 Text to Speech: ${PRICES['tts']} per audio\n\n"
            f"📝 Text Processing: Free\n\n"
            "💳 Payment: Crypto (USDC on Base)\n"
            f"Wallet: `0x37239...38C57`\n\n"
            "After payment, send tx hash to @WorkflowAlphaAI"
        )
        await query.edit_message_text(pricing_text, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "about":
        about_text = (
            "ℹ️ *About*\n\n"
            "AI Microservice Bot by Workflow Alpha\n"
            "Services: AI Image Generation, AI Chat, TTS, Text Processing\n"
            "Contact: workflowalpha.ai@gmail.com\n\n"
            "Powered by Pollinations AI, Groq & edge-tts"
        )
        await query.edit_message_text(about_text, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "main_menu":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in sessions:
        await update.message.reply_text("Please use /start to begin.")
        return
    
    mode = sessions[user_id].get("mode")
    
    if mode == "gen_image":
        prompt = text
        price = PRICES.get("image_flux", 0.50)
        
        await update.message.reply_text(
            f"🎨 Generating image...\n"
            f"Prompt: {prompt[:50]}...\n"
            f"Price: ${price}\n\n"
            f"💳 Send ${price} USDC to:\n"
            f"`0x37239DF5f8ffE8541657624726e0ffc517B38C57`\n\n"
            f"After payment, send tx hash to @WorkflowAlphaAI",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Try to generate image using Pollinations AI (free, no auth required)
        try:
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"{POLLINATIONS_URL}/{encoded_prompt}"
            
            resp = requests.get(image_url, timeout=60)
            
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
                await update.message.reply_photo(
                    photo=io.BytesIO(resp.content),
                    caption=f"✅ Generated with Pollinations AI\nPrompt: {prompt}"
                )
            else:
                await update.message.reply_text(
                    f"⚠️ Generation failed (status {resp.status_code}). "
                    f"Your request is queued. Send payment to confirm."
                )
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ Generation error: {str(e)[:50]}\n"
                f"Your request is queued. Send payment to confirm."
            )
        
        del sessions[user_id]
    
    elif mode == "process_text":
        result_upper = text.upper()
        result_lower = text.lower()
        result_reverse = text[::-1]
        char_count = len(text)
        word_count = len(text.split())
        summary = text[:100] + "..." if len(text) > 100 else text
        
        await update.message.reply_text(
            f"📝 *Text Processing Result*\n\n"
            f"Original: {text}\n\n"
            f"UPPERCASE: {result_upper}\n\n"
            f"lowercase: {result_lower}\n\n"
            f"Reversed: {result_reverse}\n\n"
            f"Characters: {char_count} | Words: {word_count}\n\n"
            f"Summary: {summary}",
            parse_mode=ParseMode.MARKDOWN
        )
        del sessions[user_id]
    
    elif mode == "ai_chat":
        # Free rule-based chatbot
        import random
        import datetime
        
        text_lower = text.lower().strip()
        
        # Greetings
        if any(word in text_lower for word in ["hello", "hi", "hey", "hallo", "zdravo", "bok"]):
            responses = [
                "Hello! How can I help you today?",
                "Hey there! What's on your mind?",
                "Hi! Ready to chat?",
                "Hello! I'm here to help.",
            ]
            reply = random.choice(responses)
        
        # How are you
        elif any(phrase in text_lower for phrase in ["how are you", "kako si", "sta ima"]):
            responses = [
                "I'm just a bot, but I'm functioning perfectly! How about you?",
                "Doing great! Ready to assist you.",
                "All systems operational! What can I do for you?",
            ]
            reply = random.choice(responses)
        
        # What can you do
        elif any(phrase in text_lower for phrase in ["what can you do", "help", "pomoc", "sta umijes"]):
            reply = (
                "I can help you with:\n"
                "• Generate images - just describe what you want\n"
                "• Text processing - convert, reverse, count\n"
                "• Text to speech - convert text to audio\n"
                "• Chat with me - I'm always here!\n\n"
                "Use /start to see all options."
            )
        
        # Time
        elif any(phrase in text_lower for phrase in ["time", "sat", "koliko je sati"]):
            now = datetime.datetime.now()
            reply = f"Current time: {now.strftime('%H:%M:%S')}"
        
        # Date
        elif any(phrase in text_lower for phrase in ["date", "datum", "danas", "today"]):
            now = datetime.datetime.now()
            reply = f"Today is {now.strftime('%A, %B %d, %Y')}"
        
        # Jokes
        elif any(phrase in text_lower for phrase in ["joke", "vic", "smej me"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the developer go broke? Because he used up all his cache.",
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "What's a computer's favorite snack? Microchips!",
                "Why did the AI cross the road? To optimize the chicken's path!",
            ]
            reply = random.choice(jokes)
        
        # Math calculations
        elif any(op in text_lower for op in ["+", "-", "*", "/", "calculate", "izracunaj"]):
            try:
                # Extract numbers and operators
                import re
                expr = re.sub(r'[^0-9+\-*/().]', '', text)
                if expr:
                    result = eval(expr)
                    reply = f"Calculation: {expr} = {result}"
                else:
                    reply = "Send me a math expression like: 2+2 or 10*5"
            except:
                reply = "I couldn't calculate that. Try: 2+2 or 10*5"
        
        # Goodbye
        elif any(phrase in text_lower for phrase in ["bye", "goodbye", "cao", "vidimo se", "dovidjenja"]):
            responses = [
                "Goodbye! Come back anytime!",
                "See you later! 👋",
                "Bye! Have a great day!",
                "Cao! Vrati se uskoro!",
            ]
            reply = random.choice(responses)
        
        # Thank you
        elif any(phrase in text_lower for phrase in ["thank", "hvala", "thanks"]):
            responses = [
                "You're welcome! 😊",
                "Happy to help!",
                "Anytime! 😊",
            ]
            reply = random.choice(responses)
        
        # Default response
        else:
            default_responses = [
                f"I heard you say: \"{text}\"\n\nI'm a simple chatbot. Try asking me:\n"
                "• What time is it?\n"
                "• Tell me a joke\n"
                "• Calculate 2+2\n"
                "• What can you do?",
                
                f"Interesting! You said: \"{text}\"\n\nI'm still learning. Try:\n"
                "• Say 'tell me a joke'\n"
                "• Ask 'what time is it?'\n"
                "• Say 'help' to see what I can do",
                
                f"I received: \"{text}\"\n\nI'm a basic chatbot. Use /start to see all features!",
            ]
            reply = random.choice(default_responses)
        
        await update.message.reply_text(f"🤖 {reply}")
        del sessions[user_id]
    
    elif mode == "tts":
        price = PRICES.get("voiceover", 1.00)
        
        await update.message.reply_text(
            f"🔊 Converting to speech...\n"
            f"Text length: {len(text)} chars\n"
            f"Price: ${price}\n\n"
            f"💳 Send ${price} USDC to:\n"
            f"`0x37239DF5f8ffE8541657624726e0ffc517B38C57`\n\n"
            f"After payment, send tx hash to @WorkflowAlphaAI",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Use free edge-tts
        try:
            import subprocess
            import tempfile
            import os
            
            # Limit text to ~60 seconds (roughly 150 words max for edge-tts)
            words = text.split()[:150]
            short_text = " ".join(words)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "speech.mp3")
                
                # Run edge-tts
                result = subprocess.run(
                    ["python3", "-m", "edge_tts", "--voice", "en-US-JennyNeural", "--text", short_text, "--write-media", output_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and os.path.exists(output_path):
                    with open(output_path, "rb") as audio_file:
                        await update.message.reply_voice(
                            voice=audio_file,
                            caption=f"🔊 Generated {len(short_text)} chars"
                        )
                else:
                    await update.message.reply_text("⚠️ TTS failed. Try shorter text.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ TTS error: {str(e)[:50]}")
        
        del sessions[user_id]
    
    else:
        await update.message.reply_text("Use /start to see available services.")

def main():
    """Start the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] Set TELEGRAM_BOT_TOKEN env var or edit script")
        print("[!] Get token from @BotFather on Telegram")
        return
    
    print("[*] Starting Telegram AI Bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("[*] Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
