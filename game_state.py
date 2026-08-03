players = {}

boards = {}

drawn_numbers = []

countdown = 60

round_number = 1


def add_player(user_id):
    if user_id not in players:
        players[user_id] = []


def remove_player(user_id):
    if user_id in players:
        del players[user_id]


def save_board(user_id, message):
    boards[user_id] = message


def set_numbers(user_id, numbers):
    players[user_id] = numbers


def get_numbers(user_id):
    return players.get(user_id, [])


def clear_round():
    players.clear()
    drawn_numbers.clear()


def next_round():
    global round_number
    round_number += 1
