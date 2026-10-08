import telebot
import time
import requests
import secrets
from flask import Flask
from threading import Thread
import io
import qrcode

# Token aur ID details
BOT_TOKEN = "8963839676:AAHbkhulxdQOFUJBRcXRAhCuL1aDDElc4-s"
ADMIN_ID = 8393210427
YOUR_UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

# YAHAN PAR PASTE KARIYE WOH SECRET API KEY:
GATEWAY_API_KEY = "76e07c40-a898-45d8-9c24-7e92ecfe2b9b"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Permanent Links Storage (Manually edit karne ke liye)
saved_links = {
    "932897e02459b3804b75": {
    "amount": 65.0,
    "photos": [],
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

# ====================================================================
# LIVE UPIQRPAY WEBHOOK RECEIVER (100% AUTOMATIC GATEWAY INTEGRATION)
# ====================================================================
from flask import request, jsonify

@app.route('/')
def home():
    return "Skybox UPIQRPay Gateway Server is Active!"

@app.route('/webhook', methods=['POST'])
def gateway_webhook():
    try:
        # Gateway se aane wala live encrypted data json format me fetch karna
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        print(f"📦 Gateway Data Logged: {data}")

        # UPIQRPay dashboard standard structure parameters check karna
        utr = str(data.get("utr", data.get("bank_Rrn", ""))).strip()
        amount_paid = float(data.get("amount", 0))
        status = str(data.get("status", "")).strip().upper()
        
        # User dynamic identification variable fetch karna (jo custom param me pass hoga)
        # Gateway checkout page create karte waqt 'custom' ya 'remark' field me metadata check hota hai
        custom_data = data.get("custom", "") 

        # Live success criteria evaluation logic
        if utr and amount_paid > 0 and (status == "SUCCESS" or status == "COMPLETED" or status == "PAID"):
            
            # Admin Dashboard Alert Update Notification Telegram message trigger karna
            admin_msg = (
                f"⚡️ <b>[UPIQRPay Webhook] Instant Payment Success!</b>\n\n"
                f"💰 <b>Amount:</b> ₹{amount_paid}\n"
                f"🧾 <b>UTR Number:</b> <code>{utr}</code>\n"
                f"⚙️ <b>Status:</b> SUCCESS\n"
                f"🔑 <b>Metadata:</b> {custom_data}"
            )
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")

            # NOTE: Jab gateway setup complete ho jayega toh data confirmation response 200 return karega
            
        return jsonify({"status": "success", "message": "Processed Successfully"}), 200

    except Exception as e:
        print(f"Gateway Critical Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Flask Keep-Alive Routing
@app.route('/')
def home():
    return "Skybox Bot is Running Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# Debug Message: Photo/Video bhejne par File ID nikalna
@bot.message_handler(content_types=['photo', 'video'])
def handle_docs(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.reply_to(message, f"📸 PHOTO FILE ID:\n{file_id}", parse_mode="Markdown")
        elif message.content_type == 'video':
            file_id = message.video.file_id
            bot.reply_to(message, f"🎥 VIDEO FILE ID:\n{file_id}", parse_mode="Markdown")

# Admin Session Renewer Command
@bot.message_handler(commands=['renew'])
def renew_session(message):
    if message.from_user.id == ADMIN_ID:
        try:
            args = message.text.split(" ")
            BHARATPE_TOKENS['token'] = args[1]
            BHARATPE_TOKENS['merchantId'] = args[2]
            bot.reply_to(message, "✅ BharatPe Credentials Successfully Updated!", parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ Format Galt Hai!\nUse: /renew <token> <merchantId>", parse_mode="Markdown")

# --- ADMIN COMMAND: Automatic Gateway Link Generate Karein ---
@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Sahi format: `/gen <amount>`")
        return
    try:
        amount = round(float(args[1]), 2)
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount!")
        return

    unique_token = secrets.token_hex(6)

    # UPIQRPay API ke server par dynamic billing link create karne ki request bhejnah
    url = "https://upiqrpay.in"
    headers = {
        "Authorization": f"Bearer {GATEWAY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": amount,
        "order_id": unique_token,
        "remark": f"Payment for token {unique_token}",
        "custom": unique_token # Yeh token webhook me wapas milega media deliver karne ke liye
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            # Gateway se aane wala payment page URL fetch karna
            payment_link = res_data.get("payment_url", "")

            # Aapke database structure ke mutabik entry save karna
            saved_links[unique_token] = {
                "amount": amount,
                "photos": [],
                "videos": []
            }

            response_text = (
                f"🔗 <b>Automatic Payment Link Taiyar Hai:</b>\n"
                f"{payment_link}\n\n"
                f"📝 <b>GitHub ke saved_links me paste karne ke liye format:</b>\n"
                f"<code>\"{unique_token}\": {{\n"
                f"    \"amount\": {amount},\n"
                f"    \"photos\": [],\n"
                f"    \"videos\": []\n"
                f"}},</code>"
            )
            bot.reply_to(message, response_text, parse_mode="HTML")
        else:
            bot.reply_to(message, f"❌ Gateway Error: Code {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Gateway API Failed: {str(e)}")

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
                    f"Pay ₹{amount} for the item\n\n"
                    f"📌 UPI ID — {YOUR_UPI_ID}\n\n"
                    f"⚠️ Instructions:\n"
                    f"1. QR Code scan karke exact ₹{amount} pay karein.\n"
                    f"2. Payment karne ke baad Submit UTR button par click karein aur 12-digit ka UTR number bhejein."
                )
                
                markup = telebot.types.InlineKeyboardMarkup()
                btn = telebot.types.InlineKeyboardButton("📥 Submit UTR", callback_data=f"sub_{amount}_{token}")
                markup.add(btn)
                
                bot.send_photo(message.chat.id, qr_img, caption=caption_text, reply_markup=markup)
            else:
                bot.reply_to(message, "❌ Yeh link invalid hai ya expire ho chuka hai.")
        else:
            bot.reply_to(message, "👋 Welcome to Skybox Bot!")
            
    except Exception as e:
        bot.reply_to(message, f"❌ System Error: {str(e)}")

# Callback for UTR Submission Trigger
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def trigger_utr_input(call):
    try:
        # FIX: maxsplit=2 kiya hai taaki lamba token perfectly split ho bina crash kiye
        data_parts = call.data.split("_", 2)
        amount = data_parts[1]
        token = data_parts[2]
        
        msg = bot.send_message(call.message.chat.id, "✍ *Ab apna 12-digit ka UTR number yahan type karke bhejein:*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_utr, amount, token)
    except Exception as e:
        print(f"Callback Error: {e}")

# Core Logic: UTR Processing & Real Verification
def process_utr(message, amount, token):
    try:
        utr = message.text.strip()
        
        # Check agar UTR valid format me hai (12 digits aur sirf numbers)
        if len(utr) != 12 or not utr.isdigit():
            bot.reply_to(message, "❌ *Galt UTR!* Kripya 12-digit ka UTR number dobara sahi se bhejein.", parse_mode="Markdown")
            return

        bot.reply_to(message, "⏳ *Apka UTR BharatPe server par verify ho raha hai... (Takes 8s)*", parse_mode="Markdown")
        time.sleep(8)

        # Direct BharatPe Live Verification check
        is_valid_payment = verify_bharatpe_payment(amount, utr)

        # Admin Alert Notification Text
        status_text = "✅ Verified & Delivered" if is_valid_payment else "❌ Fake/Unpaid"
        
        # FIX: Triple quotes use kiya hai taaki safe concatenation ho aur text parse crash na ho
        admin_caption = f"""🔔 *New UTR Submitted!*

👤 *User:* {message.from_user.first_name} (`{message.from_user.id}`)
💰 *Amount:* ₹{amount}
🧾 *UTR:* `{utr}`
⚙ *Status:* {status_text}"""
        
        # Admin ko report bhejna
        bot.send_message(ADMIN_ID, admin_caption, parse_mode="Markdown")

        if is_valid_payment:
            bot.reply_to(message, "✅ *Payment Successful!* Aapka media niche deliver kiya ja raha hai:", parse_mode="Markdown")
            
            # Ek-ek karke saari photos aur videos deliver karna
            media_data = saved_links.get(token, {})
            
            for photo_id in media_data.get("photos", []):
                try:
                    bot.send_photo(message.chat.id, photo_id)
                    time.sleep(1)
                except Exception as e:
                    print(f"Photo delivery failed: {e}")
                    
            for video_id in media_data.get("videos", []):
                try:
                    bot.send_video(message.chat.id, video_id)
                    time.sleep(1)
                except Exception as e:
                    print(f"Video delivery failed: {e}")
        else:
            bot.reply_to(message, "❌ *Apka payment receive nhi hua!*\nPlease try again....", parse_mode="Markdown")
            
    except Exception as e:
        bot.reply_to(message, f"❌ UTR Process Error: {str(e)}")

# Main Execution Control Loop
if __name__ == '__main__':
    # Flask app ko background thread me chalana
    keep_alive()
    print("🤖 Skybox Bot is launching now...")
    # Bot polling start karna bina crash huye
    bot.infinity_polling()
