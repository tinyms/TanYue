# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

from tinyms.core.web import route


@route("/")
def index_page(handler):
    handler.render("ws_test.html", data={"Name": "JK"})