import telebot
import time
import secrets
import os
import qrcode
import io
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================================
# 📦 STEP 1: CONFIGURATION & CONFIG BLOCK
# =====================================================================
# 🚨 SECURITY: Apne token ko secure rakhne ke liye yahan naya token dalein
BOT_TOKEN = "8963839676:AAHGTnd6QcysW9DrCUMQrnW8xRf52J-wBe8" 
ADMIN_ID = 8393210427
UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask('')

# =====================================================================
# 📦 STEP 2: REGISTER CACHES & PERMANENT DATABASE
# =====================================================================
processed_utrs = set()  # Active UTR cache memory to prevent spam

# 💡 LIFETIME PERMANENT DATABASE: Apne saare permanent links/products yahan niche add karein
saved_links = {
    "499d7f1d0638": {
        "amount": 1.00,
        "photos": [
            "AgACAgUAAxkBAAIFcWrKXiNhwiP3gTNbHj7oyr2d0KnjAALhE2sbjdVRVtfSc0J0EVRKAQADAgADeQADPQQ"
            "AgACAgUAAxkBAAIFcmrKXiMh_avg8qH18-xsUGpxC3JvAALiE2sbjdVRVolwvKa3ahTFAQADAgADeQADPQQ"
        ],
        "videos": [
            "BAACAgUAAxkBAAIFdWrKXj6JrQ2eMVyDKXFQPLNC8g4FAAI6IQACjdVRVgX9YrqjKeJIPQQ"
        ]
    }
}

# =====================================================================
# 📦 STEP 3: HELPER FUNCTIONS & WEB SERVER FOR RENDER
# =====================================================================
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

@app.route('/')
def home():
    return "Skybox Bot is Running Online on Render!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================================================================
# 📦 STEP 4: TELEGRAM ADMIN COMMANDS & HANDLERS
# =====================================================================

# --- FILE ID EXTRACTOR FOR ADMIN (Photos/Videos Engine) ---
@bot.message_handler(content_types=['photo', 'video'])
def get_file_id_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.reply_to(message, f"📸 *Photo File ID Detected:*\n\n`{file_id}`\n\nIse aap code ke upar `saved_links` mein manually paste kar sakte hain.", parse_mode="Markdown")
        elif message.content_type == 'video':
            file_id = message.video.file_id
            bot.reply_to(message, f"🎥 *Video File ID Detected:*\n\n`{file_id}`\n\nIse aap code ke upar `saved_links` mein manually paste kar sakte hain.", parse_mode="Markdown")

# --- TEMPORARY LINK GENERATOR COMMAND (/gen <amount>) ---
@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ *Sahi format use karein:* `/gen <amount>`", parse_mode="Markdown")
        return
        
    try:
        amount = round(float(args[1]), 2)
    except ValueError:
        bot.reply_to(message, "❌ *Invalid amount!*", parse_mode="Markdown")
        return
        
    unique_token = secrets.token_hex(6)
    
    # Upar wale permanent token se media safe-copy karne ka logic (Crash proof)
    base_token = "b22fe08295ff"
    default_photos = saved_links[base_token]["photos"] if base_token in saved_links else []
    default_videos = saved_links[base_token]["videos"] if base_token in saved_links else []
    
    saved_links[unique_token] = {
        "amount": amount,
        "photos": default_photos, 
        "videos": default_videos
    }
    
    link = f"https://t.me/{BOT_USERNAME}?start={unique_token}"
    bot.reply_to(message, f"🎯 *New Temporary Link Generated for ₹{amount}:*\n`{link}`\n\n⚠️ *Note:* Yeh link Render restart hone tak hi active rahega.", parse_mode="Markdown")

# =====================================================================
# 📦 STEP 5: USER CHECKOUT & FLOW PIPELINE
# =====================================================================

# --- USER CHECKOUT SYSTEM ---
@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        chat_id = message.chat.id
        msg_text = message.text.strip()
        
        if msg_text == "/start" or len(msg_text.split()) < 2:
            bot.reply_to(message, "👋 Welcome to SkyBox Bot! Kisi product link par click karke checkout start karein.")
            return
            
        token = msg_text.split()[1].strip()
        
        if token in saved_links:
            exact_amount = saved_links[token]["amount"]
            qr_img = generate_upi_qr(UPI_ID, exact_amount)
            
            caption_text = (
                "✨ *SkyBox Instant Checkout:*\n\n"
                f"💰 *Pay Exact Amount:* ₹{exact_amount}\n"
                f"📌 *UPI ID:* `{UPI_ID}`\n\n"
                "⚠️ *Important Note:*\n"
                "Aapko QR scan karke ya fir UPI ID se payment karna hai, "
                f"same amount (₹{exact_amount}) payment karna hai aur payment karke aapko UTR bhejna hai. "
                "Neeche wala submit button par click karke apna UTR bhejna hai verification ke liye."
            )
            
            markup = InlineKeyboardMarkup()
            submit_btn = InlineKeyboardButton("📩 Submit UTR (Verify)", callback_data=f"sub_utr:{token}:{exact_amount}")
            markup.add(submit_btn)
            
            bot.send_photo(chat_id, qr_img, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ Link invalid ya expired hai.")
    except Exception as e:
        print(f"Start Error: {e}")

# --- CALLBACK: TRIGGER UTR PROMPT ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_utr:'))
def ask_for_utr(call):
    chat_id = call.message.chat.id
    data_parts = call.data.split(':')
    token = data_parts[1]
    amount = data_parts[2]
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, "⌨️ Kripya apna **12 digit ka UTR Number** ya transaction detail reply text mein likh kar bheinjein:")
    bot.register_next_step_handler(msg, forward_utr_to_admin, token, amount)

