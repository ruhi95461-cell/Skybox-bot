import telebot
import time
import secrets
from flask import Flask
from threading import Thread
import io
import qrcode

# Token aur Admin setup
BOT_TOKEN = "8963839676:AAHbkhulxdQOFUJBRcXRAhCuL1aDDElc4-s"
ADMIN_ID = 8393210427
YOUR_UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Links Storage Array
saved_links = {
    "932897e02459b3804b75": {
        "amount": 65.0,
        "photos": [],
        "videos": []
    }
}
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
    return "Skybox Manual Gateway is Active!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
@bot.message_handler(content_types=['photo', 'video'])
def handle_docs(message):
    if message.from_user.id == ADMIN_ID:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.reply_to(message, f"📸 PHOTO FILE ID:\n`{file_id}`", parse_mode="Markdown")
        elif message.content_type == 'video':
            file_id = message.video.file_id
            bot.reply_to(message, f"🎥 VIDEO FILE ID:\n`{file_id}`", parse_mode="Markdown")

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

    unique_token = secrets.token_hex(10)
    saved_links[unique_token] = {"amount": amount, "photos": [], "videos": []}
    link = f"https://t.me/{BOT_USERNAME}?start=resell_{unique_token}"
    
    response_text = f"🔗 <b>Naya Payment Link Taiyar Hai:</b>\n{link}"
    bot.reply_to(message, response_text, parse_mode="HTML")
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
                caption_text = f"Pay ₹{amount} for the item\n\n📌 UPI ID — {YOUR_UPI_ID}"
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def trigger_utr_input(call):
    data_parts = call.data.split("_", 2)
    amount, token = data_parts[1], data_parts[2]
    msg = bot.send_message(call.message.chat.id, "✍ *Ab apna 12-digit ka UTR number yahan type karke bhejein:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_utr, amount, token)
def process_utr(message, amount, token):
    utr = message.text.strip()
    if len(utr) != 12 or not utr.isdigit():
        bot.reply_to(message, "❌ *Galt UTR!* Kripya 12-digit ka sahi number bhejein.", parse_mode="Markdown")
        return

    bot.reply_to(message, "⏳ *Aapka payment request verify kiya ja raha hai...*", parse_mode="Markdown")
    markup = telebot.types.InlineKeyboardMarkup()
    btn_yes = telebot.types.InlineKeyboardButton("✅ Accept", callback_data=f"ap_yes_{message.chat.id}_{token}")
    btn_no = telebot.types.InlineKeyboardButton("❌ Reject", callback_data=f"ap_no_{message.chat.id}_{token}")
    markup.row(btn_yes, btn_no)
    bot.send_message(ADMIN_ID, f"🔔 *New Request!*\n💰 *Amount:* ₹{amount}\n🧾 *UTR:* `{utr}`", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ap_"))
def handle_approval(call):
    _, choice, user_id, token = call.data.split("_", 3)
    if choice == "yes":
        bot.send_message(user_id, "✅ *Payment Successful!*", parse_mode="Markdown")
        bot.edit_message_text(f"{call.message.text}\n\n⚡️ *Status:* Approved!", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(user_id, "❌ *Aapka payment reject kar diya gaya hai!*", parse_mode="Markdown")
        bot.edit_message_text(f"{call.message.text}\n\n⚡️ *Status:* Rejected!", call.message.chat.id, call.message.message_id)

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
