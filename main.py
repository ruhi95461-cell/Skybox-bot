import telebot
import time
import secrets
import os
import io
import re
import requests
from datetime import datetime, timezone, timedelta
import qrcode
from PIL import Image
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================================
# 📦 STEP 1: CONFIGURATION & CONFIG BLOCK
# =====================================================================
BOT_TOKEN = "8963839676:AAE8PKKT8vO1laI-hAi5TRucdt0F3EMZLIk"
ADMIN_ID = 8393210427
UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

# Yahan apni free OCR.space API key dalein (default "helloworld" test ke liye hai)
OCR_API_KEY = "K8822071071352488957"

EXPECTED_RECEIVER_NAME = "tanu das"
MAX_TIME_GAP_MINUTES = 360

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask('')

# =====================================================================
# 📦 STEP 2: REGISTER CACHES & PERMANENT TELE-FORWARD DATABASE
# =====================================================================
saved_links = {
    "585f5f2f9ec1": {"amount": 55.00, "channel_id": "-1004389531080"}, 
    "86fb9961877b": {"amount": 54.00, "channel_id": "-1004340284198"},
    "c088b2255041": {"amount": 75.00, "channel_id": "-1004317431275"},
    "525f48b4e663": {"amount": 40.00, "channel_id": "-1004314772195"},
    "2ac98e9b09b8": {"amount": 30.00, "channel_id": "-1004350524368"},
    "ab6ce6d4b758": {"amount": 45.50, "channel_id": "-1003837639336"},
    "1165cb76e728": {"amount": 57.00, "channel_id": "-1005863322198"},
    "e42e3dc6e1e8": {"amount": 30.50, "channel_id": "-1003889265161"},
    "a3a1d01468ba": {"amount": 65.00, "channel_id": "-1004374958890"},
    "edbb7d49c67e": {"amount": 46.00, "channel_id": "-1004465256023"},
    "7c1fbab9a85a": {"amount": 36.00, "channel_id": "-1004478987840"},
    "96e7031f11a6": {"amount": 49.00, "channel_id": "-1005979059247"},
    "72d37dbac3b2": {"amount": 33.60, "channel_id": "-1005958754173"},
    "acd98d30bad7": {"amount": 43.00, "channel_id": "-1004468691722"},
    "dbcda6225404": {"amount": 48.80, "channel_id": "-1003999830076"},
    "3563b10d6d30": {"amount": 39.69, "channel_id": "-1005699028189"},
    "d8e2372dbca5": {"amount": 28.60, "channel_id": "-1004390368084"},
    "b007cbb55dc0": {"amount": 39.90, "channel_id": "-1004387748325"},
    "430965b7864f": {"amount": 42.00, "channel_id": "-1004491113314"},
    "0900e0911952": {"amount": 37.00, "channel_id": "-1003933411317"},
    "b693df24e672": {"amount": 56.00, "channel_id": "-1003925942434"},
    "912f2bca8b49": {"amount": 44.00, "channel_id": "-1004371490401"},
    "dc8480cc9c4a": {"amount": 48.00, "channel_id": "-1004493993003"},
    "6b955e534a12": {"amount": 53.00, "channel_id": "-1003706436711"},
    "a44017529327": {"amount": 33.00, "channel_id": "-1003715951395"},
    "98a555b2cc83": {"amount": 39.00, "channel_id": "-1003843572755"},
    "2dfc8251e44b": {"amount": 45.00, "channel_id": "-1003870644699"},
    "df830bffe577": {"amount": 31.00, "channel_id": "-1004421962385"},
    "bdb28f0b34d1": {"amount": 28.00, "channel_id": "-1004430858732"},
    "4ceb022fdee3": {"amount": 68.00, "channel_id": "-1003972171866"},
    "b9abcbb5be34": {"amount": 41.00, "channel_id": "-1004492451254"},
    "857d50411bad": {"amount": 38.00, "channel_id": "-1003990769898"}
} 

