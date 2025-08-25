# Multi-Threaded Architecture with Independent AsyncIO Loops

## Overview

This document describes the new architecture for the Telegram bot application that runs three independent components in separate threads, each with its own AsyncIO event loop and database connection.

## Components

### 1. Main Thread (Bot)
- **Purpose**: Handles Telegram bot interactions
- **Event Loop**: Main application thread
- **Database**: Independent connection using `async_session`
- **Handlers**: All bot command and message handlers

### 2. Parser Thread
- **Purpose**: Scrapes apartment listings and sends notifications
- **Event Loop**: Separate thread with independent event loop
- **Database**: Independent connection using `async_session`
- **Components**: 
  - Parser logic in `parser/parser.py`
  - Notification sending in `parser/sending_messages.py`

### 3. Worker Thread
- **Purpose**: Checks for expired subscriptions and sends notifications
- **Event Loop**: Separate thread with independent event loop
- **Database**: Independent connection using `async_session`
- **Components**: Subscription expiration worker in `bot/subscription_worker.py`

## Database Architecture

Each thread creates its own database engine and session maker using the `create_database_engine_and_session()` function from `db.py`. This ensures:

1. **Thread Safety**: Each thread has its own database connection
2. **Connection Pooling**: SQLAlchemy handles connection pooling per engine
3. **Session Isolation**: Each thread manages its own session lifecycle

## Implementation Details

### Thread Management

Threads are created using the standard `threading` module with custom functions:

```python
def run_parser_in_thread():
    """Run parser in its own thread with independent event loop."""
    parser_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(parser_loop)
    parser_loop.run_until_complete(main_parser())

def run_worker_in_thread():
    """Run worker in its own thread with independent event loop."""
    worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(worker_loop)
    worker_loop.run_until_complete(subscription_expiration_worker())
```

### Database Session Handling

All database functions in `db.py` now accept an optional `session` parameter:

- If no session is provided, the function creates a new session
- If a session is provided, it uses that session directly
- This allows for transaction control when needed

### Component Initialization

Each component initializes its own database connection:

1. **Main Thread**: `init_main_db()` in `main.py` and handler modules
2. **Parser Thread**: `init_parser_db()` and `init_parser_bot()` in `parser/parser.py`
3. **Worker Thread**: `init_worker_db()` and `init_worker_bot()` in `bot/subscription_worker.py`
4. **Sending Messages**: `init_sending_messages_db()` in `parser/sending_messages.py`

## Benefits

1. **Isolation**: Each component runs independently without interfering with others
2. **Scalability**: Components can be scaled independently
3. **Fault Tolerance**: If one component fails, others continue running
4. **Performance**: No blocking between components
5. **Resource Management**: Each thread manages its own resources

## File Structure

```
tg_auto/
├── main.py                 # Main application entry point
├── db.py                   # Database models and functions
├── bot/
│   ├── handlers/           # Bot command handlers
│   └── subscription_worker.py # Subscription expiration worker
└── parser/
    ├── parser.py           # Apartment listing parser
    └── sending_messages.py # Notification sending logic
```

## Testing

To test the new architecture:

1. Start the application with `python main.py`
2. Verify all three threads are running:
   - Main thread handles bot commands
   - Parser thread scrapes listings periodically
   - Worker thread checks subscriptions periodically
3. Check database connections are working in all threads
4. Verify notifications are being
4. Verify notifications are being sent correctly
5. Monitor logs for any threading or database issues

## Future Improvements

1. Add health checks for each thread
2. Implement graceful shutdown for all threads
3. Add monitoring and metrics collection
4. Consider using process-based parallelism for even better isolation