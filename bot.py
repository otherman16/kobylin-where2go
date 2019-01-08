import telebot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply, KeyboardButton
from model import User, InterestPlace
from maps import Map
import os


# import logging
# logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)
# logger.debug("Hello!")


TELEBOT_API_KEY = os.environ.get('TELEBOT_API_KEY')
bot = telebot.TeleBot(TELEBOT_API_KEY)


def command_keyboard():
    markup = ReplyKeyboardMarkup(row_width=3)
    start_btn = KeyboardButton('/start')
    help_btn = KeyboardButton('/help')
    add_btn = KeyboardButton('/add')
    list_btn = KeyboardButton('/list')
    reset_btn = KeyboardButton('/reset')
    echo_btn = KeyboardButton('/echo')
    markup.add(start_btn, help_btn, add_btn, list_btn, reset_btn, echo_btn)
    return markup


def decision_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2)
    yes_btn = KeyboardButton('да')
    no_btn = KeyboardButton('нет')
    markup.add(yes_btn, no_btn)
    return markup


def standard_keyboard():
    markup = ReplyKeyboardRemove(selective=False)
    return markup


def standard_keyboard_force_reply():
    markup = ForceReply(selective=False)
    return markup


def user_message_handler(message_handler):
    def message_handler_decorator(message: Message):
        t_user: telebot.types.User = message.from_user
        user = User.get(t_user.id)
        if not user:
            username = f"{t_user.first_name} {t_user.last_name}"
            user = User.create(t_user.id, username)
        message_handler(user, message)
    return message_handler_decorator


@bot.message_handler(commands=['help', 'start'])
@user_message_handler
def help_start_command(user: User, message: Message):
    """ Handle '/start' and '/help' """

    bot.send_message(
        chat_id=message.chat.id,
        text=f"""
Привет, {user.name}, меня зовут Where2GoBot.
Я могу сохранять для тебя интересные места.

Ты можешь использвать следующие команды для управления:

/start - начать диалог
/help - вывести справку
/add - добавить новое место
/list - отобразить добавленные места
/reset - удалить все добавленные места
/echo - эхо""",
        reply_markup=command_keyboard()
    )
    user.state = User.STATE_IDLE
    user.save()


def check_not_command(message: Message):
    return message.text is not None and message.text[0] != '/'


def next_state(user: User, message: Message):
    if user.state == User.STATE_ADD_START:
        user.new_place = InterestPlace()
        bot.send_message(
            chat_id=message.chat.id,
            text="Назови место",
            reply_markup=standard_keyboard_force_reply()
        )
        user.state = User.STATE_ADD_NAME
    elif user.state == User.STATE_ADD_NAME:
        if message.content_type == 'text':
            user.new_place.name = message.text
            bot.send_message(
                chat_id=message.chat.id,
                text="Укажи геопозицию (адрес или GPS-метку)",
                reply_markup=standard_keyboard_force_reply()
            )
            user.state = User.STATE_ADD_LOCATION
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Назови место",
                reply_markup=standard_keyboard_force_reply()
            )
    elif user.state == User.STATE_ADD_LOCATION:
        if message.content_type == 'location':
            geocode = Map.geocode_from_location((message.location.latitude, message.location.longitude))
            user.new_place.address = geocode.get('address')
            user.new_place.location = geocode.get('location')
            bot.send_message(
                chat_id=message.chat.id,
                text="Добавь фото",
                reply_markup=standard_keyboard_force_reply()
            )
            user.state = User.STATE_ADD_PHOTO
        elif message.content_type == 'text':
            geocode = Map.geocode_from_address(message.text)
            user.new_place.address = geocode.get('address')
            user.new_place.location = geocode.get('location')
            bot.send_message(
                chat_id=message.chat.id,
                text="Добавь фото",
                reply_markup=standard_keyboard_force_reply()
            )
            user.state = User.STATE_ADD_PHOTO
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Укажи геопозицию (адрес или GPS-метку)",
                reply_markup=standard_keyboard_force_reply()
            )
    elif user.state == User.STATE_ADD_PHOTO:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            user.new_place.photo = bot.download_file(file_info.file_path)
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Сохранить место \"{user.new_place.name}\" (да/нет)?",
                reply_markup=decision_keyboard()
            )
            user.state = User.STATE_ADD_SAVE
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Добавь фото",
                reply_markup=standard_keyboard_force_reply()
            )
    elif user.state == User.STATE_ADD_SAVE:
        if message.content_type == 'text':
            if "да" in message.text.lower():
                user.save_new_place()
                bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Место \"{user.new_place.name}\" сохранено.",
                    reply_markup=command_keyboard()
                )
                user.state = User.STATE_IDLE
            elif "нет" in message.text.lower():
                bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Место \"{user.new_place.name}\" не сохранено.",
                    reply_markup=command_keyboard()
                )
                user.state = User.STATE_IDLE
            else:
                bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Сохранить место \"{user.new_place.name}\" (да/нет)?",
                    reply_markup=decision_keyboard()
                )
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"Сохранить место \"{user.new_place.name}\" (да/нет)?",
                reply_markup=decision_keyboard()
            )
    elif user.state == User.STATE_RESET_START:
        bot.send_message(
            chat_id=message.chat.id,
            text="Удалить список интересных мест (да/нет)?",
            reply_markup=decision_keyboard()
        )
        user.state = User.STATE_RESET_DO
    elif user.state == User.STATE_RESET_DO:
        if message.content_type == 'text':
            if "да" in message.text.lower():
                InterestPlace.reset(user)
                bot.send_message(
                    chat_id=message.chat.id,
                    text="Список интересных мест удален",
                    reply_markup=command_keyboard()
                )
                user.state = User.STATE_IDLE
            elif "нет" in message.text.lower():
                bot.send_message(
                    chat_id=message.chat.id,
                    text="Список интересных мест не удален",
                    reply_markup=command_keyboard()
                )
                user.state = User.STATE_IDLE
            else:
                bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Сохранить место \"{user.new_place.name}\" (да/нет)?",
                    reply_markup=decision_keyboard()
                )
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text="Удалить список интересных мест (да/нет)?",
                reply_markup=decision_keyboard()
            )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="""
Ты можешь использвать следующие команды для управления:

/start - начать диалог
/help - вывести справку
/add - добавить новое место
/list - отобразить добавленные места
/reset - удалить все добавленные места
/echo - эхо""",
            reply_markup=command_keyboard()
        )
    user.save()


