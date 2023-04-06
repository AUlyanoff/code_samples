FROM python:3.7-alpine
# Это основная операционная среда, в которой будет решаться наше web-прилложение trackstudio-report.
# Она выбирается отсюда https://hub.docker.com/_/python/ Сборка Python3.7 выполнена в свою очередь в среде Alpine Linux.

# Копируем наше приложение в образ в папку src.
COPY . /src
# Так как копируется содержание корневой папки (точка), команду сборки "docker build -t trackstudio-report ."
# надо выдавать, находясь в корневой папке проекта приложения.

# Устанавливаем зависимости (критический шаг).
RUN pip3 install -r /src/requirements.txt

# Даём нашему web-приложению права на запуск.
RUN chmod +x /src/main.py

# git describe выдаёт ветку+порядкоый номер сохранения+коммит=2.2-10-g76e0b5f
# это наш номер сборки, запишем его в файл ver.txt для отоображения в нижнем правом углу приложения
RUN ["echo", "$(git describe --long --tags --always) > ver.txt"]

# переменная окружения и рабочая директория
ENV PYTHONPATH /src
WORKDIR /src

# Изнутри контейнера открыть порт 5000
EXPOSE 5000

# указываем, что запускать в контейнере
ENTRYPOINT ./main.py

MAINTAINER aulyanov
