# Telegram-бот модератор для чатов

Бот для автоматической модерации сообщений и поддержки правил сообщества в Telegram-чатах.

## Основные функции

- **Фильтрация сообщений**
  - Автоматическое удаление сообщений с нецензурной лексикой
  - Фильтрация ссылок
  - Блокировка запрещенных слов и фраз

- **Настройка правил через команды**
  - Добавление/удаление запрещенных слов
  - Настройка реакции бота на нарушения

- **Система предупреждений**
  - Счетчик нарушений для каждого пользователя
  - Автоматические наказания после накопления предупреждений

- **Отчеты для администраторов**
  - Логирование всех нарушений
  - Просмотр истории нарушений

## Установка и настройка

### Требования

- Python 3.7 или выше
- Зависимости из файла requirements.txt

### Шаги установки

1. Клонируйте репозиторий или скачайте файлы проекта

2. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

3. Создайте файл .env на основе .env.example и укажите токен вашего бота:
   ```
   BOT_TOKEN=your_bot_token_here
   DATABASE_URL=sqlite:///bot_database.db
   LOG_LEVEL=INFO
   ```

4. Запустите бота:
   ```
   python bot.py
   ```

### Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте команду /newbot и следуйте инструкциям
3. После создания бота вы получите токен, который нужно указать в файле .env

## Использование

### Добавление бота в чат

1. Добавьте бота в ваш чат
2. Назначьте бота администратором с правами на удаление сообщений и блокировку пользователей

### Команды для администраторов

- `/settings` - Показать текущие настройки фильтрации
- `/addword <слово>` - Добавить запрещенное слово
- `/delword <слово>` - Удалить запрещенное слово
- `/listwords` - Показать список запрещенных слов
- `/setaction <delete|warn|mute|ban>` - Установить действие при нарушении
- `/mute @user <время>` - Замутить пользователя (время в минутах)
- `/ban @user` - Забанить пользователя
- `/violations` - Показать список последних нарушений

## Настройка для постоянной работы

### Запуск через systemd (Linux)

Создайте файл `/etc/systemd/system/telegram-moderator-bot.service`:

```
[Unit]
Description=Telegram Moderator Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/bot/directory
ExecStart=/usr/bin/python3 /path/to/bot/directory/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем выполните:

```
sudo systemctl enable telegram-moderator-bot.service
sudo systemctl start telegram-moderator-bot.service
```

### Запуск через Docker

1. Создайте Dockerfile в корневой директории проекта:

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

2. Соберите и запустите Docker-контейнер:

```
docker build -t telegram-moderator-bot .
docker run -d --name moderator-bot --restart always telegram-moderator-bot
```

## Расширение функциональности

Бот разработан с возможностью легкого расширения. Для добавления новых функций:

1. Добавьте новые обработчики в файл handlers.py
2. При необходимости расширьте модели данных в database.py
3. Зарегистрируйте новые обработчики в функции register_handlers

## Поддержка

При возникновении проблем или для запроса новых функций, пожалуйста, создайте issue в репозитории проекта.