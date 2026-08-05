
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from keyboards import number_keyboard, play_again_keyboard
import game_state

import random
import asyncio
import os
from flask import Flask

# ==============================
# FLASK WEB SERVER
# ==============================

web = Flask(__name__)

@web.route("/")
def home():
    return "Lottery Bot is running!"


# ==============================
# BOT SETTINGS
# ==============================

TOKEN = os.getenv("BOT_TOKEN")


ROUND_TIME = 60
DRAW_COUNT = 10
TICKET_COST = 5

current_time = ROUND_TIME


# ==============================
# PAYOUT TABLE
# ==============================

PAYOUTS = {
    1: 2,
    2: 3,
    3: 5,
    4: 10,
    5: 20,
    6: 50,
    7: 100,
    8: 200,
    9: 500,
    10: 1000
}


# ==============================
# TELEBIRR SETTINGS
# ==============================

TELEBIRR_NUMBER = "0912345678"
MIN_DEPOSIT = 50


# ==============================
# WITHDRAW SETTINGS
# ==============================

MIN_WITHDRAW = 100
SUPPORT_USERNAME = "Abiy_zed"


# ==============================
# ADMIN SETTINGS
# ==============================

ADMIN_ID = 987654321   # ← PUT YOUR REAL TELEGRAM ID HERE


# ==============================
# KEYBOARDS
# ==============================

phone_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📱 Share Phone Number", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🎮 Play"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💳 Deposit"), KeyboardButton("💸 Withdraw")],
        [KeyboardButton("🆘 Support"), KeyboardButton("🏠 Start")]
    ],
    resize_keyboard=True
)


# ==============================
# DATA
# ==============================

registered_users = set()
balances = {}
confirmed_users = set()

deposit_state = {}
withdraw_state = {}


# ==============================
# START
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in registered_users:
        await update.message.reply_text(
            "🎰 Welcome to the Lottery Game!\n\n"
            "Please register first by sharing your phone number.",
            reply_markup=phone_keyboard
        )
    else:
        await update.message.reply_text(
            "🎰 Welcome back!\n\nChoose an option below:",
            reply_markup=main_menu
        )


# ==============================
# REGISTER CONTACT
# ==============================

async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id

    registered_users.add(user_id)

    if user_id not in balances:
        balances[user_id] = 10

    await update.message.reply_text(
        "✅ Registration successful!\n\n"
        f"📱 Phone: {contact.phone_number}\n\n"
        "🎁 Starting Balance: 10 ETB Points\n\n"
        "Use the buttons below to continue.",
        reply_markup=main_menu
    )


# ==============================
# BALANCE
# ==============================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in registered_users:
        await update.message.reply_text(
            "❌ You are not registered yet.\n\nUse /start first."
        )
        return

    amount = balances.get(user_id, 0)

    if amount <= 0:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💳 Deposit Now", callback_data="deposit_now")]]
        )

        await update.message.reply_text(
            "❌ Your balance is 0 ETB.\n\nPlease deposit money to continue playing.",
            reply_markup=keyboard
        )
        return

    await update.message.reply_text(
        f"💰 Your Balance:\n\n{amount} ETB Points",
        reply_markup=main_menu
    )


# ==============================
# DEPOSIT
# ==============================

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in registered_users:
        await update.message.reply_text(
            "❌ Please register first using /start."
        )
        return

    deposit_state[user_id] = "waiting_amount"

    await update.message.reply_text(
        "💳 Deposit Request\n\n👉 Please enter the amount you want to deposit:"
    )


