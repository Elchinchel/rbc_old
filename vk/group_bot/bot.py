import traceback
from lib.vkmini import LPGroup, VkApi, VkResponseException
from lib.vkmini.group_longpoll import Update
from lib.wtflog import get_boy_for_warden
from database.driver import group_id, group_token
from .handlers import (check_for_tokens, ping, warn_list, goodbyes, greetings,
                       switch_state)

logger = get_boy_for_warden('GROUP', 'Группа-бот')


vk = VkApi(group_token, excepts=True, logger=logger)


async def group_bot_runner():
    if group_token == '':
        logger.warning('Необходимо указать токен и ID группы-бота в '
                       'database/general.json.\nГруппа-бот деактивирована')
        return
    try:
        lp = await LPGroup.create_poller(vk, group_id)
    except VkResponseException as e:
        if e.error_code == 5:
            logger.error('Неверный токен группы! Группа-бот неактивна')
        return
    except Exception:
        logger.error(f'Группа-бот не завелась:\n{traceback.format_exc()}')
        return
    async for update in lp.listen():
        try:
            await handle(update)
        except Exception:
            logger.error(
                f'Ошибка обработки сообщения:\n{traceback.format_exc()}'
            )


async def handle(update: Update):
    update.lowered = update.message.text.lower()
    if update.lowered == 'пинг':
        return await ping(update)
    elif 'пред' in update.lowered:
        return await warn_list(update)
    elif update.lowered in goodbyes:
        return await switch_state(update, False)
    elif update.lowered in greetings:
        return await switch_state(update, True)
    if update.message.peer_id > 2e9:
        return
    await check_for_tokens(update, group_id)
