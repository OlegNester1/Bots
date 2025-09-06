import logging
import datetime
from aiogram import types, Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils.exceptions import ChatNotFound, BotBlocked, CantRestrictChatOwner, UserIsAnAdministratorOfTheChat
from database import ChatSettings, BannedWord, Violation, UserWarnings

logger = logging.getLogger(__name__)

# Обработчик команды /start
async def cmd_start(message: types.Message):
    if message.chat.type == 'private':
        await message.reply(
            "Привет! Я бот-модератор для чатов. \n\n"
            "Добавь меня в группу и дай права администратора, чтобы я мог модерировать сообщения.\n\n"
            "Для настройки бота используй команду /config"
        )
    else:
        await message.reply(
            "Привет! Я бот-модератор для чатов. \n"
            "Для настройки бота напиши мне в личные сообщения."
        )

# Обработчик команды /help
async def cmd_help(message: types.Message):
    if message.chat.type == 'private':
        help_text = (
            "Я бот-модератор для чатов. Вот мои команды:\n\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать справку\n"
            "/config - Настроить бота для ваших групп\n\n"
            "Команды для администраторов в группах:\n"
            "/settings - Показать текущие настройки\n"
            "/addword <слово> - Добавить запрещенное слово\n"
            "/delword <слово> - Удалить запрещенное слово\n"
            "/listwords - Показать список запрещенных слов\n"
            "/setaction <delete|warn|mute|ban> - Установить действие при нарушении\n"
            "/mute @user <время в минутах> - Замутить пользователя\n"
            "/ban @user - Забанить пользователя\n"
            "/violations - Показать список нарушений"
        )
    else:
        help_text = "Отправил справку в личные сообщения."
        await message.bot.send_message(message.from_user.id, cmd_help.__doc__)
    
    await message.reply(help_text)

