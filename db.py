from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    ARRAY,
    func,
    update,
    delete,
    select,
)
from dotenv import dotenv_values
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


env_values = dotenv_values(".env")

DB_USER = env_values.get("DB_USER")
DB_PASS = env_values.get("DB_PASS")
DB_HOST = env_values.get("DB_HOST", "localhost")
DB_PORT = env_values.get("DB_PORT")
DB_NAME = env_values.get("DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    rooms = Column(String(500), nullable=True)
    district = Column(String(1400), nullable=True)
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
    district = Column(String(1200), nullable=True)
    period = Column(String, nullable=True)
    info = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    photo_ids = Column(ARRAY(String))
    object_id = Column(String, nullable=True)
    link = Column(String)


async def add_client(user_id, min_price, max_price, rooms, district, period, user_name):
    async with async_session() as session:
        async with session.begin():
            stmt_update = update(Client).where(Client.user_id == user_id).values(status="N")
            await session.execute(stmt_update)

            await session.flush()
            if user_name == None:
                user_name = "username"
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


async def add_apartment(
    owner, name, price, rooms, district, period, info, photo_ids, object_id, link
):
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
                photo_ids=photo_ids,
                object_id=object_id,
                link=link,
            )
            session.add(new_apartment)
            await session.flush()

            matching_clients = await find_matching_clients(new_apartment)

        await session.commit()
        return new_apartment.id, matching_clients


async def find_matching_clients(apartment):
    """Поиск клиентов, чьи параметры совпадают с новой квартирой."""
    async with async_session() as session:
        query = select(Client)
        # Условия фильтрации
        if apartment.price:
            query = query.where(
                (Client.min_price <= apartment.price) & (Client.max_price >= apartment.price)
            )

        if apartment.rooms:
            query = query.where(
                (Client.rooms.contains(apartment.rooms)) | (Client.rooms == "Не выбрано")
            )
        if apartment.district:
            query = query.where(
                (Client.district.contains(apartment.district)) | (Client.district == "Не выбрано")
            )
        if apartment.period:
            query = query.where(
                (Client.period.contains(apartment.period)) | (Client.period == "Не выбрано")
            )
        result = await session.execute(query)
        clients = result.scalars().all()
        print(f"Найденные клиенты: {clients}")
        return [(client.user_id, client.user_name) for client in clients]


async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(Client.user_id))
        users = result.scalars().all()
    return users
