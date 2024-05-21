from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from database.database import Database

db = Database()


async def languages():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇺🇿 Uzbek"),
            ],
            [
                KeyboardButton(text="🇷🇺 Русский"),
            ],
        ],
        resize_keyboard=True
    )
    return keyboard


async def main_menu(lang):
    if lang == "🇺🇿 Uzbek":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Catalog 🗂"),
                    KeyboardButton(text="Sozlamalar ⚙️"),
                ],
                [
                    KeyboardButton(text="Biz bilan boglanish ☎️"),
                ],
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Catalog 🗂"),
                    KeyboardButton(text="Настройки ⚙️"),
                ],
                [
                    KeyboardButton(text="Связаться с нами ☎️"),
                ],
            ],
            resize_keyboard=True
        )
    return keyboard


async def users_for_registration(lang):
    if lang == "🇺🇿 Uzbek":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Royxatdan otish"),
                ],

            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Зарегистрироваться"),
                ],
            ],
            resize_keyboard=True
        )
    return keyboard


async def send_user_phone(lang):
    if lang == "🇺🇿 Uzbek":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Raqam yuborish ☎️", request_contact=True),
                ],

            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Отправить номер ☎️", request_contact=True),
                ],
            ],
            resize_keyboard=True
        )
    return keyboard


async def get_categories_button(category_list, lang, db):
    categories = []
    for item in category_list:
        category_name = item.split()[0]
        cat_id_result = await db.select_category_by_cat_name(category_name)
        cat_id = str(cat_id_result) if cat_id_result else None
        name = ''
        if lang == "🇺🇿 Uzbek":
            if category_name == 'kondicionery-split-sistemy':
                name = 'Konditsionerlar'
            elif category_name == 'smartfony':
                name = 'Telefonlar'
            elif category_name == 'pylesosy-dlya-doma':
                name = 'Chang yutgichlar'
            elif category_name == 'holodilniki-dvuhkamernye':
                name = 'Muzlatgich'
        else:
            if category_name == 'kondicionery-split-sistemy':
                name = 'Кондиционеры'
            elif category_name == 'smartfony':
                name = 'Телефоны'
            elif category_name == 'pylesosy-dlya-doma':
                name = 'Пылесосы'
            elif category_name == 'holodilniki-dvuhkamernye':
                name = 'Холодильники'
        button = InlineKeyboardButton(text=name, callback_data=f"category|{cat_id}")
        categories.append(button)

    inline_keyboard = []
    row = []

    for category_button in categories:
        if len(row) < 2:
            row.append(category_button)
        else:
            inline_keyboard.append(row)
            row = [category_button]
    if row:
        inline_keyboard.append(row)

    if lang == "🇺🇿 Uzbek":
        back_button = InlineKeyboardButton(text='ortga', callback_data='back_1')
        inline_keyboard.append([back_button])
    else:
        back_button = InlineKeyboardButton(text='назад', callback_data='back_1')
        inline_keyboard.append([back_button])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def get_products_by_pagination(category_id, page=1):
    limit = 6
    offset = (page - 1) * limit

    products = await db.select_products_by_pagination(category_id, offset, limit)
    count = await db.count_product_by_category_id(category_id)

    buttons = []
    for product in products:
        buttons.append(
            [InlineKeyboardButton(text=product['product_name'], callback_data=f"product|{product['product_id']}")])
    max_page = count // limit if count % limit == 0 else count // limit + 1
    back = [InlineKeyboardButton(text="⏮", callback_data=f"previous_page|{category_id}")]
    current_page = [InlineKeyboardButton(text=f"{page}", callback_data=f"current_page")]
    next = [InlineKeyboardButton(text="⏭", callback_data=f"next_page|{category_id}")]

    if 1 < page < max_page:
        buttons.append(back + current_page + next)
    elif page == 1:
        buttons.append(current_page + next)
    elif page == max_page:
        buttons.append(back + current_page)

    buttons.extend([
        [InlineKeyboardButton(text="ortga", callback_data="back_1")],
        [InlineKeyboardButton(text="Asosiy saxifa", callback_data="main_menu")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_product_control_buttons(category_id, product_id, quantity, lang):
    quantity_btn = [
        InlineKeyboardButton(text="➖", callback_data='minus'),
        InlineKeyboardButton(text=f"{quantity}", callback_data='quantity'),
        InlineKeyboardButton(text="➕", callback_data='plus'),
    ]

    card = [
        InlineKeyboardButton(text=lang == "🇺🇿 Uzbek" and "Savatga qoshish" or "Добавить в корзину",
                             callback_data=f"add|{product_id}"),
        InlineKeyboardButton(text=lang == "🇺🇿 Uzbek" and "Savat" or "Корзина", callback_data=f"show_card")
    ]

    backs = [
        InlineKeyboardButton(text=lang == "🇺🇿 Uzbek" and "ortga" or "назад",
                             callback_data=f"category|{category_id}"),
        InlineKeyboardButton(text="Catalog", callback_data="back_categories")
    ]
    main_menu = [
        InlineKeyboardButton(text=lang == "🇺🇿 Uzbek" and "Asosiy sahifa" or "Главная страница",
                             callback_data='main_menu')
    ]

    buttons = [quantity_btn, card, backs, main_menu]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_card_buttons(data: dict):
    buttons = []

    for product_name, items in data.items():
        product_id = items.get('product_id', {})
        button = InlineKeyboardButton(text=f"❌ {product_name}", callback_data=f"remove|{product_id}")
        buttons.insert(0, [button])

    markup = InlineKeyboardMarkup(inline_keyboard=[
        *buttons,
        [
            InlineKeyboardButton(text="Catalog", callback_data='back_categories'),
            InlineKeyboardButton(text="Tozalash 🗑", callback_data='clear_data')
        ],
        [
            InlineKeyboardButton(text=f"Buyurtma berish ✅", callback_data='submit')
        ]
    ])
    return markup
