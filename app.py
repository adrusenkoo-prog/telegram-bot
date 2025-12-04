import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

# --- ENV VARIABLES ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
BASE_URL = os.getenv("WEBHOOK_BASE")

WEBHOOK_PATH = f"/bot/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# user_id -> admin_message_id
links = {}

# ---------------- START ----------------
@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Заказать", callback_data="order")
    )

    await msg.answer_photo(
        photo=open("logo.jpg", "rb"),
        caption="👋 Приветствую!\nЗдесь вы можете заказать d0x1ng.",
        reply_markup=kb
    )

# ---------------- ORDER BUTTON ----------------
@dp.callback_query_handler(lambda c: c.data == "order")
async def order_pressed(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="Отлично! Ваша заявка была зарегистрирована.\n"
                "До момента, пока с вами свяжется оператор, подготовьте данные:\n"
                "[username, number, photo, ip]",
    )

    sent = await bot.send_message(
        ADMIN_CHAT_ID,
        f"📩 Новый заказ!\n"
        f"Username: @{callback.from_user.username}\n"
        f"ID: {callback.from_user.id}"
    )

    links[callback.from_user.id] = sent.message_id

    await callback.answer()

# ----------- USER → ADMIN ----------- 
@dp.message_handler(lambda m: m.chat.id != ADMIN_CHAT_ID)
async def user_to_admin(msg: types.Message):

    admin_msg = await bot.send_message(
        ADMIN_CHAT_ID,
        f"📨 От пользователя @{msg.from_user.username}:\n{msg.text}"
    )

    links[msg.from_user.id] = admin_msg.message_id

# ----------- ADMIN → USER ----------- 
@dp.message_handler(lambda m: m.chat.id == ADMIN_CHAT_ID, content_types=types.ContentTypes.TEXT)
async def admin_to_user(msg: types.Message):

    if msg.reply_to_message:

        for uid, admin_msg_id in links.items():
            if admin_msg_id == msg.reply_to_message.message_id:

                await bot.send_message(
                    uid,
                    f"📩 От оператора:\n{msg.text}"
                )
                break

# ---------------- WEBHOOK ----------------
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=8080
    )