# ==============================
# HANDLE TEXT INPUT
# ==============================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # --------------------------
    # DEPOSIT FLOW
    # --------------------------

    state = deposit_state.get(user_id)

    if state == "waiting_amount":

        if not text.isdigit():
            await update.message.reply_text(
                "❌ Please enter a valid amount."
            )
            return

        amount = int(text)

        if amount < MIN_DEPOSIT:
            await update.message.reply_text(
                f"❌ Minimum deposit is {MIN_DEPOSIT} ETB."
            )
            return

        deposit_state[user_id] = {
            "status": "waiting_confirmation",
            "amount": amount
        }

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ I Have Sent The Money",
                        callback_data="complete_deposit"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data="cancel_deposit"
                    )
                ]
            ]
        )

        await update.message.reply_text(
            "💳 Deposit Instructions\n\n"
            f"📱 Send {amount} ETB to:\n"
            f"`{TELEBIRR_NUMBER}`\n\n"
            "After sending money press the button below.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return
        
# ==============================
# WITHDRAW
# ==============================

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in registered_users:

        await update.message.reply_text(
            "❌ Please register first using /start."
        )
        return

    amount = balances.get(user_id, 0)

    if amount < MIN_WITHDRAW:

        await update.message.reply_text(
            f"❌ Minimum withdrawal is {MIN_WITHDRAW} ETB.\n\n"
            f"💰 Balance: {amount} ETB",
            reply_markup=main_menu
        )
        return

    withdraw_state[user_id] = {"step": "amount"}

    await update.message.reply_text(
        "💸 Withdrawal Request\n\n"
        f"Available Balance: {amount} ETB\n\n"
        "Enter amount:"
    )


# ==============================
# SUPPORT
# ==============================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    link = f"https://t.me/{SUPPORT_USERNAME}"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🆘 Open Support Chat", url=link)]]
    )

    await update.message.reply_text(
        "🆘 Support Center\n\n"
        "Contact support for deposits, withdrawals and game issues.",
        reply_markup=keyboard
    )


# ==============================
# PLAY
# ==============================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in registered_users:

        await update.message.reply_text(
            "❌ Please register first using /start."
        )
        return

    if balances.get(user_id, 0) < TICKET_COST:

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("💳 Deposit Now", callback_data="deposit_now")]]
        )

        await update.message.reply_text(
            "❌ Not enough balance.\n\n"
            f"Ticket cost: {TICKET_COST} ETB",
            reply_markup=keyboard
        )
        return

    confirmed_users.discard(user_id)

    game_state.add_player(user_id)

    message = await update.message.reply_text(

        f"🎰 ROUND #{game_state.round_number}\n\n"
        f"💵 Ticket: {TICKET_COST} ETB\n"
        "🎯 Select 1 to 10 numbers\n"
        f"⏳ Time Left: {current_time}s",

        reply_markup=number_keyboard(
            game_state.get_numbers(user_id),
            game_state.drawn_numbers,
            current_time
        )
    )

    game_state.save_board(user_id, message)


