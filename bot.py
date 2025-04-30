import logging
import random
import uuid
from typing import Dict, List, Set, Optional
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, BaseFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, ADMIN_IDS, LOG_LEVEL, LOG_FILE

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    filename=LOG_FILE
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Фильтр для проверки админа
class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMIN_IDS

# Состояния FSM
class UserState(StatesGroup):
    main_menu = State()
    catalog = State()
    packages = State()
    individual_selection = State()
    payment = State()
    admin_menu = State()
    add_service = State()
    edit_service = State()
    delete_service = State()
    confirm_payment = State()

# Структуры данных
class Service:
    def __init__(self, id: int, name: str, description: str, price: int, category: str):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category

class Order:
    def __init__(self, order_id: str, user_id: int, services: List[int], total_price: int, status: str = "pending"):
        self.order_id = order_id
        self.user_id = user_id
        self.services = services
        self.total_price = total_price
        self.status = status
        self.created_at = datetime.now()

# Глобальные переменные для хранения данных
SERVICES: Dict[int, Service] = {}
ORDERS: Dict[str, Order] = {}

# Данные услуг (пример)
SERVICES = {
    1: Service(1, "Разработка сайта", "Создание современного адаптивного сайта", 5000, "development"),
    2: Service(2, "SEO-оптимизация", "Продвижение сайта в поисковых системах", 3000, "marketing"),
    3: Service(3, "Контент-маркетинг", "Создание и продвижение контента", 2500, "marketing"),
    4: Service(4, "SMM-продвижение", "Продвижение в социальных сетях", 4000, "marketing"),
    5: Service(5, "Email-маркетинг", "Настройка email-рассылок", 2000, "marketing"),
    6: Service(6, "UX/UI дизайн", "Создание дизайна интерфейсов", 4500, "design"),
    7: Service(7, "Разработка мобильного приложения", "Создание iOS/Android приложений", 6000, "development"),
    8: Service(8, "Аналитика и отчетность", "Настройка систем аналитики", 3500, "analytics"),
    9: Service(9, "Копирайтинг", "Написание продающих текстов", 1500, "content"),
    10: Service(10, "Техническая поддержка", "Поддержка и обслуживание", 2000, "support")
}

