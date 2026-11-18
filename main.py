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
BOT_TOKEN = "8963839676:AAHGTnd6QcysW9DrCUMQrnW8xRf52J-wBe8" 
ADMIN_ID = 8393210427
UPI_ID = "BHARATPE2Z0D0G3U4Z52337@unitype"
BOT_USERNAME = "SkyBoxx_bot"

# Yahan apni free OCR.space API key dalein (default "helloworld" test ke liye hai)
OCR_API_KEY = "K8822071071352488957"

EXPECTED_RECEIVER_NAME = "tanu das"
MAX_TIME_GAP_MINUTES = 120

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
    "a3a1d01468ba": {"amount": 65.00, "channel_id": "-1004374958890"},
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
# 📦 STEP 3: STRICT HAND-EDIT DETECTOR + FLEXIBLE OCR ENGINE
# =====================================================================
from PIL import ImageChops, ImageStat

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

def strict_forensic_check(image_bytes, pil_img):
    raw_lower = image_bytes[:80000].lower()
    editor_markers = [b"gemini", b"imagen", b"synthid", b"c2pa", b"photoshop", b"picsart", b"canva", b"snapseed", b"remini"]
    for marker in editor_markers:
        if marker in raw_lower:
            return True, f"AI/Editing tool signature ({marker.decode()}) detected."

    w, h = pil_img.size
    if max(w, h) not in (1280, 2560) and h > w * 1.8:
        return True, f"AI/Gemini modified resolution ({w}x{h}px) detected."
    
    try:
        rgb_img = pil_img.convert("RGB")
        buf = io.BytesIO()
        rgb_img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        recompressed = Image.open(buf)
        diff = ImageChops.difference(rgb_img, recompressed)
        stat = ImageStat.Stat(diff)
        if max([b - a for a, b in stat.extrema]) > 58 and (sum(stat.mean) / 3.0) > 3.2:
            return True, "Image tampering / AI smudge patch detected."
    except Exception:
        pass
    return False, "Clean"

def check_time_gap(full_text, now_ist):
    matches_12h = re.findall(r'\b(0?[1-9]|1[0-2]):([0-5][0-9])\s*(am|pm)\b', full_text)
    if matches_12h:
        first_hr, first_mn, first_mer = next(iter(matches_12h))
        hr = int(first_hr)
        if first_mer == "pm" and hr != 12:
            hr += 12
        elif first_mer == "am" and hr == 12:
            hr = 0
        receipt_dt = now_ist.replace(hour=hr, minute=int(first_mn), second=0, microsecond=0)
        diff_minutes = (now_ist - receipt_dt).total_seconds() / 60.0
        if diff_minutes + 5 <= 0:
            return False, "Receipt time current time se aage hai.", None
        if diff_minutes > MAX_TIME_GAP_MINUTES:
            return False, "Time gap 2 ghante se zyada hai.", None
        return True, "Time gap within 2 hours", f"{int(first_hr):02d}:{first_mn}{first_mer}"
    
    matches_24h = re.findall(r'\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b', full_text)
    if matches_24h:
        hr_str, min_str = next(iter(matches_24h))
        hr, mn = int(hr_str), int(min_str)
        receipt_dt = now_ist.replace(hour=hr, minute=mn, second=0, microsecond=0)
        diff_minutes = (now_ist - receipt_dt).total_seconds() / 60.0
        if diff_minutes >= -5 and MAX_TIME_GAP_MINUTES >= diff_minutes:
            return True, "Time gap within 2 hours (24h)", f"{hr:02d}:{mn:02d}"
        return False, "Time gap 2 ghante se zyada hai ya time match nahi hua.", None
    
    return False, "Receipt ka time detect nahi hua.", None

