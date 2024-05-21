from aiogram.types import LabeledPrice, ShippingOption
from .shipping_product import Product


async def generate_product_invoice(product_data):
    query = Product(
        title="Shop bot",
        description='\n'.join(title for title in product_data),
        currency='UZS',
        prices=[LabeledPrice(
            label=f"{product_data[title]['quantity']} ta {title}",
            amount=int(product_data[title]['quantity'] * int(product_data[title]['price']) * 100)
        ) for title in product_data],
        start_parameter='create_invoice_products',
        need_name=True,
        need_phone_number=True,
        is_flexible=True
    )
    return query


EXPRESS_SHIPPING = ShippingOption(
    id="post_express",
    title=f"1 soat ichida yetkazib berish",
    prices=[LabeledPrice(label="1 soat ichida", amount=25000 * 100)]
)

REGULAR_SHIPPING = ShippingOption(
    id="post_regular",
    title=f"1 kun ichida yetkazib berish",
    prices=[LabeledPrice(label="1 kun ichida", amount=5000 * 100)]
)

PICKUP_SHIPPING = ShippingOption(
    id="post_pickup",
    title="Do'kondan olib ketish",
    prices=[LabeledPrice(label="Do'kondan olib ketish", amount=0)]
)
REGION_SHIPPING = ShippingOption(
    id="post_region",
    title=f"O'zbekiston bo'yicha yetkazib berish",
    prices=[LabeledPrice(label="O'zbekiston bo'yicha yetkazib berish", amount=150000 * 100)]
)
