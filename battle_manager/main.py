import asyncio

async def periodic_task():
    while True:
        try:
            # твоя логика: проверка БД, API, очереди и т.д.
            print("Тик...")
        except Exception as e:
            print(f"Ошибка в задаче: {e}")

        await asyncio.sleep(60)  # ждём 60 секунд без нагрузки на CPU

async def main():
    task = asyncio.create_task(periodic_task())
    try:
        # тут запускается остальной код (например, dp.start_polling(bot))
        await asyncio.Future()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())