from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Category, SubCategory
import asyncio
from .base import async_session_maker

CATEGORIES = [

    {
        "id": 1,
        "name": "⚙️ Низкоуровневое", 
        "desc": "Работа с памятью, железками, байт-кодом и системными интерфейсами", 
        "sub_categories": [
            {"id": 101, "name": "💻 ОС и Ядра", "desc": "Самописные операционные системы, ядра, модули и экспериментальные ОС"},
            {"id": 102, "name": "🔤 Языки (ЯП)", "desc": "Компиляторы, трансляторы, интерпретаторы, парсеры AST и виртуальные машины ЯП"},
            {"id": 103, "name": "🔌 Драйверы", "desc": "Модули для работы с оборудованием, контроллерами и периферией"},
            {"id": 104, "name": "🕹 Эмуляторы и ВМ", "desc": "Эмуляторы процессоров, старых ПК, чипов или изолированные среды исполнения"}
    ]},

    {
        "id": 2,
        "name": "🔌 Сети",
        "desc": "Сетевые технологии, протоколы, туннелирование, P2P и инструменты мониторинга",
        "sub_categories": [
            {"id": 201, "name": "🔗 Протоколы & RPC", "desc": "Реализации сетевых протоколов (TCP/UDP, HTTP, gRPC) и кастомные RPC-системы"},
            {"id": 202, "name": "⚡️ Сокеты и Туннели", "desc": "Сокет-сервисы, прокси-серверы, VPN-решения и инструменты туннелирования трафика"},
            {"id": 203, "name": "📡 P2P и Mesh", "desc": "Одноранговые (P2P) сети, BitTorrent-клиенты, DHT-таблицы и децентрализованные сети"},
            {"id": 204, "name": "🔍 Сетевые утилиты", "desc": "Сканеры портов, снифферы пакетов, пингеры, трассировщики и инструменты мониторинга сети"}
    ]},

    {
        "id": 3,
        "name": "🌐 Веб и Бэкенд", "desc": "Серверная логика, хранение данных и веб-сервисы", "sub_categories": [
            {"id": 301, "name": "⚙️ Бэкенд", "desc": "Микросервисы, монолиты, веб-серверы и кастомные бэкенд-фреймворки"},
            {"id": 302, "name": "🔗 API", "desc": "Реализации REST/gRPC/GraphQL"},
            {"id": 303, "name": "🕷 Парсеры", "desc": "Скраперы, боты для сбора данных, обработчики трафика и extraction-тулзы"},
            {"id": 304, "name": "🗄 Базы данных", "desc": "Кастомные СУБД, In-memory хранилища, кеши и индексные движки"},
            {"id": 305, "name": "⛓ Web3 & Crypto", "desc": "Смарт-контракты, децентрализованные сервисы, блокчейн-ноды и крипто-утилиты"}
    ]},

    {
        "id": 4,
        "name": "🤖 ИИ и Данные", "desc": "Нейросети, математические модели, анализ данных и автоматизация мышления", "sub_categories": [
            {"id": 401, "name": "🧠 ML & Нейросети", "desc": "Самописные архитектуры, алгоритмы машинного обучения и оптимизация моделей"},
            {"id": 402, "name": "💬 LLM & Агенты", "desc": "RAG-системы, обвязки для языковых моделей, автономные агенты и промпт-тулзы"},
            {"id": 403, "name": "📊 Анализ данных", "desc": "Пайплайны обработки данных, визуализация, математические расчеты"},
            {"id": 404, "name": "👁 Computer Vision", "desc": "Распознавание образов, трекинг объектов, видеоаналитика и обработка фото"},
    ]},

    {
        "id": 5,
        "name": "💻 Приложения и UI", "desc": "Визуальные приложения, UI-фреймворки, графика и всё, с чем пользователь взаимодействует напрямую", "sub_categories": [
            {"id": 501, "name": "🖥 Desktop софт", "desc": "Нативные и кроссплатформенные десктопные программы (Qt, Electron, Tauri и др.)"},
            {"id": 502, "name": "📱 Мобилки", "desc": "Нативные и кроссплатформенные мобильные приложения (Flutter, React Native, Swift, Kotlin)"},
            {"id": 503, "name": "🎮 Игры", "desc": "Полноценные игры, пет-проекты, игровые демо или прототипы на любых движках (Unity, Unreal, Godot) или на чистом коде"},
            {"id": 504, "name": "🎨 Графика", "desc": "Инструменты для работы с изображениями, текстом, видео, звуком и нестандартным визуалом (включая ASCII, рейтрейсинг и обработку пикселей)"},
            {"id": 505, "name": "🏞 Фронтенд & UI", "desc": "UI-библиотеки, компонентные системы, оригинальные сайты и веб-интерфейсы"},
    ]},

    {
        "id": 6,
        "name": "🤖 Автоматизация", "desc": "Боты, скрипты автоматизации рутины и инструменты сборки/деплоя", "sub_categories": [
            {"id": 601, "name": "🤖 Боты", "desc": "Боты для мессенджеров или любых других сервисов: админки, сервисы, полезные инструменты или игры внутри мессенджера"},
            {"id": 602, "name": "🚀 DevOps & CI/CD", "desc": "Скрипты деплоя, инфраструктурные тулзы, кастомные Docker-образы и мониторинг"},
            {"id": 603, "name": "⚡️ Скрипты", "desc": "Автоматизаторы задач, макросы, кликеры и скрипты для рутинных процессов"},
    ]},

    {
        "id": 7,
        "name": "🔒 Безопасность", "desc": "Инструменты аудита, шифрования, защиты данных и исследования уязвимостей", "sub_categories": [
            {"id": 701, "name": "🔐 Криптография", "desc": "Реализации шифров, хэш-функций, протоколов приватности, генераторов ключей, а также библиотек для защиты информации"},
            {"id": 702, "name": "🛡 Пентест & Аудит", "desc": "Сканеры уязвимостей, снифферы трафика, анализаторы кода и эксплойты"},
            {"id": 703, "name": "🧱 Файрволы & Защита", "desc": "Песочницы, файрволы, WAF и утилиты защиты от атак"},
    ]},

    {
        "id": 8,
        "name": "🛠 Разработка",
        "desc": "IDE, текстовые редакторы, компиляторы, системы контроля версий и тулзы для разработчиков",
        "sub_categories": [
            {"id": 801, "name": "💻 IDE и Редакторы", "desc": "Среды разработки, кастомные текстовые редакторы (включая ASCII/граф-редакторы) и IDE"},
            {"id": 802, "name": "⚙️ Сборка и Линтеры", "desc": "Системы сборки, линтеры, статические анализаторы кода, форматтеры и компиляторы общего назначения"},
            {"id": 803, "name": "📦 VCS и Пакеты", "desc": "Менеджеры пакетов, системы контроля версий, утилиты для работы с репозиториями и зависимостями"},
            {"id": 804, "name": "🐚 Шеллы и Терминалы", "desc": "Кастомные командные оболочки (shells), эмуляторы терминала и оконные утилиты для кодинга"}
        ]
    },

    # {"name": "", "desc": "", "sub_categories": [
    #     {"name": "", "desc": ""},
    #     {"name": "", "desc": ""},
    #     {"name": "", "desc": ""},
    # ]},

    # {"name": "", "desc": "", "sub_categories": [
    #     {"name": "", "desc": ""},
    #     {"name": "", "desc": ""},
    #     {"name": "", "desc": ""},
    # ]},

]

