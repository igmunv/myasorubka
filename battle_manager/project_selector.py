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
import logging


logger = logging.getLogger(__name__)


async def select_battle_projects(db_session: AsyncSession) -> list[Project]:
    """ Выбирает и возвращает три проекта для батла. Выбор происходит на основе множества критериев"""

    logger.info("start select battle projects")

    # Получаем все проекты только со статусом READY
    logger.info("get all projects ready to battle")
    all_projects = await get_projects_ready_battle(db_session)
    logger.info(f"all_projects count = {len(all_projects)}")

    if not all_projects:
        logger.info(f"return. all_projects is empty")
        return []

    # Получаем последний батл
    logger.info(f"get latest battle")
    latest_battle: Battle = await get_latest_battle(db_session)

    # Авторы участвовавшие в прошлом батле
    if latest_battle:
        logger.info(f"latest battle id = {latest_battle.id}")
        logger.info(f"get latest battle users")
        latest_battle_users: list[User] = await get_battle_users(db_session, latest_battle)
        excluded_users: set[User] = set(latest_battle_users)
        logger.info(f"received {len(excluded_users)} users")
    else:
        logger.info(f"latest battle is None")
        excluded_users: set[User] = []

    logger.info(f"call select_projects()")
    # здесь надо по другому. должны будут менять valid_strictness
    return await select_projects(db_session, all_projects, latest_battle, excluded_users)


