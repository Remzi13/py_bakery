@echo off

if "%~1"=="" (
    echo ❌ Ошибка: Не указано описание миграции.
    echo Использование: migrate.bat "Описание изменений"
    exit /b 1
)

echo 🔄 Создание миграции...
call .\venv_build\Scripts\alembic revision --autogenerate -m "%~1"

if %errorlevel% neq 0 (
    echo ❌ Ошибка при создании миграции.
    exit /b %errorlevel%
)

echo ✅ Миграция создана.

echo 🔄 Применение миграции...
call .\venv_build\Scripts\alembic upgrade head

if %errorlevel% neq 0 (
    echo ❌ Ошибка при применении миграции.
    exit /b %errorlevel%
)

echo ✅ База данных успешно обновлена!
