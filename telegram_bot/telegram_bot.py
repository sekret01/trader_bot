"""
Телеграм бот для управления работой тредер-бота.

version: 0.1
"""

import telebot
from telebot import types
import configparser
from app import ControlHub
from pathlib import Path
import datetime
# from app import TinkoffDataGetter

CONTROL_HUB: ControlHub | None = None
BUFF_DIR = Path("app/buff")
BUFF_OPERATION = "operations"


def set_control_hub(hub: ControlHub) -> None:
    """ Установка модуля ControlHub """
    CONTROL_HUB = hub

def get_token() -> str:
    """ Получение токена """
    parser = configparser.ConfigParser()
    parser.read("configs/.configs.ini")
    return parser["TOKENS"]["telegram"]


token = get_token()
bot = telebot.TeleBot(token)
CLIENT_ID: int | str = ""

main_menu = types.ReplyKeyboardMarkup(row_width=2)
main_menu_btn_1 = types.KeyboardButton("включить")  # text="Статус", callback_data="status")
main_menu_btn_2 = types.KeyboardButton("очистка логов")
main_menu_btn_3 = types.KeyboardButton("отчет о балансе")
main_menu_btn_4 = types.KeyboardButton("отчет об операциях")
main_menu_btn_5 = types.KeyboardButton("получить csv-отчеты")
main_menu_btn_6 = types.KeyboardButton("получить log-файл")
main_menu.add(main_menu_btn_1, main_menu_btn_2, main_menu_btn_3, main_menu_btn_4, main_menu_btn_5, main_menu_btn_6)


def get_work_status() -> int:
    """ Получение статуса работы сервиса, авто настройка кнопки на панели """
    pr = configparser.ConfigParser()
    pr.read("configs.start_app.ini")
    return int(pr["WORK"]["working_status"])

def stop_service() -> None:
    """ Остановка работы сервиса трейдинга """
    CONTROL_HUB.stop_strategies()
    main_menu.keyboard[0][0].text = "включить"

def start_service() -> None:
    """ Запуск сервиса трейдинга """
    CONTROL_HUB.run_strategies()
    main_menu.keyboard[0][0].text = "выключить"

def get_market_report() -> ...:
    """ Создание отчета об операциях бота за день """
    buff_data = []
    buf_path: Path = BUFF_DIR / BUFF_OPERATION
    with buf_path.open(mode="r", encoding='utf-8') as file:
        while True:
            i = 0
            line = file.readline
            if not line:
                break
            buff_data.append(line)
            i += 1
            if i >= 500:
                break
    report = "\n".join(buf_path)
    bot.send_message(CLIENT_ID, f"ОТЧЕТ О РАБОТЕ ЗА {datetime.datetime.now().date()}")
    bot.send_message(CLIENT_ID, report)

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
    CLIENT_ID = message.chat.id
    bot.send_message(message.chat.id, 'Welcome to trader bot!', reply_markup=main_menu)

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    if message.text == "выключить":
        stop_service()
        bot.reply_to(message, "Сервис остановлен", reply_markdown=main_menu)
        
    elif message.text == "включить":
        start_service()
        bot.reply_to(message, "Сервис запущен", reply_markdown=main_menu)
    
    elif message.text == "очистка логов":
        bot.reply_to(message, "Очистка логов (недоступно)")
        ...

    elif message.text == "отчет о балансе":
        bot.reply_to(message, "отчет о балансе (недоступно)")
        get_balance_report()
        ... 
    elif message.text == "отчет об операциях":
        bot.reply_to(message, "отчет об операциях (недоступно)")
        get_market_report()
        ...
    elif message.text == "получить csv-отчеты":
        bot.reply_to(message, "получить csv-отчеты (недоступно)")
        load_csv_reports()
        ...
    elif message.text == "получить log-файл":
        bot.reply_to(message, "получить log-файл (недоступно)")
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
    print("start telegram bot")
    bot.polling(non_stop=True)


if __name__ == "__main__":
    start_bot()




