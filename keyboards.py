from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def number_keyboard(selected=None, drawn=None, countdown=60):

    if selected is None:
        selected = []

    if drawn is None:
        drawn = []

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            f"⏳ Time Left: {countdown}s",
            callback_data="time"
        )
    ])

    row = []

    for i in range(1, 81):

        if i in drawn and i in selected:
            text = f"🟡{i}"
        elif i in drawn:
            text = f"🔴{i}"
        elif i in selected:
            text = f"🟢{i}"
        else:
            text = str(i)

        row.append(
            InlineKeyboardButton(
                text,
                callback_data=f"num_{i}"
            )
        )

        if len(row) == 8:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(
            "✅ Confirm",
            callback_data="confirm"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def play_again_keyboard():

    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "🎟️ Play Again",
                callback_data="play_again"
            )
        ]]
    )
