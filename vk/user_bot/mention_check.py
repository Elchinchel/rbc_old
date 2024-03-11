from vk.user_bot import dlp, ND
from vk.user_bot.utils import get_last_th_msgs, find_time
from typing import Tuple, List
from time import sleep


def check_resolutions(text: str) -> Tuple[bool, bool]:
    for b in {'все', 'всё'}:
        if b in text:
            return True, True
    for r in {'реплаи', 'реплай', 'ответы'}:
        if r in text:
            return False, True
    return False, False


@dlp.register('пуши', 'уведы', receive=True)
def mention_search(nd: ND) -> None:
    nd[5] = nd[5].lower()

    mention = f'[id{nd.db.user_id}|'
    msg_ids = []

    bots, replies = check_resolutions(nd[5].lower())

    time = find_time(nd[5])
    if time == 0 or time > 86400:
        time = 86400

    for msg in get_last_th_msgs(nd[3], nd.vk):
        if nd.time - msg['date'] >= time:
            break
        if msg.get('reply_message', {}).get('from_id') == nd.db.user_id and replies and not bots:  # noqa
            msg_ids.append(str(msg['id']))
        elif mention in msg['text']:
            if msg['from_id'] > 0:
                msg_ids.append(str(msg['id']))
            elif bots:
                msg_ids.append(str(msg['id']))

    kwargs = {}
    if not msg_ids:
        msg = 'Ничего не нашел 😟'
    else:
        msg = 'Собсна, вот что нашел за ' + (
         'последние 24 часа:' if time == 86400 else 'указанный период:')
        if len(msg_ids) == 1:
            kwargs.update({"reply_to": msg_ids[0]})
        elif 'отдельно' in nd[5].lower():
            return sender(nd, msg_ids)
        else:
            kwargs.update({"forward_messages": ','.join(msg_ids[:10])})

    nd.vk.msg_op(1, nd[3], msg, **kwargs)


def sender(nd: ND, msg_ids: List[int]) -> None:
    for msg_id in msg_ids:
        nd.msg_op(1, 'ссыл_очка на увед', reply_to=msg_id)
        sleep(1)
