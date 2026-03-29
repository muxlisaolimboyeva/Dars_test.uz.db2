from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    Filters, ConversationHandler, CallbackContext
)
import db

TOKEN = "8537083178:AAFcmImO9_S_ZHe_3eoka2b_yt5H4IvVPTs"
ADMIN_PASSWORD = "123"
ADMIN_IDS = set()

(
    NAME, PHONE, LOCATION, MAIN_MENU,
    EDIT_NAME, EDIT_PHONE, SETTINGS_MENU, FOOD_MENU
) = range(8)

(
    ADD_CATEGORY_NAME, ADD_CATEGORY_EMOJI,
    ADD_PRODUCT_CATEGORY, ADD_PRODUCT_NAME,
    ADD_PRODUCT_PRICE, ADD_PRODUCT_IMAGE,
    ADD_PRODUCT_DESC, ADMIN_MENU
) = range(8, 16)



def start(update: Update, context: CallbackContext):
    user = db.get_user(update.effective_user.id)
    if user:
        return main_menu(update, context)

    update.message.reply_text("👤 Ism va familiyangizni kiriting:")
    return NAME


def get_name(update, context):
    context.user_data["name"] = update.message.text
    update.message.reply_text(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
            resize_keyboard=True
        )
    )
    return PHONE


def get_phone(update, context):
    if not update.message.contact:
        update.message.reply_text("❌ Tugma orqali raqam yuboring")
        return PHONE

    context.user_data["phone"] = update.message.contact.phone_number
    update.message.reply_text(
        "📍 Location yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Location yuborish", request_location=True)]],
            resize_keyboard=True
        )
    )
    return LOCATION


def get_location(update, context):
    if not update.message.location:
        update.message.reply_text("❌ Tugma orqali location yuboring")
        return LOCATION

    loc = update.message.location
    db.add_user(
        update.effective_user.id,
        context.user_data["name"],
        context.user_data["phone"],
        loc.latitude,
        loc.longitude
    )
    update.message.reply_text("✅ Ro‘yxatdan o‘tdingiz!")
    return main_menu(update, context)


def main_menu(update, context):
    update.message.reply_text(
        "🏠 Asosiy menyu:",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["📋 Menyu"],
                ["⚙️ Sozlamalar"]
            ],
            resize_keyboard=True
        )
    )
    return MAIN_MENU


def main_menu_select(update, context):
    if update.message.text == "📋 Menyu":
        return food_menu(update, context)

    if update.message.text == "⚙️ Sozlamalar":
        return settings_menu(update, context)

    return MAIN_MENU


def settings_menu(update, context):
    update.message.reply_text(
        "✏️ Ma'lumotlarni o‘zgartirish:",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["✏️ Ism"],
                ["📞 Telefon"],
                ["⬅️ Orqaga"]
            ],
            resize_keyboard=True
        )
    )
    return SETTINGS_MENU


def setting_select(update, context):
    text = update.message.text

    if text == "✏️ Ism":
        update.message.reply_text("Yangi ismni kiriting:")
        return EDIT_NAME

    if text == "📞 Telefon":
        update.message.reply_text(
            "Yangi telefon yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
                resize_keyboard=True
            )
        )
        return EDIT_PHONE

    return main_menu(update, context)


def edit_name(update, context):
    db.update_name(update.effective_user.id, update.message.text)
    update.message.reply_text("✅ Ism yangilandi")
    return settings_menu(update, context)


def edit_phone(update, context):
    if not update.message.contact:
        update.message.reply_text("❌ Tugma orqali yuboring")
        return EDIT_PHONE

    db.update_phone(update.effective_user.id, update.message.contact.phone_number)
    update.message.reply_text("✅ Telefon yangilandi")
    return settings_menu(update, context)