# ==============================
# BUTTON HANDLER
# ==============================

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if query.data in ["time", "locked"]:
        return


    # ==========================
    # DEPOSIT NOW
    # ==========================

    if query.data == "deposit_now":

        deposit_state[user_id] = "waiting_amount"

        await query.message.reply_text(
            "💳 Please enter the amount you want to deposit:"
        )

        return


    # ==========================
    # CANCEL DEPOSIT
    # ==========================

    if query.data == "cancel_deposit":

        deposit_state.pop(user_id, None)

        await query.message.reply_text(
            "❌ Deposit cancelled."
        )

        return


    # ==========================
    # COMPLETE DEPOSIT
    # ==========================

    if query.data == "complete_deposit":

        data = deposit_state.get(user_id)

        if not data:
            return

        amount = data["amount"]

        deposit_state.pop(user_id, None)

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve Deposit",
                        callback_data=f"approve_deposit_{user_id}_{amount}"
                    ),

                    InlineKeyboardButton(
                        "❌ Reject Deposit",
                        callback_data=f"reject_deposit_{user_id}_{amount}"
                    )
                ]
            ]
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,

            text=(
                "💳 New Deposit Request\n\n"
                f"👤 User: {query.from_user.full_name}\n"
                f"🆔 ID: {user_id}\n"
                f"💰 Amount: {amount} ETB"
            ),

            reply_markup=keyboard
        )

        await query.message.reply_text(
            "✅ Deposit request sent to admin.\n"
            "Please wait for approval."
        )

        return


    # ==========================
    # APPROVE DEPOSIT
    # ==========================

    if query.data.startswith("approve_deposit_"):

        _, _, target_user, amount = query.data.split("_")

        target_user = int(target_user)
        amount = int(amount)

        balances[target_user] = (
            balances.get(target_user, 0) + amount
        )

        await context.bot.send_message(
            chat_id=target_user,

            text=(
                "✅ Deposit Approved!\n\n"
                f"💰 Added: {amount} ETB\n"
                f"🏦 Balance: {balances[target_user]} ETB"
            )
        )

        await query.edit_message_text(
            "✅ Deposit approved."
        )

        return


    # ==========================
    # REJECT DEPOSIT
    # ==========================

    if query.data.startswith("reject_deposit_"):

        _, _, target_user, amount = query.data.split("_")

        target_user = int(target_user)

        await context.bot.send_message(
            chat_id=target_user,

            text=(
                "❌ Deposit rejected.\n"
                "Please contact support."
            )
        )

        await query.edit_message_text(
            "❌ Deposit rejected."
        )

        return


    # ==========================
    # CONFIRM WITHDRAW
    # ==========================

    if query.data == "confirm_withdraw":

        data = withdraw_state.get(user_id)

        if not data:
            return

        amount = data["amount"]
        number = data["number"]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Approve Withdrawal",
                        callback_data=f"approve_withdraw_{user_id}_{amount}"
                    ),

                    InlineKeyboardButton(
                        "❌ Reject Withdrawal",
                        callback_data=f"reject_withdraw_{user_id}_{amount}"
                    )
                ]
            ]
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,

            text=(
                "💸 Withdrawal Request\n\n"
                f"👤 User ID: {user_id}\n"
                f"💰 Amount: {amount} ETB\n"
                f"📱 Telebirr: {number}"
            ),

            reply_markup=keyboard
        )

        withdraw_state.pop(user_id, None)

        await query.message.reply_text(
            "✅ Withdrawal request sent."
        )

        return


    # ==============================
    # APPROVE WITHDRAWAL
    # ==============================

    if query.data.startswith("approve_withdraw_"):

        _, _, target_user, amount = query.data.split("_")

        target_user = int(target_user)
        amount = int(amount)

        balances[target_user] -= amount

        await context.bot.send_message(
            chat_id=target_user,

            text=(
                "✅ Withdrawal Approved!\n\n"
                f"💸 Amount: {amount} ETB\n"
                f"🏦 Remaining Balance: {balances[target_user]} ETB"
            )
        )

        await query.edit_message_text(
            "✅ Withdrawal approved."
        )

        return


    # ==============================
    # REJECT WITHDRAWAL
    # ==============================

    if query.data.startswith("reject_withdraw_"):

        _, _, target_user, amount = query.data.split("_")

        target_user = int(target_user)

        await context.bot.send_message(
            chat_id=target_user,
            text="❌ Withdrawal rejected."
        )

        await query.edit_message_text(
            "❌ Withdrawal rejected."
        )

        return


    # ==============================
    # PLAY AGAIN
    # ==============================

    if query.data == "play_again":

        confirmed_users.discard(user_id)

        game_state.set_numbers(user_id, [])

        message = await query.message.reply_text(

            f"🎰 ROUND #{game_state.round_number}\n\n"
            "🎯 Select your numbers",

            reply_markup=number_keyboard(
                [],
                game_state.drawn_numbers,
                current_time
            )
        )

        game_state.save_board(user_id, message)

        return


    # ==============================
    # CONFIRM TICKET
    # ==============================

    if query.data == "confirm":

        numbers = game_state.get_numbers(user_id)

        if len(numbers) < 1:

            await query.answer(
                "Select at least one number.",
                show_alert=True
            )
            return

        if balances.get(user_id, 0) < TICKET_COST:

            await query.answer(
                "Not enough balance.",
                show_alert=True
            )
            return

        balances[user_id] -= TICKET_COST

        confirmed_users.add(user_id)

        await query.edit_message_reply_markup(

            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    "✅ Ticket Confirmed",
                    callback_data="locked"
                )]]
            )
        )

        return


    # ==============================
    # NUMBER SELECT
    # ==============================

    if user_id in confirmed_users:

        await query.answer(
            "Ticket already confirmed.",
            show_alert=True
        )

        return

    number = int(query.data.split("_")[1])

    numbers = game_state.get_numbers(user_id)

    if number in numbers:
        numbers.remove(number)
    else:
        if len(numbers) < 10:
            numbers.append(number)

    game_state.set_numbers(user_id, numbers)

    await query.edit_message_reply_markup(

        reply_markup=number_keyboard(
            numbers,
            game_state.drawn_numbers,
            current_time
        )
    )


