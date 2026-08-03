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


TOKEN = "8861601405:AAEwVqVS38Klc6PamK9P8plTVIGwBac9ZNM"

ROUND_TIME = 60
DRAW_COUNT = 10
TICKET_COST = 5

current_time = ROUND_TIME

# ==============================
# TELEBIRR SETTINGS
# ==============================
TELEBIRR_NUMBER = "0937584000"
MIN_DEPOSIT = 50

# ==============================
# WITHDRAW & SUPPORT SETTINGS
# ==============================
MIN_WITHDRAW = 100

# PUT YOUR TELEGRAM USERNAME HERE (WITHOUT @)
SUPPORT_USERNAME = "Abiy_zed"

# ==============================
# ADMIN SETTINGS
# ==============================
ADMIN_ID = 8216936710   # Replace with your Telegram numeric ID


# ==============================
# KEYBOARDS
# ==============================

phone_keyboard = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(
                "📱 Share Phone Number",
                request_contact=True
            )
        ]
    ],
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
            "🎰 Welcome back!\n\n"
            "Choose an option below:",
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

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 Deposit Now",
                    callback_data="deposit_now"
                )
            ]
        ])

        await update.message.reply_text(
            "❌ Your balance is 0 ETB.\n\n"
            "Please deposit money to continue playing.",
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
        "💳 *Deposit Request*\n\n"
        "👉 Please enter the amount you want to deposit:",
        parse_mode="Markdown"
    )


# ==============================
# HANDLE DEPOSIT AMOUNT
# ==============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    state = deposit_state.get(user_id)

    if state == "waiting_amount":

        if not text.isdigit():

            await update.message.reply_text(
                "❌ Please enter a valid number amount."
            )

            return

        amount = int(text)

        if amount < MIN_DEPOSIT:

            await update.message.reply_text(
                f"❌ Minimum deposit is {MIN_DEPOSIT} ETB.\n\n"
                "Please enter a higher amount."
            )

            return

        deposit_state[user_id] = {
            "status": "waiting_confirmation",
            "amount": amount
        }

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Complete Deposit",
                    callback_data="complete_deposit"
                )
            ]
        ])

        await update.message.reply_text(
            "💳 *Deposit Instructions*\n\n"
            f"📱 Send {amount} ETB to: `{TELEBIRR_NUMBER}`\n\n"
            "⚠️ After sending the money, press the button below:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return

    await menu_buttons(update, context)


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
            f"💰 Your Balance: {amount} ETB",
            reply_markup=main_menu
        )

        return

    await update.message.reply_text(
        "💸 *Withdrawal Request*\n\n"
        f"💰 Available Balance: *{amount} ETB*\n"
        f"📤 Minimum Withdrawal: *{MIN_WITHDRAW} ETB*\n\n"
        "Please contact support with:\n"
        "• Your Telegram username\n"
        "• Your Telebirr number\n"
        "• Amount to withdraw",
        parse_mode="Markdown",
        reply_markup=main_menu
    )


