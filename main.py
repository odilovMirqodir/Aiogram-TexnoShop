import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ShippingQuery
from config.config import BOT_TOKEN
from database.database import Database
from buttons.buttons import *
from states.states import Royxat
from Botcommand.command import set_commands
from aiogram.fsm.context import FSMContext
from shipping_data.shipping_product import *
from shipping_data.shipping_detail import *

TOKEN = BOT_TOKEN
dp = Dispatcher()
db = Database()


async def on_startup(dp):
    await db.connect()


async def on_shutdown(dp):
    await db.close()


@dp.message(CommandStart())
async def command_start_handler(message: Message, bot: Bot) -> None:
    await set_commands(bot)
    await db.create_users_table()
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    await db.insert_telegram_id(chat_id)
    await message.answer(f"*Assalomu aleykum {first_name}\nTexno shop botiga xush kelibsiz 😊*", parse_mode='markdown',
                         reply_markup=await languages())


@dp.message(lambda message: message.text == "🇺🇿 Uzbek" or message.text == "🇷🇺 Русский")
async def echo_handler(message: types.Message) -> None:
    chat_id, language = message.chat.id, message.text
    text = "*Quyidagilardan birini tanlang*" if message.text == "🇺🇿 Uzbek" else "*Выберите один из следующих*"
    await db.update_lang(language, chat_id)
    lang = await db.select_language(chat_id)
    await message.answer(text=text, parse_mode='markdown', reply_markup=await main_menu(lang))


