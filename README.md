# auto-artel-backend

Запуск с настройками для разработки

1) **Установить переменную окружения**
Для nix-систем: export DJANGO_SETTINGS_MODULE=auto_artel.develop
Для Windows PowerShell: $env:DJANGO_SETTINGS_MODULE="auto_artel.develop"
Заполнить следующие переменные окружения в файле .env:
 - AUTO_ARTEL_BOT_PASSWORD: пароль пользователя телеграм бота

2) **Миграции БД**
   ```bash
   python manage.py makemigrations home
   python manage.py makemigrations orders
   python manage.py migrate
   ```

3) **Создание групп и пользователей**
   ```bash
   python manage.py init
   python manage.py createsuperuser
   ```
