__author__ = 'i@tinyms.com'
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy import Column, Integer, Text

from tinyms.core.orm import SessionFactory, Entity, many_to_one


class DemoTable(Entity):
    fid = Column(Integer())
    main = Column(Text())
    client = Column(Text())


@many_to_one("DemoTable", True)
class OtherTable(Entity):
    asia = Column(Text)

SessionFactory.__engine__ = create_engine("sqlite:///d:/temp/db.s3db", echo=True, poolclass=QueuePool, pool_size=100)
SessionFactory.create_tables()