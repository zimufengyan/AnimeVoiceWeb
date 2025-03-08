import psycopg2
from psycopg2 import sql
import logging
from datetime import datetime

from form import UserItem

class PostgresDB:
    def __init__(self, dbname, user, password, host="localhost", port="5432"):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            logging.info("Connected to the database.")
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")

    def execute_query(self, query, params=None):
        """Execute a query with optional parameters."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                logging.info("Query executed successfully.")
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error executing query: {e}")

    def insert(self, table, data):
        """Insert data into a table."""
        columns = data.keys()
        values = [data[column] for column in columns]
        insert_query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(sql.Placeholder() * len(values))
        )
        self.execute_query(insert_query, values)

    def update(self, table, data, conditions):
        """Update data in a table based on conditions."""
        columns = data.keys()
        values = [data[column] for column in columns]
        set_clause = sql.SQL(", ").join(
            [sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()) for k in columns]
        )
        condition_clause = sql.SQL(" AND ").join(
            [sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()) for k in conditions]
        )
        update_query = sql.SQL("UPDATE {table} SET {set_clause} WHERE {condition_clause}").format(
            table=sql.Identifier(table),
            set_clause=set_clause,
            condition_clause=condition_clause
        )
        self.execute_query(update_query, values + list(conditions.values()))

    def delete(self, table, conditions):
        """Delete data from a table based on conditions."""
        condition_clause = sql.SQL(" AND ").join(
            [sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()) for k in conditions]
        )
        delete_query = sql.SQL("DELETE FROM {table} WHERE {condition_clause}").format(
            table=sql.Identifier(table),
            condition_clause=condition_clause
        )
        self.execute_query(delete_query, list(conditions.values()))

    def select(self, table, columns="*", conditions=None):
        """Select data from a table with optional conditions."""
        columns_clause = sql.SQL(", ").join([sql.Identifier(c) for c in columns]) if columns != "*" else sql.SQL("*")
        if conditions:
            condition_clause = sql.SQL(" AND ").join(
                [sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()) for k in conditions]
            )
            select_query = sql.SQL("SELECT {columns} FROM {table} WHERE {condition_clause}").format(
                columns=columns_clause,
                table=sql.Identifier(table),
                condition_clause=condition_clause
            )
            values = list(conditions.values())
        else:
            select_query = sql.SQL("SELECT {columns} FROM {table}").format(
                columns=columns_clause,
                table=sql.Identifier(table)
            )
            values = None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(select_query, values)
                results = cursor.fetchall()
                return results
        except Exception as e:
            logging.error(f"Error executing select: {e}")
            return None


class UserTable:
    def __init__(self, db, table_name):
        """
        初始化 UserTable，接受一个 PostgresDB 实例。
        :param db: 已连接的 PostgresDB 实例
        """
        self.db = db
        self.name = table_name

    def insert_user(self, user_item: UserItem):
        """插入一个新用户"""
        query = f"""
            INSERT INTO {self.name} (name, sex, age, pic, pwd, phone, email, rate, create_time, update_time, index, salt)
            VALUES (%(name)s, %(sex)s, %(age)s, %(pic)s, %(pwd)s, %(phone)s, %(email)s, %(rate)s, %(create_time)s, %(update_time)s, %(index)s, %(salt)s)
            RETURNING id;
        """
        user_dict = user_item.to_dict()
        user_id = None
        success = True
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, user_dict)
                user_id = cursor.fetchone()[0]
                self.db.connection.commit()
                logging.info(f'insert user successfully! user id: {user_id}')
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error inserting user: {e}")
            success = False
        return user_id, success

    def update_user(self, user_id: int, updates: dict):
        """更新用户信息"""
        success = True
        set_clause = sql.SQL(", ").join(
            [sql.SQL("{} = %s").format(sql.Identifier(k)) for k in updates.keys()]
        )
        query = sql.SQL("UPDATE {table} SET {set_clause}, update_time = %s WHERE id = %s").format(
            table=self.name,
            set_clause=set_clause
        )
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, list(updates.values()) + [datetime.now(), user_id])
                self.db.connection.commit()
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error updating user: {e}")
            success = False
        finally:
            return success

    def delete_user(self, user_id: int):
        """删除用户"""
        query = f"DELETE FROM {self.name} WHERE id = %s"
        success = True
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, (user_id,))
                self.db.connection.commit()
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error deleting user: {e}")
            success = False
        finally:
            return success

    def get_user_by_id(self, user_id: int) -> UserItem:
        """根据用户 ID 查询用户信息"""
        query = f"SELECT * FROM {self.name} WHERE id = %s"
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute(query, (user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    return UserItem(*user_data)
        except Exception as e:
            logging.error(f"Error fetching user: {e}")
        return None
    
    def get_user_by_email(self, email: str) -> UserItem:
        """根据邮箱获取用户信息"""
        query = f"SELECT * FROM {self.name} WHERE email = %s"
        with self.db.connection.cursor() as cursor:
            cursor.execute(query, (email,))
            user_data = cursor.fetchone()
            if user_data:
                # 将查询结果转化为 UserItem 对象
                return UserItem(
                    id=user_data[0],
                    name=user_data[1],
                    sex=user_data[2],
                    age=user_data[3],
                    pic=user_data[4],
                    pwd=user_data[5],
                    phone=user_data[6],
                    email=user_data[7],
                    rate=user_data[8],
                    create_time=user_data[9],
                    update_time=user_data[10],
                    index=user_data[11],
                    salt=user_data[12]
                )
            return None  # 如果未找到用户，返回 None
    
    def count_all_users(self) -> int:
        """统计所有用户的数量"""
        query = f"SELECT COUNT(*) FROM {self.name}"
        with self.db.connection.cursor() as cursor:
            cursor.execute(query)
            user_count = cursor.fetchone()[0]
            return user_count
