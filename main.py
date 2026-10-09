import telebot
import time
import secrets
import os
from flask import Flask, request, jsonify
from threading import Thread
import io
import qrcode
import random

# 🟢 CONFIGURATION BLOCK
BOT_TOKEN = "8963839676:AAGoxcbB_izx8FH8Qg_2FyOrbcgZe1hBzr0"
ADMIN_ID = 8393210427
YOUR_UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# 🟢 GLOBAL DATA STORAGES
active_amounts = {}  # Format: {"chat_id": {"amount": 2.02, "timestamp": 169684000}}
pending_claims = {}  # Format: {2.02: {"chat_id": 123, "token": "xyz", "timestamp": 169684000}}

# 🟢 PERMANENT MEDIA STORAGE DATA STRUCTURE (No Touch)
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

# 🟢 UPI QR CODE GENERATOR PIPELINE
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

# 🟢 UNIQUE DYNAMIC SELECTION PIPELINE (99 Slots Engine)
def get_unique_amount(base_amount, chat_id):
    current_time = time.time()
    
    # Session Timeout: 10 minute purane system slots auto-release karne ke liye
    expired_amounts = [amt for amt, data in list(pending_claims.items()) if current_time - data.get("timestamp", 0) > 600]
    for amt in expired_amounts:
        c_id = pending_claims[amt]["chat_id"]
        if c_id in active_amounts: del active_amounts[c_id]
        del pending_claims[amt]

    if chat_id in active_amounts:
        return active_amounts[chat_id]["amount"]
        
    for _ in range(100):
        paise_variant = round(base_amount + (random.randint(1, 99) / 100), 2)
        if paise_variant not in pending_claims:
            active_amounts[chat_id] = {"amount": paise_variant, "timestamp": current_time}
            return paise_variant
            
    return base_amount