# ==============================
# SUPPORT
# ==============================
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    support_link = f"https://t.me/{SUPPORT_USERNAME}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🆘 Open Support Chat",
                url=support_link
            )
        ]
    ])

    await update.message.reply_text(
        "🆘 *Support Center*\n\n"
        "Need help with:\n"
        "• Deposits\n"
        "• Withdrawals\n"
        "• Game issues\n"
        "• Account support\n\n"
        "Click the button below to open the support chat.",
        parse_mode="Markdown",
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

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 Deposit Now",
                    callback_data="deposit_now"
                )
            ]
        ])

        await update.message.reply_text(
            "❌ You do not have enough balance to play.\n\n"
            f"💵 Ticket Cost: {TICKET_COST} ETB",
            reply_markup=keyboard
        )

        return

    confirmed_users.discard(user_id)

    game_state.add_player(user_id)

    message = await update.message.reply_text(
        f"🎰 ROUND #{game_state.round_number}\n\n"
        f"💵 Ticket Cost: {TICKET_COST} ETB\n"
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

    # --------------------------
    # Deposit button
    # --------------------------
    if query.data == "deposit_now":

        deposit_state[user_id] = "waiting_amount"

        await query.message.reply_text(
            "💳 Please enter the amount you want to deposit:"
        )

        return

    # --------------------------
    # Complete deposit
    # --------------------------
    if query.data == "complete_deposit":

        data = deposit_state.get(user_id)

        if not data:
            return

        amount = data["amount"]

        deposit_state.pop(user_id, None)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{user_id}_{amount}"
                ),
                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"reject_{user_id}_{amount}"
                )
            ]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "💳 *New Deposit Request*\n\n"
                f"👤 User: {query.from_user.full_name}\n"
                f"🆔 ID: `{user_id}`\n"
                f"💰 Amount: *{amount} ETB*\n"
                f"📞 Username: @{query.from_user.username}\n\n"
                "Choose an action below:"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await query.message.reply_text(
            "✅ *Deposit request submitted!*\n\n"
            "📨 Your deposit has been sent to the admin for approval.\n"
            "⏳ Please wait until the admin confirms your payment.",
            parse_mode="Markdown"
        )

        return

    # --------------------------
    # Approve deposit
    # --------------------------
    if query.data.startswith("approve_"):

        _, target_user, amount = query.data.split("_")

        target_user = int(target_user)
        amount = int(amount)

        balances[target_user] = balances.get(target_user, 0) + amount

        await context.bot.send_message(
            chat_id=target_user,
            text=(
                "✅ *Deposit Approved!*\n\n"
                f"💰 {amount} ETB has been added to your balance.\n\n"
                f"🏦 New Balance: {balances[target_user]} ETB"
            ),
            parse_mode="Markdown"
        )

        await query.edit_message_text(
            f"✅ Deposit approved for user `{target_user}`\n"
            f"💰 Amount: {amount} ETB",
            parse_mode="Markdown"
        )

        return

    # --------------------------
    # Reject deposit
    # --------------------------
    if query.data.startswith("reject_"):

        _, target_user, amount = query.data.split("_")

        target_user = int(target_user)
        amount = int(amount)

        await context.bot.send_message(
            chat_id=target_user,
            text=(
                "❌ *Deposit Rejected*\n\n"
                f"Your deposit request for {amount} ETB was rejected.\n"
                "Please contact support if you believe this is a mistake."
            ),
            parse_mode="Markdown"
        )

        await query.edit_message_text(
            f"❌ Deposit rejected for user `{target_user}`\n"
            f"💰 Amount: {amount} ETB",
            parse_mode="Markdown"
        )

        return

    # --------------------------
    # Play again
    # --------------------------
    if query.data == "play_again":

        confirmed_users.discard(user_id)

        game_state.set_numbers(user_id, [])

        new_numbers = random.sample(range(1, 81), 20)

        message = await query.message.reply_text(
            f"🎰 ROUND #{game_state.round_number}\n\n"
            f"💵 Ticket Cost: {TICKET_COST} ETB\n"
            f"⏳ Time Left: {current_time}s",
            reply_markup=number_keyboard(
                new_numbers,
                game_state.drawn_numbers,
                current_time
            )
        )

        game_state.save_board(user_id, message)

        return

    # --------------------------
    # Confirm ticket
    # --------------------------
    if query.data == "confirm":

        numbers = game_state.get_numbers(user_id)

        if len(numbers) < 5:

            await query.answer(
                "Select at least 5 numbers.",
                show_alert=True
            )

            return

        user_balance = balances.get(user_id, 0)

        if user_balance < TICKET_COST:

            await query.answer(
                "❌ Not enough balance.",
                show_alert=True
            )

            return

        balances[user_id] -= TICKET_COST
        confirmed_users.add(user_id)

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Ticket Confirmed",
                        callback_data="locked"
                    )
                ]
            ])
        )

        await query.answer(
            f"✅ Ticket Confirmed (-{TICKET_COST} ETB)"
        )

        return

    # --------------------------
    # Prevent changes after confirm
    # --------------------------
    if user_id in confirmed_users:

        await query.answer(
            "❌ Ticket already confirmed. Press Try Again to play again.",
            show_alert=True
        )

        return

    # --------------------------
    # Number selection
    # --------------------------
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
# UPDATE ALL BOARDS
# ==============================
async def update_all_boards():

    for user_id, message in game_state.boards.items():

        try:

            await message.edit_text(
                f"🎰 ROUND #{game_state.round_number}\n\n"
                f"⏳ Time Left: {current_time}s",
                reply_markup=number_keyboard(
                    game_state.get_numbers(user_id),
                    game_state.drawn_numbers,
                    current_time
                )
            )

        except:
            pass


# ==============================
# SEND RESULTS
# ==============================
async def send_results(app):

    for user_id, numbers in game_state.players.items():

        matches = len(
            set(numbers) &
            set(game_state.drawn_numbers)
        )

        try:

            await app.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 DRAW RESULT\n\n"
                    "🔴 Winning Numbers:\n"
                    f"{game_state.drawn_numbers}\n\n"
                    "🟢 Your Numbers:\n"
                    f"{numbers}\n\n"
                    f"🏆 Matches: {matches}"
                ),
                reply_markup=play_again_keyboard()
            )

        except:
            pass


# ==============================
# LOTTERY LOOP
# ==============================
async def lottery_loop(app):

    global current_time

    while True:

        game_state.drawn_numbers.clear()

        for seconds in range(ROUND_TIME, -1, -1):

            current_time = seconds

            await update_all_boards()

            await asyncio.sleep(1)

        winning = random.sample(range(1, 81), DRAW_COUNT)

        for number in winning:

            game_state.drawn_numbers.append(number)

            await update_all_boards()

            await asyncio.sleep(2)

        await send_results(app)

        await asyncio.sleep(5)

        game_state.next_round()
        game_state.clear_round()

        current_time = ROUND_TIME


# ==============================
# MENU ROUTER
# ==============================
async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎮 Play":
        await play(update, context)

    elif text == "💰 Balance":
        await balance(update, context)

    elif text == "💳 Deposit":
        await deposit(update, context)

    elif text == "💸 Withdraw":
        await withdraw(update, context)

    elif text == "🆘 Support":
        await support(update, context)

    elif text == "🏠 Start":
        await start(update, context)

    else:
        await handle_text(update, context)


# ==============================
# POST INIT
# ==============================
async def post_init(application: Application):

    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("play", "Play the lottery"),
        BotCommand("balance", "Check your balance"),
        BotCommand("deposit", "Deposit via Telebirr"),
        BotCommand("withdraw", "Request withdrawal"),
        BotCommand("support", "Contact support"),
    ])

    asyncio.create_task(
        lottery_loop(application)
    )


# ==============================
# APP
# ==============================
app = (
    Application.builder()
    .token(TOKEN)
    .post_init(post_init)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("play", play))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("deposit", deposit))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CommandHandler("support", support))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        menu_buttons
    )
)

app.add_handler(CallbackQueryHandler(button_click))

app.add_handler(
    MessageHandler(
        filters.CONTACT,
        receive_contact
    )
)

print("🎰 Lottery Bot with Admin Deposit Approval is running...")

# FIX FOR PYTHON 3.14 ON RENDER
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

app.run_polling()
