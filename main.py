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

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# BHARATPE SESSION DATA (Isse browser se nikalna hoga)
# Admin isse /renew command se kabhi bhi badal sakta hai bina bot restart kiye
BHARATPE_TOKENS = {
    "token": "YOUR_BHARATPE_AUTH_TOKEN_HERE",
    "merchantId": "YOUR_MERCHANT_ID_HERE"
}

# Permanent Links Storage (Manually edit karne ke liye)
saved_links = {
# Iske andar aap apni photo/video IDs manually bhar sakte hain
"76d2bd64f406": {
    "amount": 65.0,
    "photos": [],
    "videos": []
},
{

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

# BHARATPE LIVE TRANSACTION CHECKER
def verify_bharatpe_payment(target_amount, target_utr):
    """
    Direct BharatPe ke server se last 10 transactions fetch karke 
    Amount aur UTR match karta hai.
    """
    url = f"https://bharatpe.in{BHARATPE_TOKENS['merchantId']}/transactions?limit=10"
    headers = {
        "Authorization": f"Bearer {BHARATPE_TOKENS['token']}",
        "Content-Type": application/json
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("transactions", [])
            
            for txn in transactions:
                # UTR aur Amount check (Kuch cases me amount float/string hota hai)
                bank_utr = str(txn.get("bankReferenceNo", ""))
                amount_paid = float(txn.get("amount", 0))
                status = txn.get("status", "")
                
                if bank_utr == str(target_utr) and amount_paid == float(target_amount) and status == "SUCCESS":
                    return True
        elif response.status_code == 401:
            # Token expire hone par Admin ko alert jayega
            bot.send_message(ADMIN_ID, "⚠️ *Alert:* Aapka BharatPe Session Token expire ho gaya hai! Kripya /renew command se naya token dalein.", parse_mode="Markdown")
    except Exception as e:
        print(f"BharatPe API Error: {e}")
    return False

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
            bot.reply_to(message, f"📸 *PHOTO FILE ID:*\n`{file_id}`", parse_mode="Markdown")
        elif message.content_type == 'video':
            file_id = message.video.file_id
            bot.reply_to(message, f"🎥 *VIDEO FILE ID:*\n`{file_id}`", parse_mode="Markdown")

# Admin Session Renewer Command
@bot.message_handler(commands=['renew'])
def renew_session(message):
    if message.from_user.id == ADMIN_ID:
        try:
            # Format: /renew NEW_TOKEN MERCHANT_ID
            args = message.text.split(" ")
            BHARATPE_TOKENS['token'] = args[1]
            BHARATPE_TOKENS['merchantId'] = args[2]
            bot.reply_to(message, "✅ *BharatPe Credentials Successfully Updated!*", parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ *Format Galt Hai!*\nUse: `/renew <token> <merchantId>`", parse_mode="Markdown")

# Link Generator Command
@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        amount = float(message.text.split()[1])
        unique_token = secrets.token_hex(6)
        bot_username = bot.get_me().username
        link = f"https://t.me{bot_username}?start=resell_{unique_token}"
        
        response_text = (
            f"🔗 *Naya Payment Link Taiyar Hai:*\n{link}\n\n"
            f"📝 *GitHub ke `saved_links` me paste karne ke liye format:*\n"
            f"`\"{unique_token}\": {{\n    \"amount\": {amount},\n    \"photos\": [],\n    \"videos\": []\n}},`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠ Command format: `/gen 80`", parse_mode="Markdown")

# User Checkout (/start)
@bot.message_handler(commands=['start'])
def start_payment(message):
    text_args = message.text.split(' ')[1] if len(message.text.split()) > 1 else ""
    
    if text_args.startswith("resell_"):
        token = text_args.replace("resell_", "")
        
        if token in saved_links:
            amount = saved_links[token]["amount"]
            qr_img = generate_upi_qr(YOUR_UPI_ID, amount)
            
            caption_text = (
                f"Pay ₹{amount} for the item\n\n"
                f"📌 UPI ID — `{YOUR_UPI_ID}`\n\n"
                f"⚠️ *Instructions:*\n"
                f"1. QR Code scan karke exact ₹{amount} pay karein.\n"
                f"2. Payment karne ke baad *Submit UTR* button par click karein aur 12-digit ka UTR number bhejein."
            )
            
            markup = telebot.types.InlineKeyboardMarkup()
            btn = telebot.types.InlineKeyboardButton("📥 Submit UTR", callback_data=f"sub_{amount}_{token}")
            markup.add(btn)
            
            bot.send_photo(message.chat.id, qr_img, caption=caption_text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Yeh link invalid hai ya expire ho chuka hai.")
    else:
        bot.reply_to(message, "👋 Welcome to Skybox Bot!")

# Callback for UTR Submission Trigger
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def trigger_utr_input(call):
    _, amount, token = call.data.split("_")
    msg = bot.send_message(call.message.chat.id, "*✍️ Ab apna 12-digit ka UTR number yahan type karke bhejein:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_utr, amount, token)

# Core Logic: UTR Processing & Real Verification
def process_utr(message, amount, token):
    utr = message.text.strip()
    
    if len(utr) != 12 or not utr.isdigit():
        bot.reply_to(message, "❌ *Galt UTR!* Kripya 12-digit ka sahi UTR number dobara bhejiyen.", parse_mode="Markdown")
        return

    bot.reply_to(message, "*⏳ Apka UTR BharatPe server par verify ho raha hai... (Takes 8s)*", parse_mode="Markdown")
    time.sleep(8)
    
    # Direct BharatPe Live Verification check
    is_valid_payment = verify_bharatpe_payment(amount, utr)
    
    # Admin Alert Notification
    admin_caption = (
        f"🔔 *New UTR Submitted!*\n\n"
        f"👤 User: {message.from_user.first_name} (`{message.from_user.id}`)\n"
        f"💰 Amount: ₹{amount}\n"
        f"🧾 UTR: `{utr}`\n"
        f"⚙️ Status: {'✅ Verified & Delivered' if is_valid_payment else '❌ Fake/Unpaid'}"
    )
    bot.send_message(ADMIN_ID, admin_caption, parse_mode="Markdown")

    if is_valid_payment:
        bot.reply_to(message, "✅ *Payment Successful!* Aapka media niche deliver kiya ja raha hai:", parse_mode="Markdown")
        
        # Ek-ek karke saari photos aur videos deliver karna
        media_data = saved_links[token]
        for photo_id in media_data.get("photos", []):
            bot.send_photo(message.chat.id, photo_id)
            time.sleep(1)
        for video_id in media_data.get("videos", []):
            bot.send_video(message.chat.id, video_id)
            time.sleep(1)
    else:
        bot.reply_to(message, "*Apka payment receive nhi hua ❌\nPlease try again....*", parse_mode="Markdown")

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