def analyze_screenshot(image_bytes, expected_amount):
    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_w, img_h = pil_img.size

        # 1. PEHLE OCR CHALAYEIN
        ocr_endpoint = "https://api.ocr.space/parse/image"
        resp = requests.post(
            ocr_endpoint,
            headers={"apikey": OCR_API_KEY},
            files={"file": ("receipt.jpg", image_bytes, "image/jpeg")},
            data={
                "language": "eng",
                "isOverlayRequired": "true",
                "OCREngine": "1"
            },
            timeout=12
        )
        if resp.status_code != 200 or not resp.text.strip():
            return "MANUAL_REVIEW", f"OCR Server busy (HTTP {resp.status_code}) -> Sent for manual check.", None

        ocr_json = resp.json()
        if ocr_json.get("IsErroredOnProcessing"):
            err_msg = str(ocr_json.get("ErrorMessage", "API Key/OCR Error"))
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

        # 2. Payment Keywords Check
        payment_keywords = ["transaction", "paid to", "upi", "successful", "success", "utr", "payment", "debited", "credited", "bharatpe", "phonepe", "gpay", "paytm", "mobikwik"]
        if not any(re.search(rf'\b{kw}\b', full_text) for kw in payment_keywords):
            return "AUTO_REJECT", "Ye valid UPI payment screenshot nahi hai.", None

        # 3. Receiver Name Check
        if EXPECTED_RECEIVER_NAME not in full_text and "tanu" not in full_text:
            return "AUTO_REJECT", "Receiver name 'Tanu Das' match nahi hua.", None

        # 4. UPI ID Check
        upi_handles = re.findall(r'[a-z0-9.\-_]+@[a-z]{2,}', full_text)
        if upi_handles:
            if not any("bharatpe2z0d0g3u4z52337" in u for u in upi_handles):
                return "AUTO_REJECT", f"Galat UPI ID ({next(iter(upi_handles))}) dikh raha hai.", None

        # 5. Exact Amount Check
        amt_float = float(expected_amount)
        amt_int = int(amt_float)
        amt_patterns = [str(amt_int), f"{amt_float:.2f}", f"{amt_float:.1f}"]
        if not any(pat in full_text for pat in amt_patterns):
            return "AUTO_REJECT", f"Amount match nahi hua (Expected: ₹{amt_int}).", None

        # 6. Date Check
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

        # 7. ULTRA-STRICT HAND-EDIT & PATCH DETECTOR (Har Line Ki Font Height, Alignment & Color Patch Check)
        overlay_lines = first_res.get("TextOverlay", {}).get("Lines", [])
        line_boxes = []
        for ln in overlay_lines:
            words = ln.get("Words", [])
            if not words:
                continue
            txt = ln.get("LineText", "").strip()
            txt_low = txt.lower()
            tops = [float(w.get("Top", 0)) for w in words]
            heights = [float(w.get("Height", 10)) for w in words]
            lefts = [float(w.get("Left", 0)) for w in words]
            widths = [float(w.get("Width", 10)) for w in words]
            avg_top = sum(tops) / len(tops)
            avg_h = sum(heights) / len(heights)

            # A. Har Important Line (Date, Time, Amount, UTR) par Font Height Jump Check!
            is_critical_line = (
                any(pat in txt_low for pat in amt_patterns)
                or any(m in txt_low for m in [m_abbr, m_full])
                or (":" in txt_low)
                or ("successful" in txt_low)
            )
            if is_critical_line and len(heights) >= 2:
                # Agar ek hi line mein koi word doosre se 3.2px bhi bada/chhota hai (e.g. '18 November' chhota aur '09:04 PM' bada!)
                if (max(heights) - min(heights)) > 3.2:
                    return "MANUAL_REVIEW", f"Hand-edit font size mismatch detected in '{txt}'.", None
                # Agar ek hi line mein words upar-neeche (> 3.0px) paste kiye gaye hain
                if (max(tops) - min(tops)) > 3.0:
                    return "MANUAL_REVIEW", f"Hand-edit alignment shift detected in '{txt}'.", None

            # B. Green Header White-Patch Detector (Date/Time line ke peeche safed dabba pakadne ke liye!)
            if (any(m in txt_low for m in [m_abbr, m_full]) or "successful" in txt_low) and avg_top < (img_h * 0.45):
                x1 = max(0, int(min(lefts)) - 4)
                y1 = max(0, int(min(tops)) - 4)
                x2 = min(img_w, int(max(l + w for l, w in zip(lefts, widths))) + 4)
                y2 = min(img_h, int(max(t + h for t, h in zip(tops, heights))) + 4)
                if x2 > x1 and y2 > y1:
                    crop = pil_img.crop((x1, y1, x2, y2))
                    pixels = list(crop.getdata())
                    green_px = sum(1 for r, g, b in pixels if g > r + 25 and g > b + 25)
                    white_px = sum(1 for r, g, b in pixels if r > 235 and g > 235 and b > 235)
                    # Agar green header ke andar safed patch dabba bana hai (jaise 09:04 PM ke peeche white box!)
                    if green_px > 20 and white_px > 40:
                        return "MANUAL_REVIEW", f"White sticker/patch edit detected over green header in '{txt}'.", None

            line_boxes.append({"text": txt, "lower": txt_low, "top": avg_top, "height": avg_h})

        # 8. Amount Row Alignment Check (₹ aur 30 ke beech height/top mismatch)
        for lb in line_boxes:
            if any(pat in lb["lower"] for pat in amt_patterns):
                peers = [o for o in line_boxes if o != lb and (lb["height"] * 0.9) > abs(o["top"] - lb["top"])]
                for p in peers:
                    if abs(p["top"] - lb["top"]) > 3.5 or abs(p["height"] - lb["height"]) > 5.0:
                        return "MANUAL_REVIEW", f"Edited amount box mismatch ('{lb['text']}' vs '{p['text']}').", None

        # 9. General Forensic & Resolution Check
        is_tampered, tamper_reason = strict_forensic_check(image_bytes, pil_img)
        if is_tampered:
            return "MANUAL_REVIEW", tamper_reason, None

        # 10. UTR Optional Logic (Date+Time ya UTR dono se Auto-Approve + Repeat Lock)
        utr_matches = re.findall(r'\b\d{12}\b', full_text)
        utr_number = next(iter(utr_matches), None)

        time_tag = "notime"
        if has_today_date:
            time_ok, time_msg, time_tag = check_time_gap(full_text, now_ist)
            if not time_ok:
                return "MANUAL_REVIEW", time_msg, utr_number
        else:
            # Agar Date hidden hai aur UTR bhi hidden hai -> Manual Review
            if not utr_number:
                return "MANUAL_REVIEW", "Date aur UTR dono hidden hain -> Manual check required.", None

        # Unique Lock (UTR hai toh UTR lock, warna Date+Time+Amount lock)
        unique_lock_key = utr_number if utr_number else f"{d0}-{m_num}-{y4}_{time_tag}_{amt_int}"

        return "AUTO_APPROVE", "Verified: Unedited Screenshot, Tanu Das/UPI, Amount & Date/Time/UTR OK.", unique_lock_key

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
