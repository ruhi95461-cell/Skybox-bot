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
    "xyz12345": 82.05,  # Example permanent link
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
    bot.reply_to(message, "⏳ *Apka UTR verify ho raha hai...*", parse_mode="Markdown")
    
    admin_caption = f"🔔 *Naya Payment Aaya Hai!*\n\n👤 User: {message.from_user.first_name} (ID: `{message.from_user.id}`)\n💰 Amount: ₹{amount}\n🧾 UTR: `{utr}`"
    markup = telebot.types.InlineKeyboardMarkup()
    approve_btn = telebot.types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{message.from_user.id}_{amount}_{utr}")
    reject_btn = telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{message.from_user.id}_{utr}")
    markup.add(approve_btn, reject_btn)
    
    bot.send_message(ADMIN_ID, admin_caption, reply_markup=markup, parse_mode="Markdown")

# --- ADMIN CALLBACK: Approve / Reject Actions ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('app_') or call.data.startswith('rej_'))
def handle_admin_action(call):
    if call.from_user.id != ADMIN_ID:
        return
    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])
    
    if action == 'app':
        amount = data[2]
        utr = data[3]
        bot.send_message(user_id, f"✅ *Aapka payment ₹{amount} successfully approve ho gaya hai!*", parse_mode="Markdown")
        bot.edit_message_text(f"✅ Approved\nUser ID: `{user_id}`\nAmount: ₹{amount}\nUTR: `{utr}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif action == 'rej':
        utr = data[2]
        bot.send_message(user_id, "❌ *Aapka payment reject kar diya gaya hai. Kripya sahi UTR check karein.*", parse_mode="Markdown")
        bot.edit_message_text(f"❌ Rejected\nUser ID: `{user_id}`\nUTR: `{utr}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

if __name__ == '__main__':
    bot.infinity_polling()
