# только выбирает проект для батла. ничего не пишет в бд

# должен выбирать по следующим моментам:
# - один чел не должен попадать в батл подряд
# - категория не может идти подряд
# - подкатегории тоже не должны идти подряд

# примерный алгоритм работы
# - v берет все проекты status = READY
# - v смотрит подкатегории в которых есть 3 проекта
# - v исключает подкатегорию которая была в батле прошлый раз
# - v выбирает подкатегорию по порядку
# - v смотрит чтобы подкатегории были равны и участвовали все по ровну
# - смотрит автора проекта, чтобы не было повторов подряд
# - также смотрит, если есть автор который никогда не участвовал, то ему приоритет
# ну либо просто сортирует авторов так чтобы сначала были те кто давно не участвовал

from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models.user import User
from shared.db.models.project import Project
from shared.db.models.battle import Battle

from shared.db.requests.project import get_projects_ready_battle
from shared.db.requests.battle import get_latest_battle, count_battle_projects_by_sub_category, count_user_battle_participations, get_battle_users, count_battle_projects_by_category

from collections import defaultdict


async def select_battle_projects(db_session: AsyncSession) -> list[Project]:
    """ Выбирает и возвращает три проекта для батла. Выбор происходит на основе множества критериев"""

    # НУЖНО РАЗДЕЛИТЬ НА ОТДЕЛЬНЫЕ ФУНКЦИИ, ДЛЯ ОБЛЕГЧЕНИЯ
    # СДЕЛАТЬ ЛОГИРОВАНИЕ КАЖДОГО ШАГА

    # Получаем все проекты только со статусом READY
    all_projects = await get_projects_ready_battle(db_session)

    if not all_projects:
        return []

    # Получаем последний батл
    latest_battle: Battle = await get_latest_battle(db_session)

    # Авторы участвовавшие в прошлом батле
    latest_battle_users: list[User] = await get_battle_users(db_session, latest_battle)
    excluded_users: set[User] = set(latest_battle_users)

    select_projects(db_session, all_projects, latest_battle, excluded_users)


