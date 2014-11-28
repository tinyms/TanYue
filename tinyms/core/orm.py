# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy import Column, Integer, ForeignKey, Table, String, DateTime
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from tinyms.core.util import Utils, DataResult
from tinyms.core.plugin import EmptyClass


@declared_attr
def __tablename__(*args):
    self = args[0]
    table_name = self.__name__.lower()
    return "%s%s" % (SessionFactory.__table_name_prefix__, table_name)


def __table_data_dict(*args):
    self = args[0]
    dict_ = args[1]
    """
    1, object to map
    2, map to object
    :param dict_:
    :return:
    """
    if not dict_:
        columns = [c.key for c in class_mapper(self.__class__).columns]
        return dict((c, getattr(self, c)) for c in columns)
    else:
        metas = self.cols_meta()
        for k, v in dict_.items():
            if not hasattr(self, k):
                continue
            for m in metas:
                if m["name"] == k:
                    if m["type"] == "int":
                        if type(v) == str:
                            setattr(self, k, Utils.parse_int(v))
                        else:
                            setattr(self, k, v)
                    elif m["type"] == "numeric":
                        if type(v) == str:
                            setattr(self, k, Utils.parse_float(v))
                        else:
                            setattr(self, k, v)
                    elif m["type"] == "datetime":
                        if type(v) == str:
                            setattr(self, k, Utils.parse_datetime(v))
                        else:
                            setattr(self, k, v)
                    elif m["type"] == "date":
                        if type(v) == str:
                            setattr(self, k, Utils.parse_date(v))
                        else:
                            setattr(self, k, v)
                    elif m["type"] == "time":
                        if type(v) == str:
                            setattr(self, k, Utils.parse_time(v))
                        else:
                            setattr(self, k, v)
                    else:
                        setattr(self, k, v)
            pass
        pass


def __table_datarow_print__(*args):
    self = args[0]
    return "<%s%s>" % (self.__tablename__.capitalize(), self.data_dict())


def __table_fields_meta__(*args):
    self = args[0]
    cols = class_mapper(self.__class__).columns
    metas = list()
    for col in cols:
        meta = dict()
        meta["pk"] = col.primary_key
        # is a set()
        meta["fk"] = col.foreign_keys
        meta["name"] = col.key
        meta["nullable"] = col.nullable
        meta["unique"] = col.unique
        meta["autoincrement"] = col.autoincrement
        meta["default"] = col.default
        if isinstance(col.type, String) and col.type.length:
            meta["length"] = col.type.length
        else:
            meta["length"] = 0
        type_name = col.type.__visit_name__
        if ["string", "text", "unicode", "unicode_text"].count(type_name) == 1:
            type_name = "string"
        elif ["integer", "small_integer", "big_integer", "boolean"].count(type_name) == 1:
            type_name = "int"
        elif ["numeric", "float"].count(type_name) == 1:
            type_name = "numeric"
            # elif ["datetime","date","time"].count(type_name)==1:
        # type_name = "date"
        meta["type"] = type_name
        metas.append(meta)
    return metas


Entity = declarative_base()
Entity.__tablename__ = __tablename__
Entity.id = Column(String(60), primary_key=True)
Entity.create_time_ = Column(DateTime())
Entity.modify_time_ = Column(DateTime())
Entity.creator_ = Column(String(60))
Entity.updator_ = Column(String(60))
Entity.cols_meta = __table_fields_meta__
Entity.data_dict = __table_data_dict
Entity.data_show = __table_datarow_print__


class SessionFactory():
    __engine__ = None

    def __init__(self):
        pass

    @declared_attr
    def __table_name_prefix__(self):
        return "landmoon_"

    @staticmethod
    def set_table_name_prefix(name):
        SessionFactory.__table_name_prefix__ = name

    @staticmethod
    def new():
        if SessionFactory.__engine__:
            return sessionmaker(bind=SessionFactory.__engine__)()
        return None

    @staticmethod
    def connect():
        if SessionFactory.__engine__:
            return SessionFactory.__engine__.connect()
        return None

    @staticmethod
    def create_tables():
        if SessionFactory.__engine__:
            Entity.metadata.create_all(SessionFactory.__engine__)

    @staticmethod
    def pk():
        """
        生成UUID表主键
        :return:
        """
        return Utils.uniq_index()

    @staticmethod
    def uniq_field_check(entity, col_name, val, err_tip="", allowed_val_null=True, id_=None):
        """
        Uniq字段唯一性检查
        :param entity: Entity Class Object
        :param col_name: table column name
        :param val: column value
        :param err_tip: web page opreration
        :param allowed_val_null:
        :param id_: table pk
        :return:
        """
        ec = EmptyClass()
        ec.checked = False
        ec.message = None
        # 字段没有填写则不进行唯一性检查，否则必须检查
        if allowed_val_null and not val:
            ec.checked = True
            return ec
        cnn = SessionFactory.new()
        if id_:
            num = cnn.query(entity).filter(entity.id != id_).filter("%s=:v" % col_name).params(v=val).count()
            if num > 0:
                r = DataResult()
                r.success = False
                r.message = err_tip
                r.data = num
                ec.message = r.dict()
            else:
                ec.checked = True
        else:
            num = cnn.query(entity).filter("%s=:v" % col_name).params(v=val).count()
            if num > 0:
                r = DataResult()
                r.success = False
                r.message = err_tip
                r.data = num
                ec.message = r.dict()
            else:
                ec.checked = True
        return ec


