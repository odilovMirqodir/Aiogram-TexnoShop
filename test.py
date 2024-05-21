import asyncio
from database.database import Database

db = Database()


async def main():
    try:
        await db.connect()

        await db.create_table_categories()
        await db.create_table_products()

        await db.insert_categories('kondicionery-split-sistemy')
        await db.insert_categories('smartfony')
        await db.insert_categories('pylesosy-dlya-doma')
        await db.insert_categories('holodilniki-dvuhkamernye')

    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