def food_menu(update, context):
    categories = db.get_categories()
    keyboard = []

    for cat_id, name, emoji in categories:
        key = f"{emoji} {name}"
        keyboard.append([key])
        context.user_data[f"cat_{key}"] = cat_id

    keyboard.append(["⬅️ Orqaga"])

    update.message.reply_text(
        "📋 Kategoriyani tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return FOOD_MENU


def food_menu_select(update, context):
    text = update.message.text

    if text == "⬅️ Orqaga":
        return main_menu(update, context)

    category_id = context.user_data.get(f"cat_{text}")
    if not category_id:
        return FOOD_MENU

    products = db.get_product_by_category(category_id)
    if not products:
        update.message.reply_text("❌ Mahsulot yo‘q")
        return FOOD_MENU

    for name, price, desc, image in products:
        update.message.reply_photo(
            photo=image,
            caption=f"🍽 {name}\n💰 {price} so‘m\n\n📝 {desc}"
        )
    return FOOD_MENU


def admin_login(update, context):
    if not context.args or context.args[0] != ADMIN_PASSWORD:
        update.message.reply_text("❌ /admin parol")
        return ConversationHandler.END

    ADMIN_IDS.add(update.effective_user.id)
    update.message.reply_text(
        "🔐 Admin panel",
        reply_markup=ReplyKeyboardMarkup(
            [["➕ Kategoriya"], ["➕ Mahsulot"]],
            resize_keyboard=True
        )
    )
    return ADMIN_MENU


def admin_menu_select(update, context):
    if update.message.text == "➕ Kategoriya":
        update.message.reply_text("Kategoriya nomi:")
        return ADD_CATEGORY_NAME

    if update.message.text == "➕ Mahsulot":
        categories = db.get_categories()
        keyboard = []

        for cid, name, emoji in categories:
            key = f"{emoji} {name}"
            keyboard.append([key])
            context.user_data[f"admin_cat_{key}"] = cid

        update.message.reply_text(
            "Kategoriya tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return ADD_PRODUCT_CATEGORY

    return ADMIN_MENU


def add_category_name(update, context):
    context.user_data["cat_name"] = update.message.text
    update.message.reply_text("Emoji yuboring:")
    return ADD_CATEGORY_EMOJI


def add_category_emoji(update, context):
    db.add_category(context.user_data["cat_name"], update.message.text)
    update.message.reply_text("✅ Kategoriya qo‘shildi")
    return ADMIN_MENU


def add_product_category(update, context):
    cid = context.user_data.get(f"admin_cat_{update.message.text}")
    if not cid:
        return ADD_PRODUCT_CATEGORY

    context.user_data["prod_cat"] = cid
    update.message.reply_text("Mahsulot nomi:")
    return ADD_PRODUCT_NAME


def add_product_name(update, context):
    context.user_data["prod_name"] = update.message.text
    update.message.reply_text("Narxi:")
    return ADD_PRODUCT_PRICE


def add_product_price(update, context):
    try:
        context.user_data["prod_price"] = int(update.message.text)
    except ValueError:
        update.message.reply_text("❌ Raqam kiriting")
        return ADD_PRODUCT_PRICE

    update.message.reply_text("Rasm yuboring:")
    return ADD_PRODUCT_IMAGE


def add_product_image(update, context):
    context.user_data["prod_img"] = update.message.photo[-1].file_id
    update.message.reply_text("Tavsif:")
    return ADD_PRODUCT_DESC


def add_product_desc(update, context):
    db.add_products(
        context.user_data["prod_cat"],
        context.user_data["prod_name"],
        context.user_data["prod_price"],
        update.message.text,
        context.user_data["prod_img"]
    )
    update.message.reply_text("✅ Mahsulot qo‘shildi")
    return ADMIN_MENU


def main():
    db.create_table()
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("admin", admin_login)
        ],
        states={
            NAME: [MessageHandler(Filters.text, get_name)],
            PHONE: [MessageHandler(Filters.contact, get_phone)],
            LOCATION: [MessageHandler(Filters.location, get_location)],

            MAIN_MENU: [MessageHandler(Filters.text, main_menu_select)],
            SETTINGS_MENU: [MessageHandler(Filters.text, setting_select)],
            EDIT_NAME: [MessageHandler(Filters.text, edit_name)],
            EDIT_PHONE: [MessageHandler(Filters.contact, edit_phone)],

            FOOD_MENU: [MessageHandler(Filters.text, food_menu_select)],

            ADMIN_MENU: [MessageHandler(Filters.text, admin_menu_select)],
            ADD_CATEGORY_NAME: [MessageHandler(Filters.text, add_category_name)],
            ADD_CATEGORY_EMOJI: [MessageHandler(Filters.text, add_category_emoji)],
            ADD_PRODUCT_CATEGORY: [MessageHandler(Filters.text, add_product_category)],
            ADD_PRODUCT_NAME: [MessageHandler(Filters.text, add_product_name)],
            ADD_PRODUCT_PRICE: [MessageHandler(Filters.text, add_product_price)],
            ADD_PRODUCT_IMAGE: [MessageHandler(Filters.photo, add_product_image)],
            ADD_PRODUCT_DESC: [MessageHandler(Filters.text, add_product_desc)],
        },
        fallbacks=[]
    )

    dp.add_handler(conv)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
