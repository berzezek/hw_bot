#!/bin/bash
set -e

echo "🤖 Запуск бота управления заданиями..."

# Запуск без активации venv
python3 main.py "$@"
