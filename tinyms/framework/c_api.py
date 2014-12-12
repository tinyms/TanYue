# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

from tinyms.core.web import api
from tinyms.core.util import DataResult


@api("/users", cache_key="users.cachekey")
def users(handler):
    dr = DataResult()
    dr.data = {"name": u"中文."}
    return dr