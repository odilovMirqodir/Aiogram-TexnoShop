import asyncio

import asyncpg
import logging
from config.config import *
from asyncpg.pool import Pool
from typing import Union
from asyncpg import Connection


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None
        print(self.pool)

    async def connect(self, use_pool: bool = False):
        try:
            if use_pool:
                await self.create_db_pool()
            else:
                self.pool = None
        except Exception as e:
            pass

    async def create_db_pool(self):
        try:
            if self.pool is None or self.pool._closed:
                self.pool = await asyncpg.create_pool(
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST
                )
        except Exception as e:
            pass
        raise Exception('xatolik')

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False,
                      commit: bool = False):
        await self.connect(use_pool=True)

        if self.pool is None or self.pool._closed:
            return None

        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
                elif commit:
                    result = await connection.execute(command, *args)
            return result

    async def create_users_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        user_full_name VARCHAR(50),
        phone_number VARCHAR(18),
        birth_date VARCHAR(18),
        language VARCHAR(15)
        )
        """
        await self.execute(sql, commit=True)

    async def insert_telegram_id(self, telegram_id):
        sql = """INSERT INTO users(telegram_id) VALUES($1) ON CONFLICT DO NOTHING"""
        await self.execute(sql, telegram_id, commit=True)

    async def update_lang(self, lang, chat_id):
        sql = """UPDATE users SET language = $1 WHERE telegram_id = $2"""
        await self.execute(sql, lang, chat_id, commit=True)

    async def select_language(self, telegram_id):
        sql = """SELECT language FROM users WHERE telegram_id = $1"""
        result = await self.execute(sql, telegram_id, fetchval=True)
        return result

    async def check_user_for_registration(self, user_id):
        sql = """SELECT user_full_name, phone_number, birth_date FROM users WHERE telegram_id = $1"""
        result = await self.execute(sql, user_id, fetchrow=True)

        if result:
            user_full_name, phone_number, birth_date = result

            all_information = {
                'user_full_name': user_full_name,
                'phone_number': phone_number,
                'birth_date': birth_date
            }
            return all_information
        else:
            return None

    async def all_info_save_users(self, username, user_phone_number, user_birth, user_id):
        sql = """UPDATE users SET user_full_name = $1,phone_number = $2,birth_date = $3 WHERE telegram_id = $4"""
        await self.execute(sql, username, user_phone_number, user_birth, user_id, execute=True)

    async def create_table_categories(self):
        sql = """CREATE TABLE IF NOT EXISTS categories(
            category_id serial PRIMARY KEY,
            category_name VARCHAR(30) UNIQUE
        )"""
        await self.execute(sql, execute=True)

    async def create_table_products(self):
        sql = """CREATE TABLE IF NOT EXISTS products(
            product_id serial PRIMARY KEY,
            product_name VARCHAR(200) UNIQUE,
            product_link TEXT,
            product_price INTEGER,
            product_image TEXT,
            category_id INTEGER REFERENCES categories(category_id)
        )"""
        await self.execute(sql, execute=True)

    async def insert_categories(self, category_name):
        sql = '''INSERT INTO categories(category_name) VALUES ($1) ON CONFLICT DO NOTHING'''
        await self.execute(sql, category_name, execute=True)

    async def insert_products(self, product_name, product_link, product_price, product_image, category_id):
        sql = """INSERT INTO products(product_name, product_link, product_price, product_image, category_id)
        VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING"""
        await self.execute(sql, product_name, product_link, product_price, product_image, category_id, execute=True)

    async def select_category_by_cat_name(self, category_name):
        sql = '''SELECT category_id FROM categories WHERE category_name = $1'''
        return await self.execute(sql, category_name, fetchval=True)

    async def select_all_categories(self):
        sql = """SELECT category_name FROM categories"""
        result = await self.execute(sql, fetch=True)
        if result:
            return [row['category_name'] for row in result]
        else:
            return []

    async def select_products_by_pagination(self, category_id, offset, limit):
        """OFFSET productni nechinchisidan olish kerakliligini ko'rsatish"""
        sql = """SELECT product_name,product_id FROM products WHERE category_id = $1 OFFSET $2 LIMIT $3"""
        result = await self.execute(sql, category_id, offset, limit, fetch=True)
        if result:
            return [{"product_name": row['product_name'], "product_id": row['product_id']} for row in result]
        else:
            return []

    async def count_product_by_category_id(self, category_id):
        sql = """SELECT count(product_id) FROM products WHERE category_id = $1"""
        result = await self.execute(sql, category_id, fetchval=True)
        return result

    async def get_product_by_id(self, product_id):
        sql = """SELECT product_name,product_link,product_price,product_image,category_id FROM products WHERE 
        product_id = $1"""
        result = await self.execute(sql, product_id, fetchrow=True)
        return result

    async def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        customer_name TEXT NOT NULL,
        date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
        await self.execute(sql, execute=True)

    async def create_table_order_item(self):
        sql = """
        CREATE TABLE IF NOT EXISTS orderitem(
        id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        product_name TEXT,
        product_quantity INTEGER,
        product_price BIGINT,
        product_total_price BIGINT,
        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE
        )
        """
        await self.execute(sql, execute=True)

    async def insert_orders(self, customer_name):
        sql = "INSERT INTO orders(customer_name) VALUES($1) RETURNING id"
        try:
            result = await self.execute(sql, customer_name, execute=True, fetchrow=True)
            if result:
                logging.info(f"Buyurtma mijoz uchun muvaffaqiyatli kiritildi{customer_name}")
                return result
            else:
                logging.warning(f"Mijoz uchun buyurtma kiritilmadi {customer_name}: Result is None")
                return None
        except Exception as e:
            logging.error(f"Mijoz uchun buyurtma kiritishda xatolik yuz berdi {customer_name}: {e}")
            return None

    async def insert_order_item(self, product_name, product_quantity, product_price, total_price, order_id):
        sql = """
        INSERT INTO orderitem(product_name, product_quantity, product_price, product_total_price, order_id)
        VALUES($1, $2, $3, $4, $5) RETURNING id
        """

        try:
            result = await self.execute(sql, product_name, product_quantity, product_price, total_price, order_id,
                                        execute=True, fetchval=True)

            if result is not None:
                logging.info(f"Order itemga'{product_name}' buyurtma qoshildi {order_id}")
                return result
            else:
                logging.warning(f"Mahsulot'{product_name}'{order_id}: qoshilmadi")
                return None
        except Exception as e:
            logging.error(f"Insert qilishda xatolik {e}")
            return None
