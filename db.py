from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import dotenv_values
from sqlalchemy import Column, Integer, String, BigInteger, update, delete


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
    user_id = Column(Integer, nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)
    rooms = Column(String(50), nullable=True)
    district = Column(String(150), nullable=True)
    period = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    user_name = Column(String(255), nullable=True)


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
