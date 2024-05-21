from bs4 import BeautifulSoup
import requests
from main import *
from database.database import *
import aiohttp
import asyncio
from pprint import pprint
from database.database import Database


class OpenShopParser:
    def __init__(self, category):
        if category == 'kondicionery-split-sistemy' or category == 'smartfony' or category == 'pylesosy-dlya-doma' or category == 'holodilniki-dvuhkamernye':
            self.URL = 'https://texnomart.uz/uz/katalog/'

        self.category = category.lower()
        self.product_url = 'https://texnomart.uz'

    async def get_soup(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.URL + self.category) as response:
                    html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except:
            print('404')

    async def get_info(self):
        data = []
        try:
            soup = await self.get_soup()
            box = soup.find('div', class_='products-box')
            products = box.find_all('div', class_='col-3')
            for product in products:
                title = product.find('a', class_='product-name f-14 c-373 mb-1 768:mb-2 btn-link w-normal').get_text(
                    strip=True)
                link = self.product_url + \
                       product.find('a', class_='product-name f-14 c-373 mb-1 768:mb-2 btn-link w-normal')['href']
                price = int(
                    product.find('div', class_='product-price__current').get_text(strip=True).split("so'm")[
                        0].replace(' ', ''))
                cat_id = await db.select_category_by_cat_name(self.category)
                a = product.find('a')
                image = a.find('img')['src']
                data.append({
                    'title': title,
                    'link': link,
                    'price': price,
                    'image': image,
                    'category_id': cat_id

                })
            return data
        except Exception as e:
            print(f"{e}")


async def main():
    from pprint import pprint
    try:
        db = Database()
        await db.connect()
        product_list = await asyncio.gather(
            OpenShopParser('kondicionery-split-sistemy').get_info(),
            OpenShopParser('smartfony').get_info(),
            OpenShopParser('pylesosy-dlya-doma').get_info(),
            OpenShopParser('holodilniki-dvuhkamernye').get_info(),
        )
        for item in product_list:
            for product in item:
                cat_id = product.get('category_id', 'Bunday key mavjud emas')
                name = product.get('title', {})
                price = product['price']
                link = product.get('link', {})
                image = product['image']

                await db.insert_products(name, link, price, image, cat_id)
    finally:
        await db.close()


if __name__ == '__main__':
    asyncio.run(main())
