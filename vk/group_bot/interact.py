from vk.group_bot.bot import vk
from lib.asyncio_utils import start_coro


def send_message(user_id: int, text: str, **kwargs) -> None:
    start_coro(
        vk('messages.send', message=text,
            peer_id=user_id, random_id=0, **kwargs)
    )
