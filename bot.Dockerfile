FROM python:3.12.4-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY bot bot

CMD python bot/main.py\
    --api-token $(cat ${BOT_TELEGRAM_TOKEN_FILE})\
    --redis-url ${BOT_REDIS_URL}