@dp.message(lambda message: message.text == "Catalog 🗂")
async def catalog_menu(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    check = await db.check_user_for_registration(chat_id)
    lang = await db.select_language(chat_id)
    if check is not None and None not in check.values():
        categories_list = await db.select_all_categories()
        text = f"*Catalog*"
        markup = await get_categories_button(categories_list, lang, db)
    else:
        if lang == '🇺🇿 Uzbek':
            text = f"*Siz ro'yxatdan o'tmagansiz\nIltimos Ro'yxatdan o'ting*"
            markup = await users_for_registration(lang)
        else:
            text = f"Вы не зарегистрированы\nПожалуйста, зарегистрируйтесь"
            markup = await users_for_registration(lang)
    await message.answer(text=text, reply_markup=markup, parse_mode='markdown')


@dp.message(lambda message: message.text in ['Зарегистрироваться', 'Royxatdan otish'])
async def resgistration_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.select_language(user_id)
    if lang == "🇺🇿 Uzbek":
        text = f"*Ism Familyangizni kiriting:\nNamuna: Aziz Azizov*"
    else:
        text = f"*Введите свое имя и фамилию:\nПример: Азиз Азизов*"
    await message.answer(text, parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Royxat.ism)


@dp.message(Royxat.ism)
async def resgistration_username(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.select_language(user_id)
    if message.text.replace(' ', '').isalpha() and len(message.text.split()) == 2:
        await state.update_data(ism=message.text)
        if lang == "🇺🇿 Uzbek":
            text = f"*Raqamingizni kiriting*"
        else:
            text = f"*Введите свой номер*"
        await message.answer(text, parse_mode='markdown', reply_markup=await send_user_phone(lang))
        await state.set_state(Royxat.phone_number)
    else:
        await message.answer(f"*Kiritilgan ismning uzunligi 3tadan ko'p va so'zlardan iborat bo'lishi kerak!*",
                             parse_mode='markdown')


@dp.message(Royxat.phone_number)
async def user_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.select_language(user_id)
    await state.update_data(phone_number=message.contact.phone_number)
    if lang == "🇺🇿 Uzbek":
        text = f"*Tug'ilgan sana,oy,yilingizni kiriting\n00.00.0000*"
    else:
        text = f"*Введите дату своего рождения, месяц, год\n00.00.0000*"
    await message.answer(text, parse_mode='markdown', reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Royxat.users_birth_date)


@dp.message(Royxat.users_birth_date)
async def user_birth_date(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.select_language(user_id)
    await state.update_data(user_birth_date=message.text)
    if lang == "🇺🇿 Uzbek":
        text = f"*Ro'yxatdan o'tdingiz ✅*"
    else:
        text = f"*Вы зарегистрировались ✅*"
    data = await state.get_data()
    user_name = data.get('ism', {})
    phone_number = data.get('phone_number', {})
    user_birth_dat = data.get('user_birth_date', {})
    await db.all_info_save_users(user_name, phone_number, user_birth_dat, user_id)
    await message.answer(f"{text}", parse_mode='markdown', reply_markup=await main_menu(lang))
    await state.clear()


@dp.callback_query(lambda c: "category|" in c.data)
async def reaction_to_category(call: CallbackQuery):
    chat_id = call.message.chat.id
    category_id = int(call.data.split('|')[1])
    lang = await db.select_language(chat_id)
    if lang == "🇺🇿 Uzbek":
        text = f"*Mahsulotlar*"
    else:
        text = f"*Продукты*"
    await call.message.answer(text, parse_mode='markdown', reply_markup=await get_products_by_pagination(category_id))
    await call.message.delete()


@dp.callback_query(lambda c: "next_page|" in c.data)
async def reaction_to_next_page(call: CallbackQuery):
    chat_id = call.message.chat.id
    category_id = int(call.data.split("|")[1])
    page = None
    elements = call.message.reply_markup.inline_keyboard[-3]
    for element in elements:
        if element.callback_data == "current_page":
            page = int(element.text)
    page += 1
    lang = await db.select_language(chat_id)
    text = f"*Mahsulotlar*" if lang == "🇺🇿 Uzbek" else f"Продукты"
    await call.message.answer(text, parse_mode='markdown',
                              reply_markup=await get_products_by_pagination(category_id, page))
    await call.message.delete()


@dp.callback_query(lambda c: "previous_page" in c.data)
async def reaction_to_previous_page(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    lang = await db.select_language(chat_id)
    category_id = int(call.data.split("|")[1])
    page = None
    elements = call.message.reply_markup.inline_keyboard[-3]
    for element in elements:
        if element.callback_data == "current_page":
            page = int(element.text)
    page -= 1
    text = f"*Mahsulotlar*" if lang == "🇺🇿 Uzbek" else f"Продукты"
    await call.message.answer(text, parse_mode='markdown',
                              reply_markup=await get_products_by_pagination(category_id, page))
    await call.message.delete()


@dp.callback_query(lambda c: "current_page" in c.data)
async def reaction_to_current_page(call: types.CallbackQuery, bot: Bot):
    chat_id = call.message.chat.id
    lang = await db.select_language(chat_id)
    page = 0
    elements = call.message.reply_markup.inline_keyboard[-3]
    for element in elements:
        if element.callback_data == "current_page":
            page = int(element.text)
    lang = await db.select_language(chat_id)
    if lang == "🇺🇿 Uzbek":
        text = f"Siz {page}-sahifadasiz"
    else:
        text = f"Вы находитесь на-{page}"
    await bot.answer_callback_query(call.id, text=text, show_alert=True)


@dp.callback_query(lambda c: "product|" in c.data)
async def reaction_to_product(call: types.CallbackQuery, bot: Bot):
    chat_id = call.message.chat.id
    lang = await db.select_language(chat_id)
    product_id = int(call.data.split("|")[1])
    product = await db.get_product_by_id(product_id)
    title, link, price, image, cat_id = product
    if lang == "🇺🇿 Uzbek":
        await bot.send_photo(chat_id=chat_id, photo=image,
                             caption=f"""{title}\nNarxi: {price} uzs\n<a href="{link}">Batafsil Malumot</a>""",
                             parse_mode='html',
                             reply_markup=await get_product_control_buttons(cat_id, product_id, 1, lang)
                             )
        await call.message.delete()
    else:
        await bot.send_photo(chat_id=chat_id, photo=image,
                             caption=f"""{title}\nЦена: {price} uzs\n<a href="{link}">Узнать больше</a>""",
                             parse_mode='html',
                             reply_markup=await get_product_control_buttons(cat_id, product_id, 1, lang))
        await call.message.delete()


@dp.callback_query(lambda c: c.data in ['minus', 'plus'])
async def reaction_plus_or_minus(call: types.CallbackQuery, bot: Bot):
    quantity = int(call.message.reply_markup.inline_keyboard[0][1].text)
    category_id = call.message.reply_markup.inline_keyboard[2][0].callback_data.split('|')[1]
    product_id = call.message.reply_markup.inline_keyboard[1][0].callback_data.split('|')[1]
    chat_id = call.message.chat.id
    lang = await db.select_language(chat_id)

    if call.data == 'plus':
        quantity += 1
    elif call.data == 'minus':
        if quantity > 1:
            quantity -= 1
    try:
        await bot.edit_message_reply_markup(chat_id, call.message.message_id,
                                            reply_markup=await get_product_control_buttons(category_id, product_id,
                                                                                           quantity, lang))
    except Exception as e:
        pass


@dp.callback_query(lambda call: 'add|' in call.data)
async def process_add_button(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    product_id = int(call.data.split('|')[1])
    product = await db.get_product_by_id(product_id)
    product_name, product_price = product[0], product[2]
    quantity = int(call.message.reply_markup.inline_keyboard[0][1].text)

    data = await state.get_data()
    cart = data.get('cart', {})
    if product_name in cart:
        cart[product_name]['quantity'] += quantity
    else:
        cart[product_name] = {
            'product_id': product_id,
            'price': product_price,
            'quantity': quantity
        }

    await state.update_data(cart=cart)
    await bot.answer_callback_query(call.id, text=f"{product_name} savatga qo'shildi", show_alert=True)


@dp.callback_query(lambda call: 'show_card' in call.data)
async def show_cart_callback(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get('cart', {})

    if not cart:
        await call.answer("Savatingiz bo'sh", show_alert=True)

    total_price = 0
    cart_text = "Savatingizdagi Mahsulotlar\n"

    for product_name, product_info in cart.items():
        product_price = product_info.get('price', {})
        product_quantity = product_info.get('quantity', {})
        product_total_price = product_price * product_quantity

        total_price += product_total_price
        cart_text += f"Mahsulot nomi: {product_name}\nMahsulot soni: {product_quantity}\nMahsulot Narxi: {product_price}\n\n"
    cart_text += f"Jami: {total_price}\n"
    await call.message.answer(cart_text, reply_markup=await show_card_buttons(cart))
    await call.message.delete()


@dp.callback_query(lambda c: c.data.startswith('remove|'))
async def remove_product_from_cart(call: types.CallbackQuery, state: FSMContext):
    product_id = int(call.data.split('|')[1])

    data = await state.get_data()
    cart = data.get('cart', {})

    items_to_remove = []
    for product_name, product_values in cart.items():
        if product_id == product_values.get('product_id'):
            items_to_remove.append(product_name)

    for item in items_to_remove:
        del cart[item]

    await state.update_data(cart=cart)

    total_price = 0
    cart_text = "Savatingizdagi Mahsulotlar\n"

    for product_name, product_info in cart.items():
        product_price = product_info.get('price', {})
        product_quantity = product_info.get('quantity', {})
        product_total_price = product_price * product_quantity

        total_price += product_total_price
        cart_text += f"Mahsulot nomi: {product_name}\nMahsulot soni: {product_quantity}\nMahsulot Narxi: {product_price}\n\n"
    cart_text += f"Jami: {total_price}\n"
    await call.message.answer(cart_text, reply_markup=await show_card_buttons(cart))
    await call.message.delete()


@dp.callback_query(lambda c: c.data == 'clear_data')
async def clear_cart_callback(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    chat_id = call.message.chat.id
    lang = await db.select_language(chat_id)

    data = await state.get_data()
    data['cart'] = {}
    text = f"*Savat tozalandi*" if lang == "🇺🇿 Uzbek" else f"*Корзина очищена*"
    await bot.delete_message(chat_id, call.message.message_id)
    await state.update_data(data=data)
    await call.message.answer(text, reply_markup=await main_menu(lang), parse_mode='markdown')


@dp.callback_query(lambda c: c.data == 'submit')
async def submit_card(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    chat_id = call.message.chat.id
    data = await state.get_data()

    product_instance = await generate_product_invoice(data['cart'])
    product_invoice = product_instance.generate_invoice()

    await bot.send_invoice(chat_id, **product_invoice, payload='shop_bot')


@dp.shipping_query(lambda query: True)
async def choose_shipping(query: types.ShippingQuery, bot: Bot):
    logging.info(query)

    if query.shipping_address.country_code != "UZ":
        await bot.answer_shipping_query(shipping_query_id=query.id, ok=False,
                                        error_message="Yetkazib berish faqatgina O'zbekiston bo'ylab")
    elif query.shipping_address.city.lower() in ['toshken', 'tashkent', 'towken', 'toshkent']:
        options = [EXPRESS_SHIPPING, REGULAR_SHIPPING, PICKUP_SHIPPING]
        await bot.answer_shipping_query(shipping_query_id=query.id, ok=True, shipping_options=options)
        logging.info(options)
    else:
        options = [REGION_SHIPPING]
        await bot.answer_shipping_query(shipping_query_id=query.id, ok=True, shipping_options=options)
        logging.info(options)


@dp.pre_checkout_query(lambda pre_checkout_query: True)
async def check(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext, bot: Bot):
    try:
        await db.create_table()
        await db.create_table_order_item()
        user_id = pre_checkout_query.from_user.id
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True, error_message='TEST')
        await bot.send_message(user_id, text=f"Xaridingiz uchun raxmat")

        data = await state.get_data()
        customer_full_name = await db.check_user_for_registration(user_id)

        if customer_full_name is None:
            logging.warning(f"User information not found for user {user_id}")
            return

        customer_order = await db.insert_orders(customer_full_name.get('user_full_name'))

        if customer_order is not None:
            order_id = customer_order.get('id', {})

            for item in data['cart']:
                product_name = item
                product_quantity = data['cart'][item]['quantity']
                product_price = data['cart'][item]['price']
                total_price = int(product_quantity) * int(product_price)
                result = await db.insert_order_item(product_name, product_quantity, product_price, total_price,
                                                    order_id)

                if result:
                    logging.info(f"Product '{product_name}' Orderga qoshildi {order_id}")
                else:
                    logging.warning(f"productni '{product_name}' order_id boyicha qoshishda xatolik {order_id}")

            await state.clear()
        else:
            logging.warning("Insert Orderni qoshishda xatolik")

    except Exception as e:
        logging.error(f"Boshqa xatolik: {e}")


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)
    await dp.startup(on_startup)
    await dp.shutdown(on_shutdown)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(main())
