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
# 📦 STEP 2: REGISTER CACHES & PERMANENT DATABASE
# =====================================================================
processed_utrs = set()  # Active UTR cache memory to prevent spam

# 💡 LIFETIME PERMANENT DATABASE: Naye products yahan niche add karte rahein
saved_links = {
    "499d7f1d0638": {
        "amount": 1.00,
        "photos": [
            "AgACAgUAAxkBAAIFcWrkXiNhw1P3gTNbHj7oyr2d0KNjAALHE2sbjdVRVtfSc0J0EVRKAQADAgADeQADPQQ",
            "AgACAgUAAxkBAAIFcmrKXiMh_avg8qH18-xsUGpxC3JvAAL1E2sbjdVRVo1wvkA3ahTFAQADAgADeQADPQQ"
        ],
        "videos": [
            "BAACAgUAAxkBAAIFdWrkXj6JrQ2eMVyDKXfQPLNC8g4FAAIGIQACjdVRVgX9YrqjKeJiPQQ"
        ]
    }, 

    "8bd622bab1a6": {
        "amount": 2.00,
        "photos": [
            "AgACAgUAAxkBAAIF1GrL5aDZ07m2hwGmNoacAsjUaKaJAAJxEgsbjdVRV1nFKFiT1rG1AQADAgADeQADPQQ"
        ],
        "videos": [
            "BAACAgUAAxkBAAIF02rL5aDw6ZGNFv-xZppIJupdJtBeAAKOIAACjdVRVjFdzqDuT1MqPQQ"
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

@bot.message_handler(content_types=['photo', 'video'])
def get_file_id_handler(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.reply_to(message, f"📸 *Photo File ID Detected:*\n\n`{file_id}`\n\nIse aap code ke upar `saved_links` mein manually paste kar sakte hain.", parse_mode="Markdown")
        elif message.content_type == 'video':
            file_id = message.video.file_id
            bot.reply_to(message, f"🎥 *Video File ID Detected:*\n\n`{file_id}`\n\nIse aap code ke upar `saved_links` mein manually paste kar sakte hain.", parse_mode="Markdown")

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
            bot.reply_to(message, f"📢 *Database Conflict Alert!*\n\n*Price Level ₹{amount} is already active under token:* `{token_key}`\n\n*Please choose a different unique value.*", parse_mode="Markdown")
            return
        
    unique_token = secrets.token_hex(6)
    user_link = f"https://t.me{BOT_USERNAME}?start={unique_token}"
    
    structure_text = (
        f"👑 *Gateway Link Generated Successfully!*\n\n"
        f"🔗 *User Action Link:* `{user_link}`\n\n"
        f"⚙️ *GitHub Permanent Code Bracket:*\n"
        f"```python\n"
        f"    \"{unique_token}\": {{\n"
        f"        \"amount\": {amount},\n"
        f"        \"photos\": [\n"
        f"            \"YAHAN_FIRST_PHOTO_FILE_ID\"\n"
        f"        ],\n"
        f"        \"videos\": [\n"
        f"            \"YAHAN_VIDEO_FILE_ID\"\n"
        f"        ]\n"
        f"    }}\n"
        f"```"
    )
    
    base_token = "499d7f1d0638"
    default_photos = saved_links[base_token]["photos"] if base_token in saved_links else []
    default_videos = saved_links[base_token]["videos"] if base_token in saved_links else []
    
    saved_links[unique_token] = {
        "amount": amount,
        "photos": default_photos, 
        "videos": default_videos
    }
    
    bot.reply_to(message, structure_text, parse_mode="Markdown")

# =====================================================================
# 📦 STEP 5: USER CHECKOUT & FLOW PIPELINE (STRICT TRACKING ENGINE)
# =====================================================================

@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        chat_id = message.chat.id
        msg_text = message.text.strip()
        
        if msg_text == "/start" or len(msg_text.split()) < 2:
            bot.reply_to(message, "👋 *Welcome to SkyBox Premium Portal!*\n\n*Kindly click on a valid product checkout link to unlock your premium contents immediately.*", parse_mode="Markdown")
            return
            
        token = msg_text.split()[1].strip()
        
        if token in saved_links:
            exact_amount = saved_links[token]["amount"]
            qr_img = generate_upi_qr(UPI_ID, exact_amount)
            
            caption_text = (
                "⚡ *SKYBOX PREMIUM CHECKOUT* ⚡\n\n"
                f"💰 *Pay Exact Amount:* `₹{exact_amount}`\n"
                f"📌 *Official UPI ID:* `{UPI_ID}`\n\n"
                "💎 *INSTRUCTIONS:*\n"
                "1️⃣ *Scan the QR code above or copy the official UPI ID.*\n"
                f"2️⃣ *Pay the exact amount of* `₹{exact_amount}` *carefully.*\n"
                "3️⃣ *After successful payment, click the button below to submit your 12-digit UTR Number for verification.*"
            )
            
            markup = InlineKeyboardMarkup()
            submit_btn = InlineKeyboardButton("📩 Submit UTR (Verify)", callback_data=f"sub_utr:{token}:{exact_amount}")
            markup.add(submit_btn)
            
            bot.send_photo(chat_id, qr_img, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ *System Alert: The checkout link you used is either invalid or has expired!*", parse_mode="Markdown")
    except Exception as e:
        print(f"Start Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_utr:'))
def ask_for_utr(call):
    try:
        chat_id = call.message.chat.id
        data_parts = call.data.split(':')
        token = data_parts[1]
        amount = data_parts[2]
        
        bot.answer_callback_query(call.id)
        
        # 🎯 TRACKING 1: Blue circled prompt message ki ID save ki
        prompt_msg = bot.send_message(chat_id, "⌨️ *Verification Prompt:*\n\n*Please type and send your 12-digit Transaction UTR Number as a text reply here:*", parse_mode="Markdown")
        bot.register_next_step_handler(prompt_msg, forward_utr_to_admin, token, amount, prompt_msg.message_id)
    except Exception as e:
        print(f"Ask UTR Callback Error: {e}")

def forward_utr_to_admin(message, token, amount, prompt_msg_id):
    try:
        chat_id = message.chat.id
        user_name = message.from_user.first_name or "Premium User"
        utr_text = message.text.strip() if message.text else ""
        
        if not utr_text:
            bot.reply_to(message, "❌ *Input Error: Please send your UTR Number strictly in text format. Click checkout to retry.*", parse_mode="Markdown")
            return

        if utr_text in processed_utrs:
            bot.send_message(chat_id, "⚠️ *Security Alert: This payment claim is already under active verification! Please wait patiently.*", parse_mode="Markdown")
            return

        processed_utrs.add(utr_text)
        
        # 🎯 TRACKING 2: Checking status message ki ID save ki
        status_msg = bot.send_message(chat_id, "⌛ *Status Alert: Your payment is being verified by our server. Please hold for up to 60 seconds...*", parse_mode="Markdown")
        status_msg_id = status_msg.message_id
        
        admin_markup = InlineKeyboardMarkup()
        # Callback data mein dono tracking IDs aur target user ID bhej rahe hain
        approve_btn = InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app:{chat_id}:{token}:{prompt_msg_id}:{status_msg_id}")
        reject_btn = InlineKeyboardButton("❌ Reject Claim", callback_data=f"adm_rej:{chat_id}:{utr_text}:{prompt_msg_id}:{status_msg_id}")
        admin_markup.row(approve_btn, reject_btn)
        
        admin_alert_text = (
            "🔔 *System Alert: New Manual Verification Request!* 🔔\n\n"
            f"👤 *Premium Customer:* {user_name} (`{chat_id}`)\n"
            f"💰 *Expected Amount:* `₹{amount}`\n"
            f"📦 *Link Token Access:* `{token}`\n"
            f"🆔 *Submitted UTR:* `{utr_text}`\n\n"
            "📎 *Action Required:* Check bank panel and manually approve or reject below."
        )
        
        bot.send_message(ADMIN_ID, admin_alert_text, parse_mode="Markdown", reply_markup=admin_markup)
    except Exception as e:
        print(f"Forward UTR Error: {e}")

# =====================================================================
# 📦 STEP 6: ADMIN CORE DECISION CALLBACK HANDLER (STRICT SEQUENCE)
# =====================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_decision(call):
    try:
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ System Protection: Not Authorized!", show_alert=True)
            return
            
        action_parts = call.data.split(':')
        action = action_parts[0]
        
        if action == "adm_app":
            target_user_id = int(action_parts[1])
            token = action_parts[2]
            prompt_msg_id = int(action_parts[3])
            status_msg_id = int(action_parts[4])
            
            bot.answer_callback_query(call.id, "✅ Gateway Action: Payment Approved!")
            bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, 
                                  text=call.message.text + "\n\n🟢 **Status Panel: Approved & Premium Delivered**")
            
            # 🔥 AUTOMATIC DELETE 1: Jaisa aapne kaha, accept par click karte hi Mark wala (UTR prompt) aur status message user chat se turant delete!
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception as del_err:
                print(f"Pre-delivery text deletion failed: {del_err}")
            
            # 🎯 STYLISH CUSTOM TEXT STATUS: Ise execute kiya aur track par rakha
            custom_msg = bot.send_message(target_user_id, "🎉 *Payment successful!*\n*Media Sending...*", parse_mode="Markdown")
            
            # 🚀 Media Engine call karke is state tracking id ko pass kiya
            deliver_media(target_user_id, token, custom_msg.message_id)
            
        elif action == "adm_rej":
            target_user_id = int(action_parts[1])
            utr_key = action_parts[2]
            prompt_msg_id = int(action_parts[3])
            status_msg_id = int(action_parts[4])
            
            bot.answer_callback_query(call.id, "❌ Gateway Action: Claim Rejected!")
            bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, 
                                  text=call.message.text + "\n\n🔴 **Status Panel: Rejected by System Admin**")
            
            # 🔥 AUTOMATIC DELETE (REJECT MODE): Reject karne par bhi dono text messages chat se gayab ho jayenge!
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception as del_err:
                print(f"Reject mode text deletion failed: {del_err}")
                
            bot.send_message(target_user_id, "❌ *Verification Failed: Admin has rejected your payment status. Please confirm the correct UTR details and try again.*", parse_mode="Markdown")
            processed_utrs.discard(utr_key)
            
    except Exception as e:
        print(f"Callback Error: {e}")

# =====================================================================
# 📦 STEP 7: DIRECT MEDIA DELIVERY ENGINE (SAFE VERIFIED QUEUE)
# =====================================================================
def deliver_media(chat_id, token, custom_msg_id):
    try:
        media_data = {}
        if token in saved_links:
            media_data = saved_links[token]
        else:
            if "499d7f1d0638" in saved_links:
                media_data = saved_links["499d7f1d0638"]

        # 📸 Photos Sequential Delivery Pipeline
        if "photos" in media_data:
            for photo_id in media_data["photos"]:
                if "YAHAN_" in str(photo_id) or not photo_id:
                    continue
                try:
                    bot.send_photo(chat_id, str(photo_id).strip())
                    time.sleep(1.5) # Anti-freeze network delay
                except Exception as e:
                    print(f"Photo stream error: {e}")
                    
        # 🎥 Videos Sequential Delivery Pipeline
        if "videos" in media_data:
            for video_id in media_data["videos"]:
                if "YAHAN_" in str(video_id) or not video_id:
                    continue
                try:
                    bot.send_video(chat_id, str(video_id).strip())
                    time.sleep(1.5) # Anti-freeze network delay
                except Exception as e:
                    print(f"Video stream error: {e}")
                    
        # 🎯 🔥 CRITICAL FIXED CLEANUP SEQUENCE
        time.sleep(1)
        try:
            bot.delete_message(chat_id=chat_id, message_id=custom_msg_id)
            print("DEBUG: Dynamic sending status text safely cleared after complete media arrival.")
        except Exception as cleanup_err:
            print(f"Custom message deletion logic break: {cleanup_err}")
            
    except Exception as e:
        print(f"Global Delivery Engine Error: {e}")

# =====================================================================
# 🚀 STEP 8: MAIN LOOP RUNNER CONTROL
# =====================================================================
if __name__ == "__main__":
    try:
        keep_alive()
        print("🚀 SkyBox Manual Pro Bot has been successfully updated on Render...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Loop Crash Restarter: {e}")
