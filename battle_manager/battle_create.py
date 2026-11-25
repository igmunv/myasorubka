import project_selector

from shared.db.conn import async_session_maker

from shared.db.models.base import Base
from shared.db.models.project import Project
from shared.db.models.battle import Battle

from shared.db.requests.battle import create_battle, get_latest_battle

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
)

async def main():
    async with async_session_maker() as session:

        projects = await project_selector.select_battle_projects(session)

        flag_category = projects["flag_category"]
        projects: list[Project] = projects["projects"]
        
        if not projects or len(projects) != 3:
            return

        project_ids: int = [proj.id for proj in projects]

        latest_battle: Battle = await get_latest_battle(session)

        number = 1
        if latest_battle:
            number = latest_battle.number + 1

        # Создаем пост. либо после create_battle
        link = ""

        sub_category = None if flag_category else projects[0].sub_category_id
        new_battle = await create_battle(session, number, link, projects[0].category_id, project_ids, sub_category_id=sub_category)

        print()
        print(f"New Battle:\n\n{new_battle.id} - {new_battle.number}\n\n")

        for proj in projects:
            print(f"P | {proj.name} - {proj.subtitle}\nU | {proj.user.name} - {proj.user.username}\n\n")


if __name__ == "__main__":
    asyncio.run(main())