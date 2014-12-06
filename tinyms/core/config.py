# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'
import json
import os
from tinyms.core.util import Utils


class Config():

    abs_path = "home"
    site_url = "http://localhost"
    temp_path = "temp"
    static_path = "static"
    plugin_path = "plugins"
    template_path = "template"

    app_config = {
        "site_url": "http://localhost",
        "db_type": "",
        "db_user": "",
        "db_pwd": "",
        "db_name": ""
    }

    def __init__(self):
            pass

    @staticmethod
    def load():
        conf_file_name = os.path.join(Config.abs_path, "landmoon.conf")
        Config.app_config = json.loads(Utils.text_read(conf_file_name))

    @staticmethod
    def save():
        conf_file_name = os.path.join(Config.abs_path, "landmoon.conf")
        conf = json.dumps(Config.app_config)
        Utils.text_write(conf_file_name, conf)