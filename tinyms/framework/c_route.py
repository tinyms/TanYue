# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

from tinyms.core.web import route


@route("/")
def index_page(handler):
    handler.render("demo.html", data={"Name": "JK"})