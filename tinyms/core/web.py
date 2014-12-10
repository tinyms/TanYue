# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

import os
import shutil
from functools import wraps
from tornado.web import RequestHandler
from .plugin import ObjectPool, EmptyClass, do_action
from tinyms.core.util import Utils, DataResult


class IWebHandler(RequestHandler):
    __key_account_id__ = "auth_account_id"
    __key_account_name__ = "auth_account_name"
    __key_account_role_name__ = "auth_account_role_name"
    __key_auth__ = "__auth__"

    def __init__(self, application, request, **kwargs):
        RequestHandler.__init__(self, application, request, **kwargs)

    def prepare(self):
        if hasattr(self.__class__, IWebHandler.__key_auth__):
            is_auth = getattr(self.__class__, IWebHandler.__key_auth__)
            if is_auth:
                if not self.get_current_user():
                    self.redirect("/signin")

    def data_received(self, chunk):
            pass

    def auth(self, points=set()):
        """
        细微控制数据输出,不产生页面跳转相关动作
        :param points:
        :return:
        """
        if self.get_current_account_points().issuperset(points):
            return True
        return False

    def get_template_namespace(self):
        namespace = dict(
            handler=self,
            request=self.request,
            current_user=self.current_user,
            locale=self.locale,
            _=self.locale.translate,
            static_url=self.static_url,
            xsrf_form_html=self.xsrf_form_html,
            reverse_url=self.reverse_url,
            # Add to auth current user security points
            auth=self.auth,
            do_action=do_action
        )
        namespace.update(self.ui)
        return namespace

    def get_login_url(self):
        return "/signin"

    def write_error(self, status_code, **kwargs):
        self.clear_all_cookies()
        if status_code == 401:
            self.redirect("/signin")
        elif status_code == 403:
            self.render("core/err.html", reason="访问禁止")
        elif status_code == 404:
            self.render("core/err.html", reason="访问禁止")
        else:
            self.render("core/err.html", reason="服务器内部错误")

    def get_current_user(self):
        """
        user id, str
        :return: user id, str type
        """
        id_ = self.get_secure_cookie(IWebHandler.__key_account_id__)
        if id_:
            return id_.decode('utf-8')
        return None

    def get_current_account_points(self):
        """
        account security points: set('key1','key2',..)
        :return:
        """
        role_name = self.get_secure_cookie(IWebHandler.__key_account_role_name__)
        if role_name:
            role_obj = ObjectPool.roles.get(role_name.decode('utf-8'), None)
            if role_obj:
                return role_obj.points()
        return set()

    def get_current_account_name(self):
        """
        current account user_login field.
        :return:
        """
        name = self.get_secure_cookie(IWebHandler.__key_account_name__)
        if name:
            return name.decode('utf-8')
        return ""

    def wrap_entity(self, entity_object, excude_keys=None):
        """
        把参数值填充到对象对应属性中，针对ORM中的Entity
        :param entity_object:
        :param excude_keys:
        :return:
        """
        if not excude_keys:
            excude_keys = ["id"]
        dict_ = dict()
        args = self.request.arguments
        for key in args.keys():
            if excude_keys.count(key) != 0:
                continue
            dict_[key] = self.get_argument(key)
        entity_object.dict(dict_)
        return entity_object

    def wrap_params_to_dict(self):
        dict_ = dict()
        args = self.request.arguments
        for key in args:
            dict_[key] = self.get_argument(key)
        return dict_

    def wrap_params_to_obj(self):
        obj = EmptyClass()
        args = self.request.arguments
        for key in args:
            setattr(obj, key, self.get_argument(key))
        return obj

    def get_webroot_path(self):
        return os.path.dirname(self.get_template_path()) + "/"


