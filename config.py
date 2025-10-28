import os
from dotenv import dotenv_values

config = dotenv_values(".env")

BOT_TOKEN = config.get("BOT_TOKEN")

ADMIN_PASSWORD = config.get("ADMIN_PASSWORD")

# Пароли для каждого пользователя
PASSWORDS = {
    "parent": config.get("ADMIN_PASSWORD"),
    "djama": config.get("DJAMA_PASSWORD"),
    "ramz": config.get("RAMZ_PASSWORD"),
    "riza": config.get("RIZA_PASSWORD")
}