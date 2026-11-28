import project_selector

from shared.db.conn import async_session_maker

from shared.db.models.base import Base
from shared.db.models.project import Project
from shared.db.models.battle import Battle

from shared.db.requests.battle import create_battle, get_latest_battle

from sqlalchemy.ext.asyncio import AsyncSession

import asyncio
import logging
import html


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
)


async def main():
    async with async_session_maker() as session:
        
        btl = create(session)
        new_battle = btl["battle"]
        projects = btl["projects"]

        print()
        print(f"New Battle:\n\n{new_battle.id} - {new_battle.number}\n\n")
        
        for proj in projects:
            print(f"P | {proj.name} - {proj.subtitle}\nU | {proj.user.name} - {proj.user.username}\n\n")

async def create(session: AsyncSession, projs_info: dict = None) -> dict:

    if not projs_info:
        projs_info = await project_selector.select_battle_projects(session)

        if not projs_info:
            return None

    flag_category = projs_info["flag_category"]
    projects: list[Project] = projs_info["projects"]
    
    if len(projects) != 3:
        return None

    project_ids: int = [proj.id for proj in projects]

    latest_battle: Battle = await get_latest_battle(session)

    number = 1
    if latest_battle:
        number = latest_battle.number + 1

    # Создаем пост. либо после create_battle
    link = ""

    sub_category = None if flag_category else projects[0].sub_category_id
    new_battle = await create_battle(session, number, link, projects[0].category_id, project_ids, sub_category_id=sub_category)

    if not new_battle:
        return None

    return {"battle": new_battle, "projects": projects}


async def text_gen(battle: Battle, projects: list[Project], parse_html=True) -> str:
    
    base = (
        f"🥩 <b>МЯСОРУБКА #{battle.number}</b>"
        if parse_html
        else f"🥩 МЯСОРУБКА #{battle.number}"
    )
    tail = f": {battle.theme}" if battle.theme else ""
    header = f"{base}{tail}\n\n"

    sponsr = f"" if parse_html else f""

    projs_info = f"" if parse_html else f""
    for n, proj in enumerate(projects):

        emojis = ("1️⃣", "2️⃣", "3️⃣")
        num_emoji = emojis[n]

        proj_info = (
                    f'{num_emoji} <b><a href="{html.escape(proj.link)}">{html.escape(proj.name)} — {html.escape(proj.subtitle)}</a></b>\n'
                    f"<b>👉 Суть: </b>{html.escape(proj.summ)}\n"
                    f"<b>🔥 Почему круто: </b>{html.escape(proj.uniq)}\n\n"
                    ) if parse_html else (
                    f'{num_emoji} {html.escape(proj.name)} — {html.escape(proj.subtitle)}\n'
                    f"👉 Суть: {html.escape(proj.summ)}\n"
                    f"🔥 Почему круто: {html.escape(proj.uniq)}\n\n"
                    )
        projs_info += f"{proj_info}"

    footer = f'💬 <b>Фидбек, критика и общение — в нашей <a href="https://t.me/rugalniya">Ругальне</a></b>' if parse_html else f"💬 Фидбек, критика и общение — в нашей Ругальне"

    result = f"{header}{sponsr}{projs_info}{footer}"

    return result


async def close():
    pass


if __name__ == "__main__":
    asyncio.run(main())