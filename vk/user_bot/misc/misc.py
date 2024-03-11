import json
import re
import time
import random
from time import sleep
from urllib.parse import quote_plus

from database.client import method
from database.driver import owner_id
from lib.microvk import VkApi, VkApiResponseException
from vk import user_bot
from vk.user_bot import ND, dlp
from vk.user_bot.calc import (CalcError, ExponentError, UnpairedBrackets,
                              ValueTooBig, evaluate)
from vk.user_bot.utils import (att_parse, digger, execme,
                               find_mention_by_message)


@dlp.register('опрос', receive=True)
def pollcreate(nd: ND):
    answers = nd.msg['payload'].split('\n')
    if not answers:
        nd.msg_op(2, 'Необходимо указать варианты ответов (с новой строки)')
        return
    if len(answers) > 10:
        answers = answers[:10]
        warning = '⚠️ Максимальное количество ответов - 10'
    else:
        warning = ''
    poll = nd.vk('polls.create', question=" ".join(nd.msg['args']),
                 add_answers=json.dumps(answers, ensure_ascii=False))
    nd.msg_op(2, warning, attachment=f"poll{poll['owner_id']}_{poll['id']}")


@dlp.register('скрин')
def screen_take(nd):
    nd.vk.msg_op(3, msg_id=nd[1])
    execme('return API.messages.sendService({peer_id:%s,action_type:"chat_screenshot",random_id:0});' % nd[3], nd.db)  # noqa


@dlp.register('команды', 'кмд')
def cmd_article(nd):
    nd.msg_op(2, 'vk.com/@rbcguide-overview', keep_forward_messages=1)


@dlp.register('колокольчик', receive=True)
def click_bell(nd):
    if nd.msg['reply']:
        push = f"[id{nd.msg['reply']['from_id']}|Нажимай] "
    else:
        push = 'Нажимай '
    nd.msg_op(2, push + 'на колокольчик [club176952405|&#128276;]',
              keep_forward_messages=1)


@dlp.register('баланс')
def balance_check(nd):
    nd.msg_op(2, f'У вас на балансе {round(method.billing_get_balance(nd.db.user_id), 1)} 🎱 (бильярдный шар восьмерка)')


@dlp.register('аттач', receive=True)
def attach_send(nd):
    nd.msg_op(1, attachment=','.join(nd.msg['args']))


@dlp.register('спам', receive=True)
def spam(nd: ND):
    count = 1
    delay = 0.5
    if nd.msg['args'] is not None:
        if nd.msg['args'][0] == 'капча':
            count = 100
        else:
            count = int(nd.msg['args'][0])
        if len(nd.msg['args']) > 1:
            delay = float(nd.msg['args'][1])
    if delay * count > 120 and nd.db.user_id != owner_id and delay > 4:
        nd.msg_op(2, 'ээ, не, иди нахер, я не буду так долго это делать, минуты две максимум')
        return "ok"
    if nd.msg['payload']:
        if (nd.msg['payload'].lower().startswith(nd.db.settings_get().prefix) or
            nd.msg['payload'].startswith("нд") or nd.msg['payload'].startswith("!!")):
            nd.msg_op(2, 'команды нельзя')
            return "ok"
        for _ in range(count):
            nd.msg_op(1, nd.msg['payload'])
            time.sleep(delay)
    else:
        for i in range(count):
            nd.msg_op(1, f'spamming {i+1}/{count}')
            time.sleep(delay)
    return "ok"


@dlp.register('msginfo', 'мсгинфо', 'смсинфо', receive=True)
def msg_info(nd):
    if nd.msg['reply']:
        nd.msg['raw'] = nd.vk(
            'messages.getById', message_ids=nd.msg['reply']['id']
        )['items'][0]
    data = json.dumps(nd.msg['raw'], indent=4, ensure_ascii=False)
    nd.msg_op(2, data.replace('    ', 'ᅠ'))  # второй символ в замене - пустой


@dlp.register('ксмс', receive=True)
def tosms(nd):
    if nd[3] < 2000000000:
        nd.vk.msg_op(2, nd[3], '❗ Не работает в ЛС', msg_id=nd[1])
        return "ok"
    msg = (nd.vk('messages.getByConversationMessageId', peer_id=nd[3],
           conversation_message_ids=re.search(r'\d+', nd[5])[0])['items'])
    if msg:
        if msg[0].get('action'):
            nd.vk.msg_op(2, nd[3], 'Это сообщение - действие, не могу переслать', msg_id=nd[1])  # noqa
        else:
            nd.msg_op(1, nd.msg['payload'] or 'Вот ента:',
                      reply_to=msg[0]['id'], delete_id=nd[1])
    else:
        nd.msg_op(2, '❗ ВК вернул пустой ответ')
    return "ok"


