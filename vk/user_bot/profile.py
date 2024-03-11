from vk.user_bot import dlp, ND
from vk.user_bot.utils import (find_mention_by_message, get_index,
                               upload_photo, format_push)


@dlp.register('профиль', 'whois', receive=True)
def whois(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if not uid:
        return nd.msg_op(2, '⚠ Не удалось найти пользователя')
    user = nd.vk('users.get', user_ids=uid,
                 fields='sex, country, city, domain, followers_count,' +
                 'subdomain,can_write_private_message,photo_max_orig' +
                 '')
    user = get_index(user, 0)
    if user is None:
        return nd.msg_op(2, '❗ Неизвестная ошибка')
    type_ = get_index(nd.msg['args'], 0, '').lower()
    if type_ == 'ава':
        photo = upload_photo(user['photo_max_orig'], nd.vk)
        nd.msg_op(2, f"Аватарка пользователя {format_push(user)}",
                  attachment=photo)
        return
    message = f'Пользователь {format_push(user)}:\n'
    message += f'ID: {user["id"]}\n'
    message += f'Дата рождения: {birthday(user)}\n'
    message += f''
    nd.msg_op(2, message)


def birthday(user: dict) -> str:
    date = user.get('bdate')
    if date is None:
        return 'не указана'
    if date.count('.') == 1:
        return date + ', год не указан'
    return date
