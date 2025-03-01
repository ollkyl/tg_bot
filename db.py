from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    func,
    update,
    delete,
    select,
)
from dotenv import dotenv_values

env_values = dotenv_values(".env")

DB_USER = env_values.get("DB_USER")
DB_PASS = env_values.get("DB_PASS")
DB_HOST = env_values.get("DB_HOST", "localhost")
DB_PORT = env_values.get("DB_PORT", "5432")
DB_NAME = env_values.get("DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    rooms = Column(String(50), nullable=True)
    district = Column(String(150), nullable=True)
    period = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    user_name = Column(String(255), nullable=True)


class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    rooms = Column(String)
    district = Column(String(150), nullable=True)
    period = Column(String, nullable=True)
    info = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


async def add_client(user_id, min_price, max_price, rooms, district, period, user_name):
    async with async_session() as session:
        async with session.begin():
            stmt_update = (
                update(Client).where(Client.user_id == user_id).values(status="N")
            )
            await session.execute(stmt_update)

            await session.flush()

            stmt_delete = delete(Client).where(Client.status == "N")
            await session.execute(stmt_delete)
            new_client = Client(
                user_id=user_id,
                min_price=min_price,
                max_price=max_price,
                rooms=rooms,
                district=district,
                period=period,
                user_name=user_name,
                status="Y",
            )
            session.add(new_client)
        await session.commit()


async def add_apartment(owner, name, price, rooms, district, period, info):
    """Добавление квартиры и уведомление подходящих клиентов."""
    async with async_session() as session:
        async with session.begin():
            new_apartment = Apartment(
                owner=owner,
                name=name,
                price=price,
                period=period,
                rooms=rooms,
                district=district,
                info=info,
            )
            session.add(new_apartment)
            await session.flush()  # Сохраняем объект, чтобы получить ID

            # После добавления квартиры ищем подходящих клиентов
            matching_clients = await find_matching_clients(new_apartment)

        await session.commit()
        return new_apartment.id, matching_clients


async def find_matching_clients(apartment):
    """Поиск клиентов, чьи параметры совпадают с новой квартирой."""
    async with async_session() as session:
        # Базовый запрос для поиска клиентов
        query = select(Client).where(Client.status == "Y")  # Только активные клиенты

        # Условия фильтрации
        if apartment.price:
            query = query.where(
                (Client.min_price <= apartment.price)
                & (Client.max_price >= apartment.price)
            )
        # if apartment.rooms:
        #     query = query.where(
        #         Client.rooms.contains(apartment.rooms.split()[0])
        #     )  # Например, "Студия" или "1-комнатная"
        # if apartment.district:
        #     query = query.where(Client.district.contains(apartment.district))
        # if apartment.period:
        #     query = query.where(Client.period == apartment.period)

        result = await session.execute(query)
        clients = result.scalars().all()
        print(f"Найденные клиенты: {clients}")
        return [client.user_id for client in clients]

    # Возвращаем ID квартиры и список клиентов
