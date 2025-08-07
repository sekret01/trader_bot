"""
Телеграм бот для управления работой тредер-бота.

version: 0.0 
"""

import telebot
from telebot import types


def get_token() -> str:
    """ Получение токена """
    return "..."


bot = telebot.TeleBot("...")

main_menu = types.ReplyKeyboardMarkup(row_width=2)
main_menu_btn_1 = types.KeyboardButton("включить")  # text="Статус", callback_data="status")
main_menu_btn_2 = types.KeyboardButton("выключить")
main_menu_btn_3 = types.KeyboardButton("отчет о балансе")
main_menu_btn_4 = types.KeyboardButton("отчет о работе")
main_menu_btn_5 = types.KeyboardButton("получить csv-отчеты")
main_menu_btn_6 = types.KeyboardButton("получить log-файл")
main_menu.add(main_menu_btn_1, main_menu_btn_2, main_menu_btn_3, main_menu_btn_4, main_menu_btn_5, main_menu_btn_6)


# MESSAGES

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Welcome to trader bot!', reply_markup=main_menu)

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    if message.text == "выключить":
        bot.reply_to(message, "Выключение сервиса...")
    elif message.text == "включить":
        bot.reply_to(message, "Включение сервиса...")

    elif message.text == "отчет о балансе":
        bot.reply_to(message, "отчет о балансе")
        ... 
    elif message.text == "отчет о работе":
        bot.reply_to(message, "отчет о работе")
        ...
    elif message.text == "получить csv-отчеты":
        bot.reply_to(message, "получить csv-отчеты")
        ...
    elif message.text == "получить log-файл":
        bot.reply_to(message, "получить log-файл")
        ...

    elif message.text == "...":
        bot.reply_to(message, "функционал будет доступен в следующих обновлениях")   
        ...
    else:
        bot.reply_to(message, "Неопознанная команда")
        ...


# CALLBACKS 

# @bot.callback_query_handler(func=lambda call: True)
# def answer(call):
#     if call.data == "status":
#         bot.reply_to(call.message, "обновление статуса...")




def start_bot():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    start_bot()




