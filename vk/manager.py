from threading import Thread
import traceback
from typing import NoReturn
import database
from lib.threading_utils import run_in_pool
from vk.user_bot.service import (reload_queue, kill_queue, vk_lp_running,
                                 lp_failed)
from vk.user_bot import dlp, service_commands, sets
from database.billing_manager import vk_users, users_added
from longpoll.lp import logger, send_to_lp
from vk.user_bot.utils import ExcReload
from vk.running_on_tasks import rot
import socket
import json
from lib.microvk import VkApi, VkApiResponseException
import asyncio
import time
import os


class User:
    token: int
    vk: VkApi
    db: database.VkDB

    def __init__(self, uid):
        self.db = database.VkDB(uid)
        self.vk = VkApi(self.db.access_token, raise_excepts=True)


server: socket.socket

FROM_CATCHER = os.path.join(os.getcwd(), 'longpoll/catcher.sock')

commands = {
    444: service_commands,
    555: sets
}


def spawn(uids: list, rel: ExcReload = ExcReload):
    global vk_lp_running
    logger(f'Запуск для {uids}')
    for uid in uids:
        if uid in vk_lp_running and rel.text is not None:
            rel.vk.msg_op(1, rel.pid, rel.text)
        if uid in lp_failed:
            lp_failed.pop(uid)
        if uid not in vk_users:
            vk_users.append(uid)
        try:
            db = database.VkDB(uid)
            settings = db.settings_get()
            send_to_lp(
                'spawn', uid=uid, token=db.access_token,
                trusted_users=settings.trusted_users, delete=settings.delete,
                mentions=settings.mentions, leave_chats=settings.leave_chats,
                prefix=settings.prefix, ignore_list=settings.ignore_list,
                repeater=settings.repeater
            )
            vk_lp_running.update({uid: User(uid)})
        except Exception as e:
            print('Пизда рулю')
            logger.error(
                f'{uid}: запрос не отправился. {e}\n{traceback.format_exc()}'
            )


def catch_n_handle(func, update_, data_, user_):
    try:
        func(update_, user_.db, user_.vk, data_['received_time'])
    except ExcReload as e:
        spawn([data_['uid']], e)
    except VkApiResponseException as e:
        logger.error(
            f"Ошибка VK\nКод ошибки:{e.error_code}\nСообщение:{e.error_msg}\n"
            f"Параметры:{e.request_params}\n{traceback.format_exc()}"
        )
    except Exception:
        logger.error('Беда_очка:\n' + traceback.format_exc())


def mkupdate(data: dict) -> list:
    return [0, data['id'], 0, data['peer_id'], data['time'],
            data['text'], data['attachments']]


def handle_signal(data: bytes):
    try:
        data = json.loads(data)
        logger.info(f'Получено от ловца: {data}')
        if type(data['type']) != str:
            user = vk_lp_running[data['uid']]
            if data['type'] in {111, 222, 333, 444, 555}:
                run_in_pool(catch_n_handle,
                            commands[data['type']], mkupdate(data), data, user)
            else:
                run_in_pool(catch_n_handle,
                            dlp.launch, mkupdate(data), data, user)
        else:
            del(vk_lp_running[data['uid']])
            if data['type'] == 'dying':
                return
            elif data['type'] == 'failstart':
                lp_failed.update({data['uid']: {
                        "reason": data['type'],
                        "restart": time.time() + 60
                    }})
            else:
                lp_failed.update({data['uid']: {"reason": data['type']}})
    except Exception:
        logger.error('Беда_очка:\n' + traceback.format_exc())


def listen_lp():
    global vk_lp_running
    if not hasattr(socket, "AF_UNIX"):
        server.listen(1)
        while True:
            client, _ = server.accept()
            data = client.recv(8192)
            client.close()
            handle_signal(data)
    else:
        while True:
            data = server.recv(8192)
            handle_signal(data)


def create_connection():
    logger('Устанавливаю соединение с ловцом...')
    global server
    if os.path.exists(FROM_CATCHER):
        os.remove(FROM_CATCHER)
    if hasattr(socket, "AF_UNIX"):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(FROM_CATCHER)
    else:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('UNIX-сокет недоступен, слушаю LP модуль через HTTP')
        send_to_lp('over_http', addr='localhost:53435')
        server.bind(('localhost', 53435))
    Thread(target=listen_lp, daemon=True,
           name="LP server").start()


async def async_reloader() -> NoReturn:
    global vk_lp_running
    while True:
        try:
            if reload_queue:
                spawn(reload_queue)
                reload_queue.clear()
            if kill_queue:
                for uid in kill_queue:
                    send_to_lp('kill', uid=uid)
                    kill_queue.remove(uid)
                    vk_lp_running.pop(uid, None)
                    if uid in vk_users:
                        vk_users.remove(uid)
            await asyncio.sleep(1)
        except Exception:
            logger.error('Ошибка при респавне из очереди:\n' +
                         traceback.format_exc())
            await asyncio.sleep(10)


async def async_poll_starter() -> NoReturn:
    await users_added.wait()
    global vk_users
    while True:
        time_ = time.time()
        try:
            for uid in vk_users:
                if lp_failed.get(uid):
                    if lp_failed[uid]['reason'] == 'tokenfail':
                        continue
                    if 'restart' in lp_failed[uid]:
                        if lp_failed[uid]['restart'] - time_ < 0:
                            lp_failed.pop(uid)
                            spawn([uid])
                elif uid not in vk_lp_running:
                    spawn([uid])
        except Exception:
            logger.error('Ошибка при запуске VK поллера:\n' +
                         traceback.format_exc())
        await asyncio.sleep(60)


async def async_autohandler() -> NoReturn:
    await users_added.wait()
    await asyncio.sleep(120)
    loop = asyncio.get_event_loop()
    while True:
        time_ = time.time()
        for uid in vk_users:
            if lp_failed.get(uid) is not None:
                continue
            loop.create_task(rot(database.VkDB(uid), time_))
        await asyncio.sleep(250)

create_connection()
