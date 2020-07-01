# base image for tgbot
FROM python:3.8.2

ARG APP_BASE_DIR

WORKDIR /APP_BASE_DIR

COPY requirements.txt /APP_BASE_DIR
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . /APP_BASE_DIR
