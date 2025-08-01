# Telegram Apartment Bot

Этот проект — Telegram-бот, который помогает пользователям находить квартиры по заданным параметрам (цена, количество комнат, район, срок аренды, меблировка), собирая данные с Bayut.com и уведомляя подписчиков о подходящих объявлениях.

## Возможности
- **Интерактивность**: Пользователи выбирают параметры через инлайн-клавиатуры и сохраняют их в базу данных PostgreSQL.
- **Сбор данных**: Бот парсит объявления о квартирах с Bayut.com, сохраняя цену, комнаты, район и фото.
- **Уведомления**: Отправляет уведомления пользователям с активной подпиской при появлении подходящих объявлений.
- **Проверка подписки**: Уведомления получают только пользователи с активной подпиской (`status="active)`.

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

    7["User<br>External Actor"]
    subgraph 1["Project Configuration & Deployment<br>Various"]
        25["Dependency Management<br>Text"]
        26["Deployment Config<br>YAML"]
        27[".gitignore<br>Text"]
        28["Project Documentation<br>Markdown"]
        subgraph 2["Docker Configuration"]
            22["Dockerfile<br>Dockerfile"]
            23["Docker Compose<br>YAML"]
            24[".dockerignore<br>Text"]
        end
    end
    subgraph 3["Database System<br>SQLite, SQLAlchemy"]
        20["DB Connection & Operations<br>Python"]
        21["Table Creation<br>Python"]
        20 -->|Initializes| 21
    end
    subgraph 4["Data Parser System<br>Python"]
        17["Main Parser Logic<br>Python"]
        18["Message Sending Component<br>Python"]
        19["Districts Data<br>JSON"]
        17 -->|Sends via| 18
        17 -->|Uses| 19
    end
    subgraph 5["Telegram Bot System<br>Python, aiogram"]
        14["Bot Keyboards<br>Python"]
        15["Bot States<br>Python"]
        16["Subscription Worker<br>Python"]
        8["Bot Core & Entry Point<br>Python"]
        subgraph 6["Bot Handlers"]
            10["Subscription Handler<br>Python"]
            11["Broadcast Handler<br>Python"]
            12["Save/Delete Handler<br>Python"]
            13["Filters<br>Python"]
            9["Start Handler<br>Python"]
        end
        8 -->|Registers| 6
        8 -->|Uses| 14
        8 -->|Manages| 15
        8 -->|Starts| 16
        6 -->|Uses| 14
        6 -->|Manages| 15
    end
    3 -->|Deployed with| 1
    4 -->|Deployed with| 1
    4 -->|Stores data in| 3
    4 -->|Sends messages via| 5
    5 -->|Deployed with| 1
    5 -->|Uses| 3
    5 -->|Triggers| 4
    16 -->|Accesses| 3
    7 -->|Interacts with| 5
```