@bot.message_handler(content_types=['text'], func=check_not_command)
@bot.message_handler(func=check_not_command)
@user_message_handler
def handle_text(user: User, message: Message):
    """ Handle text """

    next_state(user, message)


@bot.message_handler(content_types=['photo'])
@user_message_handler
def handle_photo(user: User, message: Message):
    """ Handle photo """

    next_state(user, message)


@bot.message_handler(content_types=['location'])
@user_message_handler
def handle_location(user: User, message: Message):
    """ Handle location """

    if user.state == User.STATE_IDLE:
        interest_places = InterestPlace.all(user)
        if len(interest_places) == 0:
            bot.send_message(
                chat_id=message.chat.id,
                text="Список интересных мест пуст",
                reply_markup=command_keyboard()
            )
        else:
            interest_places_locations = [interest_place.location for interest_place in interest_places]
            distances = Map.distances(
                (message.location.latitude, message.location.longitude),
                interest_places_locations
            )
            print(distances)
            bot.send_message(
                chat_id=message.chat.id,
                text="Вот, что в пределах 500 м...",
                reply_markup=command_keyboard()
            )
            for i in range(len(interest_places)):
                if distances[i] < 510:
                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=interest_places[i].photo,
                        caption=f"Название: {interest_places[i].name}.\nАдрес: {interest_places[i].address}.",
                        reply_markup=command_keyboard()
                    )
                    bot.send_location(
                        chat_id=message.chat.id,
                        latitude=interest_places[i].location[0],
                        longitude=interest_places[i].location[1],
                        reply_markup=command_keyboard()
                    )
                    bot.send_message(
                        chat_id=message.chat.id,
                        text="==========================",
                        reply_markup=command_keyboard()
                    )
    else:
        next_state(user, message)


@bot.message_handler(commands=['add'])
@user_message_handler
def handle_command_add(user: User, message: Message):
    """ Handle '/add' """

    user.state = User.STATE_ADD_START
    next_state(user, message)


@bot.message_handler(commands=['list'])
@user_message_handler
def handle_command_list(user: User, message: Message):
    """ Handle '/list' """

    interest_places = InterestPlace.all(user)
    if len(interest_places) == 0:
        bot.send_message(
            chat_id=message.chat.id,
            text="Список интересных мест пуст",
            reply_markup=command_keyboard()
        )
    else:
        bot.send_message(
            chat_id=message.chat.id,
            text="Вот, что ты сохранил ранее...",
            reply_markup=command_keyboard()
        )
        for interest_place in interest_places:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=interest_place.photo,
                caption=f"Название: {interest_place.name}.\nАдрес: {interest_place.address}.",
                reply_markup=command_keyboard()
            )
            bot.send_location(
                chat_id=message.chat.id,
                latitude=interest_place.location[0],
                longitude=interest_place.location[1],
                reply_markup=command_keyboard()
            )
            bot.send_message(
                chat_id=message.chat.id,
                text="==========================",
                reply_markup=command_keyboard()
            )

    user.state = User.STATE_IDLE
    user.save()


@bot.message_handler(commands=['reset'])
@user_message_handler
def handle_command_reset(user: User, message: Message):
    """ Handle '/reset' """

    user.state = User.STATE_RESET_START
    next_state(user, message)


@bot.message_handler(commands=['echo'])
def echo_command(message: Message):
    bot.reply_to(message, message.text)


if __name__ == "__main__":
    PROXY = os.environ.get('PROXY')
    if PROXY:
        telebot.apihelper.proxy = {'https': PROXY}
    bot.polling()
