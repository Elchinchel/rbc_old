from typing import Tuple, Union
from vk.user_bot import ND, dlp
from .utils import find_mention_by_message, get_plural


def get_likes(nd: ND) -> Union[None, Tuple[ND, int, int]]:
    user = find_mention_by_message(nd.msg, nd.vk)
    if user is None:
        nd.msg_op(2, '⚠ Пользователь не найден')
        return None
    owner_id, photo_id = nd.vk(
        'users.get', fields='photo_id', user_ids=user
    )[0]['photo_id'].split('_')
    return nd, owner_id, photo_id


@dlp.register('+лайк', receive=True)
@dlp.wrap_handler(get_likes)
def like_avatar(nd: ND, owner_id: int, photo_id: int):
    likes = nd.vk('likes.add', type='photo',
                  owner_id=owner_id, item_id=photo_id)['likes']
    nd.msg_op(f'❤ плюс сердешко 😇\nТеперь на фоточке {likes} лайк' +
              get_plural(likes, '', 'а', 'ов'), keep_forward_messages=1)


@dlp.register('-лайк', receive=True)
@dlp.wrap_handler(get_likes)
def dislike_avatar(nd: ND, owner_id: int, photo_id: int):
    likes = nd.vk('likes.delete', type='photo',
                  owner_id=owner_id, item_id=photo_id)['likes']
    nd.msg_op(f'💔 минус сердешко 😔\nТеперь на фоточке {likes} лайк' +
              get_plural(likes, '', 'а', 'ов'), keep_forward_messages=1)
