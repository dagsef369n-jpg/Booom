import os
import csv
from io import StringIO
from flask import Flask
from threading import Thread
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running actively!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_web)
    t.start()

BOT_TOKEN = "8692852807:AAHOZDtwRXNdtkBAMx86fnPtKo8J4b-u5gE"
SECRET_PASSWORD = "schooladmin123" 
DATA_FILE = "school_data.json"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

db = {
    "director_id": None,
    "admin_7_id": None,
    "admin_8_id": None,
    "teachers": {},          
    "parent_sessions": {},   
    "message_map": {},       
    "parents": {},           
    "students": {},          
    "registration_state": {},
    "broadcasting_state": {},
    "admin7_broadcasting_state": {},
    "admin8_broadcasting_state": {},
    "teacher_states": {},
    "parent_classrooms": {},        
    "teacher_broadcasting_state": {},
    "marks": {}                     
}

def load_db():
    global db
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            db.update(json.load(f))
    for key in ["parents", "students", "registration_state", "broadcasting_state", "admin7_broadcasting_state", "admin8_broadcasting_state", "teacher_states", "parent_classrooms", "teacher_broadcasting_state", "marks"]:
        if key not in db:
            db[key] = {}

def save_db():
    with open(DATA_FILE, 'w') as f:
        json.dump(db, f)

def get_grade_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Check All Children Marks", callback_data="check_marks")],
        [InlineKeyboardButton("Grade 7", callback_data="grade_7")],
        [InlineKeyboardButton("Grade 8", callback_data="grade_8")]
    ])

def get_section_keyboard(grade):
    sections = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    keyboard, row = [], []
    for sec in sections:
        row.append(InlineKeyboardButton(f"Section {sec}", callback_data=f"sec_{grade}_{sec}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    keyboard.append([InlineKeyboardButton("🔙 Back to Grades", callback_data="back_to_grades")])
    return InlineKeyboardMarkup(keyboard)

def get_director_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Send Broadcast to All Parents", callback_data="dir_broadcast")]])

def get_admin7_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Send Broadcast to Grade 7 Parents", callback_data="admin7_broadcast")]])

def get_admin8_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Send Broadcast to Grade 8 Parents", callback_data="admin8_broadcast")]])

def get_teacher_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Send Class Broadcast", callback_data="teach_broadcast")],
        [InlineKeyboardButton("📊 Manage Student Marks & Behavior", callback_data="teach_manage_student")]
    ])

