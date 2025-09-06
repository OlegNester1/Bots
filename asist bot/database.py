from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

# Модель для хранения настроек чата
class ChatSettings(Base):
    __tablename__ = 'chat_settings'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), unique=True, nullable=False)
    filter_obscene = Column(Boolean, default=True)  # Фильтр мата
    filter_links = Column(Boolean, default=True)    # Фильтр ссылок
    filter_keywords = Column(Boolean, default=True) # Фильтр ключевых слов
    action_type = Column(String(50), default='delete')  # delete, warn, mute, ban
    mute_duration = Column(Integer, default=3600)  # Длительность мута в секундах (по умолчанию 1 час)
    
    def __repr__(self):
        return f"<ChatSettings(chat_id='{self.chat_id}')>"

# Модель для хранения запрещенных слов/фраз
class BannedWord(Base):
    __tablename__ = 'banned_words'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), nullable=False)
    word = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<BannedWord(word='{self.word}')>"

# Модель для хранения нарушений пользователей
class Violation(Base):
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    message_text = Column(Text, nullable=True)
    violation_type = Column(String(50), nullable=False)  # obscene, link, keyword
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action_taken = Column(String(50), nullable=False)  # delete, warn, mute, ban
    
    def __repr__(self):
        return f"<Violation(user_id='{self.user_id}', type='{self.violation_type}')>"

# Модель для хранения счетчика предупреждений пользователей
class UserWarnings(Base):
    __tablename__ = 'user_warnings'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    warnings_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<UserWarnings(user_id='{self.user_id}', count={self.warnings_count})>"

# Функция для настройки базы данных
def setup_database(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()