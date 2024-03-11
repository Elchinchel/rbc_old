from vk.user_bot import dlp, ND
from const_data.easters import easters_common
import json
import os

# example {"id":1, "name":"дуров", "text":"азазазза"}

path = os.path.join(os.path.dirname(__file__), 'easters.json')

with open(path, 'r', encoding="utf-8") as data:
    easters: list = json.loads(data.read())


def save():
    global easters
    with open(path, 'w', encoding="utf-8") as data:
        data.write(json.dumps(easters, ensure_ascii=False, indent=2))


easter_commands = [easter['name'] for easter in easters]


@dlp.register(*easter_commands)
def easter_print(nd: ND):
    name = nd[5].lower().split(' ')[0]
    for easter in easters:
        print(easter)
        if easter['name'] == name:
            break
    nd.vk.msg_op(2, nd[3], easter['text'],  # type: ignore
                 nd[1], keep_forward_messages=1)


@dlp.register('пасхалка', receive=True)
def easter_edit(nd: ND):
    message = ' '.join(nd.msg['args']) if nd.msg['args'] else nd.msg['payload']

    if not message:
        return nd.msg_op(2, '❗️ Необходим текст')

    easter = None
    for i, easter in enumerate(easters):
        if easter['id'] == nd.db.user_id:
            easters[i]['text'] = message
            break

    if easter is not None:
        nd.msg_op(2, f'Текст команды "{easter["name"]}" успешно изменен')
        save()
    else:
        nd.msg_op(2, 'У тебя нет своей команды 🙁')


@dlp.register(*easters_common.keys())
def easter_common_print(nd: ND):
    nd.msg_op(2, easters_common[nd.msg['command']], keep_forward_messages=1)
