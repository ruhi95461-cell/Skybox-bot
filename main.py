import telebot
import time
import secrets
import os  # 🟢 Render ke PORT ke liye zaroori hai
from flask import Flask, request, jsonify
from threading import Thread
import io
import qrcode

# Token aur ID details
BOT_TOKEN = "8963839676:AAGoxcbB_izx8FH8Qg_2FyOrbcgZe1hBzr0"
ADMIN_ID = 8393210427
YOUR_UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Memory Storage for tracking payments and pending user requests
received_payments = {}  # Format: {"UTR_NUMBER": amount}
pending_claims = {}     # Format: {"UTR_NUMBER": {"chat_id": 123, "token": "xyz"}}

# Permanent Links Storage (Line 27 Fixed Comma Error)
saved_links = {
    "a22f0e8295ff": {
        "amount": 1.0,
        "photos": [
            "AgACAgUAAxkBAAIE8mrH-hLUr52qEEAaT2hHIyHA3j43AAJpEWsbLNxBVgiUcJneb6qvAQADAgADeQADPQQ",
            "AgACAgUAAxkBAAIE82rH-hLQsA9vJzBtH-b7vygRlhrtAAJoEWsbLNxBVsKuxQJbbktfAQADAgADeQADPQQ"
        ],
        "videos": []
    },
}

# UPI QR Code Generator
def generate_upi_qr(upi_id, amount):
    upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr
    
