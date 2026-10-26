import asyncio
import random
import string
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
import aiosqlite

from database import init_db, add_user, get_balance, create_order

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ============ TERI DETAILS ============
UPI_MAIN = "vanshzone377@okaxis"
UPI_BACKUP = "vanshx1@fam"
CHANNEL_LINK = "https://t.me/+FKXMpGR4uq1jYmFl"

CRYPTO_ADDRESSES = {
    "BEP20": "0x2da62b69b815dfc9BDAf440f54Be40Aa3e0FCf54",
    "LTC": "ltc1q2n02qhdqd2ppg6usensnjt7y9s9acsx3fqh2mh"
}

PRICE_INR = 20
PRICE_USDT = 0.3
PRICE_LTC = 0.0035
DB_NAME = "bot.db"

OFFLINE_NOTICE = (
    "\n\n⚠️ <b>Note:</b> Bot 1 AM se 9 AM tak offline rehta hai.\n"
    "Payment ke baad thoda wait karna pad sakta hai."
)
# ======================================

class PaymentState(StatesGroup):
    waiting_utr = State()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buy ALL BUNDLE", callback_data="buy")],
        [
            InlineKeyboardButton(text="💰 Wallet", callback_data="wallet"),
            InlineKeyboardButton(text="👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="🔗 Referral", callback_data="referral"),
            InlineKeyboardButton(text="🆘 Support", callback_data="support")
        ]
    ])

def payment_methods_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔵 UPI (Instant)", callback_data="pay_upi")],
        [InlineKeyboardButton(text="🟢 USDT (BEP20)", callback_data="pay_BEP20")],
        [InlineKeyboardButton(text="🟡 LTC", callback_data="pay_LTC")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
    ])

def generate_tx_id():
    return "ORD" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_unique_amount(base: float) -> float:
    extra = random.randint(11, 89) / 10000
    return round(base + extra, 4)

@dp.message(Command("pending"))
async def pending_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, tx_id, amount, currency, network FROM orders WHERE status = 'pending'") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("Koi pending payment nahi hai.")
        return

    text = "📋 <b>Pending Payments</b>\n\n"
    for row in rows:
        user_id, tx_id, amount, currency, network = row
        text += f"User: <code>{user_id}</code>\nOrder: <code>{tx_id}</code>\n{amount} {currency} ({network})\n\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(CommandStart())
async def start(message: Message):
    await add_user(message.from_user.id, message.from_user.username)
    text = (
        '<tg-emoji emoji-id="6320983775605955181">✨</tg-emoji> '
        '<b>ALL BUNDLE Store</b>\n\n'
        '📦 Product: <b>ALL BUNDLE</b>\n'
        '💰 Price: <b>₹20</b>  |  <b>0.3 USDT</b>\n\n'
        'Payment ke baad instantly private channel mil jayega.'
        + OFFLINE_NOTICE
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):
    await callback.message.edit_text(
        '<tg-emoji emoji-id="6320983775605955181">✨</tg-emoji> <b>Main Menu</b>',
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):
    text = (
        '<tg-emoji emoji-id="6323399149249109357">🛒</tg-emoji> '
        '<b>ALL BUNDLE</b>\n\n'
        '💰 Price: <b>₹20</b> or <b>0.3 USDT</b>\n\n'
        'Payment method choose karo:'
    )
    await callback.message.edit_text(text, reply_markup=payment_methods_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "wallet")
async def wallet(callback: CallbackQuery):
    bal = await get_balance(callback.from_user.id)
    await callback.message.edit_text(
        f'<tg-emoji emoji-id="6321315149512711396">💰</tg-emoji> '
        f'<b>Your Wallet</b>\n\nBalance: <b>${bal:.2f}</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.message.edit_text(
        f"👤 <b>Profile</b>\n\nID: <code>{callback.from_user.id}</code>\nUsername: @{callback.from_user.username or 'None'}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "referral")
async def referral(callback: CallbackQuery):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={callback.from_user.id}"
    await callback.message.edit_text(
        f"🔗 <b>Referral Link</b>\n\n<code>{link}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.edit_text(
        '<tg-emoji emoji-id="6143411531028632701">🆘</tg-emoji> '
        '<b>Support</b>\n\nKoi problem ho to yahan message karo.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]),
        parse_mode="HTML"
    )

# ================== UPI ==================
@dp.callback_query(F.data == "pay_upi")
async def pay_upi(callback: CallbackQuery, state: FSMContext):
    tx_id = generate_tx_id()
    await state.update_data(tx_id=tx_id)

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_MAIN}&pn=ALL%20BUNDLE&am={PRICE_INR}&cu=INR&tn={tx_id}"

    text = (
        f"🔵 <b>UPI Payment</b>\n\n"
        f"Amount: <b>₹{PRICE_INR}</b>\n"
        f"Order ID: <code>{tx_id}</code>\n\n"
        f"QR scan karke payment karo.\n"
        f"Payment hone ke baad <b>Payment Done</b> dabao."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Payment Done", callback_data="upi_paid")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="buy")]
    ])

    await callback.message.answer_photo(photo=qr_url, caption=text, reply_markup=kb, parse_mode="HTML")
    await callback.message.delete()
    await create_order(callback.from_user.id, PRICE_INR, "INR", "UPI", tx_id)

