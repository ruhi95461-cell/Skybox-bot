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
active_amounts = {}  # Format: {"chat_id": {"amount": 2.02, "timestamp": 169684000}}
pending_claims = {}  # Format: {2.02: {"chat_id": 123, "token": "xyz", "timestamp": 169684000}}

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

import random

def get_unique_amount(base_amount, chat_id):
    current_time = time.time()
    
    # 10 minute se purane pending slots ko free karne ke liye
    expired_amounts = [amt for amt, data in list(pending_claims.items()) if current_time - data.get("timestamp", 0) > 600]
    for amt in expired_amounts:
        c_id = pending_claims[amt]["chat_id"]
        if c_id in active_amounts: 
            del active_amounts[c_id]
        del pending_claims[amt]

    if chat_id in active_amounts:
        return active_amounts[chat_id]["amount"]
        
    for _ in range(100):
        paise_variant = round(base_amount + (random.randint(1, 99) / 100), 2)
        if paise_variant not in pending_claims:
            active_amounts[chat_id] = {"amount": paise_variant, "timestamp": current_time}
            return paise_variant
            
    return base_amount

# 🌐 FLASK WEBHOOK: Crash-Proof Dynamic Verification Logic
@app.route('/webhook', methods=['POST'])
def receive_notification():
    try:
        data = request.json
        if not data: 
            return jsonify({"status": "success"}), 200
            
        notification_text = data.get("text", "")
        print(f"📥 BharatPe Push Received: {notification_text}")
        
        def process_payment(text):
            try:
                import re
                # Notification text se strict numeric amount badalna
                amount_match = re.search(r'(?:Rs\.?|INR|Rupees|\b)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)

                if amount_match:
                    raw_amount = float(amount_match.group(1))
                    formatted_amount_str = "{:.2f}".format(raw_amount)
                    print(f"🎯 Filtered Notification Amount: {formatted_amount_str}")
                    
                    matched_key_amount = None
                    for active_amt in list(pending_claims.keys()):
                        if "{:.2f}".format(active_amt) == formatted_amount_str:
                            matched_key_amount = active_amt
                            break
                    
                    if matched_key_amount:
                        claim_data = pending_claims[matched_key_amount]
                        user_chat_id = claim_data["chat_id"]
                        user_token = claim_data["token"]
                        
                        # Direct safety backup execution to prevent missing key crash
                        try:
                            deliver_media(user_chat_id, user_token)
                        except Exception as dev_err:
                            print(f"Delivery fallback error: {dev_err}")
                        
                        # 🟢 PURE USER CHAT PE INSTANT SUCCESS MESSAGE
                        success_msg = f"✅ *Payment Success!*\n\nAapke ₹{formatted_amount_str} receive ho gaye hain. Media upar deliver kar diya gaya hai."
                        bot.send_message(user_chat_id, success_msg, parse_mode="Markdown")
                        
                        # Admin Confirmation Alert
                        bot.send_message(ADMIN_ID, f"🤖 *Auto-Verified:* Amount ₹{formatted_amount_str} se user `{user_chat_id}` ko delivery completed.")
                        
                        # 🟢 SAFE CLEANUP BLOCK: System parameters reset bina kisi data error ke
                        active_amounts.pop(user_chat_id, None)
                        pending_claims.pop(matched_key_amount, None)
                    else:
                        print(f"⚠ System Log: ₹{formatted_amount_str} ke liye active user claim nahi mila.")
            except Exception as bg_e:
                print(f"❌ Background Process Exception: {bg_e}")

        Thread(target=process_payment, args=(notification_text,)).start()
    except Exception as e:
        print(f"Webhook Main Thread Error: {e}")
        
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

# 🟢 1. USER LINK CHECKOUT SYSTEM (Line 164 block replacement)
@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        args = message.text.split()
        text_args = args[1] if len(args) > 1 else ""
        chat_id = message.chat.id
        
        if text_args.startswith("resell_"):
            token = text_args.replace("resell_", "").strip()
            if token in saved_links:
                base_amount = saved_links[token]["amount"]
                
                # Dynamic Unique Price Variant uthana (.01 se .99 ke beech)
                final_amount = get_unique_amount(base_amount, chat_id)
                
                # System me entry block karna tracking ke liye
                pending_claims[final_amount] = {"chat_id": chat_id, "token": token, "timestamp": time.time()}
                
                qr_img = generate_upi_qr(YOUR_UPI_ID, final_amount)
                
                caption_text = (
                    f"✨ *SkyBox Instant Checkout:*\n\n"
                    f"💰 Pay Exact Amount: *₹{final_amount}*\n"
                    f"📌 UPI ID: `{YOUR_UPI_ID}`\n\n"
                    f"⚠️ *Mandatory Instruction:*\n"
                    f"Aapko QR scan karke exact *₹{final_amount}* hi pay karna hai (Ek bhi paisa kam ya zyada mat karna, warna automation block ho jayega).\n\n"
                    f"🤖 *Note:* UTR submit karne ka koi jhanjhat nahi hai, payment hote hi bot 2 second me media automatic bhej dega!"
                )
                
                bot.send_photo(chat_id, qr_img, caption=caption_text, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Link invalid hai.")
        else:
            bot.reply_to(message, "👋 Welcome to Skybox Bot!")
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

# 🟢 2. NEW ADMIN CALLBACK FOR DYNAMIC AMOUNT (Purane sub_ aur adm_ wale blocks ki jagah)
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_verification(call):
    try:
        if call.from_user.id != ADMIN_ID: 
            return
        action_parts = call.data.split("_")
        amount = float(action_parts[2])
        
        if amount in pending_claims:
            claim_data = pending_claims[amount]
            deliver_media(claim_data["chat_id"], claim_data["token"])
            bot.send_message(claim_data["chat_id"], "✅ *Payment Approved Manually by Admin!*", parse_mode="Markdown")
            bot.edit_message_text(f"✅ Approved ₹{amount}", call.message.chat.id, call.message.message_id)
            if claim_data["chat_id"] in active_amounts: 
                del active_amounts[claim_data["chat_id"]]
            del pending_claims[amount]
    except Exception as e:
        print(f"Admin Action Error: {e}")

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