async def select_projects(db_session: AsyncSession, all_projects: list[Project], latest_battle: Battle, excluded_users: set[User], category: bool=False, valid_strictness: int=0):
    """ Функция непосредство выбирает проекты по множеству критериям
        Понимает когда работать с подкатегориями а когда с категориями
    """

    # РЕАЛИЗОВАТЬ потом valid_strictness, Т.Е ТРЕБОВАНИЯ: 1 - без учета повтора категорий, 2 - без учета повтора людей, 3 - и то и то. и кажый раз +1, либо ЛУЧШЕ ПУСКАЙ ТОЛЬКО ВЫЗЫВАЮЩИЙ ЗАДАЕТ
    
    logger.info(f"in select_projects(): category={category}, valid_strictness={valid_strictness}")

    # Сортируем проекты по категориям
    logger.info(f"sorting projects by sub/categories")
    by_cat: dict[int, list[Project]] = sorted_proj_by_cats(all_projects) if category else sorted_proj_by_subcats(all_projects)
    logger.info(f"sorted projects by sub/categories: categories_count={len(by_cat)}")

    # Если батл был по подкатегории
    if latest_battle and not category and latest_battle.sub_category_id:

        # Удаляем проекты с этой подкатегорией
        logger.info(f"delete projects by this subcategory: {latest_battle.sub_category_id}")
        by_cat.pop(latest_battle.sub_category_id, None)

    # Если батл был по категории
    elif latest_battle and category and not latest_battle.sub_category_id:

        # Удаляем проекты с этой категорией
        logger.info(f"delete projects by this category: {latest_battle.category_id}")
        by_cat.pop(latest_battle.category_id, None)

    # Оставляем только категории где >= 3 проектов
    logger.info(f"filtering categories min projects: need >= 3 projects in category")
    by_cat_three_more: dict[int, list[Project]] = filter_cats_min_projects(by_cat)
    logger.info(f"filtered. category_count={len(by_cat_three_more)}")

    # Если ни в одной категории нету даже 3 проекта, то
    if not by_cat_three_more:

        logger.info(f"none of them contain 3 projects")

        if not category:
            # Работаем с категориями
            logger.info(f"go to work with categories")
            return await select_projects(db_session, all_projects, latest_battle, excluded_users, True)
        else: 
            logger.info(f"return empty list")
            return []

    # Получаем сколько раз каждая категория участвовала в батлах
    logger.info("counting battle appearances per category")
    count_battle_every_cat = await get_cat_battle_count(db_session, by_cat_three_more.keys()) if category else await get_subcat_battle_count(db_session, by_cat_three_more.keys())
    logger.info(f"done. battle count for first category = {count_battle_every_cat.get(next(iter(count_battle_every_cat)))}")

    # Сортируем чтобы сначала были категории которые меньше всех участвовали в батлах
    logger.info("sorting categories: first where there’s little, at the end where there’s a lot")
    sorted_counts = dict(sorted(count_battle_every_cat.items(), key=lambda item: item[1]))
    logger.info(f"done. battle count for sorted first category = {sorted_counts.get(next(iter(sorted_counts)))}")

    # Категории и в каждой авторы проектов, и количество их участия в батлах
    categories_with_authors: dict[int, dict[User, int]] = {}

    # Словарь для поиска проекта по юзеру
    cat_authors_with_projects: dict[int, dict[User, Project]] = {}

    # Пробегаемся по каждой катеории
    logger.info("iterating over categories")
    for cat_id in sorted_counts:

        logger.info(f"ITER: category_id={cat_id}, battle_count={sorted_counts.get(cat_id)}")

        # Получаем все проекты только этой категории
        logger.info(f"get all projects only this category")
        cat_projects = by_cat_three_more[cat_id]
        logger.info(f"category project count = {len(cat_projects)}")

        # Получаем всех авторов проектов
        logger.info(f"get all projects authors")
        projects_authors: dict[Project, User] = await get_projects_authors(cat_projects)

        # Удаляем авторов (и их проекты) которые участвовали в прошлом батле
        logger.info(f"excluding authors from previous battle")
        for project in [p for p, u in projects_authors.items() if u in excluded_users]:
            del projects_authors[project]
            logger.info(f"delete: project_id={project.id}, user_id={project.user_id}")

        # Записываем юзеров с проектами, на будущее, чтобы потом легко найти проект по юзеру
        logger.info(f"create dict user:project for easy find future")
        cat_authors_with_projects[cat_id] = {}
        for proj, user in projects_authors.items():
            cat_authors_with_projects[cat_id][user] = proj

        # Получаем количество участий в батлах всех пользователей
        logger.info(f"counting battle appearances per user")
        battle_count: dict[User, int] = await get_users_battle_count(db_session, list(projects_authors.values()))
        
        categories_with_authors[cat_id] = battle_count
    
    # Оставляем в каждой категории только 3 пользователя которые меньше всех участвовали в батлах
    logger.info("keeping top 3 users with lowest battle count per category")
    filtered_categories: dict[int, dict[User, int]] = {
        cat_id: dict(sorted(authors.items(), key=lambda item: item[1])[:3])
        for cat_id, authors in categories_with_authors.items()
    }

    # У каждой категории вычисляем среднее число количества участий в батлах
    logger.info("Computing average battle count per category")
    avg_by_category: dict[int, float] = {
        cat_id: sum(authors.values()) / len(authors)
        for cat_id, authors in filtered_categories.items()
        if authors  
    }

    # Получаем категорию с самым наименьшим числом. Т.е где юзеры меньше всего участвовали в батлах 
    logger.info("Finding category with minimum battle count")
    best_cat = min(avg_by_category.items(), key=lambda item: item[1], default=None)
    best_cat_id: int | None = best_cat[0] if best_cat is not None else None
    best_avg: float | None = best_cat[1] if best_cat is not None else None
    logger.info(f"category with minimum battle count: category_id={best_cat_id}, category_battle_count={best_avg}")

    # Если все норм, юзеры есть
    if best_cat_id is not None:

        logger.info(f"users/projects exist")

        best_cat_users: dict[User, int] = filtered_categories[best_cat_id]
        best_users: list[User] = list(best_cat_users.keys())

        logger.info(
            "users: %s",
            [{"id": u.id, "username": u.username} for u in best_users],
        )
        
        authors_in_best_cat = cat_authors_with_projects.get(best_cat_id, {})

        # Получаем проекты подходящих пользователей
        logger.info(f"get users projects")
        best_projects: list[Project] = [
            authors_in_best_cat[user]
            for user in best_users
            if user in authors_in_best_cat
        ]

        logger.info(
            "projecs: %s",
            [{"id": p.id, "username": p.name} for p in best_projects],
        )

        return best_projects

    # Если юзеров нет (из-за excluded)
    else:

        logger.info(f"users/projects is not exist")
        
        if not category:
            # Работаем с категориями
            logger.info(f"go to work with categories")
            return await select_projects(db_session, all_projects, latest_battle, excluded_users, True)
        else: 
            logger.info(f"return empty list")
            return []
        

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