# =====================================================================
# 📦 MANUAL MEDIA TRANSFER COMMAND (ADMIN ONLY)
# =====================================================================
@bot.message_handler(commands=['send'])
def manual_transfer(message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "⚠ *Format:* `/send <user_id> <token>`\n*Example:* `/send 123456789 585f5f2f9ec1`", parse_mode="Markdown")
        return

    _, uid_str, token = args

    if not uid_str.isdigit() or token not in saved_links:
        bot.reply_to(message, "❌ *Invalid User ID ya Token!* GitHub par token check karein.", parse_mode="Markdown")
        return

    target_uid = int(uid_str)
    status_msg = bot.reply_to(message, f"⏳ *User `{target_uid}` ko media transfer ho raha hai...*", parse_mode="Markdown")

    wait_msg = bot.send_message(
        target_uid,
        "<blockquote>🎉 <b>𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗩𝗘𝗥𝗜𝗙𝗜𝗘𝗗!</b> ✅\n\n🚀 <b>𝗠𝗲𝗱𝗶𝗮 𝗦𝗲𝗻𝗱𝗶𝗻𝗴...</b>\n⏳ <i>Please wait while your files arrive.</i></blockquote>",
        parse_mode="HTML"
    )

    deliver_media(target_uid, token, wait_msg.message_id)
    bot.edit_message_text(f"✅ *Media Transfer Complete!* User `{target_uid}` ko token `{token}` ki saari files bhej di gayi hain.", message.chat.id, status_msg.message_id, parse_mode="Markdown")

# =====================================================================
# 📦 STEP 3: FAST CLOUD OCR, ANTI-REPEAT TIME LOCK & VERIFICATION ENGINE
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

def check_time_gap(full_text, now_ist):
    matches_12h = re.findall(r'\b(0?[1-9]|1[0-2]):([0-5][0-9])\s*(am|pm)\b', full_text)
    if matches_12h:
        for hr_str, min_str, meridiem in matches_12h:
            hr = int(hr_str)
            mn = int(min_str)
            if meridiem == "pm" and hr != 12:
                hr += 12
            elif meridiem == "am" and hr == 12:
                hr = 0
            receipt_dt = now_ist.replace(hour=hr, minute=mn, second=0, microsecond=0)
            diff_minutes = (now_ist - receipt_dt).total_seconds() / 60.0
            if diff_minutes + 5 <= 0:
                return False, f"Receipt time ({hr_str}:{min_str} {meridiem.upper()}) current time se aage hai.", None
            if diff_minutes > MAX_TIME_GAP_MINUTES:
                hrs_gap = round(diff_minutes / 60, 1)
                return False, f"Time gap 2 ghante se zyada hai ({hrs_gap} hrs purana screenshot).", None
        first_hr, first_mn, first_mer = next(iter(matches_12h))
        time_tag = f"{int(first_hr):02d}:{first_mn}{first_mer}"
        return True, "Time gap within 2 hours", time_tag
    return False, "Receipt ka exact AM/PM time detect nahi hua.", None

