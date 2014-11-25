__author__ = 'i@tinyms.com'

from tinyms.core.web import api


@api("/users")
def users(handler):
    return {"name": "Jhone."}