#!/bin/bash

# Bakery Manager - FastAPI Server Launcher
# Запускает uvicorn сервер и открывает браузер

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Переменные
HOST="127.0.0.1"
PORT="8000"
URL="http://$HOST:$PORT"

# Показываем приветствие
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🥐 Bakery Manager - FastAPI Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверяем, установлен ли Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python не найден. Пожалуйста, установите Python.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python найден:${NC} $(python --version)"
echo ""

# Проверяем, установлены ли зависимости
echo -e "${BLUE}Проверка зависимостей...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  FastAPI не установлен. Установка...${NC}"
    pip install fastapi uvicorn -q
    echo -e "${GREEN}✅ FastAPI установлен${NC}"
fi

if ! python -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Uvicorn не установлен. Установка...${NC}"
    pip install uvicorn -q
    echo -e "${GREEN}✅ Uvicorn установлен${NC}"
fi

echo ""
echo -e "${GREEN}✅ Запуск сервера...${NC}"
echo -e "${BLUE}📍 Сервер доступен по адресу: ${GREEN}$URL${NC}"
echo ""

# Определяем ОС и открываем браузер
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash / MSYS)
    echo -e "${YELLOW}🌐 Открываю браузер на Windows...${NC}"
    start "" "$URL"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo -e "${YELLOW}🌐 Открываю браузер на macOS...${NC}"
    open "$URL"
else
    # Linux
    echo -e "${YELLOW}🌐 Открываю браузер на Linux...${NC}"
    if command -v xdg-open &> /dev/null; then
        xdg-open "$URL" 2>/dev/null &
    elif command -v gnome-open &> /dev/null; then
        gnome-open "$URL" 2>/dev/null &
    elif command -v firefox &> /dev/null; then
        firefox "$URL" 2>/dev/null &
    elif command -v google-chrome &> /dev/null; then
        google-chrome "$URL" 2>/dev/null &
    else
        echo -e "${YELLOW}ℹ️  Откройте браузер и перейдите на $URL${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ Сервер запущен${NC}"
echo -e "${YELLOW}⏹️  Нажмите Ctrl+C для остановки сервера${NC}"
echo ""

# Запускаем Uvicorn с автоперезагрузкой
uvicorn main:app --host $HOST --port $PORT --reload