# Обработчик команды /settings
async def cmd_settings(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Проверяем, является ли пользователь администратором
    member = await message.chat.get_member(message.from_user.id)
    if not (member.is_chat_admin() or member.is_chat_creator()):
        await message.reply("Эта команда доступна только администраторам чата.")
        return
    
    db_session = message.bot.get('db_session')
    
    # Получаем или создаем настройки для чата
    chat_settings = db_session.query(ChatSettings).filter(
        ChatSettings.chat_id == str(message.chat.id)
    ).first()
    
    if not chat_settings:
        chat_settings = ChatSettings(chat_id=str(message.chat.id))
        db_session.add(chat_settings)
        db_session.commit()
    
    # Формируем текст с текущими настройками
    settings_text = (
        f"Настройки для чата {message.chat.title}:\n\n"
        f"Фильтр мата: {'Включен' if chat_settings.filter_obscene else 'Выключен'}\n"
        f"Фильтр ссылок: {'Включен' if chat_settings.filter_links else 'Выключен'}\n"
        f"Фильтр ключевых слов: {'Включен' if chat_settings.filter_keywords else 'Выключен'}\n"
        f"Действие при нарушении: {chat_settings.action_type}\n"
        f"Длительность мута: {chat_settings.mute_duration // 60} минут"
    )
    
    await message.reply(settings_text)

# Обработчик команды /addword
async def cmd_addword(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Получаем слово из аргументов команды
    args = message.get_args().split()
    if not args:
        await message.reply("Укажите слово для добавления в запрещенные.")
        return
    
    word = args[0].lower()
    db_session = message.bot.get('db_session')
    
    # Проверяем, есть ли уже такое слово в базе
    existing_word = db_session.query(BannedWord).filter(
        BannedWord.chat_id == str(message.chat.id),
        BannedWord.word == word
    ).first()
    
    if existing_word:
        await message.reply(f"Слово '{word}' уже в списке запрещенных.")
        return
    
    # Добавляем слово в базу
    banned_word = BannedWord(chat_id=str(message.chat.id), word=word)
    db_session.add(banned_word)
    db_session.commit()
    
    await message.reply(f"Слово '{word}' добавлено в список запрещенных.")

# Обработчик команды /delword
async def cmd_delword(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Получаем слово из аргументов команды
    args = message.get_args().split()
    if not args:
        await message.reply("Укажите слово для удаления из запрещенных.")
        return
    
    word = args[0].lower()
    db_session = message.bot.get('db_session')
    
    # Ищем слово в базе
    banned_word = db_session.query(BannedWord).filter(
        BannedWord.chat_id == str(message.chat.id),
        BannedWord.word == word
    ).first()
    
    if not banned_word:
        await message.reply(f"Слово '{word}' не найдено в списке запрещенных.")
        return
    
    # Удаляем слово из базы
    db_session.delete(banned_word)
    db_session.commit()
    
    await message.reply(f"Слово '{word}' удалено из списка запрещенных.")

# Обработчик команды /listwords
async def cmd_listwords(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    db_session = message.bot.get('db_session')
    
    # Получаем список запрещенных слов для этого чата
    banned_words = db_session.query(BannedWord).filter(
        BannedWord.chat_id == str(message.chat.id)
    ).all()
    
    if not banned_words:
        await message.reply("Список запрещенных слов пуст.")
        return
    
    # Формируем текст со списком запрещенных слов
    words_text = "Список запрещенных слов:\n\n"
    for word in banned_words:
        words_text += f"- {word.word}\n"
    
    await message.reply(words_text)

# Обработчик команды /setaction
async def cmd_setaction(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Получаем действие из аргументов команды
    args = message.get_args().split()
    if not args:
        await message.reply(
            "Укажите действие при нарушении: delete, warn, mute или ban.\n"
            "Например: /setaction warn"
        )
        return
    
    action = args[0].lower()
    if action not in ['delete', 'warn', 'mute', 'ban']:
        await message.reply("Недопустимое действие. Используйте: delete, warn, mute или ban.")
        return
    
    db_session = message.bot.get('db_session')
    
    # Получаем или создаем настройки для чата
    chat_settings = db_session.query(ChatSettings).filter(
        ChatSettings.chat_id == str(message.chat.id)
    ).first()
    
    if not chat_settings:
        chat_settings = ChatSettings(chat_id=str(message.chat.id))
        db_session.add(chat_settings)
    
    # Обновляем действие при нарушении
    chat_settings.action_type = action
    db_session.commit()
    
    await message.reply(f"Действие при нарушении установлено: {action}")

# Обработчик команды /mute
async def cmd_mute(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Получаем аргументы команды
    args = message.get_args().split()
    if len(args) < 1:
        await message.reply(
            "Укажите пользователя и время мута в минутах.\n"
            "Например: /mute @username 60"
        )
        return
    
    # Получаем пользователя
    user_mention = args[0]
    if not user_mention.startswith('@'):
        await message.reply("Укажите имя пользователя, начиная с @.")
        return
    
    # Получаем время мута
    mute_duration = 60  # По умолчанию 60 минут
    if len(args) >= 2 and args[1].isdigit():
        mute_duration = int(args[1])
    
    # Получаем информацию о пользователе
    try:
        chat_member = await message.chat.get_member(user_mention[1:])
    except ChatNotFound:
        await message.reply(f"Пользователь {user_mention} не найден в этом чате.")
        return
    
    # Проверяем, можно ли замутить пользователя
    try:
        until_date = datetime.datetime.now() + datetime.timedelta(minutes=mute_duration)
        await message.chat.restrict(chat_member.user.id, until_date=until_date, can_send_messages=False)
        
        await message.reply(f"Пользователь {user_mention} замучен на {mute_duration} минут.")
    except (CantRestrictChatOwner, UserIsAnAdministratorOfTheChat):
        await message.reply(f"Невозможно замутить пользователя {user_mention}, так как он является администратором.")
    except Exception as e:
        logger.error(f"Ошибка при муте пользователя: {e}")
        await message.reply(f"Произошла ошибка при муте пользователя: {e}")

# Обработчик команды /ban
async def cmd_ban(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    # Получаем аргументы команды
    args = message.get_args().split()
    if not args:
        await message.reply(
            "Укажите пользователя для бана.\n"
            "Например: /ban @username"
        )
        return
    
    # Получаем пользователя
    user_mention = args[0]
    if not user_mention.startswith('@'):
        await message.reply("Укажите имя пользователя, начиная с @.")
        return
    
    # Получаем информацию о пользователе
    try:
        chat_member = await message.chat.get_member(user_mention[1:])
    except ChatNotFound:
        await message.reply(f"Пользователь {user_mention} не найден в этом чате.")
        return
    
    # Проверяем, можно ли забанить пользователя
    try:
        await message.chat.kick(chat_member.user.id)
        
        await message.reply(f"Пользователь {user_mention} забанен.")
    except (CantRestrictChatOwner, UserIsAnAdministratorOfTheChat):
        await message.reply(f"Невозможно забанить пользователя {user_mention}, так как он является администратором.")
    except Exception as e:
        logger.error(f"Ошибка при бане пользователя: {e}")
        await message.reply(f"Произошла ошибка при бане пользователя: {e}")

# Обработчик команды /violations
async def cmd_violations(message: types.Message):
    # Проверяем, что команда вызвана в группе и пользователь - администратор
    if message.chat.type == 'private':
        await message.reply("Эта команда доступна только в группах.")
        return
    
    db_session = message.bot.get('db_session')
    
    # Получаем список последних нарушений для этого чата (максимум 10)
    violations = db_session.query(Violation).filter(
        Violation.chat_id == str(message.chat.id)
    ).order_by(Violation.timestamp.desc()).limit(10).all()
    
    if not violations:
        await message.reply("Список нарушений пуст.")
        return
    
    # Формируем текст со списком нарушений
    violations_text = "Последние нарушения:\n\n"
    for violation in violations:
        username = violation.username or f"ID: {violation.user_id}"
        violations_text += (
            f"Пользователь: {username}\n"
            f"Тип нарушения: {violation.violation_type}\n"
            f"Действие: {violation.action_taken}\n"
            f"Время: {violation.timestamp}\n"
            f"Сообщение: {violation.message_text[:50]}...\n\n"
        )
    
    await message.reply(violations_text)

# Обработчик для фильтрации сообщений
async def handle_violation(message: types.Message, violation_type: str):
    db_session = message.bot.get('db_session')
    
    # Получаем настройки чата
    chat_settings = db_session.query(ChatSettings).filter(
        ChatSettings.chat_id == str(message.chat.id)
    ).first()
    
    if not chat_settings:
        chat_settings = ChatSettings(chat_id=str(message.chat.id))
        db_session.add(chat_settings)
        db_session.commit()
    
    # Получаем или создаем счетчик предупреждений для пользователя
    user_warnings = db_session.query(UserWarnings).filter(
        UserWarnings.chat_id == str(message.chat.id),
        UserWarnings.user_id == str(message.from_user.id)
    ).first()
    
    if not user_warnings:
        user_warnings = UserWarnings(
            chat_id=str(message.chat.id),
            user_id=str(message.from_user.id),
            warnings_count=0
        )
        db_session.add(user_warnings)
    
    # Создаем запись о нарушении
    violation = Violation(
        chat_id=str(message.chat.id),
        user_id=str(message.from_user.id),
        username=message.from_user.username,
        message_text=message.text,
        violation_type=violation_type,
        action_taken=chat_settings.action_type
    )
    db_session.add(violation)
    
    # Выполняем действие в зависимости от настроек
    action = chat_settings.action_type
    
    # Удаляем сообщение в любом случае
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    if action == 'warn':
        # Увеличиваем счетчик предупреждений
        user_warnings.warnings_count += 1
        db_session.commit()
        
        # Отправляем предупреждение пользователю в личные сообщения
        try:
            await message.bot.send_message(
                message.from_user.id,
                f"Ваше сообщение в чате {message.chat.title} было удалено за нарушение правил. "
                f"Тип нарушения: {violation_type}. "
                f"Предупреждение {user_warnings.warnings_count}/3."
            )
        except (BotBlocked, ChatNotFound):
            logger.warning(f"Не удалось отправить предупреждение пользователю {message.from_user.id}")
        
        # Отправляем предупреждение в чат с упоминанием пользователя
        user_mention = f"@{message.from_user.username}" if message.from_user.username else f"[Пользователь](tg://user?id={message.from_user.id})"
        await message.bot.send_message(
            message.chat.id,
            f"{user_mention}, ваше сообщение было удалено за нарушение правил. "
            f"Тип нарушения: {violation_type}. "
            f"Предупреждение {user_warnings.warnings_count}/3.",
            parse_mode="Markdown"
        )
        
        # Если у пользователя 3 предупреждения, применяем более строгое наказание
        if user_warnings.warnings_count >= 3:
            if chat_settings.action_type == 'warn':
                # Если действие по умолчанию - предупреждение, то мутим пользователя
                try:
                    until_date = datetime.datetime.now() + datetime.timedelta(seconds=chat_settings.mute_duration)
                    await message.chat.restrict(
                        message.from_user.id,
                        until_date=until_date,
                        can_send_messages=False
                    )
                    
                    await message.bot.send_message(
                        message.chat.id,
                        f"Пользователь @{message.from_user.username or message.from_user.id} получил мут на "
                        f"{chat_settings.mute_duration // 60} минут за накопление 3 предупреждений."
                    )
                except Exception as e:
                    logger.error(f"Ошибка при муте пользователя: {e}")
            
            # Сбрасываем счетчик предупреждений
            user_warnings.warnings_count = 0
            db_session.commit()
    
    elif action == 'mute':
        # Мутим пользователя
        try:
            until_date = datetime.datetime.now() + datetime.timedelta(seconds=chat_settings.mute_duration)
            await message.chat.restrict(
                message.from_user.id,
                until_date=until_date,
                can_send_messages=False
            )
            
            await message.bot.send_message(
                message.chat.id,
                f"Пользователь @{message.from_user.username or message.from_user.id} получил мут на "
                f"{chat_settings.mute_duration // 60} минут за нарушение правил."
            )
        except Exception as e:
            logger.error(f"Ошибка при муте пользователя: {e}")
    
    elif action == 'ban':
        # Баним пользователя
        try:
            await message.chat.kick(message.from_user.id)
            
            await message.bot.send_message(
                message.chat.id,
                f"Пользователь @{message.from_user.username or message.from_user.id} забанен за нарушение правил."
            )
        except Exception as e:
            logger.error(f"Ошибка при бане пользователя: {e}")
    
    db_session.commit()

# Обработчик сообщений с нецензурной лексикой
async def handle_obscene(message: types.Message):
    await handle_violation(message, 'obscene')

# Обработчик сообщений со ссылками
async def handle_link(message: types.Message):
    await handle_violation(message, 'link')

# Обработчик сообщений с запрещенными словами
async def handle_banned_word(message: types.Message):
    await handle_violation(message, 'keyword')

# Обработчик команды /config для настройки бота через личные сообщения
async def cmd_config(message: types.Message):
    # Проверяем, что команда вызвана в личных сообщениях
    if message.chat.type != 'private':
        await message.reply("Эта команда доступна только в личных сообщениях с ботом.")
        return
    
    db_session = message.bot.get('db_session')
    
    # Получаем список чатов, где пользователь является администратором
    user_chats = []
    
    # Получаем все настройки чатов из базы данных
    all_chats = db_session.query(ChatSettings).all()
    
    for chat_settings in all_chats:
        try:
            chat_id = int(chat_settings.chat_id)
            chat = await message.bot.get_chat(chat_id)
            member = await chat.get_member(message.from_user.id)
            
            if member.is_chat_admin() or member.is_chat_creator():
                user_chats.append({
                    'id': chat_id,
                    'title': chat.title
                })
        except Exception as e:
            logger.error(f"Ошибка при получении информации о чате {chat_settings.chat_id}: {e}")
    
    if not user_chats:
        await message.reply(
            "Я не нашел чатов, где вы являетесь администратором. \n\n"
            "Добавьте меня в группу и назначьте администратором, чтобы настроить модерацию."
        )
        return
    
    # Формируем список чатов для выбора
    chat_list = "Выберите чат для настройки:\n\n"
    for i, chat in enumerate(user_chats, 1):
        chat_list += f"{i}. {chat['title']}\n"
    
    chat_list += "\nОтправьте номер чата для настройки."
    
    # Сохраняем список чатов в контексте пользователя
    message.bot['user_chats'] = message.bot.get('user_chats', {})
    message.bot['user_chats'][message.from_user.id] = user_chats
    
    # Устанавливаем состояние пользователя
    message.bot['user_states'] = message.bot.get('user_states', {})
    message.bot['user_states'][message.from_user.id] = 'select_chat'
    
    await message.reply(chat_list)

# Обработчик для выбора чата
async def handle_chat_selection(message: types.Message):
    user_id = message.from_user.id
    user_chats = message.bot.get('user_chats', {}).get(user_id, [])
    
    try:
        chat_index = int(message.text) - 1
        if 0 <= chat_index < len(user_chats):
            selected_chat = user_chats[chat_index]
            
            # Сохраняем выбранный чат
            message.bot['selected_chat'] = message.bot.get('selected_chat', {})
            message.bot['selected_chat'][user_id] = selected_chat
            
            # Показываем меню настроек
            await show_settings_menu(message, selected_chat['id'])
        else:
            await message.reply("Неверный номер чата. Пожалуйста, выберите чат из списка.")
    except ValueError:
        await message.reply("Пожалуйста, введите номер чата из списка.")

# Функция для отображения меню настроек
async def show_settings_menu(message: types.Message, chat_id):
    db_session = message.bot.get('db_session')
    
    # Получаем настройки чата
    chat_settings = db_session.query(ChatSettings).filter(
        ChatSettings.chat_id == str(chat_id)
    ).first()
    
    if not chat_settings:
        chat_settings = ChatSettings(chat_id=str(chat_id))
        db_session.add(chat_settings)
        db_session.commit()
    
    # Формируем меню настроек
    settings_menu = (
        f"Настройки для чата {message.bot['selected_chat'][message.from_user.id]['title']}:\n\n"
        f"1. Фильтр мата: {'Включен' if chat_settings.filter_obscene else 'Выключен'}\n"
        f"2. Фильтр ссылок: {'Включен' if chat_settings.filter_links else 'Выключен'}\n"
        f"3. Фильтр ключевых слов: {'Включен' if chat_settings.filter_keywords else 'Выключен'}\n"
        f"4. Действие при нарушении: {chat_settings.action_type}\n"
        f"5. Длительность мута: {chat_settings.mute_duration // 60} минут\n"
        f"6. Управление запрещенными словами\n\n"
        f"Отправьте номер настройки, которую хотите изменить, или 'назад' для возврата к выбору чата."
    )
    
    # Устанавливаем состояние пользователя
    message.bot['user_states'][message.from_user.id] = 'settings_menu'
    
    await message.reply(settings_menu)

# Обработчик для меню настроек
async def handle_settings_menu(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    if message.text.lower() == 'назад':
        await cmd_config(message)
        return
    
    try:
        option = int(message.text)
        if 1 <= option <= 6:
            if option == 1:  # Фильтр мата
                message.bot['user_states'][user_id] = 'toggle_obscene'
                await message.reply(
                    "Фильтр мата:\n\n"
                    "1. Включить\n"
                    "2. Выключить\n\n"
                    "Выберите опцию."
                )
            elif option == 2:  # Фильтр ссылок
                message.bot['user_states'][user_id] = 'toggle_links'
                await message.reply(
                    "Фильтр ссылок:\n\n"
                    "1. Включить\n"
                    "2. Выключить\n\n"
                    "Выберите опцию."
                )
            elif option == 3:  # Фильтр ключевых слов
                message.bot['user_states'][user_id] = 'toggle_keywords'
                await message.reply(
                    "Фильтр ключевых слов:\n\n"
                    "1. Включить\n"
                    "2. Выключить\n\n"
                    "Выберите опцию."
                )
            elif option == 4:  # Действие при нарушении
                message.bot['user_states'][user_id] = 'set_action'
                await message.reply(
                    "Действие при нарушении:\n\n"
                    "1. Удалить сообщение\n"
                    "2. Предупредить пользователя\n"
                    "3. Замутить пользователя\n"
                    "4. Забанить пользователя\n\n"
                    "Выберите опцию."
                )
            elif option == 5:  # Длительность мута
                message.bot['user_states'][user_id] = 'set_mute_duration'
                await message.reply(
                    "Введите длительность мута в минутах (от 1 до 10080)."
                )
            elif option == 6:  # Управление запрещенными словами
                await show_banned_words_menu(message, selected_chat['id'])
        else:
            await message.reply("Неверный номер опции. Пожалуйста, выберите опцию из меню.")
    except ValueError:
        await message.reply("Пожалуйста, введите номер опции из меню.")

# Функция для отображения меню управления запрещенными словами
async def show_banned_words_menu(message: types.Message, chat_id):
    db_session = message.bot.get('db_session')
    
    # Получаем список запрещенных слов
    banned_words = db_session.query(BannedWord).filter(
        BannedWord.chat_id == str(chat_id)
    ).all()
    
    words_list = "Список запрещенных слов:\n\n"
    if banned_words:
        for i, word in enumerate(banned_words, 1):
            words_list += f"{i}. {word.word}\n"
    else:
        words_list += "Список пуст\n"
    
    words_list += "\nВыберите действие:\n"
    words_list += "1. Добавить слово\n"
    words_list += "2. Удалить слово\n"
    words_list += "3. Назад к настройкам\n"
    
    # Устанавливаем состояние пользователя
    message.bot['user_states'][message.from_user.id] = 'banned_words_menu'
    
    await message.reply(words_list)

# Обработчик для меню управления запрещенными словами
async def handle_banned_words_menu(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    try:
        option = int(message.text)
        if option == 1:  # Добавить слово
            message.bot['user_states'][user_id] = 'add_banned_word'
            await message.reply("Введите слово, которое нужно добавить в список запрещенных.")
        elif option == 2:  # Удалить слово
            db_session = message.bot.get('db_session')
            banned_words = db_session.query(BannedWord).filter(
                BannedWord.chat_id == str(selected_chat['id'])
            ).all()
            
            if not banned_words:
                await message.reply("Список запрещенных слов пуст.")
                await show_banned_words_menu(message, selected_chat['id'])
                return
            
            words_list = "Выберите номер слова для удаления:\n\n"
            for i, word in enumerate(banned_words, 1):
                words_list += f"{i}. {word.word}\n"
            
            # Сохраняем список слов в контексте пользователя
            message.bot['banned_words'] = message.bot.get('banned_words', {})
            message.bot['banned_words'][user_id] = banned_words
            
            message.bot['user_states'][user_id] = 'delete_banned_word'
            await message.reply(words_list)
        elif option == 3:  # Назад к настройкам
            await show_settings_menu(message, selected_chat['id'])
        else:
            await message.reply("Неверный номер опции. Пожалуйста, выберите опцию из меню.")
    except ValueError:
        await message.reply("Пожалуйста, введите номер опции из меню.")

# Обработчик для добавления запрещенного слова
async def handle_add_banned_word(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    word = message.text.lower()
    db_session = message.bot.get('db_session')
    
    # Проверяем, есть ли уже такое слово в базе
    existing_word = db_session.query(BannedWord).filter(
        BannedWord.chat_id == str(selected_chat['id']),
        BannedWord.word == word
    ).first()
    
    if existing_word:
        await message.reply(f"Слово '{word}' уже в списке запрещенных.")
    else:
        # Добавляем слово в базу
        banned_word = BannedWord(chat_id=str(selected_chat['id']), word=word)
        db_session.add(banned_word)
        db_session.commit()
        await message.reply(f"Слово '{word}' добавлено в список запрещенных.")
    
    # Возвращаемся к меню управления запрещенными словами
    await show_banned_words_menu(message, selected_chat['id'])

# Обработчик для удаления запрещенного слова
async def handle_delete_banned_word(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    banned_words = message.bot.get('banned_words', {}).get(user_id, [])
    
    if not selected_chat or not banned_words:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    try:
        word_index = int(message.text) - 1
        if 0 <= word_index < len(banned_words):
            db_session = message.bot.get('db_session')
            word_to_delete = banned_words[word_index]
            
            db_session.delete(word_to_delete)
            db_session.commit()
            
            await message.reply(f"Слово '{word_to_delete.word}' удалено из списка запрещенных.")
        else:
            await message.reply("Неверный номер слова. Пожалуйста, выберите слово из списка.")
    except ValueError:
        await message.reply("Пожалуйста, введите номер слова из списка.")
    
    # Возвращаемся к меню управления запрещенными словами
    await show_banned_words_menu(message, selected_chat['id'])

# Обработчики для изменения настроек
async def handle_toggle_setting(message: types.Message, setting_name):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    try:
        option = int(message.text)
        db_session = message.bot.get('db_session')
        
        chat_settings = db_session.query(ChatSettings).filter(
            ChatSettings.chat_id == str(selected_chat['id'])
        ).first()
        
        if not chat_settings:
            chat_settings = ChatSettings(chat_id=str(selected_chat['id']))
            db_session.add(chat_settings)
        
        if setting_name == 'obscene':
            chat_settings.filter_obscene = (option == 1)
            setting_text = "Фильтр мата"
        elif setting_name == 'links':
            chat_settings.filter_links = (option == 1)
            setting_text = "Фильтр ссылок"
        elif setting_name == 'keywords':
            chat_settings.filter_keywords = (option == 1)
            setting_text = "Фильтр ключевых слов"
        
        db_session.commit()
        
        status = "включен" if option == 1 else "выключен"
        await message.reply(f"{setting_text} {status}.")
    except ValueError:
        await message.reply("Пожалуйста, выберите 1 (Включить) или 2 (Выключить).")
    
    # Возвращаемся к меню настроек
    await show_settings_menu(message, selected_chat['id'])

# Обработчик для изменения действия при нарушении
async def handle_set_action(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    try:
        option = int(message.text)
        db_session = message.bot.get('db_session')
        
        chat_settings = db_session.query(ChatSettings).filter(
            ChatSettings.chat_id == str(selected_chat['id'])
        ).first()
        
        if not chat_settings:
            chat_settings = ChatSettings(chat_id=str(selected_chat['id']))
            db_session.add(chat_settings)
        
        if option == 1:
            chat_settings.action_type = 'delete'
            action_text = "Удаление сообщения"
        elif option == 2:
            chat_settings.action_type = 'warn'
            action_text = "Предупреждение пользователя"
        elif option == 3:
            chat_settings.action_type = 'mute'
            action_text = "Мут пользователя"
        elif option == 4:
            chat_settings.action_type = 'ban'
            action_text = "Бан пользователя"
        else:
            await message.reply("Неверный номер опции. Пожалуйста, выберите опцию из меню.")
            return
        
        db_session.commit()
        
        await message.reply(f"Действие при нарушении установлено: {action_text}.")
    except ValueError:
        await message.reply("Пожалуйста, введите номер опции из меню.")
    
    # Возвращаемся к меню настроек
    await show_settings_menu(message, selected_chat['id'])

# Обработчик для изменения длительности мута
async def handle_set_mute_duration(message: types.Message):
    user_id = message.from_user.id
    selected_chat = message.bot.get('selected_chat', {}).get(user_id)
    
    if not selected_chat:
        await message.reply("Произошла ошибка. Пожалуйста, начните настройку заново с команды /config")
        return
    
    try:
        duration = int(message.text)
        if 1 <= duration <= 10080:  # от 1 минуты до 7 дней
            db_session = message.bot.get('db_session')
            
            chat_settings = db_session.query(ChatSettings).filter(
                ChatSettings.chat_id == str(selected_chat['id'])
            ).first()
            
            if not chat_settings:
                chat_settings = ChatSettings(chat_id=str(selected_chat['id']))
                db_session.add(chat_settings)
            
            chat_settings.mute_duration = duration * 60  # переводим минуты в секунды
            db_session.commit()
            
            await message.reply(f"Длительность мута установлена: {duration} минут.")
        else:
            await message.reply("Пожалуйста, введите значение от 1 до 10080 минут (7 дней).")
            return
    except ValueError:
        await message.reply("Пожалуйста, введите числовое значение.")
    
    # Возвращаемся к меню настроек
    await show_settings_menu(message, selected_chat['id'])

# Обработчик для всех сообщений в личных чатах (для работы с состояниями)
async def handle_private_messages(message: types.Message):
    user_id = message.from_user.id
    user_state = message.bot.get('user_states', {}).get(user_id)
    
    if not user_state:
        return
    
    if user_state == 'select_chat':
        await handle_chat_selection(message)
    elif user_state == 'settings_menu':
        await handle_settings_menu(message)
    elif user_state == 'banned_words_menu':
        await handle_banned_words_menu(message)
    elif user_state == 'add_banned_word':
        await handle_add_banned_word(message)
    elif user_state == 'delete_banned_word':
        await handle_delete_banned_word(message)
    elif user_state == 'toggle_obscene':
        await handle_toggle_setting(message, 'obscene')
    elif user_state == 'toggle_links':
        await handle_toggle_setting(message, 'links')
    elif user_state == 'toggle_keywords':
        await handle_toggle_setting(message, 'keywords')
    elif user_state == 'set_action':
        await handle_set_action(message)
    elif user_state == 'set_mute_duration':
        await handle_set_mute_duration(message)

# Регистрация всех обработчиков
def register_handlers(dp: Dispatcher, bot: Bot, db_session):
    # Сохраняем сессию базы данных в боте для доступа из обработчиков
    bot['db_session'] = db_session
    
    # Регистрация команд
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_help, commands=['help'])
    dp.register_message_handler(cmd_config, commands=['config'])
    dp.register_message_handler(cmd_settings, commands=['settings'])
    dp.register_message_handler(cmd_addword, commands=['addword'], is_admin=True)
    dp.register_message_handler(cmd_delword, commands=['delword'], is_admin=True)
    dp.register_message_handler(cmd_listwords, commands=['listwords'], is_admin=True)
    dp.register_message_handler(cmd_setaction, commands=['setaction'], is_admin=True)
    dp.register_message_handler(cmd_mute, commands=['mute'], is_admin=True)
    dp.register_message_handler(cmd_ban, commands=['ban'], is_admin=True)
    dp.register_message_handler(cmd_violations, commands=['violations'], is_admin=True)
    
    # Регистрация обработчика для личных сообщений
    dp.register_message_handler(handle_private_messages, lambda message: message.chat.type == 'private', content_types=types.ContentTypes.TEXT)
    
    # Регистрация обработчиков фильтров
    dp.register_message_handler(handle_obscene, is_obscene=True)
    dp.register_message_handler(handle_link, has_link=True)
    dp.register_message_handler(handle_banned_word, has_banned_word=True)