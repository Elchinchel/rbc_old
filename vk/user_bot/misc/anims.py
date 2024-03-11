from const_data.anims import rotating_animations, animations
from vk.user_bot import dlp, ND
import time


animation_names = ['зарплата', 'дорога', 'поддержка', 'ф']
animation_names.extend(animations.keys())
animation_names.extend(rotating_animations.keys())


def player(pic: list, nd: ND):
    for i in range(len(pic)):
        nd.msg_op(2, f'{pic[i]}', keep_forward_messages=1)
        time.sleep(2.5)


def animating_player(pics: list, nd: ND):
    for _ in range(len(pics[0]) + 1):
        nd.msg_op(2, '\n'.join(pics), keep_forward_messages=1)
        for i in range(len(pics)):
            pics[i] = pics[i][-1:] + pics[i][:-1]
        time.sleep(1.5)


@dlp.register(*animation_names, receive=True)
def animation_play(nd: ND):
    text = ' '.join([nd.msg['command']]+nd.msg['args']).lower()

    if text in {'ф', 'f', 'луна', 'ъуъ'}:
        if text == 'ф':
            text = text.replace('ф', 'f')
        pics = rotating_animations.get(text, [])
        animating_player(pics, nd)
        return "ok"

    if 'зарплата' in text:
        text = text.replace('зарплата', 'зп')
    elif 'дорога' in text:
        text = text.replace('дорога', 'дрг')
    elif 'поддержка' in text:
        text = text.replace('поддержка', 'под')
    elif 'помощь' in text:
        text = text.replace('помощь', 'под')

    pic = animations.get(text)
    if pic:
        player(pic, nd)
    return "ok"


@dlp.register('ж', receive=True)
def text_rolling(nd):
    if nd.msg['args'][0].isdigit():
        delay = float(nd.msg['args'].pop(0))
    else:
        delay = 3

    text = nd.msg['payload'] if nd.msg['payload'] else ' '.join(nd.msg['args'])
    if not text:
        nd.msg_op(3)

    for i in range(len(text) + 1):
        nd.msg_op(2, text)
        text = text[-1:] + text[:-1]
        time.sleep(delay)
