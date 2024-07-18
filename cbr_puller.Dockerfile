FROM python:3.12.4-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY cbr_puller cbr_puller

CMD python -u cbr_puller/main.py\
    --redis-url ${CBR_PULLER_REDIS_URL}\
    --rates-url ${CBR_PULLER_RATES_URL}\
    --pull-once
