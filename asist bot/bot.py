import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from database import setup_database
from handlers import register_handlers
from filters import setup_filters

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Настройка базы данных
db_session = setup_database(os.getenv('DATABASE_URL', 'sqlite:///bot_database.db'))

# Сохраняем сессию базы данных в контексте бота
bot['db_session'] = db_session

# Регистрация обработчиков и фильтров
setup_filters(dp)
register_handlers(dp, bot, db_session)

# Запуск бота
if __name__ == '__main__':
    logger.info("Бот запущен")
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")