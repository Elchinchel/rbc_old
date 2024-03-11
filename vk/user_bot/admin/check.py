from vk.user_bot import dlp, ND
from time import time as timenow
from vk.user_bot.utils import find_mention_by_message
from vk.user_bot.service import vk_users, lp_failed, vk_lp_running
from longpoll.lp import send_to_lp
from database.client import method

from .admin import check_admin


def _check_user_state(uid: int) -> str:
    if uid not in vk_users:
        return ('А пользователь отключен... Скажите пользователю, что ему '
                'нужно написать [randombotclub|в лс бота] "включи"')
    if uid in lp_failed:
        reason = lp_failed[uid]['reason']
        if reason == 'tokenfail':
            reason = 'токен инвалид 💔'
        return (
            f"😳 Беда_очка: {reason}"
            '' if not lp_failed.get('restart') else
            (f'Перезапуск через ' +
             str(round(lp_failed[uid]["restart"] - timenow())) +
             ' сек.')
        )
    if send_to_lp('check', uid=uid):
        return '✅ Пользователь заведен и бегает!'
    return '❓ Пользователь не бегает, причина неизвестна...'


def _get_user_state(uid: int) -> str:
    if uid is None:
        return '❗ Не указан пользователь'
    if not method.is_user(uid):
        return '👀 Пользователь не зарегистрирован'
    return _check_user_state(uid)


@dlp.register('check', 'чек', receive=True)
def check_is_user(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    nd.msg_op(2, _get_user_state(uid), keep_forward_messages=1)


@dlp.register('checkall', 'чеквсех', 'глочек', receive=True)
@dlp.wrap_handler(check_admin)
def check_all_users(nd: ND):
    usrs_in = 0
    usrs_out = []
    deactivated = 0
    all_users = method.start()
    for uid in vk_users:
        if uid in vk_lp_running:
            usrs_in += 1
        else:
            usrs_out.append(uid)
    for uid in all_users:
        if uid not in vk_users:
            deactivated += 1
    for i, user in enumerate(usrs_out):
        if user not in lp_failed:
            reason = 'причина неизвестна'
        else:
            reason = lp_failed[user]['reason']
            if reason == 'failstart':
                reason = (
                    'ошибка запуска, повторная попытка через ' +
                    f'{round(lp_failed[user]["restart"] - timenow())} с.'
                )
            elif reason == 'tokenfail':
                reason = 'токен - инвалид'
        usrs_out[i] = f'vk.com/id{user} ({reason})'
    nd.msg_op(
        f'Зарегистрировано пользователей: {len(all_users)}\n'
        f'Деактивированные пользователи: {deactivated}\n'
        f'LP запущен у {usrs_in}\n'
        f"Неактивные пользователи:\n{'<br>'.join(usrs_out)}"
    )


# @dlp.register('test', 'тест', receive=True)
# def test_user(nd: ND):
#     uid = find_mention_by_message(nd.msg, nd.vk)
#     try:
#         VkApi(method.get_tokens(nd[3])['access_token'], raise_excepts=True).msg_op(1, owner_id, 'нд')
#     except VkApiResponseException:
#         vk.msg_op(2, nd[3], '❗ Неверный основной токен', nd[1])