def analyze_screenshot(image_bytes, expected_amount):
    try:
        ocr_endpoint = "https://api.ocr.space/parse/image"
        resp = requests.post(
            ocr_endpoint,
            headers={"apikey": OCR_API_KEY},
            files={"file": ("receipt.jpg", image_bytes, "image/jpeg")},
            data={
                "language": "eng",
                "isOverlayRequired": "false",
                "OCREngine": "2"
            },
            timeout=15
        )
        if resp.status_code != 200 or not resp.text.strip():
            return "MANUAL_REVIEW", f"OCR Server busy (HTTP {resp.status_code}) -> Sent for manual check.", None

        ocr_json = resp.json()
        if ocr_json.get("IsErroredOnProcessing"):
            err_msg = str(ocr_json.get("ErrorMessage", "API Key/OCR Error"))
            print(f"OCR API Error: {err_msg}")
            return "MANUAL_REVIEW", f"OCR API Alert ({err_msg}) -> Sent for manual check.", None

        parsed_results = ocr_json.get("ParsedResults") or []
        if not parsed_results:
            return "MANUAL_REVIEW", "OCR server empty response -> Sent for manual check.", None

        first_res = next(iter(parsed_results))
        raw_text = first_res.get("ParsedText", "")
        full_text = " ".join(raw_text.lower().split())
        print("OCR TEXT:", full_text)

        if not full_text:
            return "AUTO_REJECT", "Ye payment screenshot nahi hai (Koi text nahi mila).", None

        # 0. Fake Payment Generator Template Blacklist
        fake_generator_phrases = [
            "wallet txn id",
            "updated wallet balance",
            "add money to wallet",
            "for you on phonepe",
            "top-up wallet",
            "view details check balance"
        ]
        for phrase in fake_generator_phrases:
            if phrase in full_text:
                return "AUTO_REJECT", f"Fake payment generator template detected ('{phrase}').", None

        # 1. Payment Keywords Check
        payment_keywords = ["transaction", "paid to", "upi", "successful", "success", "utr", "payment", "debited", "credited", "bharatpe", "phonepe", "gpay", "paytm", "mobikwik"]
        if not any(re.search(rf'\b{kw}\b', full_text) for kw in payment_keywords):
            return "AUTO_REJECT", "Ye valid UPI payment screenshot nahi hai.", None

        # 2. Receiver Name ya Official UPI ID Check
        has_receiver = (
            EXPECTED_RECEIVER_NAME in full_text
            or "tanu" in full_text
            or "bharatpe2z0d0g3u4z52337" in full_text
        )
        if not has_receiver:
            return "AUTO_REJECT", "Receiver name 'Tanu Das' ya official UPI ID nahi mila.", None

        # 3. Exact Amount Check (39.9, 39.90, 399, 3990 sab supported)
        amt_float = float(expected_amount)
        amt_int = int(amt_float)
        no_dot_2 = f"{amt_float:.2f}".replace(".", "")
        no_dot_1 = f"{amt_float:.1f}".replace(".", "")
        amt_patterns = [str(amt_int), f"{amt_float:.2f}", f"{amt_float:.1f}", no_dot_2, no_dot_1]
        if not any(pat in full_text for pat in amt_patterns):
            return "AUTO_REJECT", f"Amount ₹{expected_amount} match nahi hua.", None

        # 4. Flexible Date Check
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        d0, d1 = now_ist.strftime("%d"), str(now_ist.day)
        m_abbr, m_full, m_num = now_ist.strftime("%b").lower(), now_ist.strftime("%B").lower(), now_ist.strftime("%m")
        y4, y2 = now_ist.strftime("%Y"), now_ist.strftime("%y")
        valid_dates = [
            f"{d0} {m_abbr} {y4}", f"{d1} {m_abbr} {y4}",
            f"{d0} {m_abbr} '{y2}", f"{d1} {m_abbr} '{y2}",
            f"{d0} {m_abbr} {y2}", f"{d1} {m_abbr} {y2}",
            f"{d0} {m_full} {y4}", f"{d1} {m_full} {y4}",
            f"{m_abbr} {d0}, {y4}", f"{m_abbr} {d1}, {y4}",
            f"{d0}/{m_num}/{y4}", f"{d0}-{m_num}-{y4}",
            f"{d0}/{m_num}/{y2}", f"{d0}-{m_num}-{y2}"
        ]
        has_today_date = any(dt in full_text for dt in valid_dates)
        if not has_today_date:
            any_other_date = re.search(r'\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+[\']?\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', full_text)
            if any_other_date:
                return "AUTO_REJECT", f"Purani/galat date ({any_other_date.group(0)}) mili.", None

        # 5. UTR ya Time-Amount Fingerprint Lock
        utr_matches = re.findall(r'\b\d{12}\b', full_text)
        utr_number = next(iter(utr_matches), None)
        if not has_today_date and not utr_number:
            return "MANUAL_REVIEW", "Date aur UTR dono hidden hain -> Manual check required.", None

        time_tag = "notime"
        if has_today_date:
            time_ok, time_msg, time_tag = check_time_gap(full_text, now_ist)
            if not time_ok:
                return "MANUAL_REVIEW", time_msg, utr_number

        unique_lock_key = utr_number if utr_number else f"{d0}-{m_num}-{y4}_{time_tag}_{amt_int}"
        return "AUTO_APPROVE", "Verified: Tanu Das/UPI, Amount, Date/Time & Unique Lock OK.", unique_lock_key

    except Exception as e:
        print(f"Cloud OCR Analysis Error: {e}")
        return "MANUAL_REVIEW", f"OCR Timeout/Error ({e}) -> Sent for manual check.", None

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
        _, raw_amt = args
        amount = round(float(raw_amt), 2)
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
# 📦 STEP 5: USER CHECKOUT & FLOW PIPELINE (SHORT & AUTOMATIC)
# =====================================================================
@bot.message_handler(commands=['start'])
def start_payment(message):
    try:
        chat_id = message.chat.id
        msg_text = message.text.strip()
        parts = msg_text.split()
        
        if msg_text == "/start" or len(parts) in (0, 1):
            bot.reply_to(message, "👋 *Welcome to SkyBox Premium Portal!*\n\n*Kindly click on a valid product checkout link to unlock your premium contents immediately.*", parse_mode="Markdown")
            return
            
        _, raw_token = parts
        token = raw_token.strip()
        
        if token in saved_links:
            exact_amount = saved_links[token]["amount"]
            qr_img = generate_upi_qr(UPI_ID, exact_amount)
            
            caption_text = (
                "⚡ *SKYBOX PREMIUM CHECKOUT* ⚡\n\n"
                f"💰 *Pay Exact Amount:* `₹{exact_amount}`\n"
                f"📌 *Official UPI ID:* `{UPI_ID}`\n\n"
                "💎 *INSTRUCTIONS:*\n"
                "1️⃣ *Scan QR or pay via UPI ID.*\n"
                "2️⃣ *Open 'View Details' (so Date & UTR are visible) and send Screenshot below.*"
            )
            
            markup = InlineKeyboardMarkup()
            submit_btn = InlineKeyboardButton("✅ Paid? Send Screenshot", callback_data=f"sub_scr:{token}:{exact_amount}")
            markup.add(submit_btn)
            
            bot.send_photo(chat_id, qr_img, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.reply_to(message, "❌ *System Alert: The checkout link you used is either invalid or has expired!*", parse_mode="Markdown")
    except Exception as e:
        print(f"Start Error: {e}")

used_utrs = set()

def format_user_identity(user):
    uid = user.id
    fname = (user.first_name or "Customer").replace("*", "").replace("_", "").replace("[", "").replace("]", "")
    uname = f"@{user.username}".replace("_", "\\_") if user.username else "Not Set"
    profile_link = f"[{fname}](tg://user?id={uid})"
    return f"{profile_link} (`{uid}`)\n🆔 *Username:* {uname}"

@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_scr:'))
def ask_for_screenshot(call):
    try:
        chat_id = call.message.chat.id
        _, token, amount = call.data.split(':')
        
        bot.answer_callback_query(call.id)
        
        prompt_msg = bot.send_message(
            chat_id,
            "📸 <b>𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🧾 <i>Please upload your <b>Payment Screenshot</b> below to unlock your content instantly.</i>\n\n"
            "⚡ <b>Status:</b> <code>Waiting for Photo...</code>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(prompt_msg, handle_user_screenshot, token, amount, prompt_msg.message_id)
    except Exception as e:
        print(f"Ask Screenshot Callback Error: {e}")

# =====================================================================
# 📦 STEP 6: 3-WAY SMART SCREENSHOT ROUTER & ADMIN MANUAL FALLBACK
# =====================================================================
def handle_user_screenshot(message, token, amount, prompt_msg_id):
    try:
        chat_id = message.chat.id
        user_identity = format_user_identity(message.from_user)
        
        if not message.photo:
            bot.reply_to(message, "❌ *Input Error: Please send your proof strictly as a Photo/Screenshot. Click checkout button again to retry.*", parse_mode="Markdown")
            return

        status_msg = bot.send_message(chat_id, "⏳ *Verifying payment automatically... Please wait a few seconds.*", parse_mode="Markdown")
        status_msg_id = status_msg.message_id

        photo_file_id = message.photo[-1].file_id
        file_info = bot.get_file(photo_file_id)
        downloaded_bytes = bot.download_file(file_info.file_path)

        decision, reason, utr_number = analyze_screenshot(downloaded_bytes, amount)

        if utr_number and utr_number in used_utrs:
            decision = "AUTO_REJECT"
            reason = f"Duplicate UTR ({utr_number}) pehle hi use ho chuka hai."

        # CASE 1: 100% VERIFIED -> AUTO-APPROVE & DELIVER MEDIA
        if decision == "AUTO_APPROVE":
            if utr_number:
                used_utrs.add(utr_number)

            try:
                bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=chat_id, message_id=status_msg_id)
            except Exception:
                pass

            custom_msg = bot.send_message(
                chat_id,
                "<blockquote>🎉 <b>𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟!</b> ✅\n\n"
                "🚀 <b>𝗠𝗲𝗱𝗶𝗮 𝗦𝗲𝗻𝗱𝗶𝗻𝗴...</b>\n"
                "⏳ <i>Please wait a moment while your files arrive.</i></blockquote>",
                parse_mode="HTML"
            )
            time.sleep(5)
            deliver_media(chat_id, token, custom_msg.message_id)

            admin_info = (
                "✅ *Auto-Accepted & Delivered!* ✅\n\n"
                f"👤 *Customer:* {user_identity}\n"
                f"💰 *Paid Amount:* `₹{amount}`\n"
                f"🔢 *UTR:* `{utr_number}`\n"
                f"📦 *Token:* `{token}`\n\n"
                "🤖 *Status:* Bot verified Receiver Name (*Tanu Das*), Today's Date, Amount, <=2hr Time & Alignment."
            )
            bot.send_message(ADMIN_ID, admin_info, parse_mode="Markdown")

        # CASE 2: SUSPICIOUS / >2HR GAP / EDIT DOUBT -> MANUAL ADMIN TRANSFER
        elif decision == "MANUAL_REVIEW":
            admin_markup = InlineKeyboardMarkup()
            approve_btn = InlineKeyboardButton("✅ Accept (Deliver)", callback_data=f"adm_app:{chat_id}:{token}:{prompt_msg_id}:{status_msg_id}:{utr_number or 'none'}")
            reject_btn = InlineKeyboardButton("❌ Reject Claim", callback_data=f"adm_rej:{chat_id}:none:{prompt_msg_id}:{status_msg_id}:none")
            admin_markup.row(approve_btn, reject_btn)

            admin_manual_text = (
                "⚠️ *Manual Verification Required!* ⚠️\n\n"
                f"👤 *Customer:* {user_identity}\n"
                f"💰 *Expected Amount:* `₹{amount}`\n"
                f"📦 *Link Token:* `{token}`\n"
                f"🔍 *Bot Hold Reason:* _{reason}_\n\n"
                "📎 *Action Required:* Screenshot check karke neeche se manually Accept ya Reject karein."
            )
            bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_manual_text, parse_mode="Markdown", reply_markup=admin_markup)

        # CASE 3: FAKE IMAGE / WRONG NAME / WRONG DATE -> AUTO-REJECT + ALERT
        else:
            try:
                bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=chat_id, message_id=status_msg_id)
            except Exception:
                pass

            bot.send_message(
                chat_id,
                f"❌ *Automatic Verification Failed!*\n\n*Reason:* {reason}\n*Please pay exact ₹{amount} to TANU DAS today and upload a valid screenshot.*",
                parse_mode="Markdown"
            )

            admin_reject_alert = (
                "🚫 *Payment Auto-Rejected by Bot!* 🚫\n\n"
                f"👤 *Customer:* {user_identity}\n"
                f"💰 *Expected Amount:* `₹{amount}`\n"
                f"📦 *Token:* `{token}`\n"
                f"❌ *Reject Reason:* _{reason}_"
            )
            bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_reject_alert, parse_mode="Markdown")

    except Exception as e:
        print(f"Handle Screenshot Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_decision(call):
    try:
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Not Authorized!", show_alert=True)
            return
            
        action, uid_str, token, p_id_str, s_id_str, utr_val = call.data.split(':')
        target_user_id = int(uid_str)
        prompt_msg_id = int(p_id_str)
        status_msg_id = int(s_id_str)
        
        if action == "adm_app":
            if utr_val != "none":
                used_utrs.add(utr_val)

            bot.answer_callback_query(call.id, "✅ Payment Approved!")
            bot.edit_message_caption(
                chat_id=ADMIN_ID, 
                message_id=call.message.message_id, 
                caption=call.message.caption + "\n\n🟢 **Status: Manually Approved & Delivered**"
            )
            
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception:
                pass
                
            custom_msg = bot.send_message(
                target_user_id,
                "<blockquote>🎉 <b>𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟!</b> ✅\n\n"
                "🚀 <b>𝗠𝗲𝗱𝗶𝗮 𝗦𝗲𝗻𝗱𝗶𝗻𝗴...</b>\n"
                "⏳ <i>Please wait a moment while your files arrive.</i></blockquote>",
                parse_mode="HTML"
            )
            time.sleep(5)
            deliver_media(target_user_id, token, custom_msg.message_id)
            
        elif action == "adm_rej":
            bot.answer_callback_query(call.id, "❌ Claim Rejected!")
            bot.edit_message_caption(
                chat_id=ADMIN_ID, 
                message_id=call.message.message_id, 
                caption=call.message.caption + "\n\n🔴 **Status: Manually Rejected by Admin**"
            )
            
            try:
                bot.delete_message(chat_id=target_user_id, message_id=prompt_msg_id)
                bot.delete_message(chat_id=target_user_id, message_id=status_msg_id)
            except Exception:
                pass
                
            bot.send_message(
                target_user_id, 
                "❌ *Verification Failed: Payment could not be confirmed. Please confirm you paid the exact amount, send a valid screenshot and try again.*", 
                parse_mode="Markdown"
            )
            
    except Exception as e:
        print(f"Admin Callback Error: {e}")

# =====================================================================
# 📦 STEP 7: PRIVATE CHANNEL MESSAGES AUTO-FORWARD ENGINE
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
            for msg_id in range(1, 100):
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=channel_id, message_id=msg_id)
                    media_forwarded = True
                    time.sleep(1.0) 
                except Exception:
                    continue
        
        if media_forwarded:
            time.sleep(1)
            try:
                bot.delete_message(chat_id=chat_id, message_id=custom_msg_id)
            except Exception:
                pass
        else:
            bot.send_message(chat_id, "⚠️ *System Notice: Target channel ID is either incorrect or bot is not added as Admin in the private channel.*", parse_mode="Markdown")
                    
    except Exception as e:
        print(f"Global Delivery Engine Error: {e}")

# =====================================================================
# 🚀 STEP 8: MAIN LOOP RUNNER CONTROL
# =====================================================================
if __name__ == "__main__":
    keep_alive()
    time.sleep(5)
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            print("🚀 SkyBox Forwarder Pro Bot is Running on Render...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except Exception as e:
            print(f"Loop Crash Restarter: {e}")
            time.sleep(3)
