from logging.handlers import TimedRotatingFileHandler
import os
import logging


class ProductionConfig:
    SECRET_KEY = os.urandom(24)
    sso_url = ""
    local_url = "1001"


class DevelopmentConfig:
    SECRET_KEY = os.urandom(24)
    sso_url = "http://test.auth.gddci.com"
    local_url = "2001"


def log():
    log_mgr = logging.getLogger(__name__)
    log_mgr.setLevel(logging.INFO)
    if not log_mgr.handlers:
        # file_handler = logging.FileHandler("../serverlog/app.log", encoding="utf-8")
        file_handler = TimedRotatingFileHandler("../serverlog/app.log", when="W6", interval=1, encoding="utf-8")
        formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(filename)s %(message)s",
                                      datefmt="%Y/%m/%d %X")
        file_handler.setFormatter(formatter)
        log_mgr.addHandler(file_handler)
    return log_mgr


flask_config = {
    "production": ProductionConfig,
    "development": DevelopmentConfig
}
logger = log()
