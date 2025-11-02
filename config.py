import os
import logging
import sys
from pathlib import Path
from datetime import datetime

from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),
    **os.environ,
}

BOT_TOKEN = config.get("BOT_TOKEN")
print(BOT_TOKEN)

ADMIN_PASSWORD = config.get("ADMIN_PASSWORD")

# Пароли для каждого пользователя
PASSWORDS = {
    "parent": config.get("ADMIN_PASSWORD"),
    "djama": config.get("DJAMA_PASSWORD"),
    "ramz": config.get("RAMZ_PASSWORD"),
    "riza": config.get("RIZA_PASSWORD")
}


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
