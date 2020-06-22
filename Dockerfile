FROM python:3.8-alpine

COPY python/requirements.txt /

RUN pip install -r /requirements.txt

COPY python /app

WORKDIR /app

ENTRYPOINT python3 ./main.py
