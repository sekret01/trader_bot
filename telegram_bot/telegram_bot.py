"""
Телеграм бот для управления работой тредер-бота.

version: 0.1
"""

import telebot
from telebot import types
import configparser


def get_token() -> str:
    """ Получение токена """
    parser = configparser.ConfigParser()
    parser.read("../configs/.configs.ini")  # без ../ в итоговом варианте
    return parser["TOKENS"]["telegram"]


token = get_token()
bot = telebot.TeleBot(token)

main_menu = types.ReplyKeyboardMarkup(row_width=2)
main_menu_btn_1 = types.KeyboardButton("включить")  # text="Статус", callback_data="status")
main_menu_btn_2 = types.KeyboardButton("выключить")
main_menu_btn_3 = types.KeyboardButton("отчет о балансе")
main_menu_btn_4 = types.KeyboardButton("отчет об операциях")
main_menu_btn_5 = types.KeyboardButton("получить csv-отчеты")
main_menu_btn_6 = types.KeyboardButton("получить log-файл")
main_menu.add(main_menu_btn_1, main_menu_btn_2, main_menu_btn_3, main_menu_btn_4, main_menu_btn_5, main_menu_btn_6)


def get_work_status() -> int:
    """ Получение статуса работы сервиса, авто настройка кнопки на панели """
    pass

def stop_service() -> None:
    """ Остановка работы сервиса трейдинга """
    pass

def start_service() -> None:
    """ Запуск сервиса трейдинга """
    pass

def get_market_report() -> ...:
    """ Создание отчета об операциях бота за день """
    pass

def get_balance_report() -> ...:
    """ Создание отчета о балансе счета и распределении активов на данный момент """
    pass

def load_csv_reports() -> ...:
    """ Загрузка csv-данных, хранящихся на сервере (файлы balance_data.csv и market_data.csv) """
    pass

def load_logs() -> ...:
    """ Загрузка log-файла, хранящегося на сервере """
    pass




"""
main_menu.keyboard[0][0]['text'] = "qweqweqwe"
print(main_menu.keyboard[0][0])
"""

# MESSAGES

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Welcome to trader bot!', reply_markup=main_menu)

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    if message.text == "выключить":
        bot.reply_to(message, "Выключение сервиса...")
        stop_service()
    elif message.text == "включить":
        bot.reply_to(message, "Включение сервиса...")
        start_service()

    elif message.text == "отчет о балансе":
        bot.reply_to(message, "отчет о балансе")
        get_balance_report()
        ... 
    elif message.text == "отчет об операциях":
        bot.reply_to(message, "отчет об операциях")
        get_market_report()
        ...
    elif message.text == "получить csv-отчеты":
        bot.reply_to(message, "получить csv-отчеты")
        load_csv_reports()
        ...
    elif message.text == "получить log-файл":
        bot.reply_to(message, "получить log-файл")
        load_logs()
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