# ==============================
# PAYOUT RESULTS
# ==============================

async def send_results(app):

    for user_id, numbers in game_state.players.items():

        matches = len(
            set(numbers) &
            set(game_state.drawn_numbers)
        )

        payout = 0

        if matches in PAYOUTS:

            payout = TICKET_COST * PAYOUTS[matches]

            balances[user_id] = (
                balances.get(user_id, 0) + payout
            )

        await app.bot.send_message(

            chat_id=user_id,

            text=(
                "🎉 RESULT\n\n"
                f"🔴 Winning: {game_state.drawn_numbers}\n"
                f"🟢 Your numbers: {numbers}\n\n"
                f"🎯 Matches: {matches}\n"
                f"💰 Win: {payout} ETB"
            ),

            reply_markup=play_again_keyboard()
        )


# ==============================
# UPDATE BOARDS
# ==============================

async def update_all_boards():

    for user_id, message in game_state.boards.items():

        try:

            await message.edit_text(
                f"🎰 ROUND #{game_state.round_number}\n\n"
                f"💵 Ticket: {TICKET_COST} ETB\n"
                "🎯 Select 1 to 10 numbers\n"
                f"⏳ Time Left: {current_time}s",

                reply_markup=number_keyboard(
                    game_state.get_numbers(user_id),
                    game_state.drawn_numbers,
                    current_time
                )
            )

        except Exception as e:
            print(f"Board update error: {e}")


# ==============================
# LOTTERY LOOP
# ==============================

async def lottery_loop(app):

    global current_time

    while True:

        game_state.drawn_numbers.clear()

        # countdown
        for seconds in range(ROUND_TIME, -1, -1):

            current_time = seconds

            await update_all_boards()

            await asyncio.sleep(1)

        # draw 10 numbers from 1-80
        winning = random.sample(range(1, 81), DRAW_COUNT)

        game_state.drawn_numbers.extend(winning)

        # send results
        await send_results(app)

        # wait before next round
        await asyncio.sleep(5)

        # next round
        game_state.next_round()

        game_state.clear_round()

        current_time = ROUND_TIME


# ==============================
# MENU BUTTONS
# ==============================

async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎮 Play":
        return await play(update, context)

    if text == "💰 Balance":
        return await balance(update, context)

    if text == "💳 Deposit":
        return await deposit(update, context)

    if text == "💸 Withdraw":
        return await withdraw(update, context)

    if text == "🆘 Support":
        return await support(update, context)

    if text == "🏠 Start":
        return await start(update, context)


# ==============================
# POST INIT
# ==============================

async def post_init(application: Application):

    await application.bot.set_my_commands(
        [
            BotCommand("start", "Start"),
            BotCommand("play", "Play"),
            BotCommand("balance", "Balance"),
            BotCommand("deposit", "Deposit"),
            BotCommand("withdraw", "Withdraw"),
            BotCommand("support", "Support")
        ]
    )

    # start lottery timer loop
    asyncio.create_task(
        lottery_loop(application)
    )


# ==============================
# APPLICATION
# ==============================

app = (
    Application.builder()
    .token(TOKEN)
    .post_init(post_init)
    .build()
)


# ------------------------------
# COMMANDS
# ------------------------------

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("play", play))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("deposit", deposit))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CommandHandler("support", support))


# ------------------------------
# CONTACT REGISTRATION
# ------------------------------

app.add_handler(
    MessageHandler(
        filters.CONTACT,
        receive_contact
    )
)


# ------------------------------
# TEXT HANDLER
# IMPORTANT: use handle_text
# ------------------------------

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    )
)


# ------------------------------
# BUTTON HANDLER
# ------------------------------

app.add_handler(
    CallbackQueryHandler(button_click)
)


# ==============================
# MAIN
# ==============================

async def main():

    print("🎰 Lottery Bot running")

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    # keep bot alive forever
    while True:
        await asyncio.sleep(3600)


# ==============================
# RENDER WEB SERVER
# ==============================
from flask import Flask
import threading
import os

import threading

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)


if __name__ == "__main__":

    print("🎰 Lottery Bot running on Render")

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    app.run_polling()

