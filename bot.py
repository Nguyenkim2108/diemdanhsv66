import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

# === CẤU HÌNH ===
TOKEN = '8554364289:AAEGv2oVxpxMUi_V7VY4cXIqTbntoQnM-IU'
SHEET_NAME = 'ĐIỂM DANH SV66'
LINK_DIEMDANH = 'https://docs.google.com/forms/d/e/1FAIpQLSePlOrs-6E84RBmGlG8jL2cTQJVhZuT1opfiYHlL0_cD97fHA/viewform'

AUTO_SEND_CHAT_IDS = set()

# === KẾT NỐI GOOGLE SHEETS ===
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === GHI LOG ===
def log_to_sheet(user):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    username = f"@{user.username}" if user.username else "Không có"
    full_name = user.full_name
    sheet.append_row([timestamp, username, full_name, LINK_DIEMDANH])

# === GỬI TIN NHẮN ===
async def send_diemdanh_message(chat_id, context):
    keyboard = [[InlineKeyboardButton("ĐIỂM DANH NGAY", url=LINK_DIEMDANH)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    hour = datetime.now().strftime("%H:%M")
    msg = f"*ĐIỂM DANH SV66*\n\n*⏰ {hour}* – Đã đến giờ điểm danh!\nNhấn nút để xác nhận có mặt.\n\n_Tự động ghi vào Google Sheets._"
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown', reply_markup=reply_markup)

# === LỆNH /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    await send_diemdanh_message(chat_id, context)
    log_to_sheet(user)
    AUTO_SEND_CHAT_IDS.add(chat_id)

# === LỆNH /diemdanh ===
async def diemdanh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# === LỆNH /help ===
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*BOT ĐIỂM DANH SV66*\n\n/start – Nhận link\n/diemdanh – Gửi lại\n/help – Hướng dẫn\n\nTự động gửi 4 lần/ngày",
        parse_mode='Markdown'
    )

# === TỰ ĐỘNG GỬI ===
async def auto_send_all(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(AUTO_SEND_CHAT_IDS):
        try:
            await send_diemdanh_message(chat_id, context)
        except:
            AUTO_SEND_CHAT_IDS.discard(chat_id)

# === LÊN LỊCH NGẪU NHIÊN ===
async def schedule_random_reminders(app):
    today = datetime.now().date()
    jobs = []
    for _ in range(2):
        h = 13 + random.randint(0, 2)
        m = random.randint(0, 59)
        dt = datetime(today.year, today.month, today.day, h, m)
        if dt < datetime.now():
            dt += timedelta(days=1)
        jobs.append(dt)
    for _ in range(2):
        h = 19 + random.randint(0, 2)
        m = random.randint(0, 59)
        dt = datetime(today.year, today.month, today.day, h, m)
        if dt < datetime.now():
            dt += timedelta(days=1)
        jobs.append(dt)
    
    # Xóa job cũ
    for job in app.job_queue.jobs():
        job.schedule_removal()
    
    # Thêm job mới
    for dt in jobs:
        app.job_queue.run_once(auto_send_all, dt)
    
    print(f"[LỊCH] Gửi lúc: {', '.join([j.strftime('%H:%M') for j in jobs])}")

# === POST_INIT: LÊN LỊCH SAU KHI BOT KHỞI ĐỘNG ===
async def post_init(app: Application):
    await schedule_random_reminders(app)
    # Lên lịch cập nhật hàng ngày
    app.job_queue.run_daily(
        lambda ctx: asyncio.create_task(schedule_random_reminders(app)),
        time=datetime.strptime("00:05", "%H:%M").time()
    )

# === CHẠY BOT ===
def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("diemdanh", diemdanh))
    app.add_handler(CommandHandler("help", help_cmd))
    
    print("Bot ĐIỂM DANH SV66 đang chạy... (16/11/2025 02:30 AM)")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()