def api(pattern="/", method="get", auth=False, points=set(), cache_key="", cache_time=300, cache_storage="mem"):
    def handle_func(func):
        @wraps(func)
        def wrap_func(*args_, **kwargs_):
            func.__controller__ = True
            pattern_ = "/api%s" % pattern
            cls_name = "tinyms_web_api_%s" % Utils.md5(pattern_)
            handler = type(cls_name, (IWebHandler,), {})
            handler.cache_path = cache_key
            handler.cache_time = cache_time
            handler.cache_storage = cache_storage

            def unauth(*args, **kwargs):
                this = args[0]
                result = DataResult()
                result.success = False
                result.message = "UnAuth"
                result.data = ""
                this.write(Utils.encode(result.dict()))

            def generic_func(*args, **kwargs):
                this = args[0]
                this.set_header("Content-Type", "application/json; charset=UTF-8")
                if auth:
                    account_id = this.get_current_user()
                    if not account_id:
                        unauth(*args, **kwargs)
                    if len(points) > 0:
                        points_ = this.get_current_account_points()
                        same = points & points_
                        if len(same) > 0:
                            result = func(*args, **kwargs)
                            this.write(Utils.encode(result.dict()))
                        else:
                            unauth(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                        this.write(Utils.encode(result.dict()))
                else:
                    result = func(*args, **kwargs)
                    this.write(result.dict())

            if "post" == method:
                handler.post = generic_func
            else:
                handler.get = generic_func

            if pattern not in ObjectPool.api.keys():
                ObjectPool.api[pattern_] = (pattern_, handler)

        return wrap_func

    return handle_func


def route(pattern="/", method="get", auth=False, points=set(), cache_key="", cache_time=300, cache_storage="mem"):
    def handle_func(func):
        @wraps(func)
        def wrap_func(*args_, **kwargs_):
            func.__controller__ = True
            cls_name = "tinyms_web_controller_%s" % Utils.md5(pattern)
            handler = type(cls_name, (IWebHandler,), {})
            handler.cache_path = cache_key
            handler.cache_time = cache_time
            handler.cache_storage = cache_storage

            def unauth(*args, **kwargs):
                this = args[0]
                this.redirect(this.get_login_url())

            def generic_func(*args, **kwargs):
                this = args[0]
                if auth:
                    account_id = this.get_current_user()
                    if not account_id:
                        unauth(*args, **kwargs)
                    if len(points) > 0:
                        points_ = this.get_current_account_points()
                        same = points & points_
                        if len(same) > 0:
                            func(*args, **kwargs)
                        else:
                            unauth(*args, **kwargs)
                    else:
                        func(*args, **kwargs)
                else:
                    func(*args, **kwargs)

            if "post" == method:
                handler.post = generic_func
            else:
                handler.get = generic_func

            if pattern not in ObjectPool.route.keys():
                ObjectPool.route[pattern] = (pattern, handler)

        return wrap_func

    return handle_func


def upload(handler, thumbnail_size="", store_level="Private", callback_func=None):
    results = list()
    # 预先创建要存放的目录
    """
    文件上传
    :param request: tornado request handler
    :param thumbnail_size: 缩略图尺寸，格式200x200，即宽x高
    :param store_level: 存放文档级别 `Public` or `Private`
    :param callback_func: pass file inf, dict type
    """
    store_path = "static/upload/%s"
    if store_level == "Private":
        store_path = "upload/%s"
    store_path = store_path % Utils.format_year_month(Utils.current_datetime(), "/")
    Utils.mkdirs(store_path)

    if handler.request.files:
        for fn in handler.request.files.keys():
            f = handler.request.files[fn][0]
            raw_name = f["filename"]
            ext_name = os.path.splitext(raw_name)[-1]
            mime_type = f["content_type"]
            uniq_name = Utils.uniq_index()
            dist_name = "%s%s" % (uniq_name, ext_name)
            tnb_name = "thumb_%s%s" % (uniq_name, ext_name)
            tf = open("temp/%s" % Utils.uniq_index(), mode="w+b")
            # tf = tempfile.NamedTemporaryFile()
            try:
                tf.write(f["body"])
                tf.seek(0)
                tf.close()
                b = True
            except Exception as e:
                b = False
                print(e)
            if b:
                # 拷贝到目标目录
                file_inf = dict()
                file_inf["author"] = handler.get_current_user()
                file_inf["raw_name"] = raw_name
                file_inf["ext_name"] = ext_name
                file_inf["mime_type"] = mime_type
                file_inf["size"] = Utils.get_file_size(tf.name)
                file_inf["rel_store_path"] = ""
                file_inf["rel_store_thumbnail_path"] = ""
                file_inf["store_level"] = store_level
                final_normal_save_path = "%s/%s/%s" % (os.getcwd(), store_path, dist_name)
                final_thumbnail_save_path = "%s/%s/%s" % (os.getcwd(), store_path, tnb_name)
                shutil.move(tf.name, final_normal_save_path)
                rel_thumbnail_store_path = "%s/%s" % (store_path, tnb_name)
                if thumbnail_size and mime_type.startswith("image/"):
                    Utils.create_thumbnail(final_normal_save_path, final_thumbnail_save_path, size=thumbnail_size)
                    file_inf["rel_store_thumbnail_path"] = rel_thumbnail_store_path
                rel_store_path = "%s/%s" % (store_path, dist_name)
                file_inf["rel_store_path"] = rel_store_path
                file_inf["__extra_data__"] = callback_func(file_inf, handler)
                r = DataResult()
                r.success = True
                r.message = "Success"
                r.data = file_inf
                results.append(r.dict())
            else:
                r = DataResult()
                r.success = False
                r.message = "Failure"
                r.data = raw_name
                results.append(r.dict())
    else:
        r = DataResult()
        r.success = False
        r.message = "NoFilesUpload"
        r.data = ""
        results.append(r.dict())

    return results