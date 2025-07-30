from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    ARRAY,
    Boolean,
    func,
    update,
    delete,
    select,
)
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".") / ".env")
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=False)
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
    furnishing = Column(Boolean, nullable=True)
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
    furnishing = Column(Boolean, nullable=True)
    info = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    photo_ids = Column(ARRAY(String))
    object_id = Column(String, nullable=True)
    link = Column(String)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    subscription_type = Column(String(50), nullable=False)  # day, week, month
    start_date = Column(DateTime, nullable=False, server_default=func.now())
    end_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, expired


async def add_client(
    user_id, min_price, max_price, rooms, district, period, user_name, furnishing=None
):
    async with async_session() as session:
        async with session.begin():
            # Проверяем, есть ли запись с user_id и status="Y"
            query = select(Client).where(Client.user_id == user_id, Client.status == "Y")
            result = await session.execute(query)
            existing_client = result.scalars().first()

            if user_name is None:
                user_name = "username"

            if existing_client:
                # Обновляем существующую запись
                await session.execute(
                    update(Client)
                    .where(Client.user_id == user_id, Client.status == "Y")
                    .values(
                        min_price=min_price,
                        max_price=max_price,
                        rooms=rooms,
                        district=district,
                        period=period,
                        furnishing=furnishing,
                        user_name=user_name,
                        status="Y",
                    )
                )
            else:
                # Создаём новую запись, если нет существующей
                new_client = Client(
                    user_id=user_id,
                    min_price=min_price,
                    max_price=max_price,
                    rooms=rooms,
                    district=district,
                    period=period,
                    furnishing=furnishing,
                    status="Y",
                    user_name=user_name,
                )
                session.add(new_client)
        await session.commit()


async def add_apartment(
    owner, name, price, rooms, district, period, furnishing, info, photo_ids, object_id, link
):
    async with async_session() as session:
        async with session.begin():
            new_apartment = Apartment(
                owner=owner,
                name=name,
                price=price,
                period=period,
                rooms=rooms,
                district=district,
                furnishing=furnishing,
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
    async with async_session() as session:
        query = select(Client).where(Client.status == "Y")  # Только активные клиенты
        if apartment.price:
            query = query.where(
                ((Client.min_price <= apartment.price) | (Client.min_price == None))
                & ((Client.max_price >= apartment.price) | (Client.max_price == None))
            )
        if apartment.rooms:
            query = query.where((Client.rooms.contains(apartment.rooms)) | (Client.rooms == None))
        if apartment.district:
            query = query.where(
                (Client.district.contains(apartment.district)) | (Client.district == None)
            )
        if apartment.period:
            query = query.where(
                (Client.period.contains(apartment.period)) | (Client.period == None)
            )
        if apartment.furnishing is not None:
            query = query.where(
                (Client.furnishing == apartment.furnishing) | (Client.furnishing == None)
            )
        result = await session.execute(query)
        clients = result.scalars().all()
        return [(client.user_id, client.user_name) for client in clients]


async def get_all_users():
    async with async_session() as session:
        result = await session.execute(select(Client.user_id))
        users = result.scalars().all()
    return users


async def add_subscription(user_id, subscription_type):
    async with async_session() as session:
        async with session.begin():
            now = datetime.utcnow()
            duration = {
                "day": timedelta(days=1),
                "week": timedelta(days=7),
                "month": timedelta(days=30),
            }[subscription_type]

            # 1. Деактивируем все старые
            await session.execute(
                update(Subscription)
                .where(Subscription.user_id == user_id, Subscription.status == "active")
                .values(status="expired")
            )

            # 2. Создаём новую
            new_subscription = Subscription(
                user_id=user_id,
                subscription_type=subscription_type,
                start_date=now,
                end_date=now + duration,
                status="active",
            )
            session.add(new_subscription)
        await session.commit()


async def check_subscription(user_id):
    async with async_session() as session:
        query = (
            select(Subscription.status)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.end_date.desc())
            .limit(1)
        )
        result = await session.execute(query)
        status = result.scalar()
        print(f"check_subscription for user_id={user_id}: status={status}")
        return status
