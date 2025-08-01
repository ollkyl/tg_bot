# Telegram Apartment Bot

Этот проект — Telegram-бот, который помогает пользователям находить квартиры по заданным параметрам (цена, количество комнат, район, срок аренды, меблировка), собирая данные с Bayut.com и уведомляя подписчиков о подходящих объявлениях.

## Возможности
- **Интерактивность**: Пользователи выбирают параметры через инлайн-клавиатуры и сохраняют их в базу данных PostgreSQL.
- **Сбор данных**: Бот парсит объявления о квартирах с Bayut.com, сохраняя цену, комнаты, район и фото.
- **Уведомления**: Отправляет уведомления пользователям с активной подпиской при появлении подходящих объявлений.
- **Проверка подписки**: Уведомления получают только пользователи с активной подпиской (`status="active)`

<img src="https://github.com/user-attachments/assets/0b65b8b0-e926-4871-a2b6-1995cdac9099" width="40%">
<img src="https://github.com/user-attachments/assets/78cccf20-021f-4011-a9ca-40041f5c9070" width="40%">


## Установка
1. **Зависимости**: Установите зависимости из `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
2. **База данных**: PostgreSQL с таблицами `apartments`, `clients` и `subscriptions`. Таблицы создаются самостоятельно с помощью create_table.py, если еще не созданы.
3. **Telegram-бот**: Создайте бота через BotFather, укажите токен в переменных окружения или конфиге.
4. **Запуск**: Запустите `main.py`:
   ```bash
   python main.py
   ```

## Использование
1. Запустите бота командой `/start`.
2. Выберите параметры (район, комнаты, диапазон цен и т.д.) через инлайн-клавиатуры.
3. Сохраните параметры кнопкой "Сохранить". Убедитесь, что подписка активна.
4. Получайте уведомления о подходящих квартирах при активной подписке.


## Архитектура проекта

```mermaid
graph TD
    %% Основные узлы
    User["User<br>External Actor"]
    
    subgraph "Project Configuration & Deployment<br>Various"
        subgraph "Docker Configuration"
            Dockerfile["Dockerfile<br>Dockerfile"]
            DockerCompose["Docker Compose<br>YAML"]
            DockerIgnore[".dockerignore<br>Text"]
        end
        Deps["Dependency Management<br>Text"]
        DeployConfig["Deployment Config<br>YAML"]
        GitIgnore[".gitignore<br>Text"]
        Docs["Project Documentation<br>Markdown"]
    end
    
    subgraph "Database System<br>PostgreSQL, SQLAlchemy"
        DB["DB Connection & Operations<br>Python"]
        Tables["Table Creation<br>Python"]
        DB --> Tables
    end
    
    subgraph "Data Parser System<br>Python"
        Parser["Main Parser Logic<br>Python"]
        Sender["Message Sending Component<br>Python"]
        Districts["Districts Data<br>JSON"]
        Parser --> Sender
        Parser --> Districts
    end
    
    subgraph "Telegram Bot System<br>Python, aiogram"
        subgraph "Bot Handlers"
            Start["Start Handler<br>Python"]
            Sub["Subscription Handler<br>Python"]
            Broadcast["Broadcast Handler<br>Python"]
            Save["Save/Delete Handler<br>Python"]
            Filters["Filters<br>Python"]
        end
        
        Core["Bot Core & Entry Point<br>Python"]
        Keyboards["Bot Keyboards<br>Python"]
        States["Bot States<br>Python"]
        Worker["Subscription Worker<br>Python"]
        
        Core --> Start
        Core --> Sub
        Core --> Broadcast
        Core --> Save
        Core --> Filters
        Core --> Keyboards
        Core --> States
        Core --> Worker
    end
    
    %% Связи между компонентами
    User --> Core
    
    "Database System<br>PostgreSQL, SQLAlchemy" -->|Deployed with| "Project Configuration & Deployment<br>Various"
    "Data Parser System<br>Python" -->|Deployed with| "Project Configuration & Deployment<br>Various"
    "Data Parser System<br>Python" -->|Stores data in| "Database System<br>PostgreSQL, SQLAlchemy"
    "Data Parser System<br>Python" -->|Sends messages via| "Telegram Bot System<br>Python, aiogram"
    "Telegram Bot System<br>Python, aiogram" -->|Deployed with| "Project Configuration & Deployment<br>Various"
    "Telegram Bot System<br>Python, aiogram" -->|Uses| "Database System<br>PostgreSQL, SQLAlchemy"
    "Telegram Bot System<br>Python, aiogram" -->|Triggers| "Data Parser System<br>Python"
    Worker -->|Accesses| "Database System<br>PostgreSQL, SQLAlchemy"