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
### Сборка Docker образа
1) **Установить переменные окружения**
2) **Сборка статических файлов**
   ````bash
   python manage.py collectstatic --noinput --clear
   ````
3) **Сборка docker образа**
   ````bash
   docker build -t auto_artel_backend:<tag1> .
   ````
4) **Создание docker образа для тестирования**
   ````bash
   docker tag -t auto_artel_backend:<tag1> <your_docker_account>/auto_artel_backend:latest
   ````
5) **Создание docker образа с определенной версией**
   ````bash
   docker tag -t auto_artel_backend:<tag1> <your_docker_account>/auto_artel_backend:<version>
   ````
6) **Публикация docker образов на hub.docker.com**
   ````bash
   docker push <your_docker_account>/auto_artel_backend:<version>
   docker push <your_docker_account>/auto_artel_backend:latest
   ````