# ... твой словарь CATEGORIES остается здесь без изменений ...

async def sync_categories(session: AsyncSession) -> None:
    """Синхронизирует категории и подкатегории из словаря с базой: создает, обновляет и удаляет лишнее."""
    print("🔄 Синхронизация категорий с базой данных...")

    # 1. Собираем все ID категорий и подкатегорий, которые актуальны в коде (словаре)
    valid_category_ids = {cat["id"] for cat in CATEGORIES}
    valid_subcategory_ids = {sub["id"] for cat in CATEGORIES for sub in cat["sub_categories"]}

    # 2. Обрабатываем добавление и обновление существующих категорий
    for cat_data in CATEGORIES:
        category = await session.get(Category, cat_data["id"])
        
        if not category:
            category = Category(id=cat_data["id"], name=cat_data["name"], desc=cat_data["desc"])
            session.add(category)
        else:
            category.name = cat_data["name"]
            category.desc = cat_data["desc"]

        for sub_data in cat_data["sub_categories"]:
            sub_category = await session.get(SubCategory, sub_data["id"])
            
            if not sub_category:
                sub_category = SubCategory(
                    id=sub_data["id"],
                    name=sub_data["name"],
                    desc=sub_data["desc"],
                    category_id=cat_data["id"]
                )
                session.add(sub_category)
            else:
                sub_category.name = sub_data["name"]
                sub_category.desc = sub_data["desc"]
                sub_category.category_id = cat_data["id"]

    # 3. Удаляем подкатегории, которых больше нет в словаре
    all_subcategories = await session.execute(select(SubCategory))
    for sub in all_subcategories.scalars().all():
        if sub.id not in valid_subcategory_ids:
            print(f"🗑 Удалена устаревшая подкатегория: {sub.name} (ID: {sub.id})")
            await session.delete(sub)

    # 4. Удаляем категории, которых больше нет в словаре
    all_categories = await session.execute(select(Category))
    for cat in all_categories.scalars().all():
        if cat.id not in valid_category_ids:
            print(f"🗑 Удалена устаревшая категория: {cat.name} (ID: {cat.id})")
            await session.delete(cat)

    await session.commit()
    print("✅ Синхронизация завершена успешно!")


async def main():

    async with async_session_maker() as session:
        await sync_categories(session)


if __name__ == "__main__":
    asyncio.run(main())
