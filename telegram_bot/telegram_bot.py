"""
Телеграм бот для управления работой тредер-бота.
"""

import telebot
import configparser
import datetime
from telebot import types
from pathlib import Path

from app import ControlHub
from app import TinkoffDataGetter
from app import Logger
from app import CSV_Saver
# from app import TinkoffDataGetter

CONTROL_HUB: ControlHub | None = None
BUFF_DIR = Path("app/buff")
BUFF_OPERATION = "operations"
DATA_GETTER: TinkoffDataGetter = None
LOGGER = Logger()

def check_client_id(func: callable):
    global CLIENT_ID
    def wrapper(*args, **kwargs):
        if CLIENT_ID == "":
            return None
        res = func(*args, **kwargs)
        return res
    return wrapper


def set_control_hub(hub: ControlHub) -> None:
    """ Установка модуля ControlHub """
    global CONTROL_HUB, DATA_GETTER, LOGGER
    CONTROL_HUB = hub
    DATA_GETTER = TinkoffDataGetter(CONTROL_HUB.client, CONTROL_HUB.account_id)
    LOGGER.info(message=f"TG-BOT SETUP >> hub has been loaded", module=__name__)

def get_token() -> str:
    """ Получение токена """
    parser = configparser.ConfigParser()
    parser.read("configs/.configs.ini")
    return parser["TOKENS"]["telegram"]


token = get_token()
bot = telebot.TeleBot(token)
CLIENT_ID: str = ""

main_menu = types.ReplyKeyboardMarkup(row_width=2)
main_menu_btn_1 = types.KeyboardButton("включить")  # text="Статус", callback_data="status")
main_menu_btn_2 = types.KeyboardButton("очистка логов")
main_menu_btn_3 = types.KeyboardButton("отчет о балансе")
main_menu_btn_4 = types.KeyboardButton("отчет об операциях")
main_menu_btn_5 = types.KeyboardButton("получить csv-отчеты")
main_menu_btn_6 = types.KeyboardButton("получить log-файл")
main_menu.add(main_menu_btn_1, main_menu_btn_2, main_menu_btn_3, main_menu_btn_4, main_menu_btn_5, main_menu_btn_6)



def get_work_status() -> str:
    """ Получение статуса работы сервиса, авто настройка кнопки на панели """
    try:
        pr = configparser.ConfigParser()
        pr.read("configs/start_app.ini")
        return pr["WORK"]["working_status"]
    except Exception as ex:
        LOGGER.error(f"ERROR IN GET WORK STATUS :: {ex}", f"{__name__}.get_work_status")

@check_client_id
def stop_service() -> None:
    """ Остановка работы сервиса трейдинга """
    if CONTROL_HUB.get_work_status == '0':
        bot.send_message(CLIENT_ID, "Сервис не включен")
    else:
        CONTROL_HUB.stop_strategies()
        main_menu.keyboard[0][0]["text"] = "включить"
        bot.send_message(CLIENT_ID, "Сервис остановлен", reply_markup=main_menu)
        LOGGER.info(message="TG-BOT >> STOP SERVICE", module=f"{__name__}.stop_service")

@check_client_id
def start_service() -> None:
    """ Запуск сервиса трейдинга """
    if CONTROL_HUB.get_work_status == '1':
        bot.send_message(CLIENT_ID, "Сервис уже работает")
    else:
        CONTROL_HUB.run_strategies()
        main_menu.keyboard[0][0]["text"] = "выключить"
        bot.send_message(CLIENT_ID, "Сервис запущен", reply_markup=main_menu)

@check_client_id
def get_market_report() -> ...:
    """ Создание отчета об операциях бота за день """
    buff_data = []
    buf_path: Path = BUFF_DIR / BUFF_OPERATION
    if not buf_path.exists():
        buf_path.touch()

    with buf_path.open(mode="r", encoding='utf-8') as file:
        i = 0
        while True:
            line = file.readline()
            if not line:
                break
            buff_data.append(line)
            i += 1
            if i >= 500:
                break
    report = "".join(buff_data)
    if len(report) == 0:
        report = "no data yet"
    bot.send_message(CLIENT_ID, f"ОТЧЕТ О РАБОТЕ ЗА {datetime.datetime.now().date()}")
    bot.send_message(CLIENT_ID, report)