# Создание клавиатуры главного меню
def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📋 Каталог услуг")],
        [KeyboardButton(text="📦 Тарифные пакеты")],
        [KeyboardButton(text="🎯 Индивидуальный подбор")],
        [KeyboardButton(text="ℹ️ Информация")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Создание инлайн-клавиатуры для выбора услуг
def get_services_keyboard(selected_services: Set[int]) -> InlineKeyboardMarkup:
    keyboard = []
    for service_id, service in SERVICES.items():
        checkbox = "✅" if service_id in selected_services else "⬜"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{checkbox} {service['name']} - {service['price']}₽",
                callback_data=f"service_{service_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Создание клавиатуры админ-панели
def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📋 Управление услугами", callback_data="admin_services")],
        [InlineKeyboardButton(text="📦 Управление пакетами", callback_data="admin_packages")],
        [InlineKeyboardButton(text="💰 Заказы и оплаты", callback_data="admin_orders")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Создание клавиатуры управления услугами
def get_services_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить услугу", callback_data="add_service")],
        [InlineKeyboardButton(text="✏️ Редактировать услугу", callback_data="edit_service")],
        [InlineKeyboardButton(text="❌ Удалить услугу", callback_data="delete_service")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Создание клавиатуры для подтверждения оплаты
def get_payment_confirmation_keyboard(order_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm_{order_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{order_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(UserState.main_menu)
    await message.answer(
        "👋 Добро пожаловать в бота!\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=get_main_keyboard()
    )

@dp.message(UserState.main_menu)
async def handle_main_menu(message: types.Message, state: FSMContext):
    if message.text == "📋 Каталог услуг":
        await show_catalog(message)
    elif message.text == "📦 Тарифные пакеты":
        await show_packages(message)
    elif message.text == "🎯 Индивидуальный подбор":
        await state.set_state(UserState.individual_selection)
        await state.update_data(selected_services=set())
        await show_individual_selection(message)
    elif message.text == "ℹ️ Информация":
        await show_info(message)

async def show_catalog(message: types.Message):
    catalog_text = "📋 *Каталог услуг*\n\n"
    for service_id, service in SERVICES.items():
        catalog_text += f"*{service['name']}*\n"
        catalog_text += f"Описание: {service['description']}\n"
        catalog_text += f"Цена: {service['price']}₽\n\n"
    await message.answer(catalog_text, parse_mode="Markdown")

async def show_packages(message: types.Message):
    packages_text = "📦 *Тарифные пакеты*\n\n"
    
    # Базовый пакет
    base_services = list(SERVICES.items())[:3]
    base_price = sum(service['price'] for _, service in base_services)
    base_discount = base_price * 0.1
    packages_text += f"*Базовый пакет*\n"
    packages_text += f"Включенные услуги: {', '.join(service['name'] for _, service in base_services)}\n"
    packages_text += f"Общая стоимость: {base_price}₽\n"
    packages_text += f"Цена со скидкой: {base_price - base_discount}₽\n"
    packages_text += f"Экономия: {base_discount}₽\n\n"
    
    # Стандарт пакет
    standard_services = list(SERVICES.items())[3:7]
    standard_price = sum(service['price'] for _, service in standard_services)
    standard_discount = standard_price * 0.15
    packages_text += f"*Стандарт пакет*\n"
    packages_text += f"Включенные услуги: {', '.join(service['name'] for _, service in standard_services)}\n"
    packages_text += f"Общая стоимость: {standard_price}₽\n"
    packages_text += f"Цена со скидкой: {standard_price - standard_discount}₽\n"
    packages_text += f"Экономия: {standard_discount}₽\n\n"
    
    # Премиум пакет
    premium_services = list(SERVICES.items())[7:10]
    premium_price = sum(service['price'] for _, service in premium_services)
    premium_discount = premium_price * 0.2
    packages_text += f"*Премиум пакет*\n"
    packages_text += f"Включенные услуги: {', '.join(service['name'] for _, service in premium_services)}\n"
    packages_text += f"Общая стоимость: {premium_price}₽\n"
    packages_text += f"Цена со скидкой: {premium_price - premium_discount}₽\n"
    packages_text += f"Экономия: {premium_discount}₽\n\n"
    
    # Полный пакет
    full_price = sum(service['price'] for _, service in SERVICES.items())
    full_discount = full_price * 0.25
    packages_text += f"*Полный пакет*\n"
    packages_text += f"Включенные услуги: Все услуги\n"
    packages_text += f"Общая стоимость: {full_price}₽\n"
    packages_text += f"Цена со скидкой: {full_price - full_discount}₽\n"
    packages_text += f"Экономия: {full_discount}₽"
    
    await message.answer(packages_text, parse_mode="Markdown")

async def show_individual_selection(message: types.Message):
    await message.answer(
        "🎯 *Выберите нужные вам услуги:*\n\n"
        "Нажмите на услугу, чтобы добавить/убрать её из выбора.\n"
        "После выбора нажмите 'Назад' для расчета стоимости.",
        reply_markup=get_services_keyboard(set()),
        parse_mode="Markdown"
    )

@dp.callback_query(UserState.individual_selection)
async def handle_service_selection(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "back_to_main":
        data = await state.get_data()
        selected_services = data.get("selected_services", set())
        
        if selected_services:
            total_price = sum(SERVICES[service_id].price for service_id in selected_services)
            discount = total_price * 0.05 if len(selected_services) >= 3 else 0
            final_price = total_price - discount
            
            order_id = str(uuid.uuid4())[:8]
            ORDERS[order_id] = Order(order_id, callback.from_user.id, list(selected_services), final_price)
            
            result_text = "🎯 *Ваш индивидуальный пакет*\n\n"
            result_text += f"Выбранные услуги:\n"
            for service_id in selected_services:
                service = SERVICES[service_id]
                result_text += f"• {service.name} - {service.price}₽\n"
            result_text += f"\nОбщая стоимость: {total_price}₽\n"
            result_text += f"Ваша скидка: {discount}₽\n"
            result_text += f"Итоговая цена: {final_price}₽\n\n"
            result_text += f"ID заказа: {order_id}"
            
            keyboard = [[InlineKeyboardButton(text="💳 Оплатить", callback_data=f"pay_{order_id}")]]
            await callback.message.answer(
                result_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
        
        await state.set_state(UserState.main_menu)
        await callback.message.answer(
            "Выберите интересующий вас раздел:",
            reply_markup=get_main_keyboard()
        )
    elif callback.data.startswith("service_"):
        service_id = int(callback.data.split("_")[1])
        data = await state.get_data()
        selected_services = data.get("selected_services", set())
        
        if service_id in selected_services:
            selected_services.remove(service_id)
        else:
            selected_services.add(service_id)
        
        await state.update_data(selected_services=selected_services)
        await callback.message.edit_reply_markup(
            reply_markup=get_services_keyboard(selected_services)
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def handle_payment(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    order = ORDERS.get(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    payment_text = "💳 *Оплата заказа*\n\n"
    payment_text += f"ID заказа: {order_id}\n"
    payment_text += f"Сумма к оплате: {order.total_price}₽\n\n"
    payment_text += "*Реквизиты для оплаты:*\n"
    payment_text += "Банковская карта: 1234 5678 9012 3456\n"
    payment_text += "Криптовалюта: BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n\n"
    payment_text += "После оплаты отправьте скриншот чека администратору"
    
    await callback.message.edit_text(payment_text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def handle_payment_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔️ У вас нет прав для подтверждения оплаты")
        return
    
    order_id = callback.data.split("_")[1]
    order = ORDERS.get(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден")
        return
    
    order.status = "completed"
    await bot.send_message(
        order.user_id,
        f"✅ *Оплата подтверждена*\n\n"
        f"Ваш заказ #{order_id} успешно оплачен!\n"
        f"Спасибо за покупку!",
        parse_mode="Markdown"
    )
    
    await callback.message.edit_text(
        f"✅ Оплата заказа #{order_id} подтверждена",
        reply_markup=None
    )
    await callback.answer()

async def show_info(message: types.Message):
    await message.answer(
        "ℹ️ *Информация о боте*\n\n"
        "Версия: 1.0\n"
        "Разработчик: @your_username\n"
        "Описание: Многофункциональный бот с каталогом услуг и тарифными пакетами",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ У вас нет доступа к админ-панели")
        return
    
    await state.set_state(UserState.admin_menu)
    await message.answer(
        "👑 *Админ-панель*\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(UserState.admin_menu)
async def handle_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "admin_services":
        await callback.message.edit_text(
            "📋 *Управление услугами*\n\n"
            "Выберите действие:",
            reply_markup=get_services_management_keyboard(),
            parse_mode="Markdown"
        )
    elif callback.data == "admin_orders":
        orders_text = "💰 *Список заказов*\n\n"
        for order_id, order in ORDERS.items():
            orders_text += f"*Заказ #{order_id}*\n"
            orders_text += f"Пользователь: {order.user_id}\n"
            orders_text += f"Сумма: {order.total_price}₽\n"
            orders_text += f"Статус: {order.status}\n"
            orders_text += f"Дата: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await callback.message.edit_text(orders_text, parse_mode="Markdown")
    elif callback.data == "admin_back":
        await state.set_state(UserState.main_menu)
        await callback.message.edit_text(
            "Выберите интересующий вас раздел:",
            reply_markup=get_main_keyboard()
        )

@dp.callback_query(F.data == "add_service")
async def start_add_service(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserState.add_service)
    await callback.message.edit_text(
        "➕ *Добавление новой услуги*\n\n"
        "Отправьте данные услуги в формате:\n"
        "Название\n"
        "Описание\n"
        "Цена\n"
        "Категория\n\n"
        "Пример:\n"
        "Разработка сайта\n"
        "Создание современного адаптивного сайта\n"
        "5000\n"
        "development",
        parse_mode="Markdown"
    )

@dp.message(UserState.add_service)
async def add_service(message: types.Message, state: FSMContext):
    try:
        name, description, price_str, category = message.text.split('\n')
        price = int(price_str)
        
        if price <= 0:
            raise ValueError("Цена должна быть положительным числом")
        
        service_id = max(SERVICES.keys()) + 1 if SERVICES else 1
        SERVICES[service_id] = Service(service_id, name, description, price, category)
        
        await message.answer(
            f"✅ *Услуга успешно добавлена*\n\n"
            f"ID: {service_id}\n"
            f"Название: {name}\n"
            f"Цена: {price}₽",
            parse_mode="Markdown"
        )
        await state.set_state(UserState.admin_menu)
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}\nПопробуйте еще раз")
    except Exception as e:
        await message.answer("❌ Ошибка при добавлении услуги. Проверьте формат данных")

@dp.callback_query(F.data == "edit_service")
async def start_edit_service(callback: types.CallbackQuery, state: FSMContext):
    services_text = "✏️ *Выберите услугу для редактирования*\n\n"
    keyboard = []
    
    for service_id, service in SERVICES.items():
        services_text += f"{service_id}. {service.name} - {service.price}₽\n"
        keyboard.append([InlineKeyboardButton(
            text=f"{service_id}. {service.name}",
            callback_data=f"edit_{service_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(
        services_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("edit_"))
async def edit_service(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    service = SERVICES.get(service_id)
    
    if not service:
        await callback.answer("❌ Услуга не найдена")
        return
    
    await state.set_state(UserState.edit_service)
    await state.update_data(editing_service_id=service_id)
    
    await callback.message.edit_text(
        f"✏️ *Редактирование услуги #{service_id}*\n\n"
        f"Текущие данные:\n"
        f"Название: {service.name}\n"
        f"Описание: {service.description}\n"
        f"Цена: {service.price}₽\n"
        f"Категория: {service.category}\n\n"
        f"Отправьте новые данные в том же формате:",
        parse_mode="Markdown"
    )

@dp.message(UserState.edit_service)
async def save_edited_service(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        service_id = data.get("editing_service_id")
        
        if not service_id:
            raise ValueError("ID услуги не найден")
        
        name, description, price_str, category = message.text.split('\n')
        price = int(price_str)
        
        if price <= 0:
            raise ValueError("Цена должна быть положительным числом")
        
        SERVICES[service_id] = Service(service_id, name, description, price, category)
        
        await message.answer(
            f"✅ *Услуга успешно обновлена*\n\n"
            f"ID: {service_id}\n"
            f"Название: {name}\n"
            f"Цена: {price}₽",
            parse_mode="Markdown"
        )
        await state.set_state(UserState.admin_menu)
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}\nПопробуйте еще раз")
    except Exception as e:
        await message.answer("❌ Ошибка при редактировании услуги. Проверьте формат данных")

@dp.callback_query(F.data == "delete_service")
async def start_delete_service(callback: types.CallbackQuery, state: FSMContext):
    services_text = "❌ *Выберите услугу для удаления*\n\n"
    keyboard = []
    
    for service_id, service in SERVICES.items():
        services_text += f"{service_id}. {service.name} - {service.price}₽\n"
        keyboard.append([InlineKeyboardButton(
            text=f"{service_id}. {service.name}",
            callback_data=f"delete_{service_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await callback.message.edit_text(
        services_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("delete_"))
async def delete_service(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    service = SERVICES.get(service_id)
    
    if not service:
        await callback.answer("❌ Услуга не найдена")
        return
    
    del SERVICES[service_id]
    await callback.message.edit_text(
        f"✅ Услуга '{service.name}' успешно удалена",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ])
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 