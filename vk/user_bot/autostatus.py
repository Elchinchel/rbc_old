import re
from vk.user_bot import dlp, ND
from vk.user_bot.utils import get_text_from_message
from vk.autostatus_formatter import (avatar_vars, counters_vars,
                                     time_re, blacklist_var)


@dlp.register('автостатус', receive=True)
def autostatus(nd: ND):
    new_formatter = get_text_from_message(nd.msg)
    if new_formatter == '':
        formatter = nd.db.settings_get().autostatus_format
        if formatter == '':
            message = '⚠️ Форматтер статуса не установлен'
        else:
            message = 'Текущий форматтер статуса:\n' + formatter
        return nd.msg_op(2, message)
    unknown = None
    for var in re.findall(r'\{(.+?)\}', new_formatter):
        if var in avatar_vars or var in counters_vars or var in blacklist_var:
            continue
        time = time_re.findall(var)
        if time != []:
            if time[0][0] == '':
                continue
            delay = int(time[0][0])
            if -24 <= delay <= 24:
                continue
            unknown = 'Сдвиг часового пояса должен находиться в пределах от -24 до 24 часов'  # noqa
            break
        unknown = f'Неизвестная переменная "{{{var}}}"'
        break
    if unknown is not None:
        return nd.msg_op(2, '⚠️ ' + unknown)
    settings = nd.db.settings_get()
    settings.autostatus_format = new_formatter
    nd.db.settings_set(settings)
    nd.msg_op(2, '✅ Новый форматтер установлен')


@dlp.register('+автостатус', '-автостатус', receive=True)
def autostatus_info(nd: ND):
    nd.msg_op(2, f'ℹ️ Для переключения автостатуса используй команду "нд {nd.msg["command"]}"')  # noqa
