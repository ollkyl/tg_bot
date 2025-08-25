# New Architecture: Separate Asyncio Loops

## Overview

This document describes the new architecture for the application that runs three independent components (bot, parser, and worker) in separate asyncio loops, each with its own database connection.

## Architecture Diagram

```
Main Process
├── Thread 1: Bot Loop (Main Thread)
│   ├── Bot Instance
│   ├── Database Engine & Session
│   └── Event Loop
├── Thread 2: Parser Loop
│   ├── Parser Task
│   ├── Database Engine & Session
│   ├── Bot Instance (for notifications)
│   └── Event Loop
└── Thread 3: Worker Loop
    ├── Worker Task
    ├── Database Engine & Session
    ├── Bot Instance (for notifications)
    └── Event Loop
```

## Component Details

### 1. Bot Loop (Main Thread)
- **Location**: Main thread
- **Purpose**: Handles Telegram bot interactions
- **Database**: Own database engine and session
- **Bot**: Own bot instance
- **Event Loop**: Main asyncio event loop

### 2. Parser Loop (Thread 2)
- **Location**: Separate thread
- **Purpose**: Parses apartment listings from external sources
- **Database**: Own database engine and session
- **Bot**: Own bot instance for sending notifications
- **Event Loop**: Independent asyncio event loop

### 3. Worker Loop (Thread 3)
- **Location**: Separate thread
- **Purpose**: Handles subscription expiration notifications
- **Database**: Own database engine and session
- **Bot**: Own bot instance for sending notifications
- **Event Loop**: Independent asyncio event loop

## Database Management

Each thread creates its own database engine and session using the `create_database_engine_and_session()` function from `db.py`. This ensures:

1. **Thread Safety**: Each thread has its own database connection
2. **Connection Pooling**: SQLAlchemy manages connection pooling per engine
3. **Isolation**: Database operations in one thread don't block others

## Implementation Details

### Database Functions
All database functions in `db.py` have been updated to accept an optional `session` parameter:
- When `session` is provided, the function uses that session
- When `session` is `None`, the function creates a new session using the global session maker

### Thread Management
The main application (`main.py`) creates two separate threads:
1. **Parser Thread**: Runs `run_parser_in_thread()` function
2. **Worker Thread**: Runs `run_worker_in_thread()` function

Each thread creates its own asyncio event loop using `asyncio.new_event_loop()`.

### Component Initialization
Each component (parser and worker) initializes its own:
- Database engine and session using `init_parser_db()` or `init_worker_db()`
- Bot instance using `init_parser_bot()` or `init_worker_bot()`

## Benefits

1. **True Parallelism**: Components run independently without blocking each other
2. **Scalability**: Each component can be scaled independently
3. **Fault Isolation**: Issues in one component don't affect others
4. **Resource Management**: Each component manages its own resources
5. **Database Performance**: Separate database connections reduce contention

## Files Modified

1. `db.py` - Added session parameter support to database functions
2. `main.py` - Updated thread management and event loop creation
3. `parser/parser.py` - Added database and bot initialization
4. `bot/subscription_worker.py` - Added database and bot initialization
5. `parser/sending_messages.py` - Updated to accept bot as parameter

## Testing

To test the new architecture:
1. Run the application with `python main.py`
2. Verify that all three components start correctly
3. Check that each component logs its activity independently
4. Verify that database operations work correctly in each thread
5. Confirm that Telegram notifications are sent properly