async def select_projects(db_session: AsyncSession, all_projects: list[Project], latest_battle: Battle, excluded_users: set[User], category: bool=False, valid_strictness: int=0):
    """ Функция непосредство выбирает проекты по множеству критериям
        Понимает когда работать с подкатегориями а когда с категориями
    """

    # РЕАЛИЗОВАТЬ потом valid_strictness, Т.Е ТРЕБОВАНИЯ: 1 - без учета повтора категорий, 2 - без учета повтора людей, 3 - и то и то. и кажый раз +1, либо ЛУЧШЕ ПУСКАЙ ТОЛЬКО ВЫЗЫВАЮЩИЙ ЗАДАЕТ

    # Сортируем проекты по категориям
    by_cat: dict[int, list[Project]] = sorted_proj_by_cats(all_projects) if category else sorted_proj_by_subcats(all_projects)

    # Если батл был по подкатегории
    if not category and latest_battle.sub_category_id:

        # Удаляем проекты с этой подкатегорией
        by_cat.pop(latest_battle.sub_category_id, None)

    # Если батл был по категории
    elif category and not latest_battle.sub_category_id:

        # Удаляем проекты с этой категорией
        by_cat.pop(latest_battle.category_id, None)

    # Оставляем только категории где >= 3 проектов
    by_cat_three_more: dict[int, list[Project]] = filter_cats_min_projects(by_cat)

    # Если ни в одной категории нету даже 3 проекта, то
    if not by_cat_three_more:

        if not category:
            # Работаем с категориями
            return await select_projects(db_session, all_projects, latest_battle, excluded_users, True)
        else: 
            return []

    # Получаем сколько каждая категория участвовала раз в батлах
    count_battle_every_cat = await get_cat_battle_count(db_session, by_cat_three_more.keys()) if category else await get_subcat_battle_count(db_session, by_cat_three_more.keys())

    # Сортируем чтобы сначала были категории которые меньше всех участвовали в батлах
    sorted_counts = dict(sorted(count_battle_every_cat.items(), key=lambda item: item[1]))

    # Категории и в каждой авторы проектов, и количество их участия в батлах
    categories_with_authors: dict[int, dict[User, int]] = {}

    # Словарь для поиска проекта по юзеру
    cat_authors_with_projects: dict[int, dict[User, Project]] = {}

    # Пробегаемся по каждой катеории
    for cat_id in sorted_counts:

        # Получаем все проекты только этой категории
        cat_projects = by_cat_three_more[cat_id]

        # Получаем всех авторов проектов
        projects_authors: dict[Project, User] = await get_projects_authors(cat_projects)

        # Удаляем авторов которые участвовали в прошлом батле
        for project in [p for p, u in projects_authors.items() if u in excluded_users]:
            del projects_authors[project]

        # Записываем юзеров с проектами, на будущее, чтобы потом легко найти проект по юзеру
        cat_authors_with_projects[cat_id] = {}
        for proj, user in projects_authors.items():
            cat_authors_with_projects[cat_id][user] = proj

        # Получаем количество участий в батлах всех пользователей
        battle_count: dict[User, int] = await get_users_battle_count(db_session, list(projects_authors.values()))
        
        categories_with_authors[cat_id] = battle_count
    
    # Оставляем в каждой категории только 3 пользователя которые меньше всех участвовали в батлах
    filtered_categories: dict[int, dict[User, int]] = {
        cat_id: dict(sorted(authors.items(), key=lambda item: item[1])[:3])
        for cat_id, authors in categories_with_authors.items()
    }

    # У каждой категории вычисляем среднее число количества участий в батлах
    avg_by_category: dict[int, float] = {
        cat_id: sum(authors.values()) / len(authors)
        for cat_id, authors in filtered_categories.items()
        if authors  
    }

    # Получаем категорию с самым наименьшим числом. Т.е где юзеры меньше всего участвовали в батлах 
    best_cat_id: int | None = min(avg_by_category, key=avg_by_category.get, default=None)
    best_cat_users: dict[User, int] = filtered_categories[best_cat_id]
    best_users: list[User] = list(best_cat_users.keys())
    
    authors_in_best_cat = cat_authors_with_projects.get(best_cat_id, {})

    # Получаем проекты подходящих пользователей
    best_projects: list[Project] = [
        authors_in_best_cat[user]
        for user in best_users
        if user in authors_in_best_cat
    ]

    return best_projects

    # ТУТ ЕЩЕ ПРОБЛЕМА В ТОМ ЧТО НУЖНО ВСЕХ СОБРАТЬ ПОЛЬЗОВАТЕЛЕЙ, ДЛЯ ВСЕХ ПОДКАТЕГОРИЙ
    # А ПОТОМ ЕЩЕ НАДО ИХ МЕЖДУ СОБОЙ ВСЕХ СРАВНИТЬ КАК ТО
    # И КТО МЕНЬШЕ ВСЕГО УЧАСТВОВАЛ, КАКАЯ КАТЕГОРИЯ, ТЕ И УЧАСТВУЮТ В БАТЛЕ
    # > МОЖНО ПРОСТО ДЛЯ КАЖДОЙ КАТЕГОРИИ СРЕДНЕЕ ЗНАЧЕНИЕ. И В КОТОРОЙ МЕНЬШЕ ВСЕГО, ТЕ И УЧАСТВУЮТ
    # !!! ТАКЖЕ НЕ ЗАБУДЬ ЧТО НУЖНО ПРОВЕРЯТЬ, ЧТОБЫ ПОЛЬЗОВАТЕЛЬ ПОВТОРНО НЕ УЧАСТВОВАЛ В БАТЛЕ!!! НУЖНО ТАКИХ УДАЛЯТЬ СРАЗУ, КТО В ПРОШЛОМ УЧАСТВОВАЛ БАТЛЕ
    
    # Также этот алгоритм должен если проектов мало, то брать уже любой: сначала любую категорию, затем он уже должен перестать придераться к пользователям

    # словарь где будет написан юзер и сколько раз он участвовал в батлах: {user123: 4}. и фильтрация по value, у кого меньше тот и в приоритете
    # и это нужно выполнять только для одной подка  тегории
    # то же самое нужно делать с категориями и подкатеориями: сколько раз они участвовали в батлах. и в приоритете те у кого меньше количество участий, чтоб все участвоавали крч. сначала по подкатегориям потом уже по юзерам



async def get_users_battle_count(db_session, users: list[User]) -> dict[User, int]:
    result: dict[User, int] = {}

    for user in users:
        result[user] = await count_user_battle_participations(db_session, user)
    
    return result


async def get_projects_authors(projects: list[Project]) -> dict[Project, User]:
    result: dict[Project, User] = {}
    for proj in projects:
        result[proj] = proj.user
    return result


async def get_subcat_battle_count(db_session, sub_categories: list[int]) -> dict[int, int]:

    result: dict[int, int] = {}

    for scat_id in sub_categories:
        result[scat_id] = await count_battle_projects_by_sub_category(db_session, scat_id)

    return result


async def get_cat_battle_count(db_session, categories: list[int]) -> dict[int, int]:

    result: dict[int, int] = {}

    for cat_id in categories:
        result[cat_id] = await count_battle_projects_by_category(db_session, cat_id)

    return result


def sorted_proj_by_subcats(projects: list[Project]) -> dict[int, list[Project]]:

    result: dict[int, list[Project]] = defaultdict(list)
    
    for project in projects:
        result[project.sub_category_id].append(project)

    return result


def sorted_proj_by_cats(projects: list[Project]) -> dict[int, list[Project]]:

    result: dict[int, list[Project]] = defaultdict(list)
    
    for project in projects:
        result[project.category_id].append(project)

    return result


def filter_cats_min_projects(
        src: dict[int, list[Project]], 
        min_count: int = 3
    ) -> dict[int, list[Project]]:
    
    result: dict[int, list[Project]] = defaultdict(list)
    
    for k, v in src.items():
        if len(v) >= min_count:
            result[k] = v

    return result


if __name__ == "__main__":
    pass