# 🌐 FLASK WEBHOOK: Multi-Line Flexible Text Matching System (100% Fixed Auto-Verify)
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
                # Multi-line aur text formats se clean decimal digit (e.g. 1.83) extract karne ka master pattern
                amount_match = re.search(r'(?:received|rs\.?|inr|rupees|\b)\s*(\d+\.\d{2})', text, re.IGNORECASE)
                
                if not amount_match:
                    amount_match = re.search(r'(?:received|rs\.?|inr|rupees|\b)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)

                if amount_match:
                    raw_amount = float(amount_match.group(1))
                    formatted_amount_str = "{:.2f}".format(raw_amount)
                    print(f"🎯 100% Cleaned Target Amount String: {formatted_amount_str}")
                    
                    matched_key_amount = None
                    for active_amt in list(pending_claims.keys()):
                        if "{:.2f}".format(active_amt) == formatted_amount_str:
                            matched_key_amount = active_amt
                            break
                    
                    if matched_key_amount:
                        claim_data = pending_claims[matched_key_amount]
                        user_chat_id = claim_data["chat_id"]
                        user_token = claim_data["token"]
                        
                        # Direct Media Delivery Block Pipeline Trigger
                        try:
                            deliver_media(user_chat_id, user_token)
                        except Exception as dev_err:
                            print(f"Delivery runtime operational fault: {dev_err}")
                        
                        # 🟢 PURE USER CHAT PAR INSTANT SUCCESS MESSAGE
                        success_text = f"✅ *Payment Success!*\n\nAapke ₹{formatted_amount_str} receive ho gaye hain. Media upar deliver kar diya gaya hai."
                        bot.send_message(user_chat_id, success_text, parse_mode="Markdown")
                        
                        # Admin Confirmation Dashboard Alert
                        bot.send_message(ADMIN_ID, f"🤖 *Auto-Verified:* Amount ₹{formatted_amount_str} se user `{user_chat_id}` ko delivery completed.")
                        
                        # System memory clean up layers
                        active_amounts.pop(user_chat_id, None)
                        pending_claims.pop(matched_key_amount, None)
                    else:
                        print(f"⚠ System Log: ₹{formatted_amount_str} ke liye koi active pending session nahi mila.")
            except Exception as bg_e:
                print(f"❌ Webhook Background Processing Core Exception: {bg_e}")

        Thread(target=process_payment, args=(notification_text,)).start()
    except Exception as e:
        print(f"Webhook Main Thread Exception Event: {e}")
        
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "Skybox Bot is Running Online on Render!"

def run():
    # 🟢 FIX FOR RENDER: Dynamic Port Binding Mechanism
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🟢 ADMIN DEBUG SYSTEM: Photo/Video bhejne par instant copy-paste JSON block dega (No Touch)
@bot.message_handler(content_types=['photo', 'video'])
def handle_docs(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
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

# 🟢 LINK GENERATOR COMMAND FOR ADMIN
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

# 🟢 USER LINK CHECKOUT SYSTEM (Cleaned Premium Look)
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
                
                # Dynamic Unique Price Variant allocate karna (.01 se .99 ke beech)
                final_amount = get_unique_amount(base_amount, chat_id)
                
                # System storage me tracking params save karna
                pending_claims[final_amount] = {"chat_id": chat_id, "token": token, "timestamp": time.time()}
                
                qr_img = generate_upi_qr(YOUR_UPI_ID, final_amount)
                
                # Cleaned Caption Text: Customer ko darane wale text aur UTR note saaf kar diye hain
                caption_text = (
                    f"✨ *SkyBox Instant Checkout:*\n\n"
                    f"💰 Pay Exact Amount: *₹{final_amount}*\n"
                    f"📌 UPI ID: `{YOUR_UPI_ID}`\n\n"
                    f"⚠️ *Important Note:*\n"
                    f"Aapko QR scan karke exact *₹{final_amount}* hi pay karna hai (Ek bhi paisa kam ya zyada mat karna) taaki aapka payment instantly verify ho sake."
                )
                
                # 🟢 BACKUP SYSTEM BUTTON: Admin manual verification ke liye button jod diya hai
                markup = telebot.types.InlineKeyboardMarkup()
                backup_btn = telebot.types.InlineKeyboardButton("📥 Payment Done (Verify)", callback_data=f"adm_req_{final_amount}")
                markup.add(backup_btn)
                
                bot.send_photo(chat_id, qr_img, caption=caption_text, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Link invalid hai.")
        else:
            bot.reply_to(message, "👋 Welcome to Skybox Bot!")
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

# 🟢 ADMIN FUNCTIONAL MANUAL BACKUP CALLBACK HANDLER
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def handle_admin_verification(call):
    try:
        action_parts = call.data.split("_")
        action = action_parts[1]  # 'req', 'app', ya 'rej'
        
        # 1. User ne jab "Payment Done" par click kiya (Manual Backup Alert for Admin)
        if action == "req":
            amount = float(action_parts[2])
            chat_id = call.message.chat.id
            
            bot.answer_callback_query(call.id, "⏳ Check kiya ja raha hai, thoda wait karein...")
            bot.send_message(chat_id, "⏳ *Admin aapka payment check kar rahe hain, kripya 1 minute ka wait karein...*", parse_mode="Markdown")
            
            # Admin Verification Control Dashboard Control Buttons
            admin_markup = telebot.types.InlineKeyboardMarkup()
            approve_btn = telebot.types.InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app_{amount}_{chat_id}")
            reject_btn = telebot.types.InlineKeyboardButton("❌ Reject Claim", callback_data=f"adm_rej_{amount}_{chat_id}")
            admin_markup.row(approve_btn, reject_btn)
            
            admin_caption = (
                f"🔔 *Manual Alert: New Backup Request!*\n\n"
                f"👤 *User:* {call.from_user.first_name} (`{chat_id}`)\n"
                f"💰 *Expected Amount:* ₹{amount}\n\n"
                f"📎 *Action:* Agar app notification miss ho gaya hai toh verify karke manually Approve karein."
            )
            bot.send_message(ADMIN_ID, admin_caption, parse_mode="Markdown", reply_markup=admin_markup)
            return

        # Security Check: Buttons par sirf asli Admin hi click kar sakta hai
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Aap admin nahi ho!", show_alert=True)
            return

        amount = float(action_parts[2])
        target_user_chat_id = int(action_parts[3])

        if amount in pending_claims:
            claim_data = pending_claims[amount]
            user_token = claim_data["token"]

            if action == "app":
                # Manual override media execution pipeline
                deliver_media(target_user_chat_id, user_token)
                bot.send_message(target_user_chat_id, f"✅ *Payment Approved Manually by Admin!*\n\nAapke ₹{amount} verify ho gaye hain. Media upar deliver kar diya gaya hai.", parse_mode="Markdown")
                bot.edit_message_text(f"✅ *Approved ₹{amount}!* User `{target_user_chat_id}` ko media deliver kar diya gaya.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, "✅ Approved successfully!")
                
            elif action == "rej":
                bot.send_message(target_user_chat_id, "❌ *Payment Rejected!*\n\nAdmin ne aapka verification request reject kar diya hai. Kripya sahi se pay karke support se sampark karein.", parse_mode="Markdown")
                bot.edit_message_text(f"❌ *Rejected ₹{amount}* for user `{target_user_chat_id}`.", call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, "❌ Request declined.")

            # Memory allocation cleanup
            active_amounts.pop(target_user_chat_id, None)
            pending_claims.pop(amount, None)
        else:
            bot.answer_callback_query(call.id, "⚠ Yeh request pehle hi process ho chuki hai ya expire ho gayi.", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    except Exception as e:
        print(f"Admin Callback Operational Error: {e}")

# 🟢 CORE MEDIA DELIVERY PIPELINE (Aapka original mechanism bina kisi touch ke)
def deliver_media(chat_id, token):
    try:
        media_data = {}
        if token in saved_links:
            media_data = saved_links[token]
        else:
            if "a22f0e8295ff" in saved_links:
                media_data = saved_links["a22f0e8295ff"]

        # Photos loops execution
        for photo_id in media_data.get("photos", []):
            try:
                bot.send_photo(chat_id, photo_id)
                time.sleep(1)
            except Exception as e:
                print(f"Photo delivery failed: {e}")

        # Videos loops execution
        for video_id in media_data.get("videos", []):
            try:
                bot.send_video(chat_id, video_id)
                time.sleep(1)
            except Exception as e:
                print(f"Video delivery failed: {e}")
                
    except Exception as main_e:
        print(f"Global Delivery Error: {main_e}")

# 🟢 MAIN RUNNING ENGINE CONTROL LOOP (Render Stability Fixes)
if __name__ == '__main__':
    try:
        # Flask continuous web server launch mapping thread
        keep_alive()
        print("🤖 Skybox Pro Automation Bot has been safely launched on Render...")
        
        # Long polling configuration to prevent timeout crashes
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"🔴 Main Loop System Error: {e}")
