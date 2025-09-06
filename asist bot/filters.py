import re
import logging
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from database import ChatSettings, BannedWord

logger = logging.getLogger(__name__)

# Список стоп-слов (нецензурная лексика)
OBSCENE_WORDS = [
    # Здесь должен быть список нецензурных слов
    # Для примера используем заглушки
    'бля', 'нецензурное_слово2', 'оскорбление1', 'оскорбление2'
]

# Регулярное выражение для поиска URL
URL_PATTERN = r'(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?'

class ObsceneFilter(BoundFilter):
    """Фильтр для проверки сообщений на наличие нецензурной лексики"""
    key = 'is_obscene'
    
    def __init__(self, is_obscene):
        self.is_obscene = is_obscene
    
    async def check(self, message: types.Message):
        if not message.text:
            return False
        
        # Получаем db_session из контекста бота
        db_session = message.bot.get('db_session')
        
        # Проверяем, включен ли фильтр для этого чата
        chat_settings = db_session.query(ChatSettings).filter(
            ChatSettings.chat_id == str(message.chat.id)
        ).first()
        
        if not chat_settings or not chat_settings.filter_obscene:
            return False
        
        # Проверяем наличие нецензурных слов
        text = message.text.lower()
        for word in OBSCENE_WORDS:
            if word.lower() in text:
                logger.info(f"Обнаружено нецензурное слово в сообщении от {message.from_user.id}")
                return True
        
        return False

class LinkFilter(BoundFilter):
    """Фильтр для проверки сообщений на наличие ссылок"""
    key = 'has_link'
    
    def __init__(self, has_link):
        self.has_link = has_link
    
    async def check(self, message: types.Message):
        if not message.text:
            return False
        
        # Получаем db_session из контекста бота
        db_session = message.bot.get('db_session')
        
        # Проверяем, включен ли фильтр для этого чата
        chat_settings = db_session.query(ChatSettings).filter(
            ChatSettings.chat_id == str(message.chat.id)
        ).first()
        
        if not chat_settings or not chat_settings.filter_links:
            return False
        
        # Проверяем наличие ссылок
        if re.search(URL_PATTERN, message.text):
            logger.info(f"Обнаружена ссылка в сообщении от {message.from_user.id}")
            return True
        
        return False

class BannedWordFilter(BoundFilter):
    """Фильтр для проверки сообщений на наличие запрещенных слов"""
    key = 'has_banned_word'
    
    def __init__(self, has_banned_word):
        self.has_banned_word = has_banned_word
    
    async def check(self, message: types.Message):
        if not message.text:
            return False
        
        # Получаем db_session из контекста бота
        db_session = message.bot.get('db_session')
        
        # Проверяем, включен ли фильтр для этого чата
        chat_settings = db_session.query(ChatSettings).filter(
            ChatSettings.chat_id == str(message.chat.id)
        ).first()
        
        if not chat_settings or not chat_settings.filter_keywords:
            return False
        
        # Получаем список запрещенных слов для этого чата
        banned_words = db_session.query(BannedWord).filter(
            BannedWord.chat_id == str(message.chat.id)
        ).all()
        
        # Проверяем наличие запрещенных слов
        text = message.text.lower()
        for banned_word in banned_words:
            if banned_word.word.lower() in text:
                logger.info(f"Обнаружено запрещенное слово в сообщении от {message.from_user.id}")
                return True
        
        return False

class IsAdmin(BoundFilter):
    """Фильтр для проверки, является ли пользователь администратором чата"""
    key = 'is_admin'
    
    def __init__(self, is_admin):
        self.is_admin = is_admin
    
    async def check(self, message: types.Message):
        if message.chat.type == 'private':
            return False
        
        # Получаем информацию о пользователе в чате
        member = await message.chat.get_member(message.from_user.id)
        
        # Проверяем, является ли пользователь администратором или создателем
        return member.is_chat_admin() or member.is_chat_creator()

def setup_filters(dp):
    """Регистрация фильтров в диспетчере"""
    dp.filters_factory.bind(ObsceneFilter)
    dp.filters_factory.bind(LinkFilter)
    dp.filters_factory.bind(BannedWordFilter)
    dp.filters_factory.bind(IsAdmin)