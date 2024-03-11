import re
from time import sleep
from typing import List
from datetime import datetime, timedelta, timezone
from vk.user_bot import ND, dlp
from vk.user_bot.utils import att_parse, upload_photo
from .life_is_strange import Rewind
from .operations import list_templates, remove_template


def get_reply_info(nd: ND) -> dict:
    if nd.msg['reply']:
        rep_user = nd.vk('users.get', fields='domain',
                         user_ids=nd.msg['reply']['from_id'])[0]
        link = f"vk.com/{rep_user['domain']}"
        push = f"[id{rep_user['id']}|@{rep_user['domain']}]"
        first_name = f"[id{rep_user['id']}|{rep_user['first_name']}]"
        last_name = f"[id{rep_user['id']}|{rep_user['last_name']}]"
    else:
        link = first_name = last_name = push = ''
    return {
        '#рпуш': push,
        '#римя': first_name,
        '#рфамилия': last_name,
        '#рссылка': link
    }


def render(nd: ND, variables: list, text: str) -> str:
    default_vars = {
        '&время': datetime.now(timezone(timedelta(hours=+3))).strftime("%H:%M:%S") # noqa
        }
    reply_vars = {}
    defined_vars = {}
    for var_text in variables:
        var = re.findall(r'([^:]+):([^:]+)', var_text)
        if not var: continue # noqa
        defined_vars.update({var[0][0]: var[0][1]})
    for text_var in re.findall(r'{([^(}]+)(\((.+)\))?}', text):
        var_low = text_var[0].lower()
        default = text_var[2]
        if var_low.startswith('#'):
            if not reply_vars:
                reply_vars.update(get_reply_info(nd))
            replacement = reply_vars.get(var_low, 'ашипко!!1!')
        elif var_low.startswith('&'):
            replacement = default_vars.get(var_low, 'ашипко!!1!')
        else:
            replacement = defined_vars.get(var_low)
        if not replacement and default:
            text = text.replace('{'+text_var[0]+text_var[1]+'}', default)
        elif replacement:
            text = text.replace('{'+text_var[0]+'}', replacement)
    return text


def upload_atts(nd: ND, atts: List[dict]) -> List[str]:
    reuploads = 0
    for i, att in enumerate(atts):  # да, я знаю, но хз че еще сделать
        if att['type'] == 'photo':
            reuploads += 1
    if reuploads > 1:
        nd.msg_op(2, f'Перезаливаю {reuploads} фото, жди...')
        sleep(1)
    for i, att in enumerate(atts):
        if att['type'] == 'photo':
            url = att['photo']['sizes'][-1]['url']
            atts[i] = upload_photo(url, nd.vk)
            sleep(1)
    return att_parse(atts)


@dlp.register('+шаб', receive=True)
def template_create(nd: ND):
    name = re.findall(r"([^|]+)\|?([^|]*)", ' '.join(nd.msg['args']))
    if not name:
        nd.vk.msg_op(2, nd[3], "❗ Не указано название", msg_id=nd[1], delete=3)
        return "ok"
    category = name[0][1].lower().strip()
    name = name[0][0].lower().strip()
    if ':' in name or ':' in category:
        return nd.msg_op(2, '❗ Символ ":" нельзя использовать в названии', delete=3) # noqa

    if ((nd.msg['payload'] == '') and len(nd.msg['attachments']) == 0
            and nd.msg['reply'] is None):
        nd.vk.msg_op(2, nd[3], "❗ Нет данных", msg_id=nd[1], delete=3)
        return "ok"

    if nd.msg['reply']:
        payload = nd.msg['reply']['text']
        nd.msg['attachments'] = upload_atts(nd, nd.msg['reply']['attachments'])
    else:
        payload = nd.msg['payload']

    old = nd.db.template_create(name, nd.msg['attachments'], payload, category)

    if old['name']:
        rew_id = Rewind(nd.db.user_id, 'common', old).ident
        msg = (f'✍ Шаблон "{name}" перезаписан.\n' +
               'Вернуть старый можно в течении 5 минут командой !!rewind ' +
               str(rew_id))
    else:
        msg = f'✍ Шаблон "{name}" сохранен'

    nd.vk.msg_op(2, nd[3], msg, msg_id=nd[1], delete=0 if old['name'] else 1)
    return "ok"


@dlp.register('шаб', receive=True)
def template_print(nd: ND):
    def send(text, atts): # noqa
        if atts.startswith('graffiti'):
            nd.vk.exe("""API.messages.send({"peer_id":%d,
            "attachment":"%s","reply_to":"%s","random_id":0});
            API.messages.delete({"message_ids":%d,"delete_for_all":1});""" %
            (nd[3], atts, nd.msg['reply']['id'] if nd.msg['reply'] else '', nd[1])) # noqa
        else:
            nd.vk.msg_op(2, nd[3], text, attachment=atts, msg_id=nd[1],
                         keep_forward_messages=1)
    if len(nd.msg['args']) > 0:
        var = []
        for arg in nd.msg['args']:
            if ':' in arg:
                var.append(arg.lower())
                nd.msg['args'].remove(arg)
        name = ' '.join(nd.msg['args'])
        template = nd.db.template_get('common', name)
        if template:
            if nd.msg['attachments']:
                template['attachments'] += ',' + ','.join(nd.msg['attachments']) # noqa
            text = nd.msg['payload'] + '\n' + template['text']
            message = render(nd, var, text)
            return send(message, template['attachments'])
        else:
            e = (f'❗ Не существует шаблона "{name}"')
    else:
        e = ('❗ Не существует безымянных шаблонов, чел')
    nd.vk.msg_op(2, nd[3], e, msg_id=nd[1], delete=3)
    return "ok"


@dlp.register('-шаб', receive=True)
def template_remove(nd: ND):
    return remove_template(nd,
                           'common',
                           ['Шаблон', ''],
                           'шаблона')


@dlp.register('шабы', receive=True)
def template_list(nd: ND):
    return list_templates(nd,
                          'common',
                          'шаблонов',
                          'У тебя нет ни одного шаблона 😕\nДобавь командой +шаб', # noqa
                          'Шаблоны')