def one_to_one(foreign_entity_name):
    """
    一对一，比如: 从表对主表
    一旦映射成功，彼此获取到对方表名实体对象变量，也就是你可以直接访问我，我可以直接访问你
    :param foreign_entity_name: 目标实体名
    :return:
    """

    def ref_table(cls):
        foreign_entity_name_lower = foreign_entity_name.lower()
        foreign_table_name = "%s%s" % (SessionFactory.__table_name_prefix__, foreign_entity_name_lower)
        setattr(cls, '{0}_id'.format(foreign_entity_name_lower),
                Column(String(60), ForeignKey('{0}.id'.format(foreign_table_name), ondelete="CASCADE")))
        setattr(cls, foreign_entity_name_lower,
                relationship(foreign_entity_name,
                             backref=backref(cls.__name__.lower(), uselist=False)))
        return cls

    return ref_table


def many_to_one(foreign_entity_name, delete_cascard=True):
    """
    多对一，一对多共用这种形式
    一旦映射成功，one的一方将自动拥有many一方集合变量名`表名s`
    :param foreign_entity_name: 目标实体名
    :return:
    """

    def ref_table(cls):
        foreign_entity_name_lower = foreign_entity_name.lower()
        foreign_table_name = "%s%s" % (SessionFactory.__table_name_prefix__, foreign_entity_name_lower)
        # 自己关联自己
        if foreign_entity_name == cls.__name__:
            foreign_entity_name_lower = "parent"

        if foreign_entity_name == cls.__name__:
            setattr(cls, '{0}_id'.format(foreign_entity_name_lower),
                    Column(String(60), ForeignKey('{0}.id'.format(foreign_table_name))))
            setattr(cls, foreign_entity_name_lower,
                    relationship(foreign_entity_name, backref=backref("children", remote_side=cls.id)))
        else:
            if delete_cascard:
                setattr(cls, '{0}_id'.format(foreign_entity_name_lower),
                        Column(String(60), ForeignKey('{0}.id'.format(foreign_table_name), ondelete="CASCADE")))
            else:
                setattr(cls, '{0}_id'.format(foreign_entity_name_lower),
                        Column(String(60), ForeignKey('{0}.id'.format(foreign_table_name))))
            setattr(cls, foreign_entity_name_lower,
                    relationship(foreign_entity_name, backref=backref(cls.__name__.lower() + 's')))

        return cls

    return ref_table


def many_to_many(foreign_entity_name):
    """
    多对多，装饰到有关联关系的任意实体之上
    一旦映射成功，彼此皆可获取对方`表名s`集合变量
    :param foreign_entity_name: 目标实体名
    :return:
    """

    def ref_table(cls):
        target_name = foreign_entity_name.lower()
        self_name = cls.__name__.lower()
        association_table = Table(
            '{0}{1}_{2}_relationships'.format(SessionFactory.__table_name_prefix__, self_name, target_name),
            Entity.metadata,
            Column('{0}_id'.format(target_name), String(60),
                   ForeignKey('{0}{1}.id'.format(SessionFactory.__table_name_prefix__, target_name),
                              ondelete="CASCADE")),
            Column('{0}_id'.format(self_name), String(60),
                   ForeignKey('{0}{1}.id'.format(SessionFactory.__table_name_prefix__, self_name),
                              ondelete="CASCADE"))
        )

        setattr(cls, target_name + 's',
                relationship(foreign_entity_name, secondary=association_table,
                             backref=backref(cls.__name__.lower() + 's', lazy='dynamic')))
        return cls

    return ref_table


# 特别的数据库处理函数

# 计算两个日期之间以分钟为单位的差值，返回整数
class MinuteDiff(FunctionElement):
    type = Integer()
    name = "minute_diff"


@compiles(MinuteDiff, 'mssql')
def _mssql_minute_diff(element, compiler, **kw):
    return "DATEDIFF(MINUTE, %s, %s)" % (compiler.process(element.clauses.clauses[0]),
                                         compiler.process(element.clauses.clauses[1]))


@compiles(MinuteDiff, 'mysql')
def _mysql_minute_diff(element, compiler, **kw):
    return "TIMESTAMPDIFF(MINUTE, %s, %s)" % (compiler.process(element.clauses.clauses[0]),
                                              compiler.process(element.clauses.clauses[1]))


@compiles(MinuteDiff, 'sqlite')
def _mysql_minute_diff(element, compiler, **kw):
    return "(julianday(%s) - julianday(%s))*24*60" % (compiler.process(element.clauses.clauses[0]),
                                                      compiler.process(element.clauses.clauses[1]))