@dp.callback_query(F.data == "upi_paid")
async def upi_paid(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✍️ <b>UTR Number bhejo</b>\n\n"
        "Payment ka UTR / Reference number yahan type karke bhej do.",
        parse_mode="HTML"
    )
    await state.set_state(PaymentState.waiting_utr)
    await callback.answer()

@dp.message(PaymentState.waiting_utr)
async def receive_utr(message: Message, state: FSMContext):
    utr = message.text.strip()
    data = await state.get_data()
    tx_id = data.get("tx_id", "N/A")
    user = message.from_user

    admin_text = (
        f"🔔 <b>New UPI Payment</b>\n\n"
        f"User: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: @{user.username or 'None'}\n"
        f"Order ID: <code>{tx_id}</code>\n"
        f"UTR: <code>{utr}</code>"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm & Deliver", callback_data=f"confirm_{user.id}")],
        [InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user.id}")]
    ])

    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_kb, parse_mode="HTML")
    await message.answer(
        "✅ UTR receive ho gaya!\n\n"
        "Admin verify kar raha hai."
        + OFFLINE_NOTICE,
        parse_mode="HTML"
    )
    await state.clear()

# ================== CRYPTO ==================
@dp.callback_query(F.data.startswith("pay_"))
async def pay_crypto(callback: CallbackQuery, state: FSMContext):
    network = callback.data.replace("pay_", "")
    
    if network == "BEP20":
        amount = generate_unique_amount(PRICE_USDT)
        currency = "USDT"
    else:
        amount = generate_unique_amount(PRICE_LTC)
        currency = "LTC"

    tx_id = generate_tx_id()
    address = CRYPTO_ADDRESSES[network]

    text = (
        f"🟢 <b>{currency} DEPOSIT · {network}</b>\n\n"
        f"💰 Amount: <b>{amount} {currency}</b>\n"
        f"🆔 Order ID: <code>{tx_id}</code>\n\n"
        f"➡️ <b>Deposit Address:</b>\n<code>{address}</code>\n\n"
        f"⚠️ Exactly <b>{amount} {currency}</b> hi bhejo.\n"
        f"⏳ Valid for: <b>5 minutes</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Payment Done", callback_data=f"done_{network}_{tx_id}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="buy")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await create_order(callback.from_user.id, amount, currency, network, tx_id)

@dp.callback_query(F.data.startswith("done_"))
async def payment_done(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    network = parts[1]
    tx_id = parts[2]
    user = callback.from_user

    admin_text = (
        f"🔔 <b>New Crypto Payment</b>\n\n"
        f"User: <a href='tg://user?id={user.id}'>{user.full_name}</a>\n"
        f"ID: <code>{user.id}</code>\n"
        f"Method: <b>{network}</b>\n"
        f"Order ID: <code>{tx_id}</code>"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Confirm & Deliver", callback_data=f"confirm_{user.id}")],
        [InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user.id}")]
    ])

    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_kb, parse_mode="HTML")
    await callback.message.edit_text(
        "✅ Payment claim received!\nAdmin verify kar raha hai."
        + OFFLINE_NOTICE,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("confirm_"))
async def admin_confirm(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Only admin", show_alert=True)

    user_id = int(callback.data.split("_")[1])
    await bot.send_message(
        user_id,
        f'<tg-emoji emoji-id="6113869066634532142">🎉</tg-emoji> '
        f'<b>Payment Confirmed!</b>\n\n'
        f"Ye raha aapka <b>ALL BUNDLE</b> private channel:\n\n"
        f"{CHANNEL_LINK}",
        parse_mode="HTML"
    )
    await callback.message.edit_text("✅ Successfully Delivered!")
    await callback.answer("Delivered!")

@dp.callback_query(F.data.startswith("reject_"))
async def admin_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ Payment rejected. Support se contact karo.")
    await callback.message.edit_text("❌ Rejected")

async def main():
    await init_db()
    print("Bot started successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())