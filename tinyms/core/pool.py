# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'
from concurrent.futures import ThreadPoolExecutor
from tinyms.core.plugin import do_action


class WebSocketPoolFactory(object):
    __sockets__ = list()

    @staticmethod
    def execute(message):
        # TODO 分页
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(websocket_worker, message, WebSocketPoolFactory.__sockets__, 1, 10000, executor)


def websocket_worker(message, sockets=list(), page_num=1, limit=10000, executor=None):
    shutdown = False
    for socket_item in sockets[(page_num-1)*limit:limit]:
        if not socket_item:
            continue
        target_user_id = message["to"]
        if target_user_id and socket_item.user_id != target_user_id:
            do_action("websocket_message", socket_item, message)
            shutdown = True
            break
        else:
            do_action("websocket_message", socket_item, message)
    if shutdown and executor:
        executor.shutdown(False)