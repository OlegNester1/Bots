FROM python:3.9-slim

WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . .

# Создание файла .env из примера, если его нет
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Запуск бота
CMD ["python", "bot.py"]