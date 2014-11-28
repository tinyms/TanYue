# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'
import sys
import os
import types
from importlib import import_module


class EmptyClass(object):
    pass


class ObjectPool():
    def __init__(self):
        pass

    hooks = dict()
    # Api
    api = dict()
    # Route
    route = dict()
    # Roles
    roles = dict()


# 插件实现函数
def add_action(hook_name, func_obj):
    """
    自定义插件，扩展插件点，定制功能
    :param hook_name: 插件点名称，名称具备唯一性
    :param func_obj: 插接进来的函数对象
    """
    funcs = ObjectPool.hooks.get(hook_name)
    if not funcs:
        ObjectPool.hooks[hook_name] = list()
    ObjectPool.hooks[hook_name].append(func_obj)


def do_action(hook_name, *args, **kwargs):
    """
    安置扩展点
    :param hook_name: 插件点名称
    :param args: 函数参数
    :param kwargs: 函数参数
    :return: 返回结果集
    """
    results = dict()
    funcs = ObjectPool.hooks.get(hook_name)
    if funcs:
        for func in funcs:
            r = func(*args, **kwargs)
            if r:
                results[r[0]] = r[1]
    return results


def list_plugin_modules(plugin_folder):
    """
    列出插件目录下所有模块，包含包结构的字符串形式
    :param plugin_folder: 插件目录
    :return: ['pkg1.pkg2.module',...]
    """
    sys.path.append(plugin_folder)
    valid_file_extnames = ['.py', '.pyc']
    length = len(plugin_folder.split(os.path.sep))
    modules_str_arr = list()
    dir_tree = os.walk(plugin_folder)
    for root, dirs, files in dir_tree:
        for f in files:
            file_part = os.path.splitext(f)
            if len(file_part) == 2:
                ext_name = file_part[1]
                if valid_file_extnames.count(ext_name) == 0:
                    continue
                pkg = '.'.join(root.split(os.path.sep)[length:])
                module = "%s.%s" % (pkg, file_part[0])
                if modules_str_arr.count(module) == 0:
                    modules_str_arr.append(module)
    return modules_str_arr


def import_plugin_modules(modules_arr):
    """
    加载插件文件夹下的所有模块
    :param modules_arr:
    :return:
    """
    modules = list()
    for item in modules_arr:
        m = import_module(item)
        modules.append(m)
    return modules


def preprocess_func_wrapper(modules):
    """
    被包装函数不会真正执行,只是把被包装函数做些预处理,放入全局对象池中,供其它模块真正调用
    :param modules:
    """
    for m in modules:
        attrs = dir(m)
        for attr_name in attrs:
            if attr_name.startswith("__"):
                continue
            live_attr = getattr(m, attr_name)

            if isinstance(live_attr, types.FunctionType):
                code = live_attr.func_code
                if code.co_name == "wrapper" or code.co_name == "wrap_func":
                    arr = code.co_names
                    if arr.count('__controller__') == 0:
                        continue
                    apply(live_attr)
