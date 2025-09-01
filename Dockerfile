# FROM python:3.12
FROM python:3.12-slim
# FROM python:3.12-alpine3.22

WORKDIR trader_bot

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app /trader_bot/app
COPY configs /trader_bot/configs
COPY reports /trader_bot/reports
COPY telegram_bot /trader_bot/telegram_bot

COPY start_app.py /trader_bot/.
COPY main.py /trader_bot/.

CMD ["python", "start_app.py"]