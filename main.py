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
# 📦 STEP 1: CONFIGURATION & CONFIG BLOCK (PREMIUM EMISSARY)
# =====================================================================
BOT_TOKEN = "8963839676:AAHGTnd6QcysW9DrCUMQrnW8xRf52J-wBe8" 
ADMIN_ID = 8393210427
UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask('')

# =====================================================================
# 📦 STEP 2: REGISTER CACHES & PERMANENT TELE-FORWARD DATABASE
# =====================================================================
processed_utrs = set()  # Active UTR cache memory to prevent spam

# 💡 LIFETIME FORWARDER DATABASE: Yahan apne product channels link karein
saved_links = {
    "585f5f2f9ec1": {
        "amount": 55.00,
        "channel_id": "-1004389531080" 
    }, 

    "712033235ffd": {
        "amount": 3.00,
        "channel_id": "@SkyBoxTestChannel2"  
    },

    "a3a1d01468ba": {
        "amount": 65.00,
        "channel_id": "-1004374958890"  
    },

    "4ceb022fdee3": {
        "amount": 68.00, 
        "channel_id": -1003972171866
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
    return "Skybox Forwarder Bot is Running Online on Render!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================================================================
# 📦 STEP 4: TELEGRAM ADMIN COMMANDS & HANDLERS
# =====================================================================

@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ *Format Setup Engine:*\n\n*Use exact format:* `/gen <amount>`\n*Example:* `/gen 5`", parse_mode="Markdown")
        return
        
    try:
        amount = round(float(args[1]), 2)
    except ValueError:
        bot.reply_to(message, "❌ *System Alert: Invalid Numeric Amount!*", parse_mode="Markdown")
        return
        
    for token_key, data in saved_links.items():
        if data.get("amount") == amount:
            bot.reply_to(message, f"📢 *Database Conflict Alert!*\n\n*Price Level ₹{amount} is already active under token:* `{token_key}`", parse_mode="Markdown")
            return
        
    unique_token = secrets.token_hex(6)
    user_link = f"https://t.me/{BOT_USERNAME}?start={unique_token}"
    
    structure_text = (
        f"👑 *Gateway Forwarder Link Generated!* 👑\n\n"
        f"🔗 *User Action Link:* `{user_link}`\n\n"
        f"⚙️ *GitHub Permanent Code Bracket:*\n"
        f"```python\n"
        f"    \"{unique_token}\": {{\n"
        f"        \"amount\": {amount},\n"
        f"        \"channel_id\": \"YAHAN_APNE_NEW_CHANNEL_KI_ID_DALEIN\"\n"
        f"    }}\n"
        f"```"
    )
    
    saved_links[unique_token] = {
        "amount": amount,
        "channel_id": "@ChangeMe"
    }
    
    bot.reply_to(message, structure_text, parse_mode="Markdown")

# =====================================================================
# 📦 STEP 5: USER CHECKOUT & IMAGE PIPELINE (EXPLICIT DATA SYNC)
# =====================================================================

@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        chat_id = message.chat.id
        msg_text = message.text.strip()
        
        if msg_text == "/start" or len(msg_text.split()) < 2:
            bot.reply_to(message, "👋 *Welcome! Please click a valid product checkout link to start.*", parse_mode="Markdown")
            return
            
        # ✅ FIX: Sahi se token nikalne ke liye split ka index use kiya aur strip lagaya
        token = msg_text.split()[1].strip()
        
        if token in saved_links:
            exact_amount = saved_links[token]["amount"]
            qr_img = generate_upi_qr(UPI_ID, exact_amount)
            
            caption_text = (
                "⚡ *SKYBOX PREMIUM CHECKOUT* ⚡\n\n"
                f"💰 *Pay Amount:* `₹{exact_amount}`\n"
                f"📌 *UPI ID:* `{UPI_ID}`\n\n"
                "💎 *INSTRUCTIONS:*\n"
                f"1️⃣ *Pay exact* `₹{exact_amount}` *via QR or UPI ID.*\n"
                "2️⃣ *Click below to upload your payment screenshot image.*"
            )
            
            markup = InlineKeyboardMarkup()
            submit_btn = InlineKeyboardButton("📤 Upload Payment Screenshot", callback_data=f"sub_utr:{token}:{exact_amount}")
            markup.add(submit_btn)
            
            bot.send_photo(chat_id, qr_img, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ *Error: Invalid or expired checkout link!*", parse_mode="Markdown")
    except Exception as e:
        print(f"Start Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_utr:'))
def ask_for_utr(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split(':')
        
        # ✅ FIX: Indexes ko explicitly wapas restore kiya taaki crash na ho
        token = data_parts[1]
        amount = data_parts[2]
        
        bot.answer_callback_query(call.id)
        
        prompt_msg = bot.send_message(
            chat_id, 
            "📸 *PAYMENT VERIFICATION*\n\n"
            "👉 *Please upload and send your successful transaction screenshot receipt now.*", 
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(prompt_msg, lambda msg: forward_utr_to_admin(msg, token, amount, prompt_msg.message_id))
    except Exception as e:
        print(f"Ask UTR Callback Error: {e}")

def forward_utr_to_admin(message, token, amount, prompt_msg_id):
    try:
        chat_id = message.chat.id
        user_name = message.from_user.first_name or "Premium Customer"
        user_username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        
        if not message.photo:
            bot.reply_to(message, "❌ *Error: Please upload an actual photo screenshot file only!*", parse_mode="Markdown")
            return

        photo_file_id = message.photo[-1].file_id

        if photo_file_id in processed_utrs:
            bot.send_message(chat_id, "⚠️ *Alert: This receipt is already processing! Please wait.*", parse_mode="Markdown")
            return

        processed_utrs.add(photo_file_id)
        
        status_msg = bot.send_message(chat_id, "⌛ *Verifying your payment. Please wait patiently...*", parse_mode="Markdown")
        status_msg_id = status_msg.message_id
        
        admin_markup = InlineKeyboardMarkup()
        # ✅ FIX: Proper string formatting callback data ke liye
        approve_btn = InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app:{chat_id}:{token}:{prompt_msg_id}:{status_msg_id}")
        reject_btn = InlineKeyboardButton("❌ Reject Claim", callback_data=f"adm_rej:{chat_id}:{photo_file_id}:{prompt_msg_id}:{status_msg_id}")
        admin_markup.row(approve_btn, reject_btn)
        
        admin_alert_text = (
            "🔔 *NEW VERIFICATION REQUEST!* 🔔\n\n"
            f"👤 *Customer Name:* *{user_name}*\n"
            f"🆔 *User Chat ID:* `{chat_id}`\n"
            f"🌐 *Telegram Username:* {user_username}\n"
            f"💰 *Expected Amount:* `₹{amount}`\n"
            f"📦 *Link Token ID:* `{token}`\n\n"
            "📎 *Action:* Verify the photo below and manual approve/reject."
        )
        
        # Yahan ADMIN_ID string format se int casting automatic handle ho jayega
        bot.send_photo(int(ADMIN_ID), photo_file_id, caption=admin_alert_text, parse_mode="Markdown", reply_markup=admin_markup)
        print("DEBUG: Admin Alert pushed successfully.")
    except Exception as e:
        print(f"Forward UTR Error: {e}")

# =====================================================================
# 📦 STEP 6: ADMIN CORE DECISION CALLBACK HANDLER (STRICT SEQUENCE)
# =====================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_decision(call):
    try:
        # ⚡ INSTANT FIX: Click hote hi sabse pehle Telegram ko response dena hai taaki NOT RESPONDING error na aaye
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        # 🔧 ADMIN SELF-TEST FIX: int() casting ki wajah se ab aap apni Admin ID se bhi test kar payenge
        if int(call.from_user.id) != int(ADMIN_ID):
            try:
                bot.answer_callback_query(call.id, "❌ Protected: Not Authorized!", show_alert=True)
            except Exception:
                pass
            return
            
        action_parts = call.data.split(':')
        action = action_parts[0]
        
        if action == "adm_app":
            target_user_id = int(action_parts[1])
            token = action_parts[2]
            prompt_msg_id = int(action_parts[3])
            status_msg_id = int(action_parts[4])
            
            # Admin panel ka caption instantly badlein
            bot.edit_message_caption(chat_id=int(ADMIN_ID), message_id=call.message.message_id, 
                                     caption=call.message.caption + "\n\n🟢 **Status: Approved & Media Delivered**")
            
            # 🔥 AUTOMATIC CLEANUP: User text logs ko delete karna (Aapka original feature)
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception as del_err:
                print(f"Deletion failed: {del_err}")
            
            custom_msg = bot.send_message(target_user_id, "🎉 *Payment successful!*\n*Media Sending...*", parse_mode="Markdown")
            
            deliver_media(target_user_id, token, custom_msg.message_id)
            
        elif action == "adm_rej":
            target_user_id = int(action_parts[1])
            photo_key = action_parts[2]
            prompt_msg_id = int(action_parts[3])
            status_msg_id = int(action_parts[4])
            
            # Admin panel ka caption instantly badlein
            bot.edit_message_caption(chat_id=int(ADMIN_ID), message_id=call.message.message_id, 
                                     caption=call.message.caption + "\n\n🔴 **Status: Rejected by Admin**")
            
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception as del_err:
                print(f"Deletion failed: {del_err}")
                
            bot.send_message(target_user_id, "❌ *Payment status rejected by Admin. Please recheck your screenshot proof and try again.*", parse_mode="Markdown")
            processed_utrs.discard(photo_key)
            
    except Exception as e:
        print(f"Callback Error: {e}")

# =====================================================================
# 📦 STEP 7: PRIVATE CHANNEL MESSAGES AUTO-FORWARD ENGINE (SHORT ENGINE)
# =====================================================================
def deliver_media(chat_id, token, custom_msg_id):
    try:
        media_data = {}
        if token in saved_links:
            media_data = saved_links[token]
        else:
            if "499d7f1d0638" in saved_links:
                media_data = saved_links["499d7f1d0638"]

        channel_id = media_data.get("channel_id", "")
        media_forwarded = False

        if channel_id and channel_id != "@ChangeMe":
            # 🚀 TELE-FORWARD ENGINE: Private channel ke content ko bulk forward karega
            for msg_id in range(1, 100):
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=channel_id, message_id=msg_id)
                    media_forwarded = True
                    time.sleep(1.0) # Buffer rate delay for anti-freeze security
                except Exception as forward_err:
                    # Invalid/Khali slots ko bina crash kiye automatic skip karega
                    continue
        
        # 🎯 🔥 CLEANUP SEQUENCE: Media aane ke baad hi "Media Sending..." text delete hoga
        if media_forwarded:
            time.sleep(1)
            try:
                bot.delete_message(chat_id=chat_id, message_id=custom_msg_id)
                print("DEBUG: Status layout optimized after transmission complete.")
            except Exception as cleanup_err:
                print(f"Cleanup skip: {cleanup_err}")
        else:
            bot.send_message(chat_id, "⚠️ *System Notice: Target premium channel config error. Contact Admin.*", parse_mode="Markdown")
                    
    except Exception as e:
        print(f"Global Delivery Engine Error: {e}")

# =====================================================================
# 🚀 STEP 8: MAIN LOOP RUNNER CONTROL
# =====================================================================
if __name__ == "__main__":
    try:
        # Render Flask dashboard background verification sync engine trigger
        keep_alive()
        print("🚀 SkyBox Premium Forwarder Pro has been successfully updated on Render...")
        
        # Infinite tracking polling activation restarter cycle loop
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Loop Crash Restarter Alert: {e}")
