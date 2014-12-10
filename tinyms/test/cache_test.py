__author__ = 'i@tinyms.com'

from tinyms.core.cache import CacheFactory

CacheFactory.STORAGE_PATH = "d:/temp/flask/demo2"
c = CacheFactory.simple()
c.set('cc', 'ddddddddddd')
print(c.get('cc'))

f = CacheFactory.file()
# f.set("user3", {"Name": "Jhone"})
print(f.get("user3"))

