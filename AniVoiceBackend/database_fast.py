# database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import logging
import sqlalchemy as sa
from sqlalchemy import select, func


# ----------------------- 数据库配置 -----------------------
class DatabaseConfig:
    def __init__(self, database_url):
        self.DATABASE_URL = database_url
        self.async_engine = create_async_engine(self.DATABASE_URL, echo=True)
        self.async_session_maker = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )


# ----------------------- 基类模型 -----------------------
Base = declarative_base()


class UserInfo(Base):
    __tablename__ = 'userinfo'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    sex = Column(Integer)
    age = Column(Integer)
    pic = Column(String(255))
    pwd = Column(String(128), nullable=False)
    phone = Column(String(20))
    email = Column(String(120), unique=True)
    rate = Column(String(5))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    index = Column(String(255))
    salt = Column(String(64))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    

# ----------------------- Pydantic 模型 -----------------------
class UserItem(BaseModel):
    id: Optional[int] = None
    name: str
    sex: Optional[int] = None
    age: Optional[int] = None
    pic: Optional[str] = None
    pwd: str
    phone: Optional[str] = None
    email: str
    rate: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    index: Optional[str] = None
    salt: Optional[str] = None

    class Config:
        from_attributes = True


# ----------------------- 数据库管理器 -----------------------
class UserManager:
    __ID_BASE__ = 10000000

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        logging.info('Successfully initialized UserManager')

    async def get_db_session(self):
        return self.db_config.async_session_maker()

    async def insert_user(self, user_item: UserItem) -> tuple:
        async with self.db_config.async_session_maker() as session:
            try:
                # 计算用户ID
                count = await self.count_all_users(session)
                user_id = count + 1 + self.__ID_BASE__

                # 创建 ORM 对象
                user = UserInfo(
                    id=user_id,
                    **user_item.dict(exclude={'id'})
                )

                session.add(user)
                await session.commit()
                logging.info(f'Insert user successfully! ID: {user.id}')
                return user.id, True
            except Exception as e:
                await session.rollback()
                logging.error(f"Error inserting user: {e}")
                return None, False

    async def update_user(self, user_id: int, updates: dict) -> bool:
        async with self.db_config.async_session_maker() as session:
            try:
                stmt = select(UserInfo).where(UserInfo.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return False

                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

                await session.commit()
                logging.info(f'Updated user {user_id}')
                return True
            except Exception as e:
                await session.rollback()
                logging.error(f"Error updating user: {e}")
                return False

    async def delete_user(self, user_id: int) -> bool:
        async with self.db_config.async_session_maker() as session:
            try:
                stmt = select(UserInfo).where(UserInfo.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return False

                await session.delete(user)
                await session.commit()
                logging.info(f'Deleted user {user_id}')
                return True
            except Exception as e:
                await session.rollback()
                logging.error(f"Error deleting user: {e}")
                return False

    async def get_user_by_id(self, user_id: int) -> Optional[UserItem]:
        async with self.db_config.async_session_maker() as session:
            stmt = select(UserInfo).where(UserInfo.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return UserItem.from_orm(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[UserItem]:
        async with self.db_config.async_session_maker() as session:
            stmt = select(UserInfo).where(UserInfo.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return UserItem.from_orm(user) if user else None

    async def count_all_users(self, session) -> int:
        async with self.db_config.async_session_maker() as session:
            stmt = select(func.count(UserInfo.id))
            result = await session.execute(stmt)
            return result.scalar()
