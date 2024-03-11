import re
from typing import Tuple
from vk.user_bot import dlp, ND
from datetime import datetime
from vk.user_bot.utils import find_time, parse
from .timers import Timer, Cycle, get_timers, del_timer, get_cycles


@dlp.register('цтаймеры')
def cycles_list(nd: ND):
    _list(nd, True, '⏳ Список циклотаймеров:\n',
          '❔ Ни один циклотаймер не установлен')


@dlp.register('таймеры')
def timer_list(nd: ND):
    _list(nd, False, '⏳ Список таймеров:\n',
          '❔ Ни один таймер не установлен')


def _list(nd: ND, cycle: bool, *text: Tuple[str, str]):
    if cycle:
        timers, _ = get_cycles(nd.db.user_id)
    else:
        timers, _ = get_timers(nd.db.user_id)
    if timers:
        message = text[0] + timers
    else:
        message = text[1]
    nd.msg_op(2, message)


# TODO: вернуть
# @dlp.register('-цтаймер', receive=True)
# def cycle_unset(nd: ND):
#     _unset(nd, True, '❗️ Необходимо указать номер циклотаймера',
#            '✅ Циклотаймер #{} удален', '❗️ Циклотаймер #{} не найден')


@dlp.register('-таймер', receive=True)
def timer_unset(nd: ND):
    _unset(nd, False, '❗️ Необходимо указать номер таймера',
           '✅ Таймер #{} удален', '❗️ Таймер #{} не найден')


def _unset(nd: ND, cycle: bool, *text: Tuple[str, str, str]):
    if not nd.msg['args']:
        return nd.msg_op(2, text[0])

    ident = re.findall(r'\d+', nd.msg['text'])
    if ident:
        ident = int(ident[0])
    else:
        return nd.msg_op(2, text[0])

    if del_timer(nd.db.user_id, ident, cycle):
        nd.msg_op(2, text[1].format(ident))
    else:
        return nd.msg_op(2, text[2].format(ident))


@dlp.register('цтаймер', '+цтаймер', receive=True)
def cycle_set(nd: ND):
    nd.msg_op(2, 'отключено в целях повышения стабильности')
    # _set(nd, True,
    #      '❗ Необходимо указать период, через который должен срабатывать циклотаймер',  #noqa
    #      )


@dlp.register('таймер', '+таймер', receive=True)
def timer_set(nd: ND):
    _set(nd, False,
         '❗ Необходимо указать период, через который должен сработать таймер',
         )


def _set(nd: ND, cycle: bool, *text: Tuple[str, str, str]):
    delay = find_time(' '.join(nd.msg['args']))

    if not delay:
        return nd.msg_op(2, text[0])

    if cycle:
        _, count = get_cycles(nd.db.user_id)
    else:
        _, count = get_timers(nd.db.user_id)
    if count > 5:
        nd.msg_op(2, '❗ Возможно установить максимум 5 таймеров')

    prefix = nd.db.settings_get().prefix
    if nd.msg['payload'].startswith(prefix):
        nd.msg['payload'] = nd.msg['payload'].replace(prefix, '', 1)

    target_msg = parse({"text": nd.msg['payload']}, cut_prefix=False)

    if target_msg['command'] not in dlp.commands_list:
        args = [target_msg['command']]
        args.extend(target_msg['args'])
        target_msg['args'] = args
        target_msg['command'] = 'повтори'

    if target_msg['command'] in dlp.receive_message:
        target_msg.update({'attachments': nd.msg['attachments'],
                           'reply': nd.msg['reply'],
                           'fwd': nd.msg['fwd']})

    if target_msg['command'] != 'повтори':
        return nd.msg_op(2, 'отключено в целях повышения стабильности')

    if cycle:
        Cycle(nd, target_msg, delay)
    else:
        Timer(nd, target_msg, delay)

    if delay > 15768000:
        return nd.msg_op(2, '🤨 Ну ты запрос до полугода-то ограничь, чел')

    time = datetime.fromtimestamp(datetime.now().timestamp() + delay)
    if cycle:
        nd.msg_op(2, f'Команда "{target_msg["command"]}" сработает ' +
                  time.strftime("%d.%m в %H:%M:%S") +
                  f' и будет повторяться каждые {delay} сек.')
    else:
        nd.msg_op(2, f'Команда "{target_msg["command"]}" сработает ' +
                  time.strftime("%d.%m в %H:%M:%S"))
