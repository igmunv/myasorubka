from aiogram import Router, F, types

fallback_router = Router()

@fallback_router.callback_query()
async def unhandled_callbacks(callback: types.CallbackQuery):
    await callback.answer("✋ Недоступно", show_alert=True)