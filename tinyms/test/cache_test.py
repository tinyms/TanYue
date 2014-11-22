__author__ = 'i@tinyms.com'

from tinyms.cache.cache import SimpleCache, FileSystemCache

c = SimpleCache()
c.set('cc', 'ddddddddddd')
print(c)
print(c.get('cc'))

f = FileSystemCache("d:/temp/flask")
f.set("user", {"Name": "Jhone"})
print(f.get("user"))

