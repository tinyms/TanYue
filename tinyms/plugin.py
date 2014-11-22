# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'


class EmptyClass(object):
    pass


class ObjectPool():
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
