from traceback import print_exc
from asyncio import sleep
from time import time

from database import VkDB
from lib.vkmini import VkApi
from random import choice

from vk.autostatus_formatter import render


rate_limit_friends = {}


async def autofriends(vk: VkApi, uid: int):
    requests = (await vk('friends.getRequests', need_viewed=True))['items']
    await sleep(1)
    for user in (await vk('users.get',
                          user_ids=','.join([str(i) for i in requests]))):
        if user.get('deactivated') is None:
            res = await vk('friends.add', user_id=user['id'])
            if type(res) == dict:
                if res.get('error', {}).get('error_code') == 29:
                    rate_limit_friends.update({uid: time()})
            break


async def rot(db: VkDB, time_now: float) -> None:
    try:
        await _rot(db, time_now)
    except Exception:
        print_exc()


async def _rot(db: VkDB, time_now: float):  # noqa
    settings = db.settings_get()

    if db.me_token:
        vk = VkApi(choice([db.access_token, db.me_token]))
    else:
        vk = VkApi(db.access_token)

    # адвд
    if settings.friends_add:
        if db.user_id not in rate_limit_friends:
            await autofriends(vk, db.user_id)
            await sleep(1)
        else:
            if time_now - rate_limit_friends[db.user_id] > 86400:
                rate_limit_friends.pop(db.user_id)

    # автоотписка
    if settings.del_requests:
        await vk.exe("""
        var i = 0;
        var items = API.friends.getRequests({"out": true}).items;
        while (i < 24 && i <= items.length) {
            if (items[i].deactivated == null) {
                API.friends.delete({"user_id": items[i]});
                };
            i = i + 1;
        };""")
        await sleep(1)

    # удсобак
    if settings.dogs_del:
        for friend in (await vk('friends.get', fields='nickname'))['items']:
            if friend.get('deactivated'):
                await vk('friends.delete', user_id=friend['id'])
                await sleep(1)

    # автоонлайн
    if settings.online:
        await VkApi(db.access_token)('account.setOnline')
        await sleep(1)

    # автоферма
    farm = settings.farm
    if farm['on'] and time_now - farm['last_time'] > 14500:
        comment = (await vk('wall.createComment', owner_id=-174105461,
                            post_id=35135, message='Ферма'))['comment_id']
        farm['last_time'] = time_now
        db.settings_set(settings)
        await sleep(1)
        await vk('wall.deleteComment', owner_id=-174105461, comment_id=comment)
        await sleep(1)

    # автостатус
    if settings.autostatus_on:
        await vk('status.set', text=await render(settings.autostatus_format, vk))  # noqa
        await sleep(1)
