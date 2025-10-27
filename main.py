import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Уменьшаем шум от библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

logger = logging.getLogger("main")

async def wait_for_internet():
    """Ожидание интернет-подключения"""
    import aiohttp
    import socket
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Простая проверка DNS
            socket.gethostbyname('api.telegram.org')
            
            # Проверка HTTP подключения
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.telegram.org', timeout=5) as response:
                    if response.status == 200:
                        logger.info("✅ Интернет-подключение установлено")
                        return True
        except Exception as e:
            if attempt == 0:
                logger.warning(f"📡 Ожидание интернет-подключения... (попытка {attempt + 1}/{max_attempts})")
            await asyncio.sleep(2)
    
    logger.error("❌ Не удалось установить интернет-подключение")
    return False

async def main():
    """Основная функция запуска бота"""
    try:
        setup_logging()
        logger.info("🤖 Начало запуска бота")
        
        # Ожидаем интернет-подключение
        if not await wait_for_internet():
            print("❌ Нет интернет-подключения!")
            print("🔧 Проверьте сеть и запустите бота снова")
            return
        
        # Импорты после проверки подключения
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.exceptions import TelegramNetworkError
        
        import config
        from database import Database
        
        # Импорт обработчиков
        from handlers.common import router as common_router
        from handlers.parent import router as parent_router
        from handlers.child import router as child_router
        
        # Проверка токена
        if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not config.BOT_TOKEN:
            logger.error("❌ Токен бота не установлен!")
            print("❌ Токен бота не установлен!")
            print("📝 Откройте config.py и замените YOUR_BOT_TOKEN_HERE на реальный токен")
            print("💡 Получите токен у @BotFather в Telegram")
            return
        
        # Инициализация базы данных
        logger.info("📊 Инициализация базы данных")
        db = Database()
        
        # Инициализация бота с увеличенным таймаутом
        logger.info("🔧 Инициализация бота")
        bot = Bot(
            token=config.BOT_TOKEN,
            timeout=60  # Увеличиваем таймаут
        )
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрация роутеров
        logger.info("🔄 Регистрация обработчиков")
        dp.include_router(common_router)
        dp.include_router(parent_router)
        dp.include_router(child_router)
        
        # Проверка подключения к Telegram
        try:
            logger.info("🔗 Проверка подключения к Telegram API...")
            bot_info = await bot.get_me()
            logger.info(f"✅ Бот инициализирован: @{bot_info.username} ({bot_info.first_name})")
            logger.info(f"👥 Дети в системе: {', '.join(db.get_all_children())}")
            
            print("=" * 50)
            print("🤖 Бот успешно запущен!")
            print(f"📝 Бот: {bot_info.first_name} (@{bot_info.username})")
            print("📊 Логи сохраняются в папке logs/")
            print("⏹️  Для остановки нажмите Ctrl+C")
            print("=" * 50)
            
        except TelegramNetworkError as e:
            logger.error(f"❌ Ошибка сети при подключении к Telegram: {e}")
            print("❌ Ошибка сети!")
            print("🔧 Возможные решения:")
            print("   1. Проверьте интернет-подключение")
            print("   2. Если Telegram заблокирован, используйте VPN")
            print("   3. Попробуйте позже (возможны временные проблемы у Telegram)")
            return
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке бота: {e}")
            print(f"❌ Ошибка: {e}")
            print("🔧 Проверьте токен бота в config.py")
            return
        
        # Запуск бота с обработкой сетевых ошибок
        logger.info("🚀 Запуск поллинга бота")
        
        restart_count = 0
        max_restarts = 5
        
        while restart_count < max_restarts:
            try:
                await dp.start_polling(bot)
                break  # Если бот остановлен нормально
                
            except TelegramNetworkError as e:
                restart_count += 1
                logger.warning(f"📡 Сетевая ошибка (перезапуск {restart_count}/{max_restarts}): {e}")
                
                if restart_count < max_restarts:
                    wait_time = restart_count * 10  # Увеличиваем время ожидания
                    logger.info(f"⏳ Ожидание {wait_time} секунд перед перезапуском...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ Достигнут лимит перезапусков из-за сетевых ошибок")
                    break
                    
            except Exception as e:
                logger.exception(f"❌ Непредвиденная ошибка: {e}")
                break
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        print("❌ Ошибка: Проверьте установлены ли все зависимости")
        print("📦 Установите: pip install aiogram")
        
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")
        
    finally:
        logger.info("👋 Завершение работы бота")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️  Бот остановлен пользователем")
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.exception(f"❌ Непредвиденная ошибка: {e}")