from vk.user_bot.utils import find_mention_by_message
from vk.user_bot import dlp, ND
from .admin import check_owner, check_moder

from database.data_classes import Account
from database.client import method


def refactor(uid: int):
    if uid in [561316861]:
        by = 365530525
    else:
        by = 332619272
    acc = Account(method.get_account(uid))
    acc.added_by = by
    method.update_account(uid, acc)


@dlp.register('refactor')
@dlp.wrap_handler(check_owner)
def use_refactor(nd: ND):
    count = 0
    for uid in nd.db.method.start():
        refactor(uid)
        count += 1
    nd.msg_op(f'обработано: {count}')


@dlp.register('added by?', receive=True)
@dlp.wrap_handler(check_moder)
def view_added_by(nd: ND):
    user = find_mention_by_message(nd.msg, nd.vk)
    acc = Account(method.get_account(user))
    nd.msg_op(f'vk.me/id{acc.added_by}')
