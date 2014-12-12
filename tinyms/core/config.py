# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'
import json
import os
from tinyms.core.util import Utils


class Config():
    __CONFIG_FILE_NAME__ = "config.json"

    APS_PATH = "/home"
    STATIC_PATH = "/home/static"
    PLUGIN_PATH = "/home/plugin"
    TEMPLATE_PATH = "/home/template"

    # key value.
    items = {
        "site_url": "http://localhost",
        "temp_path": "/home/temp",
        "database_type": "sqlite"
    }

    def __init__(self):
            pass

    @staticmethod
    def load():
        conf_file_name = os.path.join(Config.APS_PATH, Config.__CONFIG_FILE_NAME__)
        if os.path.exists(conf_file_name):
            Config.items = json.loads(Utils.text_read(conf_file_name))
        else:
            Config.save()

    @staticmethod
    def save():
        conf_file_name = os.path.join(Config.APS_PATH, Config.__CONFIG_FILE_NAME__)
        conf = json.dumps(Config.items, indent=True)
        Utils.text_write(conf_file_name, conf)

    @staticmethod
    def site_url():
        return Config.items.get("site_url", "http://localhost")

    @staticmethod
    def temp_path():
        return Config.items.get("temp_path", "/home/temp")