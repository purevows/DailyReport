from .DailyReportPlugin import logger
from .db_config import DailyReportDbPoolConfig as Config
from dbutils.pooled_db import PooledDB
import pymysql
import datetime
import uuid
import traceback

pool = PooledDB(creator=pymysql, mincached=Config.mincached, maxcached=Config.maxcached,
                maxconnections=Config.maxconnections, maxusage=Config.maxusage, maxshared=Config.maxshared,
                blocking=Config.blocking, setsession=Config.setsession, reset=Config.reset, user=Config.user,
                host=Config.host, port=Config.port, password=Config.password, database=Config.db)


def create_new_item(list_form_data):
    deadline = datetime.time(17, 50)
    if datetime.datetime.now().time() > deadline:
        return "提交截止了哦亲，明天请早哦~~~。截止时间：每日17:50"
    for form_data in list_form_data:
        ret = check_form_data(form_data)
        if ret != 1:
            return ret
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        for form_data in list_form_data:
            db_cursor.execute("insert into daily_report(id, content, department, operator, remark, uploader,"
                              "upload_time) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" %
                              (str(uuid.uuid1()).replace('-', ''), form_data["content"], form_data["department"],
                               form_data["operator"], form_data["remark"], form_data["uploader"],
                               datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db_conn.commit()
        db_conn.close()
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return 1


def delete_item(form_data):
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        db_cursor.execute("delete from daily_report where id = '%s'" % form_data["id"])
        db_conn.commit()
        db_conn.close()
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return 1


def modify_content(form_data):
    ret = check_form_data(form_data)
    if ret != 1:
        return ret
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        db_cursor.execute("update daily_report set content = '%s', operator = '%s', remark = '%s',"
                          "department = '%s' where id = '%s'" %
                          (form_data["content"], form_data["operator"], form_data["remark"],
                           form_data["department"], form_data["id"]))
        db_conn.commit()
        db_conn.close()
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return 1


def query_data(timestamp):
    db_conn = pool.connection()
    db_cursor = db_conn.cursor()
    db_cursor.execute("select id, content, department, operator, remark, uploader, upload_time,"
                      "first_check, first_check_time, double_check, double_check_time from daily_report"
                      " where date(upload_time) = '%s'" % timestamp)
    data = db_cursor.fetchall()
    ret = []
    for i in data:
        ret.append({"id": i[0], "content": i[1], "department": i[2], "operator": i[3], "remark": i[4],
                    "uploader": i[5], "upload_time": i[6], "first_check": i[7], "first_check_time": i[8],
                    "double_check": i[9], "double_check_time": i[10]})
    # ('id', 'content', 'department', ...)
    return ret


def submit_first_check(list_form_data, current_user):
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        for form_data in list_form_data:
            db_cursor.execute("select first_check, first_check_time from daily_report where id = '%s'"
                              % form_data)
            res = db_cursor.fetchone()
            if res[0] is None or res[1] is None:
                db_cursor.execute("update daily_report set first_check = '%s', first_check_time = '%s'"
                                  " where id = '%s'" %
                                  (current_user, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   form_data))
                db_conn.commit()
        db_conn.close()
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return 1


def submit_double_check(list_form_data, current_user):
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        for form_data in list_form_data:
            db_cursor.execute("select double_check, double_check_time from daily_report where id = '%s'"
                              % form_data)
            res = db_cursor.fetchone()
            if res[0] is None or res[1] is None:
                db_cursor.execute("update daily_report set double_check = '%s', double_check_time = '%s'"
                                  " where id = '%s'" %
                                  (current_user, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   form_data))
                db_conn.commit()
        db_conn.close()
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return 1


def query_mobile():
    # noinspection PyBroadException
    try:
        db_conn = pool.connection()
        db_cursor = db_conn.cursor()
        db_cursor.execute("select id, name, mobile from org_person where status = 1 and mobile <> ''")
        ret = []
        mobile_result = db_cursor.fetchall()
        db_cursor.execute("select json_data from org_work_group where name = '综合岗'")
        workgroup_result = db_cursor.fetchone()[0]
        db_cursor.execute("select person_id from org_staff where org_id = '8e921ad266f2979a0166f2b093af0008'")
        staff_result = db_cursor.fetchall()
        leader_id_list = []
        for person_id in staff_result:
            leader_id_list.append(person_id[0])
        for i in mobile_result:
            if i[0] not in leader_id_list:
                if i[1] in workgroup_result:
                    ret.append({"name": i[1], "phone_number": i[2], "workgroup": "综合岗"})
                else:
                    ret.append({"name": i[1], "phone_number": i[2], "workgroup": ""})
    except Exception:
        logger.error(traceback.format_exc())
        return traceback.format_exc()
    return ret


def check_form_data(form_data):
    for key, value in form_data.items():
        if key == "content":
            if len(value) > 1000:
                return "the length of \"事项\" is out of range"
        elif key == "department":
            if len(value) > 15:
                return "the length of \"部门\" is out of range"
        elif key == "operator":
            if len(value) > 50:
                return "the length of \"经办人\" is out of range"
        elif key == "remark":
            if len(value) > 255:
                return "the length of \"备注\" is out of range"
        elif key == "uploader":
            if len(value) > 10:
                return "the length of \"填报人\" is out of range"
    return 1