# --- PROCESS, ANTI-SPAM VERIFY AND FORWARD UTR TO ADMIN ---
def forward_utr_to_admin(message, token, amount):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "User"
    utr_text = message.text.strip() if message.text else ""
    
    if not utr_text:
        bot.reply_to(message, "❌ Kripya sirf Text mein UTR likh kar bheinjein. Link par fir se click karke retry karein.")
        return

    # Anti-Spam Check Module
    if utr_text in processed_utrs:
        bot.send_message(chat_id, "⚠️ *Aapka yeh payment verification pehle se processing mein hai. Kripya wait karein aur baar-baar spam na karein!*", parse_mode="Markdown")
        return

    # UTR Registry Lock
    processed_utrs.add(utr_text)
    
    bot.send_message(chat_id, "⌛ *Aapka payment check ho raha hai. Please kripya 1 minute tak wait karein...*", parse_mode="Markdown")
    
    # Admin Panel UI Layout
    admin_markup = InlineKeyboardMarkup()
    approve_btn = InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app:{chat_id}:{token}:{utr_text}")
    reject_btn = InlineKeyboardButton("❌ Reject Claim", callback_data=f"adm_rej:{chat_id}:{utr_text}")
    admin_markup.row(approve_btn, reject_btn)
    
    admin_alert_text = (
        "🔔 *Manual Alert: New Manual Verification Request!*\n\n"
        f"👤 *User:* {user_name} (`{chat_id}`)\n"
        f"💰 *Expected Amount:* ₹{amount}\n"
        f"📦 *Link Token:* `{token}`\n"
        f"🆔 *Submitted UTR:* `{utr_text}`\n\n"
        "📎 *Action:* Details verify karke manual approve ya reject karein."
    )
    
    bot.send_message(ADMIN_ID, admin_alert_text, parse_mode="Markdown", reply_markup=admin_markup)

# =====================================================================
# 📦 STEP 6: ADMIN CORE DECISION CALLBACK HANDLER
# =====================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_decision(call):
    try:
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Not Authorized!", show_alert=True)
            return
            
        action_parts = call.data.split(':')
        action = action_parts[0]
        
        if action == "adm_app":
            target_user_id = int(action_parts[1])
            token = action_parts[2]
            
            bot.answer_callback_query(call.id, "✅ Payment Approved!")
            bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, 
                                  text=call.message.text + "\n\n🟢 **Status: Approved & Media Delivered**")
            
            bot.send_message(target_user_id, "🎉 Aapka payment verify ho gaya hai! Aapka media niche deliver kiya ja raha hai:")
            deliver_media(target_user_id, token)
            
        elif action == "adm_rej":
            target_user_id = int(action_parts[1])
            utr_key = action_parts[2]
            
            bot.answer_callback_query(call.id, "❌ Claim Rejected!")
            bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, 
                                  text=call.message.text + "\n\n🔴 **Status: Rejected by Admin**")
            
            bot.send_message(target_user_id, "❌ Sorry! Admin ne aapka payment status reject kar diya hai. Kripya correct UTR verify karke dobara bhejein.")
            
            # Anti-spam release
            processed_utrs.discard(utr_key)
            
    except Exception as e:
        print(f"Callback Error: {e}")

# =====================================================================
# 📦 STEP 7: MEDIA DELIVERY ENGINE & MAIN ENGINE INTERACTION
# =====================================================================
def deliver_media(chat_id, token):
    try:
        # Check ki token database mein hai ya nahi
        if token in saved_links:
            media_data = saved_links[token]
        else:
            # Agar koi dynamic ya explicit fallback nahi milta, toh pehla available item uthao
            first_key = list(saved_links.keys())[0] if saved_links else None
            if first_key:
                media_data = saved_links[first_key]
            else:
                print("❌ No media configuration found in database.")
                return
                
        # --- PHOTOS DELIVERY LOOP ---
        # Safeguard syntax verification to prevent empty element crash
        photos_list = media_data.get("photos", [])
        for photo_id in photos_list:
            if photo_id and str(photo_id).strip(): # Check empty space elements
                try:
                    bot.send_photo(chat_id, photo_id)
                    time.sleep(1)
                except Exception as e:
                    print(f"Photo delivery failed: {e}")
                
        # --- VIDEOS DELIVERY LOOP ---
        videos_list = media_data.get("videos", [])
        for video_id in videos_list:
            if video_id and str(video_id).strip():
                try:
                    bot.send_video(chat_id, video_id)
                    time.sleep(1)
                except Exception as e:
                    print(f"Video delivery failed: {e}")
                
    except Exception as e:
        print(f"Global Delivery Error: {e}")

# --- MAIN LOOP RUNNER CONTROL ---
if __name__ == "__main__":
    try:
        keep_alive()
        print("🚀 SkyBox Manual Pro Bot has been successfully updated on Render...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Loop Crash Restarter: {e}")