def get_more_children_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ I have another child", callback_data="add_more_child")],
        [InlineKeyboardButton("✅ No other child, finish registration", callback_data="finish_registration")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in db["parent_sessions"]:
        del db["parent_sessions"][chat_id]
        save_db()
    if chat_id in db["parents"]:
        student_ids = db["parents"][chat_id]
        ids_str = ", ".join(student_ids) if isinstance(student_ids, list) else student_ids
        await update.message.reply_text(
            f"👋 Welcome back! You are linked to Student ID(s): <b>{ids_str}</b>.\n\n"
            f"<i>(If you want to reset or add children again, type /changeid)</i>\n\nWhat would you like to do?",
            parse_mode="HTML", reply_markup=get_grade_keyboard()
        )
    else:
        db["registration_state"][chat_id] = "waiting_for_id"
        save_db()
        await update.message.reply_text(
            "👋 እንኳን ደና መጡ! Welcome to the SWA School Communication Bot!\n\n"
            "To receive behavior alerts and grades, please reply with your child's unique Student ID (Example: SWA-105)."
        )

async def change_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in db["parents"]:
        old_ids = db["parents"][chat_id]
        if isinstance(old_ids, list):
            for s_id in old_ids:
                if s_id in db["students"]: del db["students"][s_id]
        del db["parents"][chat_id]
        db["registration_state"][chat_id] = "waiting_for_id"
        save_db()
        await update.message.reply_text("🔄 <b>Family Profile Reset!</b>\nPlease type your first child's unique Student ID.", parse_mode="HTML")
    else:
        await update.message.reply_text("You are not linked to any student right now. Type /start to begin.")

async def exit_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    if chat_id in db["parent_sessions"]:
        del db["parent_sessions"][chat_id]
        save_db()
        await update.message.reply_text("You have disconnected from the chat. Use /start to open the menu.")
    else:
        await update.message.reply_text("You are not currently connected to any teacher.")

async def set_director(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1 and context.args[0] == SECRET_PASSWORD:
        db["director_id"] = update.message.chat_id
        save_db()
        await update.message.reply_text("👑 ✅ Registered as Director.\nType /director to open panel.")
    else:
        await update.message.reply_text("❌ Incorrect password. Usage: /setdirector schooladmin123")

async def set_admin7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1 and context.args[0] == SECRET_PASSWORD:
        db["admin_7_id"] = update.message.chat_id
        save_db()
        await update.message.reply_text("🏛️ ✅ Registered as Grade 7 Admin.\nType /admin7 to open panel.")
    else:
        await update.message.reply_text("❌ Incorrect password. Usage: /setadmin7 schooladmin123")

async def set_admin8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 1 and context.args[0] == SECRET_PASSWORD:
        db["admin_8_id"] = update.message.chat_id
        save_db()
        await update.message.reply_text("🏛️ ✅ Registered as Grade 8 Admin.\nType /admin8 to open panel.")
    else:
        await update.message.reply_text("❌ Incorrect password. Usage: /setadmin8 schooladmin123")

async def set_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) >= 4:
        grade, sec, password = context.args[0], context.args[1].upper(), context.args[-1]
        name = " ".join(context.args[2:-1])
        if password == SECRET_PASSWORD:
            key = f"{grade}_{sec}"
            db["teachers"][key] = {"chat_id": update.message.chat_id, "name": name}
            save_db()
            await update.message.reply_text(f"✅ Registered! Homeroom Teacher for Grade {grade}{sec}: {name}.\nType /teacher to open dashboard.")
        else:
            await update.message.reply_text("❌ Invalid password.")
    else:
        await update.message.reply_text("❌ Usage: /setteacher [Grade] [Section] [Name] schooladmin123")

async def director_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == db.get("director_id"):
        await update.message.reply_text("👑 <b>Director Control Panel</b>", reply_markup=get_director_keyboard(), parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Access Denied.")

async def admin7_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == db.get("admin_7_id"):
        await update.message.reply_text("🏛️ <b>Grade 7 Admin Control Panel</b>", reply_markup=get_admin7_keyboard(), parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Access Denied.")

async def admin8_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == db.get("admin_8_id"):
        await update.message.reply_text("🏛️ <b>Grade 8 Admin Control Panel</b>", reply_markup=get_admin8_keyboard(), parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Access Denied.")

async def teacher_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    teacher_key = next((k for k, d in db["teachers"].items() if d["chat_id"] == chat_id), None)
    if not teacher_key:
        await update.message.reply_text("❌ Access Denied: Only registered teachers can use this.")
        return
    grade_sec = teacher_key.replace("_", "")
    await update.message.reply_text(f"👨‍🏫 <b>Teacher Control Panel (Grade {grade_sec})</b>", reply_markup=get_teacher_keyboard(), parse_mode="HTML")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in [db.get("director_id"), db.get("admin_7_id"), db.get("admin_8_id")] and not any(t["chat_id"] == chat_id for t in db["teachers"].values()):
        await update.message.reply_text("❌ Access Denied.")
        return
    doc = update.message.document
    if not doc.file_name.endswith('.csv'):
        await update.message.reply_text("❌ Upload a valid .csv file.")
        return
    file = await context.bot.get_file(doc.file_id)
    byte_array = await file.download_as_bytearray()
    reader = csv.reader(StringIO(byte_array.decode('utf-8')))
    next(reader, None)
    count = 0
    for row in reader:
        if len(row) >= 3:
            s_id, sub, score = row[0].strip().upper(), row[1].strip(), row[2].strip()
            if s_id not in db["marks"]: db["marks"][s_id] = {}
            db["marks"][s_id][sub] = score
            count += 1
    save_db()
    await update.message.reply_text(f"✅ Successfully updated {count} marks!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data, chat_id_str, chat_id_int = query.data, str(query.message.chat_id), query.message.chat_id

    if data == "add_more_child":
        db["registration_state"][chat_id_str] = "waiting_for_id"
        save_db()
        await query.edit_message_text("📝 Type your next child's Student ID:")
    elif data == "finish_registration":
        db["registration_state"].pop(chat_id_str, None)
        save_db()
        await query.edit_message_text("✅ Registration Complete!", reply_markup=get_grade_keyboard())
    elif data == "check_marks":
        s_ids = db["parents"].get(chat_id_str, [])
        report = "📊 <b>Family Marks Report</b>\n\n"
        for s_id in s_ids:
            report += f"👨‍🎓 <b>{s_id}</b>\n"
            for sub, sc in db["marks"].get(s_id, {}).items():
                report += f" • {sub}: {sc}\n"
            report += "\n"
        await query.edit_message_text(report, parse_mode="HTML", reply_markup=get_grade_keyboard())
    elif data == "dir_broadcast":
        db["broadcasting_state"][chat_id_str] = True
        save_db()
        await query.edit_message_text("📝 Type your broadcast message to ALL parents:")
    elif data == "admin7_broadcast":
        db["admin7_broadcasting_state"][chat_id_str] = True
        save_db()
        await query.edit_message_text("📝 Type your broadcast to Grade 7 parents:")
    elif data == "admin8_broadcast":
        db["admin8_broadcasting_state"][chat_id_str] = True
        save_db()
        await query.edit_message_text("📝 Type your broadcast to Grade 8 parents:")
    elif data == "teach_broadcast":
        t_key = next((k for k, d in db["teachers"].items() if d["chat_id"] == chat_id_int), None)
        if t_key:
            db["teacher_broadcasting_state"][chat_id_str] = t_key
            save_db()
            await query.edit_message_text("📝 Type your class broadcast message:")
    elif data == "teach_manage_student":
        db["teacher_managing_state"] = db.get("teacher_managing_state", {})
        db["teacher_managing_state"][chat_id_str] = True
        save_db()
        await query.edit_message_text("👨‍🎓 Type the Student ID you want to manage (e.g. SWA-600):")
    elif data.startswith("menu_mark_"):
        s_id = data.replace("menu_mark_", "")
        await query.edit_message_text(f"📊 Upload a CSV file for {s_id} with format:\n<code>Student ID, Subject, Mark</code>", parse_mode="HTML")
    elif data.startswith("behave_good_") or data.startswith("behave_bad_"):
        parts = data.split("_")
        s_id, b_type = parts[2], parts[1]
        db["teacher_states"][chat_id_str] = {"student_id": s_id, "type": b_type}
        save_db()
        await query.edit_message_text(f"📝 Type your {b_type} behavior comment for {s_id}:")
    elif data == "back_to_grades":
        await query.edit_message_text("What would you like to do?", reply_markup=get_grade_keyboard())
    elif data.startswith("grade_"):
        await query.edit_message_text("Select section:", reply_markup=get_section_keyboard(data.split("_")[1]))
    elif data.startswith("sec_"):
        _, g, s = data.split("_")
        t = db["teachers"].get(f"{g}_{s}")
        if t:
            await query.edit_message_text(f"Teacher: {t['name']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Connect", callback_data=f"connect_{g}_{s}")]]))
        else:
            await query.edit_message_text("No teacher assigned yet.")
    elif data.startswith("connect_"):
        key = data.replace("connect_", "")
        db["parent_sessions"][chat_id_str] = key
        db["parent_classrooms"][chat_id_str] = key
        save_db()
        await query.edit_message_text("✅ Connected! Type messages below. Type /exit when done.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return 
    chat_id, text = str(update.message.chat_id), update.message.text.strip()

    if text.startswith('/'): return

    if db.get("admin7_broadcasting_state", {}).pop(chat_id, None):
        save_db()
        for p in db["parents"]:
            try: await context.bot.send_message(chat_id=p, text=f"📢 <b>Grade 7 Announcement:</b>\n\n{text}", parse_mode="HTML")
            except: pass
        await update.message.reply_text("✅ Grade 7 broadcast sent!")
        return

    if db.get("admin8_broadcasting_state", {}).pop(chat_id, None):
        save_db()
        for p in db["parents"]:
            try: await context.bot.send_message(chat_id=p, text=f"📢 <b>Grade 8 Announcement:</b>\n\n{text}", parse_mode="HTML")
            except: pass
        await update.message.reply_text("✅ Grade 8 broadcast sent!")
        return

    if db.get("teacher_managing_state", {}).pop(chat_id, None):
        save_db()
        s_id = text.upper()
        await update.message.reply_text(f"👨‍🎓 Student: {s_id}", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Add Mark", callback_data=f"menu_mark_{s_id}")],
            [InlineKeyboardButton("🧠 Behavior Report", callback_data=f"menu_behavior_{s_id}")]
        ]))
        return

    if db.get("registration_state", {}).get(chat_id) == "waiting_for_id":
        s_id = text.upper()
        if chat_id not in db["parents"]: db["parents"][chat_id] = []
        if s_id not in db["parents"][chat_id]: db["parents"][chat_id].append(s_id)
        db["students"][s_id] = chat_id
        db["registration_state"][chat_id] = "asking_more"
        save_db()
        await update.message.reply_text(f"✅ Added {s_id}!", reply_markup=get_more_children_keyboard())
        return

    if db.get("teacher_broadcasting_state", {}).pop(chat_id, None):
        save_db()
        for p, c in db.get("parent_classrooms", {}).items():
            if c == db.get("teacher_broadcasting_state", {}).get(chat_id):
                try: await context.bot.send_message(chat_id=p, text=f"📢 <b>Class Announcement:</b>\n\n{text}", parse_mode="HTML")
                except: pass
        await update.message.reply_text("✅ Class broadcast sent!")
        return

    if db.get("broadcasting_state", {}).pop(chat_id, None):
        save_db()
        for p in db["parents"]:
            try: await context.bot.send_message(chat_id=p, text=f"📢 <b>Director Announcement:</b>\n\n{text}", parse_mode="HTML")
            except: pass
        await update.message.reply_text("✅ School-wide broadcast sent!")
        return

    if chat_id in db["teacher_states"]:
        state = db.get("teacher_states").pop(chat_id)
        save_db()
        p_chat = db["students"].get(state["student_id"])
        prefix = "🌟 Positive Update" if state["type"] == "good" else "🚨 Behavior Alert"
        try: await context.bot.send_message(chat_id=p_chat, text=f"{prefix} for {state['student_id']}:\n\n{text}", parse_mode="HTML")
        except: pass
        await update.message.reply_text("✅ Sent to parent!")
        return

    if chat_id in db["parent_sessions"]:
        key = db["parent_sessions"][chat_id]
        t_chat = db["teachers"].get(key, {}).get("chat_id")
        if t_chat:
            await context.bot.send_message(chat_id=t_chat, text=f"👤 Parent message:\n{text}")
        return

    await update.message.reply_text("Please type /start to begin.")

if __name__ == '__main__':
    load_db()
    keep_alive()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('exit', exit_chat))
    app.add_handler(CommandHandler('changeid', change_id))
    app.add_handler(CommandHandler('setdirector', set_director))
    app.add_handler(CommandHandler('setadmin7', set_admin7))
    app.add_handler(CommandHandler('setadmin8', set_admin8))
    app.add_handler(CommandHandler('setteacher', set_teacher))
    app.add_handler(CommandHandler('director', director_panel))
    app.add_handler(CommandHandler('admin7', admin7_panel))
    app.add_handler(CommandHandler('admin8', admin8_panel))
    app.add_handler(CommandHandler('teacher', teacher_panel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
