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
    return parser["TOKENS"]["telegram_bot_token"]

def get_owner_id() -> str:
    """ Получение id пользователя """
    parser = configparser.ConfigParser()
    parser.read("configs/.configs.ini")
    return parser["TOKENS"]["owner_telegram_id"]

def authorization(message) -> bool:
    """
    Функция сравнения id пишущего с ID полученного из конфигураций.
    При совпадении возвращает True, иначе False
    """
    if str(message.from_user.id) == str(CLIENT_ID):
        return True
    LOGGER.error(message=f"CLIENT ID >> попытка использовать бота пользователем @{message.from_user.username} [{message.from_user.first_name}] id: {message.from_user.id}",
                 module=__name__)
    LOGGER.warning(message=f"message info\n\n{str(message)}", module=__name__)
    return False


token = get_token()
bot = telebot.TeleBot(token)
CLIENT_ID: str = get_owner_id()

main_menu = types.ReplyKeyboardMarkup(row_width=2)
main_menu_btn_1 = types.KeyboardButton("приостановить")  # text="Статус", callback_data="status")
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

def get_paused_status() -> str:
    """ Получение статуса работы сервиса, авто настройка кнопки на панели """
    try:
        pr = configparser.ConfigParser()
        pr.read("configs/start_app.ini")
        return pr["WORK"]["paused"]
    except Exception as ex:
        LOGGER.error(f"ERROR IN GET PAUSED STATUS :: {ex}", f"{__name__}.get_paused_status")

@check_client_id
def pause_service() -> None:
    """ Пристановка работы сервиса трейдинга """
    # if CONTROL_HUB.get_work_status == '0':
    if CONTROL_HUB.get_paused_status == '1':
        bot.send_message(CLIENT_ID, "Сервис уже приостановлен")
    else:
        # CONTROL_HUB.stop_strategies()
        CONTROL_HUB.pause_strategise()
        main_menu.keyboard[0][0]["text"] = "возобновить"
        bot.send_message(CLIENT_ID, "Сервис приостановлен", reply_markup=main_menu)
        LOGGER.info(message="TG-BOT >> PAUSED SERVICE", module=f"{__name__}.stop_service")

@check_client_id
def resume_service() -> None:
    """ Возобновление работы сервиса трейдинга """
    # if CONTROL_HUB.get_work_status == '1':
    if CONTROL_HUB.get_paused_status == '0':
        bot.send_message(CLIENT_ID, "Сервис уже работает")
    else:
        # CONTROL_HUB.run_strategies()
        CONTROL_HUB.resume_strategise()
        main_menu.keyboard[0][0]["text"] = "приостановить"
        bot.send_message(CLIENT_ID, "Сервис возобновлен", reply_markup=main_menu)

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
    total_price = DATA_GETTER.get_total_balance()
    bot.send_message(CLIENT_ID, f"Всего на счету: {round(total_price, 2)} руб")
    
    for instrument_type, instruments in report_data.items():
        # bot.send_message(CLIENT_ID, f"инструмент {instrument_type.upper()}")
        instr_report = f"инструмент {instrument_type.upper()}\n\n"
        for instr in instruments:
            rep_str = f"> {instr["ticker"]} [{instr["figi"]}]\n    amount: {instr["amount"]}\n    {instr["cur_price_for_one"]} руб >> {instr["cur_price"]} руб\n"
            # bot.send_message(CLIENT_ID, rep_str)
            instr_report += rep_str
        bot.send_message(CLIENT_ID, instr_report)

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
    if not authorization(message):
        bot.send_message(message.chat.id, f"Пользователь @{message.from_user.username} не имеет доступа к функционалу", reply_markup=types.ReplyKeyboardRemove())
        return
    global CLIENT_ID
    CLIENT_ID = message.chat.id
    bot.send_message(message.chat.id, "Управляюший трейдер-системой бот", reply_markup=main_menu)

@bot.message_handler(func=lambda message: True)
def other_messages(message):
    if not authorization(message):
        return

    if message.text == "приостановить":
        try:
            pause_service()
        except Exception as ex:
            LOGGER.error(f"TG-BOT >> ERROR IN STOP SERVISE :: {ex}", f"{__name__}.stop_service")
        # bot.reply_to(message, "Сервис остановлен", reply_markdown=main_menu)
        
    elif message.text == "возобновить":
        try:
            resume_service()
        except Exception as ex:
            LOGGER.error(f"TG-BOT >> ERROR IN START SERVISE :: {ex}", f"{__name__}.start_service")
        # bot.reply_to(message, "Сервис запущен", reply_markdown=main_menu)
    
    elif message.text == "очистка логов":
        # bot.reply_to(message, "Очистка логов")
        clear_save_files()

    elif message.text == "отчет о балансе":
        # bot.reply_to(message, "отчет о балансе")
        get_balance_report()
        
    elif message.text == "отчет об операциях":
        # bot.reply_to(message, "отчет об операциях")
        get_market_report()
        
    elif message.text == "получить csv-отчеты":
        # bot.reply_to(message, "получить csv-отчеты")
        load_csv_reports()

    elif message.text == "получить log-файл":
        # bot.reply_to(message, "получить log-файл")
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
        main_menu.keyboard[0][0]["text"] = "приостановить"
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




