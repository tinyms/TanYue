# -*- coding: utf-8 -*-
from tinyms.core.web import WebSocketController

__author__ = 'i@tinyms.com'

import os

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.wsgi
from .plugin import list_plugin_modules, import_plugin_modules, preprocess_func_wrapper

from tinyms.core.plugin import ObjectPool
from tinyms.core.util import Utils
from tinyms.core.config import Config
import tinyms.framework.c_api as c_api_module
import tinyms.framework.c_route as c_route_module


class HelloHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        self.write("OK, Land Moon.")


class HttpServer():
    def __init__(self):
        pass

    @staticmethod
    def startup():
        workdir = os.getcwd()
        Config.APS_PATH = workdir
        Config.STATIC_PATH = "%s/static" % Config.APS_PATH
        Config.TEMPLATE_PATH = "%s/template" % Config.APS_PATH
        Config.PLUGIN_PATH = "%s/plugin" % Config.APS_PATH
        Config.load()

        temp_dir = os.path.join(workdir, "temp")
        Utils.rmdirs(temp_dir)
        Utils.mkdirs(temp_dir)
        plugin_dir = os.path.join(workdir, "plugins")
        Utils.mkdirs(plugin_dir)
        modules = list_plugin_modules(plugin_dir)
        alive_module = import_plugin_modules(modules)
        preprocess_func_wrapper(alive_module)
        platform_modules = [c_api_module, c_route_module]
        preprocess_func_wrapper(platform_modules)

        handlers_ = [(r"/ws", WebSocketController)]
        for k in ObjectPool.api.keys():
            print(ObjectPool.api[k])
            handlers_.append(ObjectPool.api[k])

        for k in ObjectPool.route.keys():
            print(ObjectPool.route[k])
            handlers_.append(ObjectPool.route[k])

        app = tornado.web.Application(
            debug=True,
            handlers=handlers_,
            static_path=os.path.join(workdir, "static"),
            template_path=os.path.join(workdir, "template"),
            cookie_secret="www.tinyms.com"
        )
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(80)
        tornado.ioloop.IOLoop.instance().start()
