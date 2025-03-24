version = "0.5.3 indev"

import os, sys
from lib.wtflog import warden, create_warden

# Создание логгера LongPoll
create_warden('LP', 'logs/LP.log', level=warden.USELESS,
              printing=True, clear_on_start='backup')
# Создание логгера базы данных
create_warden('DB', 'logs/DB.log', level=warden.USELESS,
              printing=True, clear_on_start='backup')
# Создание логгера групп-бота
create_warden('GROUP', 'logs/GROUP.log', level=warden.USELESS,
              printing=True, clear_on_start='backup')
# Создание логгера таймеров
create_warden('TIMER', 'logs/TIMER.log', level=warden.USELESS,
              printing=True, clear_on_start='backup')
# Настройка главного логгера
logger = warden.setup(
    os.path.join(os.path.dirname((__file__)), "logs/main.log"),
    level=warden.INFO, printing=True, clear_on_start='backup'
)


from database import set_version
set_version(version)


from vk.user_bot.driver import print_info
print_info()


from vk.manager import async_autohandler, async_poll_starter, async_reloader
from database.billing_manager import async_users_filler
from vk.user_bot.timers.timers import async_timers_checker
from vk.user_bot.templates.life_is_strange import async_rewind_checker
from vk.user_bot.fake_activity import async_fake_typer
from vk.group_bot.bot import group_bot_runner

from lib.asyncio_utils import aio_loop

aio_loop.create_task(async_autohandler())
aio_loop.create_task(async_reloader())
aio_loop.create_task(async_poll_starter())

aio_loop.create_task(async_users_filler())

aio_loop.create_task(async_rewind_checker())
aio_loop.create_task(async_timers_checker())

aio_loop.create_task(async_fake_typer())

aio_loop.create_task(group_bot_runner())

from database.client import method

try:
    logger.info('Запускаю...')
    aio_loop.run_forever()
except KeyboardInterrupt:
    # TODO: сделать нормально
    if sys.platform != 'win32':
        method.die()