@check_client_id
def get_balance_report() -> ...:
    """ Создание отчета о балансе счета и распределении активов на данный момент """
    bot.send_message(CLIENT_ID, f"ОТЧЕТ О СОСТОЯНИИ БАЛАНСА\n[{str(datetime.datetime.now())}]")
    report_data = DATA_GETTER.get_balance()
    
    for instrument_type, instruments in report_data.items():
        bot.send_message(CLIENT_ID, f"инструмент {instrument_type.upper()}")
        for instr in instruments:
            rep_str = f"{instr["ticker"]} [{instr["figi"]}]\namount: {instr["amount"]}\n{instr["cur_price_for_one"]} руб >> {instr["cur_price"]} руб"
            bot.send_message(CLIENT_ID, rep_str)

@check_client_id
def load_csv_reports() -> ...:
    """ Загрузка csv-данных, хранящихся на сервере (файлы balance_data.csv и market_data.csv) """
    bot.send_message(CLIENT_ID, f"CSV-ОТЧЕТЫ")
    try:
        with open("reports/balance_statistic.csv", encoding='utf-8') as file:
            bot.send_document(CLIENT_ID, file)
        with open("reports/market_data.csv", encoding='utf-8') as file:
            bot.send_document(CLIENT_ID, file)
    except Exception as ex:
        LOGGER.error(f"TG-BOT LOAD_CSV_REPORT ERROR :: {ex}", module=__name__)
    

@check_client_id
def load_logs() -> ...:
    """ Загрузка log-файла, хранящегося на сервере """
    bot.send_message(CLIENT_ID, f"ЗАГРУЗКА LOG-ФАЙДА")
    try:
        with open("app/logs/main_logs.log", encoding='utf-8') as file:
            bot.send_document(CLIENT_ID, file)
    except Exception as ex:
        LOGGER.error(f"TG-BOT LOAD_LOGS ERROR :: {ex}", module=__name__)
        bot.send_message(CLIENT_ID, "Log-файл пуст")

@check_client_id
def clear_save_files() -> None:
    """ Очистка log и csv данных """
    csv_redactor = CSV_Saver(CONTROL_HUB.client, CONTROL_HUB.account_id)
    csv_redactor._create_files()
    log_path = Path("app/logs/main_logs.log")
    log_path.write_text("")
    bot.send_message(CLIENT_ID, "Были очищены данные из csv- и log-файлов")



# MESSAGES

@bot.message_handler(commands=['start'])
def start(message):
    global CLIENT_ID
    CLIENT_ID = message.chat.id
    bot.send_message(message.chat.id, 'Welcome to trader bot!', reply_markup=main_menu)

@bot.message_handler(func=lambda message: True)
def other_messages(message):

    if message.text == "выключить":
        try:
            stop_service()
        except Exception as ex:
            LOGGER.error(f"TG-BOT >> ERROR IN STOP SERVISE :: {ex}", f"{__name__}.stop_service")
        # bot.reply_to(message, "Сервис остановлен", reply_markdown=main_menu)
        
    elif message.text == "включить":
        try:
            start_service()
        except Exception as ex:
            LOGGER.error(f"TG-BOT >> ERROR IN START SERVISE :: {ex}", f"{__name__}.start_service")
        # bot.reply_to(message, "Сервис запущен", reply_markdown=main_menu)
    
    elif message.text == "очистка логов":
        bot.reply_to(message, "Очистка логов")
        clear_save_files()

    elif message.text == "отчет о балансе":
        bot.reply_to(message, "отчет о балансе")
        get_balance_report()
        
    elif message.text == "отчет об операциях":
        bot.reply_to(message, "отчет об операциях")
        get_market_report()
        
    elif message.text == "получить csv-отчеты":
        bot.reply_to(message, "получить csv-отчеты")
        load_csv_reports()

    elif message.text == "получить log-файл":
        bot.reply_to(message, "получить log-файл")
        load_logs()


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
    LOGGER.info(message=f"TG-BOT >> start polling bot", module=__name__)
    if get_work_status() == '1':
        main_menu.keyboard[0][0]["text"] = "выключить"
    bot.polling(non_stop=True)

def print_error(msg: str) -> None:
    bot.send_message(CLIENT_ID, "СБОЙ В СИСТЕМЕ")
    bot.send_message(CLIENT_ID, msg)

def stop_bot():
    print("stop telegram bot")
    LOGGER.info(message=f"TG-BOT >> stop polling bot", module=__name__)
    bot.stop_polling()
    

if __name__ == "__main__":
    start_bot()




