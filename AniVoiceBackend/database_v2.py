from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from form import UserItem, AudioRecordItem
import logging
from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()

class UserInfo(db.Model):
    __tablename__ = 'userinfo'  # 保持与原始表名一致

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.Integer)
    age = db.Column(db.Integer)
    pic = db.Column(db.String(255))
    pwd = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    rate = db.Column(db.String(5))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    index = db.Column(db.String(255))
    salt = db.Column(db.String(64))

    def to_form(self):
        """将 ORM 对象转换为 UserItem"""
        return UserItem(
            id=self.id,
            name=self.name,
            sex=self.sex,
            age=self.age,
            pic=self.pic,
            pwd=self.pwd,
            phone=self.phone,
            email=self.email,
            rate=self.rate,
            create_time=self.create_time,
            update_time=self.update_time,
            index=self.index,
            salt=self.salt
        )
    

class AudioRecord(db.Model):
    __tablename__ = 'audio_records'
    
    audio_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(  # 外键关联到 userinfo 表
        db.Integer,
        db.ForeignKey('userinfo.id', ondelete='CASCADE'),  # 级联删除（可选）
        nullable=False
    )
    audio_character = db.Column(db.String(50), nullable=False)  # 音频对应的角色名
    audio_belong = db.Column(db.String(50), nullable=False)  # 音频所属的IP名
    audio_path = db.Column(db.String(255), nullable=False)  # 音频文件路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 使用 UTC 时间
    
    # 定义与 UserInfo 的关系（可选，方便反向查询）
    user = db.relationship('UserInfo', backref=db.backref('audios', lazy='dynamic', cascade="all, delete-orphan"))

    # 联合索引优化查询性能
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )

    def to_form(self) -> AudioRecordItem:
        return AudioRecordItem(
            audio_id=self.audio_id,
            user_id=self.user_id,
            audio_path=self.audio_path,
            audio_character=self.audio_character,
            audio_belong=self.audio_belong,
            create_at=self.created_at
        )


class UserManager:
    __ID_BASE__ = 10000000
    def __init__(self, app):
        self.app = app
        logging.info('Successfully initialized UserManager with app context')

    def insert_user(self, user_item: UserItem):
        """插入新用户"""
        with self.app.app_context():
            try:
                count = self.count_all_users()
                user_id = count + 1 + self.__ID_BASE__  # 自增ID
                user = UserInfo(
                    id=user_id,
                    name=user_item.name,
                    sex=user_item.sex,
                    age=user_item.age,
                    pic=user_item.pic,
                    pwd=user_item.pwd,
                    phone=user_item.phone,
                    email=user_item.email,
                    rate=user_item.rate,
                    index=user_item.index,
                    salt=user_item.salt
                )
                db.session.add(user)
                db.session.commit()
                logging.info(f'Insert user successfully! ID: {user.id}')
                return user.id, True
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error inserting user: {e}")
                return None, False

    def update_user(self, user_id: int, updates: dict):
        """更新用户信息"""
        with self.app.app_context():
            try:
                user = UserInfo.query.get(user_id)
                if not user:
                    return False
                
                # 动态更新字段
                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                db.session.commit()
                logging.info(f'Updated user {user_id}')
                return True
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error updating user: {e}")
                return False

    def delete_user(self, user_id: int):
        """删除用户"""
        with self.app.app_context():
            try:
                user = UserInfo.query.get(user_id)
                if not user:
                    return False
                
                db.session.delete(user)
                db.session.commit()
                logging.info(f'Deleted user {user_id}')
                return True
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error deleting user: {e}")
                return False

    def get_user_by_id(self, user_id: int) -> UserItem:
        """根据ID获取用户"""
        with self.app.app_context():
            user = UserInfo.query.get(user_id)
            return user.to_form() if user else None

    def get_user_by_email(self, email: str) -> UserItem:
        """根据邮箱获取用户"""
        with self.app.app_context():
            user = UserInfo.query.filter_by(email=email).first()
            return user.to_form() if user else None

    def count_all_users(self) -> int:
        """统计用户总数"""
        with self.app.app_context():
            return UserInfo.query.count()


class AudioRecordManager:
    def __init__(self, app):
        """
        初始化管理器
        :param app: 
        """
        self.app = app
        logging.info('Successfully initialized AudioRecordManager')

    def create_audio_record(self, user_id: int, audio_path: str) -> tuple:
        """
        创建音频记录 (带用户存在性验证)
        :return: (success: bool, message: str)
        """
        with self.app.app_context():
            try:
                # 验证用户是否存在
                if not self._user_exists(user_id):
                    return False, "User does not exist"

                # 插入新记录
                new_record = AudioRecord(
                    user_id=user_id,
                    audio_path=audio_path,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_record)
                db.session.commit()
                return True, "Audio record created successfully"

            except SQLAlchemyError as e:
                db.session.rollback()
                return False, f"Database error: {str(e)}"

    def get_recent_audios(self, user_id: int) -> tuple:
        """
        获取用户最近7天的音频记录
        :return: (success: bool, data: list/dict/None)
        """
        with self.app.app_context():
            try:
                seven_days_ago = datetime.utcnow() - timedelta(days=7)
                records = AudioRecord.query.filter(
                    AudioRecord.user_id == user_id,
                    AudioRecord.created_at >= seven_days_ago
                ).order_by(AudioRecord.created_at.desc()).all()

                return True, [record.to_dict() for record in records]

            except SQLAlchemyError as e:
                return False, f"Database error: {str(e)}"

    def delete_old_records(self, days_threshold: int = 7) -> tuple:
        """
        清理超过指定天数的旧记录
        :return: (success: bool, message: str)
        """
        with self.app.app_context():
            try:
                threshold = datetime.utcnow() - timedelta(days=days_threshold)
                deleted_count = AudioRecord.query.filter(
                    AudioRecord.created_at < threshold
                ).delete()
                db.session.commit()
                return True, f"Deleted {deleted_count} old records"

            except SQLAlchemyError as e:
                db.session.rollback()
                return False, f"Database error: {str(e)}"

    def _user_exists(self, user_id: int) -> bool:
        """内部方法：验证用户是否存在"""
        with self.app.app_context():
            return db.session.query(
                exists().where(UserInfo.user_id == user_id)
            ).scalar()