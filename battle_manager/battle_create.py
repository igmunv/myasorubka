import project_selector

from shared.db.conn import init_db, async_session_maker
from shared.db.models.base import Base
from shared.db.models.project import Project

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
)

async def main():
    async with async_session_maker() as session:
        projects = await project_selector.select_battle_projects(session)

        for project in projects:
            print()
            print(f"category | {project.category.name}\n"
                f"subcategory | {project.sub_category.name}\n"
                f"project | {project.id} : {project.name}\n"
                f"user | {project.user_id} : {project.user.name}\n"
                )
            print()


if __name__ == "__main__":
    asyncio.run(main())