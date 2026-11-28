import asyncio

import manager_bot.main as man_bot


async def runner() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(man_bot.main())


if __name__ == "__main__":
    asyncio.run(runner())