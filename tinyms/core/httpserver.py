__author__ = 'i@tinyms.com'

import os

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.wsgi
import wsgiref.simple_server
from .plugin import list_plugin_modules, import_plugin_modules, preprocess_func_wrapper

from tinyms.core.plugin import ObjectPool
from tinyms.core.util import Utils
import tinyms.framework.c_api as c_api_module


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
        temp_dir = os.path.join(workdir, "temp")
        Utils.rmdirs(temp_dir)
        Utils.mkdirs(temp_dir)
        plugin_dir = os.path.join(workdir, "plugins")
        Utils.mkdirs(plugin_dir)
        modules = list_plugin_modules(plugin_dir)
        alive_module = import_plugin_modules(modules)
        preprocess_func_wrapper(alive_module)
        platform_modules = [c_api_module]
        preprocess_func_wrapper(platform_modules)

        handlers_ = [(r"/hello", HelloHandler)]
        for k in ObjectPool.api.keys():
            handlers_.append(ObjectPool.api[k])
        print(handlers_)
        app = tornado.web.Application(
            debug=True,
            handlers=handlers_,
            static_path=os.path.join(workdir, "static"),
            template_path=os.path.join(workdir, "template"),
            cookie_secret="www.tinyms.com"
        )
        wsgi_app = tornado.wsgi.WSGIAdapter(app)
        server = wsgiref.simple_server.make_server('', 80, wsgi_app)
        server.serve_forever()
