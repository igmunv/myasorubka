from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Category, Project, ProjectStatus, SubCategory
from typing import Optional


async def get_all_categories(session: AsyncSession) -> list[dict]:
    """Получить все общие категории в виде списка словарей."""
    result = await session.execute(
        select(Category.id, Category.name)
    )
    
    # превращает каждую строчку результата в словарь id: name
    return [dict(row) for row in result.mappings().all()]


async def get_subcategories_by_category(session: AsyncSession, category_id: int) -> list[dict]:
    """Получить все подкатегории определенной категории в виде списка словарей."""
    
    stmt = select(
        SubCategory.id, 
        SubCategory.name, 
        SubCategory.desc
    ).where(
        SubCategory.category_id == category_id
    )
    
    result = await session.execute(stmt)
    
    # Превращаем результат в список словарей как в друг функции id: name
    return [dict(row) for row in result.mappings().all()]


# Прилетел новый проект
async def create_new_project(
    session: AsyncSession, 
    user_id: int, 
    category_id: int, 
    sub_category_id: int,
    name: str,
    link: str,
    summ: str,
    uniq: str
):

    new_project = Project(
        name=name,
        link=link,
        summ=summ,
        uniq=uniq,
        status=ProjectStatus.WAIT,
        user_id=user_id,
        category_id=category_id,
        sub_category_id=sub_category_id
    )

    session.add(new_project)

    await session.commit()

    await session.refresh(new_project)

    return new_project


# Человек обновил инфу о проекте
async def update_project(
    session: AsyncSession,
    project_id: int,
    name: Optional[str] = None,
    link: Optional[str] = None,
    summ: Optional[str] = None,
    uniq: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
) -> Optional[Project]:

    project = await session.get(Project, project_id)
    
    if not project:
        return None  # Проект не найден
    
    if name is not None:
        project.name = name
    if link is not None:
        project.link = link
    if summ is not None:
        project.summ = summ
    if uniq is not None:
        project.uniq = uniq
    if status is not None:
        project.status = ProjectStatus.RECHECK

    await session.commit()

    await session.refresh(project)

    return project