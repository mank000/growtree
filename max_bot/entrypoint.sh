#!/bin/sh
# Ждём базы и Redis
python utils/wait_services.py

# Инициализация миграций Aerich
aerich init-db || true
aerich migrate
aerich upgrade

# Запуск бота
exec python main.py