# 🌐 FLASK WEBHOOK: Android App Se Payment Notification Receive Karne Ke Liye
@app.route('/webhook', methods=['POST'])
def receive_notification():
    try:
        data = request.json  # App se JSON data aayega
        if not data:
            return jsonify({"status": "success"}), 200  # App ko shaant rakhne ke liye
            
        notification_text = data.get("text", "")
        
        # Background process ke liye alag function chalayenge taaki delay na ho
        def process_payment(text):
            try:
                import re
                # Optimized Regex: Yeh Rupees, Rs, INR aur direct digits sab handle karega
                utr_match = re.search(r'\b\d{12}\b', text)
                
                # BharatPe specific text "Received 1.00 Rupees" ko bhi match karega
                amount_match = re.search(r'(?:Rs\.?|INR|Rupees|\b)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                
                if utr_match:
                    utr = utr_match.group(0)
                    amount = float(amount_match.group(1)) if amount_match else 0.0
                    
                    # Payment ko local database me save karlo
                    received_payments[utr] = amount
                    
                    # System Check: Offline Auto-Verification
                    if utr in pending_claims:
                        claim_data = pending_claims[utr]
                        deliver_media(claim_data["chat_id"], claim_data["token"])
                        bot.send_message(claim_data["chat_id"], "✅ *Payment Auto-Verified!* Aapka media deliver kar diya gaya hai.", parse_mode="Markdown")
                        bot.send_message(ADMIN_ID, f"🤖 *Auto-Verified:* UTR `{utr}` ka payment app se verify karke user ko deliver kar diya gaya.")
                        del pending_claims[utr]
            except Exception as bg_e:
                print(f"Background Processing Error: {bg_e}")

        # Thread ka use karke process ko background mein daal do
        Thread(target=process_payment, args=(notification_text,)).start()

    except Exception as e:
        print(f"Webhook Main Error: {e}")
        
    # App ko hamesha 200 status code hi bhejna hai
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "Skybox Bot is Running Online on Render!"

def run():
    # 🟢 FIX FOR RENDER: Render port dynamic allocate karta hai, isliye os.environ use kiya
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🟢 UPDATED DEBUG SYSTEM: Photo/Video bhejne par instant copy-paste JSON block dega
@bot.message_handler(content_types=['photo', 'video'])
def handle_docs(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            # Sabse highest quality ki photo ki File ID nikalna
            file_id = message.photo[-1].file_id
            
            # Aapko direct copy-paste format dene ke liye response text
            reply_text = (
                f"📸 *PHOTO FILE ID DETECTED!*\n\n"
                f"`{file_id}`\n\n"
                f"📝 *GitHub JSON code me aise jodein:*\n"
                f'`"{file_id}",`'
            )
            bot.reply_to(message, reply_text, parse_mode="Markdown")
            
        elif message.content_type == 'video':
            file_id = message.video.file_id
            
            reply_text = (
                f"🎥 *VIDEO FILE ID DETECTED!*\n\n"
                f"`{file_id}`\n\n"
                f"📝 *GitHub JSON code me aise jodein:*\n"
                f'`"{file_id}",`'
            )
            bot.reply_to(message, reply_text, parse_mode="Markdown")

# Link Generator Command
@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Sahi format: `/gen <amount>`", parse_mode="Markdown")
        return
        
    try:
        amount = round(float(args[1]), 2)
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount!", parse_mode="Markdown")
        return
        
    for token, data in saved_links.items():
        if isinstance(data, dict) and data.get("amount") == amount:
            old_link = f"https://t.me/{BOT_USERNAME}?start=resell_{token}"
            bot.reply_to(message, f"⚠ ₹{amount} ka link pehle se bana hai:\n`{old_link}`", parse_mode="Markdown")
            return
            
    unique_token = secrets.token_hex(6)
    saved_links[unique_token] = {"amount": amount, "photos": [], "videos": []}
    
    link = f"https://t.me/{BOT_USERNAME}?start=resell_{unique_token}"
    bot.reply_to(message, f"✅ *Link Generated:*\n\n`{link}`", parse_mode="Markdown")

# User Checkout (/start)
@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        args = message.text.split()
        text_args = args[1] if len(args) > 1 else ""
        
        if text_args.startswith("resell_"):
            token = text_args.replace("resell_", "").strip()
            if token in saved_links:
                amount = saved_links[token]["amount"]
                qr_img = generate_upi_qr(YOUR_UPI_ID, amount)
                
                caption_text = (
                    f"Pay ₹{amount} for the item\n\n📌 UPI ID — {YOUR_UPI_ID}\n\n"
                    f"⚠️ Instructions:\n1. QR Code scan karke exact ₹{amount} pay karein.\n"
                    f"2. Pay karke Submit UTR par click karein aur 12-digit UTR bhejein."
                )
                
                markup = telebot.types.InlineKeyboardMarkup()
                btn = telebot.types.InlineKeyboardButton("📥 Submit UTR", callback_data=f"sub_{amount}_{token}")
                markup.add(btn)
                bot.send_photo(message.chat.id, qr_img, caption=caption_text, reply_markup=markup)
            else:
                bot.reply_to(message, "❌ Yeh link invalid hai.")
        else:
            bot.reply_to(message, "👋 Welcome to Skybox Bot!")
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

# Callback for UTR Submission Trigger
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def trigger_utr_input(call):
    try:
        data_parts = call.data.split("_", 2)
        amount = data_parts[1]
        token = data_parts[2]
        msg = bot.send_message(call.message.chat.id, "✍ *Ab apna 12-digit ka UTR number yahan type karke bhejein:*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_utr, amount, token)
    except Exception as e:
        print(f"Callback Error: {e}")

# Core Logic: Manual Control + App Auto Backup Verification
def process_utr(message, amount, token):
    try:
        utr = message.text.strip()
        if len(utr) != 12 or not utr.isdigit():
            bot.reply_to(message, "❌ *Galt UTR!* 12-digit ka number sahi se bhejein.", parse_mode="Markdown")
            return

        chat_id = message.chat.id
        
        # 1. PEHLE CHECK KARO: Kya Android App ne ye UTR pehle hi fetch kar liya hai?
        if utr in received_payments:
            bot.reply_to(message, "✅ *Payment Verified via System!* Delivery shuru...", parse_mode="Markdown")
            deliver_media(chat_id, token)
            del received_payments[utr]
            return

        # 2. AGAR APP SE NAHI MILA: Toh isko Pending list me daalo aur Admin ko alert karo
        pending_claims[utr] = {"chat_id": chat_id, "token": token}
        bot.reply_to(message, "⏳ *Aapka UTR check kiya ja raha hai...* Admin ke response ya app auto-verification ka wait karein.", parse_mode="Markdown")

        # Admin Verification Keyboard
        admin_markup = telebot.types.InlineKeyboardMarkup()
        approve_btn = telebot.types.InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app_{utr}")
        reject_btn = telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{utr}")
        admin_markup.row(approve_btn, reject_btn)

        admin_caption = f"""🔔 *Manual Alert: New Payment Claim!*

👤 *User:* {message.from_user.first_name} (`{chat_id}`)
💰 *Expected Amount:* ₹{amount}
🧾 *Submitted UTR:* `{utr}`

*Action:* Agar aap online hain toh check karke manually Approve karein, warna phone app notification aate hi ye khud verify ho jayega."""
        
        bot.send_message(ADMIN_ID, admin_caption, parse_mode="Markdown", reply_markup=admin_markup)
            
    except Exception as e:
        bot.reply_to(message, f"❌ UTR Process Error: {str(e)}")

# Admin Manual Click Actions Handler (FIXED DATA CLEAR & PARSING)
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_decision(call):
    try:
        action_parts = call.data.split("_")
        action = action_parts[1]
        utr = action_parts[2]

        if utr not in pending_claims:
            bot.answer_callback_query(call.id, "⚠ Yeh request pehle hi process ho chuki hai (Ya expired).")
            return

        user_chat_id = pending_claims[utr]["chat_id"]
        user_token = pending_claims[utr]["token"]

        if action == "app":
            bot.send_message(user_chat_id, "✅ *Payment Successful!* Admin ne aapki request approve kar di hai. Media deliver ho raha hai:", parse_mode="Markdown")
            deliver_media(user_chat_id, user_token)
            bot.edit_message_text(f"✅ Aapne UTR `{utr}` ko manually *Approve* kar diya.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        elif action == "rej":
            bot.send_message(user_chat_id, "❌ *Payment Rejected!* Aapka UTR admin dwara decline kar diya gaya hai.", parse_mode="Markdown")
            bot.edit_message_text(f"❌ Aapne UTR `{utr}` ko *Reject* kar diya.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
        # Safe memory cleanup dono condition ke baad
        del pending_claims[utr]

    except Exception as e:
        print(f"Admin Callback Error: {e}")

# Media delivery execution helper function with Smart Fallback Mechanism
def deliver_media(chat_id, token):
    try:
        media_data = {}
        # 1. Check if token maps directly to data package
        if token in saved_links:
            media_data = saved_links[token]
        else:
            # 2. Smart Match Fallback: Agar token custom string hai, to use hardcoded asset pack pe bypass karo
            if "a22f0e8295ff" in saved_links:
                media_data = saved_links["a22f0e8295ff"]

        # Photos sending mechanism loop
        for photo_id in media_data.get("photos", []):
            try:
                bot.send_photo(chat_id, photo_id)
                time.sleep(1)
            except Exception as e:
                print(f"Photo delivery failed: {e}")

        # Videos sending mechanism loop
        for video_id in media_data.get("videos", []):
            try:
                bot.send_video(chat_id, video_id)
                time.sleep(1)
            except Exception as e:
                print(f"Video delivery failed: {e}")
                
    except Exception as main_e:
        print(f"Global Delivery Error: {main_e}")

# Main Execution Control Loop
if __name__ == '__main__':
    try:
        # Flask server ko background thread me chalana
        keep_alive()
        print("🤖 Skybox Bot is launching now on Render...")
        
        # Telegram bot polling start karna bina crash huye
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"🔴 Main Loop Error: {e}")
