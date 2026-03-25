# database.py
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Index, Integer, String, delete, exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref

from server.schemas.audio import AudioRecordItem
from server.schemas.profile import UserItem


# ----------------------- 数据库配置 -----------------------
class DatabaseConfig:
    UID_BASE = 100000000

    def __init__(self, database_url):
        self.DATABASE_URL = database_url
        self.async_engine = create_async_engine(self.DATABASE_URL, echo=True)
        self.async_session_maker = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_models(self):
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self.ensure_userinfo_profile_columns(conn)
        logging.info("Database schema ensured successfully")

    async def ensure_userinfo_profile_columns(self, conn):
        """
        为 userinfo 表补齐个人中心需要的新字段。
        这里直接走轻量 DDL，适合当前用户量很小的场景。
        """
        await conn.execute(
            sa.text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'userinfo' AND column_name = 'index'
                    ) AND NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'userinfo' AND column_name = 'uid'
                    ) THEN
                        ALTER TABLE userinfo RENAME COLUMN "index" TO uid;
                    END IF;
                END $$;
                """
            )
        )
        await conn.execute(sa.text("ALTER TABLE userinfo ALTER COLUMN age DROP NOT NULL"))
        await conn.execute(
            sa.text(
                f"""
                ALTER TABLE userinfo
                ALTER COLUMN uid TYPE BIGINT
                USING (
                    CASE
                        WHEN uid IS NULL OR btrim(uid::text) = '' THEN NULL
                        WHEN uid::bigint >= {self.UID_BASE} THEN uid::bigint
                        ELSE {self.UID_BASE} + uid::bigint - 1
                    END
                )
                """
            ),
        )
        await conn.execute(sa.text("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS signature TEXT"))
        await conn.execute(sa.text("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS profile_banner TEXT"))
        await conn.execute(sa.text("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS birthday DATE"))
        await conn.execute(sa.text("ALTER TABLE userinfo ADD COLUMN IF NOT EXISTS gender VARCHAR(16)"))
        await conn.execute(
            sa.text(
                f"""
                UPDATE userinfo
                SET uid = {self.UID_BASE} + id - (
                    SELECT MIN(id) FROM userinfo
                )
                WHERE uid IS NULL OR uid < {self.UID_BASE}
                """
            ),
        )
        await conn.execute(sa.text("UPDATE userinfo SET signature = '' WHERE signature IS NULL"))
        await conn.execute(sa.text("UPDATE userinfo SET profile_banner = '' WHERE profile_banner IS NULL"))
        await conn.execute(sa.text("UPDATE userinfo SET gender = '' WHERE gender IS NULL"))
        await conn.execute(
            sa.text(
                """
                UPDATE userinfo
                SET age = DATE_PART('year', AGE(CURRENT_DATE, birthday))::BIGINT
                WHERE birthday IS NOT NULL
                """
            )
        )
        await conn.execute(sa.text("UPDATE userinfo SET age = NULL WHERE birthday IS NULL"))
        await conn.execute(
            sa.text('CREATE UNIQUE INDEX IF NOT EXISTS idx_userinfo_uid_unique ON userinfo (uid)')
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
    uid = Column(BigInteger, unique=True)
    salt = Column(String(64))
    signature = Column(String)
    profile_banner = Column(String)
    birthday = Column(Date)
    gender = Column(String(16))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    

class AudioRecords(Base):
    __tablename__ = 'audio_records'

    audio_id = Column(Integer, primary_key=True, autoincrement=True)
   
    user_id = Column(   # 外键关联到 userinfo 表
        Integer,
        ForeignKey('userinfo.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    audio_character = Column(String(50), nullable=False)     # 音频对应的角色名
    audio_belong = Column(String(50), nullable=False)   # 音频所属的IP名
    audio_path = Column(String(255), nullable=False)     # 音频文件URL
    created_at = Column(DateTime, default=datetime.utcnow)   # 创建时间
    audio_text = Column(String(255))   # 音频文本
    text_lang = Column(String(10))   # 音频语言
    character_avator_path = Column(String(255))   # 音频对应的角色头像URL
    audio_filename = Column(String(255))   # 音频文件名

    # 定义关系
    user = relationship(
        'UserInfo',
        backref=backref(
            'audios',
            lazy='dynamic',  # 保持动态查询
            cascade="all, delete-orphan"  # 应用层级联设置
        )
    )
    
    # 联合索引
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )


# ----------------------- 数据库管理器 -----------------------
class UserManager:
    __UID_BASE__ = 100000000

    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        logging.info('Successfully initialized UserManager')

    async def get_db_session(self):
        return self.db_config.async_session_maker()

    async def insert_user(self, user_item: UserItem) -> tuple:
        async with self.db_config.async_session_maker() as session:
            try:
                next_uid = user_item.uid or await self.generate_next_uid(session)

                # 创建 ORM 对象
                user = UserInfo(
                    **user_item.model_dump(exclude={"id", "uid"}),
                    uid=next_uid,
                )

                session.add(user)
                await session.commit()
                await session.refresh(user)
                logging.info(f'Insert user successfully! ID: {user.id}')
                return user.id, True
            except Exception as e:
                await session.rollback()
                logging.error(f"Error inserting user: {e}")
                return None, False

    async def generate_next_uid(self, session: AsyncSession) -> int:
        """
        生成下一个九位展示 UID，从 100000000 开始递增。
        :param session: 当前数据库会话。
        """
        stmt = select(func.max(UserInfo.uid))
        result = await session.execute(stmt)
        current_max_uid = result.scalar()
        if current_max_uid is None or current_max_uid < self.__UID_BASE__:
            return self.__UID_BASE__
        return int(current_max_uid) + 1

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
            return UserItem.model_validate(user) if user else None

    async def get_user_by_uid(self, uid: int) -> Optional[UserItem]:
        """
        根据对外展示 UID 获取用户资料。
        :param uid: 九位展示 UID。
        """
        async with self.db_config.async_session_maker() as session:
            stmt = select(UserInfo).where(UserInfo.uid == uid)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return UserItem.model_validate(user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[UserItem]:
        async with self.db_config.async_session_maker() as session:
            stmt = select(UserInfo).where(UserInfo.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return UserItem.model_validate(user) if user else None

    async def count_all_users(self, session) -> int:
        async with self.db_config.async_session_maker() as session:
            stmt = select(func.count(UserInfo.id))
            result = await session.execute(stmt)
            return result.scalar()


class AudioRecordManager:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        logging.info('Successfully initialized AudioRecordManager')

    async def get_db_session(self):
        return self.db_config.async_session_maker()
    
    async def create_audio_record(self, audio_record_item: AudioRecordItem) -> Tuple[bool, str]:
        async with self.db_config.async_session_maker() as session:
            try:
                # 验证用户是否存在
                if not await self._user_exists(audio_record_item.user_id):
                    return False, "User does not exist"

                # 创建 ORM 对象
                audio_record = AudioRecords(
                    **audio_record_item.model_dump()
                )

                session.add(audio_record)
                await session.commit()
                return True, "create audio record successfully"
            
            except SQLAlchemyError as e:
                await session.rollback()
                return False, f"database error: {str(e)}"
            
    async def get_rencent_audio_records_by_user_id(self, user_id: int, days: int = 7) -> Tuple[bool, List[AudioRecordItem]]:
        """
        获取用户最近7天的音频记录 
        :param user_id: 用户ID
        :param days: 天数
        :return: (success: bool, data/list/error)
        """
        seven_days_ago = datetime.utcnow() - timedelta(days=days)
        async with self.db_config.async_session_maker() as session:
            stmt = select(AudioRecords).where(
                AudioRecords.user_id == user_id,
                AudioRecords.created_at >= seven_days_ago
            ).order_by(AudioRecords.created_at.desc())
            result = await session.execute(stmt)
            audio_records = result.scalars().all()
            return True, [AudioRecordItem.model_validate(audio_record) for audio_record in audio_records]
        
    async def delete_audio_record_by_id(self, audio_id: int) -> Tuple[bool, str]:
        """
        根据ID删除音频记录
        :param audio_id: 音频ID
        :return: (success: bool, message: str)
        """
        async with self.db_config.async_session_maker() as session:
            try:
                stmt = delete(AudioRecords).where(AudioRecords.audio_id == audio_id)
                result = await session.execute(stmt)
                await session.commit()
                return True, f"delete audio record {audio_id} successfully"
            except SQLAlchemyError as e:
                await session.rollback()
                return False, f"database error: {str(e)}"
            
    async def delete_audio_records_by_ids(self, audio_ids: List[int]) -> Tuple[bool, str]:
        """
        根据ID列表批量删除音频记录
        :param audio_ids: 音频ID列表
        :return: (success: bool, message: str)
        """
        if not audio_ids:
            return False, "音频ID列表不能为空"
        
        async with self.db_config.async_session_maker() as session:
            try:
                # 构建批量删除语句，使用in_操作符匹配多个ID
                stmt = delete(AudioRecords).where(AudioRecords.audio_id.in_(audio_ids))
                result = await session.execute(stmt)
                await session.commit()
                
                # 获取受影响的行数（注意不同数据库驱动的差异）
                deleted_count = result.rowcount
                return True, f"成功删除 {deleted_count} 条音频记录"
                
            except SQLAlchemyError as e:
                await session.rollback()
                return False, f"数据库错误: {str(e)}"

    async def delete_old_audio_records(self, days: int = 7) -> Tuple[bool, str]:
        """
        异步清理旧记录
        :param days: 天数阈值
        :return: (success: bool, message: str)
        """
        async with self.db_config.async_session_maker() as session:
            threshold = datetime.utcnow() - timedelta(days=days)
            try:
                result = await session.execute(
                    delete(AudioRecords)
                    .where(AudioRecords.created_at < threshold)
                )
                await session.commit()
                return True, f"deleted {result.rowcount} old records"
            except SQLAlchemyError as e:
                await session.rollback()
                return False, f"database error: {str(e)}"

    async def _user_exists(self, user_id: int) -> bool:
        """ 异步用户存在性验证 """
        async with self.db_config.async_session_maker() as session:
            result = await session.execute(
                select(exists().where(UserInfo.id == user_id))
            )
            return result.scalar()
