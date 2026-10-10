import json
import os
import telebot
from telebot import types
import requests

# Configuration
TOKEN = "8886471898:AAFZ77-c2skU1Qpf1a3ypwqQLyssVnTh6KM"
ADMIN_ID = 8764166382
JOIN_BONUS = 10
REF_POINT = 6
LOOKUP_COST = 2

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# Database load and save functions
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "banned": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "banned": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Start Command & Referral Handling
@bot.message_handler(commands=['start'])
def send_welcome(message):
    db = load_db()
    user_id_str = str(message.from_user.id)
    
    if message.from_user.id in db["banned"]:
        bot.reply_to(message, "⚠️ Apnake bot theke ban kora hoyeche.")
        return

    # New user registration & join bonus
    if user_id_str not in db["users"]:
        db["users"][user_id_str] = {
            "balance": JOIN_BONUS,
            "username": message.from_user.username or "None",
            "name": message.from_user.first_name
        }
        
        # Check for referral link
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            referrer_id = args[1]
            if referrer_id in db["users"] and referrer_id != user_id_str:
                db["users"][referrer_id]["balance"] += REF_POINT
                try:
                    bot.send_message(
                        int(referrer_id), 
                        f"🎉 Abhinandan! Apni ekta successful referral theke {REF_POINT} point peyechhen."
                    )
                except:
                    pass
        save_db(db)

    # Main Menu Reply Keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔍 Instagram Lookup"), types.KeyboardButton("👤 My Profile"))
    markup.add(types.KeyboardButton("🎁 Earn Points"), types.KeyboardButton("ℹ️ Help"))
    
    welcome_text = (
        f"👋 Assalamu Alaikum, **{message.from_user.first_name}**!\n\n"
        f"Instagram Full Info & Lookup Bot-e apnake shagotom.\n"
        f"• Join Bonus: **{JOIN_BONUS} Points**\n"
        f"• Per Lookup Cost: **{LOOKUP_COST} Points**\n"
        f"• Referral Bonus: **{REF_POINT} Points**\n\n"
        f"Niche theke button select korun:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# Button Handlers
@bot.message_handler(func=lambda message: message.text == "👤 My Profile")
def my_profile(message):
    db = load_db()
    user_id_str = str(message.from_user.id)
    if user_id_str in db["users"]:
        balance = db["users"][user_id_str]["balance"]
        ref_link = f"https://t.me/insta_infoKVbot?start={message.from_user.id}"
        text = (
            f"👤 **User Profile**\n\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"💰 Balance: **{balance} Points**\n\n"
            f"🔗 Referral Link:\n`{ref_link}`\n"
            f"(Prottek refer-e paben {REF_POINT} points!)"
        )
        bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🎁 Earn Points")
def earn_points(message):
    ref_link = f"https://t.me/insta_infoKVbot?start={message.from_user.id}"
    text = (
        f"🎁 **Free Points Arjon Korun**\n\n"
        f"Bondhuder kache nicher link share korun. Kew ei link theke join korle apni paben **{REF_POINT} points**!\n\n"
        f"`{ref_link}`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def help_menu(message):
    text = (
        f"ℹ️ **Help & Guide**\n\n"
        f"1. Lookup korar jonno '🔍 Instagram Lookup' button-e click korun.\n"
        f"2. Tarpor Instagram username din (e.g., `tech_master_a2z`).\n"
        f"3. Prottek lookup-e **{LOOKUP_COST} points** kete nebe.\n"
        f"4. Point sesh hole referral er madhhon-e free point earn korte parben."
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔍 Instagram Lookup")
def start_lookup(message):
    db = load_db()
    user_id_str = str(message.from_user.id)
    
    if user_id_str not in db["users"] or db["users"][user_id_str]["balance"] < LOOKUP_COST:
        bot.reply_to(message, f"❌ Apnar sufficient balance nei! Lookup korar jonno kompokhe {LOOKUP_COST} points lagbe. Bondhuder refer kore point earn korun.")
        return

    msg = bot.reply_to(message, "🔍 Je Instagram profile-ti lookup korte chan tar **username** din (without @ symbol):")
    bot.register_next_step_handler(msg, process_instagram_lookup)

def process_instagram_lookup(message):
    # Check if user sent text or something else
    if not message.text:
        bot.reply_to(message, "❌ Doya kore sothik Instagram username din.")
        return

    username = message.text.strip().replace("@", "")
    user_id_str = str(message.from_user.id)
    db = load_db()
    
    if user_id_str not in db["users"] or db["users"][user_id_str]["balance"] < LOOKUP_COST:
        bot.reply_to(message, "❌ Apnar balance sesh ba register kora nei!")
        return

    wait_msg = bot.reply_to(message, "⏳ Instagram data fetch hoccha, ektu opeksha korun...")

    # --- Integrated API Call ---
    api_url = f"https://techmster.site/api/instagram-info.php?username={username}"
    
    try:
        response = requests.get(api_url, timeout=15)
        data = response.json()
        
        if not data or "error" in data:
            bot.edit_message_text("❌ Profile pawa jayni ba API te kono somossa hocche.", chat_id=message.chat.id, message_id=wait_msg.message_id)
            return

        # Deduct Points after successful API response
        db["users"][user_id_str]["balance"] -= LOOKUP_COST
        save_db(db)

        # Extracting details safely based on your API structure
        username_res = data.get('username', username)
        full_name = data.get('full_name', 'N/A')
        followers = data.get('followers', 'N/A')
        following = data.get('following', 'N/A')
        posts = data.get('posts', 'N/A')
        bio = data.get('bio', 'N/A')
        email = data.get('email', 'N/A')
        website = data.get('website', 'N/A')
        is_verified = data.get('is_verified', False)
        is_private = data.get('is_private', False)

        result_text = (
            f"✅ **Instagram Lookup Result**\n\n"
            f"👤 Username: `{username_res}`\n"
            f"📌 Full Name: {full_name}\n"
            f"👥 Followers: {followers}\n"
            f"👣 Following: {following}\n"
            f"📸 Posts: {posts}\n"
            f"✍️ Bio: {bio}\n"
            f"📧 Email: {email}\n"
            f"🌐 Website: {website}\n"
            f"✔ Verified: {'Yes' if is_verified else 'No'}\n"
            f"🔒 Private: {'Yes' if is_private else 'No'}\n\n"
            f"📉 Balance Kete newa hoyeche: {LOOKUP_COST} points\n"
            f"💰 Baki Balance: {db['users'][user_id_str]['balance']} points"
        )
        bot.edit_message_text(result_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ Data fetch korte somossa hoyeche ba server down ache.", chat_id=message.chat.id, message_id=wait_msg.message_id)

# --- ADMIN PANEL COMMANDS ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text = (
        f"🛠 **Admin Control Panel**\n\n"
        f"• `/stats` - Total users & bot statistics\n"
        f"• `/users` - User list count\n"
        f"• `/broadcast <msg>` - Send broadcast to all users\n"
        f"• `/gift <userid> <amount>` - Gift points to user\n"
        f"• `/ban <userid>` - Ban user\n"
        f"• `/unban <userid>` - Unban user"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    db = load_db()
    total_users = len(db["users"])
    banned_users = len(db["banned"])
    bot.reply_to(message, f"📊 **Bot Statistics**\n\n• Total Users: {total_users}\n• Banned Users: {banned_users}")

@bot.message_handler(commands=['users'])
def admin_userlist(message):
    if message.from_user.id != ADMIN_ID:
        return
    db = load_db()
    user_count = len(db["users"])
    bot.reply_to(message, f"👥 Total Registered Users: {user_count}")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    text_to_send = message.text.replace("/broadcast", "").strip()
    if not text_to_send:
        bot.reply_to(message, "⚠️ Broadcast message ti faka rakha jabe na. Byabohar: `/broadcast Your Message`", parse_mode="Markdown")
        return
    
    db = load_db()
    success = 0
    failed = 0
    
    for uid in db["users"]:
        try:
            bot.send_message(int(uid), f"📢 **Announcement:**\n\n{text_to_send}", parse_mode="Markdown")
            success += 1
        except:
            failed += 1
            
    bot.reply_to(message, f"✅ Broadcast Complete!\n• Success: {success}\n• Failed: {failed}")

@bot.message_handler(commands=['gift'])
def admin_gift(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        bot.reply_to(message, "⚠️ Sothik format: `/gift <userid> <amount>`", parse_mode="Markdown")
        return
    
    target_id = args[1]
    amount = int(args[2])
    db = load_db()
    
    if target_id in db["users"]:
        db["users"][target_id]["balance"] += amount
        save_db(db)
        bot.reply_to(message, f"✅ User {target_id}-ke {amount} points gift kora holo.")
        try:
            bot.send_message(int(target_id), f"🎁 Admin apnake {amount} points gift korechen!")
        except:
            pass
    else:
        bot.reply_to(message, "❌ User database-e pawa jayni.")

@bot.message_handler(commands=['ban'])
def admin_ban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Sothik format: `/ban <userid>`")
        return
    try:
        target_id = int(args[1])
        db = load_db()
        if target_id not in db["banned"]:
            db["banned"].append(target_id)
            save_db(db)
            bot.reply_to(message, f"✅ User {target_id} ban kora hoyeche.")
    except:
        bot.reply_to(message, "⚠️ Sothik User ID din.")

@bot.message_handler(commands=['unban'])
def admin_unban(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Sothik format: `/unban <userid>`")
        return
    try:
        target_id = int(args[1])
        db = load_db()
        if target_id in db["banned"]:
            db["banned"].remove(target_id)
            save_db(db)
            bot.reply_to(message, f"✅ User {target_id} unban kora hoyeche.")
    except:
        bot.reply_to(message, "⚠️ Sothik User ID din.")

if __name__ == "__main__":
    print("Bot is running successfully...")
    bot.infinity_polling(none_stop=True)
