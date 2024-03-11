import time
from vk.user_bot import dlp, ND
from longpoll.lp import send_to_lp
from database.client import method
from vk.user_bot.ping import pingvk
from vk.user_bot.utils import get_plural
from vk.user_bot.admin.admin import check_moder


@dlp.register('stat', 'state', 'stats')
@dlp.wrap_handler(check_moder)
def stat(nd: ND):
    delta = round(nd.time - nd[4], 1)
    ct = time.time()
    data = send_to_lp('info')
    print(data)
    ping_lp = round((time.time() - ct) * 1000, 1)
    uptime = round(data['seconds']/60)
    msg = f"""
    Получено за {delta}(±0.5) сек
    Обработано за {round((time.time() - nd.time) * 1000, 1)} мс
    Пинг базы данных: {method.ping()} мс
    Пинг execute: {pingvk(nd.vk)} мс
    Время затраченное на получение сообщения: {
        pingvk(nd.vk, 'messages.getById', message_ids=nd[1])} мс
    LP модуль:
    -- пинг: {ping_lp} мс
    -- событий в секунду: {round(data['events']/data['seconds'], 1)}
    -- входящие сообщения: {round(data['messages']/data['events']*100)
                            }% от всех событий
    -- команд: {data['commands']}
    -- время работы: {uptime} минут{get_plural(uptime, 'а', 'ы', '')}
    """.replace('    ', '')
    nd.msg_op(2, msg)