@dlp.register('начало')
def first_message(nd):
    for msg in nd.vk('messages.getHistory', peer_id=nd[3],
                     rev=1, count=200)['items']:
        if msg.get('action'):
            continue
        else:
            break
    nd.msg_op(1, '☝🏻 Первое сообщение в диалоге...',
              delete_id=nd[1], reply_to=msg['id'])  # type: ignore


@dlp.register('cc', 'сс', receive=True)
def link_shortener(nd):
    link = nd.msg['args'][0] if nd.msg['args'] else nd.msg['payload']
    try:
        shortened = nd.vk('utils.getShortLink', url=link)
        nd.msg_op(2, shortened['short_url'].replace('https://', ''))
    except VkApiResponseException:
        nd.msg_op(2, '❗ Произошла ошибка. Скорее всего неверный формат ссылки')


@dlp.register('повтори', 'напиши', receive=True)
def repeat(nd):
    nd.msg_op(1, ' '.join(nd.msg['args']) + '\n' + nd.msg['payload'],
              attachment=','.join(nd.msg['attachments']))


@dlp.register('lmgtfy', receive=True)
def lmgtfy(nd: ND):
    request = ' '.join(nd.msg['args']) or nd.msg['payload']
    if not request:
        return nd.msg_op(2, '❗ Указан пустой запрос')
    nd.msg_op(2, f'Смотри, что нашел:\nhttps://lmgtfy.app/?q={quote_plus(request)}')  # noqa


@dlp.register('тм', receive=True)
def add_trademark(nd):
    nd.msg_op(2, ' '.join(nd.msg['args'])+'™',
              attachment=','.join(nd.msg['attachments']))


@dlp.register('dig', 'диг', receive=True)
def dig_attachments(nd: ND):
    if nd.msg['reply']:
        sleep(0.5)
        nd.msg['raw'] = nd.vk(
            'messages.getById', message_ids=nd.msg['reply']['id']
        )['items'][0]
    atts = digger(nd.msg['raw'])
    if atts == []:
        return nd.msg_op(2, '🙈 Ничего не найдено')
    for att in att_parse(atts):
        nd.msg_op(1, attachment=att)
        sleep(1)


@dlp.register('токены')
def check_tokens(nd):
    me_token = method.get_tokens(nd.db.user_id)['me_token']
    try:
        VkApi(me_token, raise_excepts=True).exe('return 1;')
    except VkApiResponseException:
        me_token = False
    msg = ('Основной токен в порядке, раз это читаешь\n'
           'Токен VkMe ' +
           ('в порядке' if me_token else 'пошел по пизде'))  # type: ignore
    nd.msg_op(2, msg)


@dlp.register('статус', receive=True)
def status_set(nd):
    if not nd.msg['payload']:
        status = " ".join(nd.msg['args'])
    else:
        status = nd.msg['payload']
    if not status:
        return nd.msg_op(2, '🤷🏼‍♀️ Необходим текст')
    try:
        nd.vk("status.set", text=status)
        nd.msg_op(2, '✅ Статус успешно установлен')
    except VkApiResponseException:
        nd.msg_op(2, '❌ Ошибка установки статуса')


@dlp.register('реши', receive=True)
def calc(nd: ND):
    if not nd.msg['payload']:
        text = " ".join(nd.msg['args'])
    else:
        text = nd.msg['payload'].split('\n')[0]
    if not text:
        return nd.msg_op(2, '🤔 А че решать-то?')
    try:
        msg = evaluate(text.replace(',', '.'))
    except CalcError as e:
        if type(e) == ValueTooBig:
            msg = '❗️ Слишком большое число'
        elif type(e) == UnpairedBrackets:
            msg = '❗️ Непарные скобки'
        elif type(e) == ExponentError:
            msg = '❗️ Возведение в отрицательную степень'
        else:
            msg = '❗️ Деление на ноль'
        msg += '\nВыражение, в котором произошла ошибка: ' + e.sentence
    nd.delete_and_send(msg)


@dlp.register('пуш', 'пушнуть', receive=True)
def ment_user(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None:
        uid = nd.db.user_id
    if not nd.msg['payload']:
        return nd.msg_op(2, '⚠ Текст с новой строки')
    nd.msg_op(2, f"@id{uid}({nd.msg['payload']})")


@dlp.register('булыгоген', 'генератор булыжника')
def stone_generator(nd: ND):
    msg = ''
    while True:
        msg += '🗿'
        nd.msg_op(2, msg)
        sleep(1)


@dlp.register('сброс уведов')
def reset_notifications(nd: ND):
    nd.vk('notifications.markAsViewed')
    nd.msg_op(3)


@dlp.register('выбери')
def choose(nd: ND):
    text = nd.msg['payload'] or ' '.join(nd.msg['args'])
    nd.msg_op(1, random.choice(text.split('или')), reply_to=nd[1])
