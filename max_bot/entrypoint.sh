#!/bin/sh
# Ждём базы и Redis
python utils/wait_services.py

# Инициализация миграций Aerich
sleep 2
aerich init-db
aerich migrate
aerich upgrade

# Запуск бота
exec python main.py
