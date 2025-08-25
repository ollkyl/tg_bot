# Telegram Apartment Bot  
t.me/FindApartmentsBot
Telegram-бот, который помогает пользователям находить квартиры по заданным параметрам (цена, количество комнат, район, срок аренды, меблировка), собирая данные с **Bayut.com** и уведомляя подписчиков о подходящих объявлениях.  

## Возможности  
- **Интерактивность** — выбор параметров через инлайн-клавиатуры и сохранение их в PostgreSQL.  
- **Сбор данных** — парсинг объявлений с Bayut.com с ценой, количеством комнат, районом и фото.  
- **Уведомления** — отправка подходящих предложений пользователям с активной подпиской.  
- **Проверка подписки** — уведомления только для пользователей со статусом `active`.  

<img src="https://github.com/user-attachments/assets/0b65b8b0-e926-4871-a2b6-1995cdac9099" width="40%">  
<img src="https://github.com/user-attachments/assets/fab729e6-51d3-4b9f-be20-19b5c851a01c" width="300" alt="image" />  

## Установка  
1. **Зависимости**  
   ```bash
   pip install -r requirements.txt
   ```  
2. **База данных** — PostgreSQL с таблицами `apartments`, `clients`, `subscriptions`. Таблицы создаются через `create_table.py`.  
3. **Запуск**  
   ```bash
   python main.py
   ```  



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

## Proposed Solution
Run three independent asyncio loops in separate threads:
1. **Bot Loop** - Main thread
2. **Parser Loop** - Separate thread
3. **Worker Loop** - Separate thread

## Architecture Diagram

```mermaid
graph TD
    A[Main Process] --> B[Thread 1: Bot Loop]
    A --> C[Thread 2: Parser Loop]
    A --> D[Thread 3: Worker Loop]
    
    B --> B1[Bot Instance]
    B --> B2[Database Connection 1]
    
    C --> C1[Parser Task]
    C --> C2[Database Connection 2]
    
    D --> D1[Worker Task]
    D --> D2[Database Connection 3]
    
    B2 --> E[(Shared Database)]
    C2 --> E
    D2 --> E
```

## Implementation Plan

### 1. Database Management
- Create a function to initialize database engine and session maker for each thread
- Each thread will have its own engine and session maker
- All engines connect to the same database

### 2. Thread Management
- Use `asyncio.new_event_loop()` and `loop.run_until_complete()` for each thread
- Properly handle thread lifecycle and cleanup

### 3. Component Modifications
- Parser: Remove global bot instance, create local one
- Worker: Remove global bot instance, create local one
- Sending Messages: Remove global bot instance, pass as parameter

## File Structure Changes
```
main.py          # Main entry point, thread management
db.py            # Database utilities, engine creation function
parser/parser.py # Parser logic with local event loop
bot/subscription_worker.py # Worker logic with local event loop