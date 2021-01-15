from flask import Blueprint, render_template, request, session, jsonify
from flask import send_from_directory
from .DbManager import create_new_item, delete_item, modify_content, query_data
from .DbManager import submit_first_check, submit_double_check, query_mobile
from .DailyReportPlugin import write_to_workbook, logger, MessageSetting, login_required, authority_required
import requests
import datetime
import json


DailyReport = Blueprint("DailyReport", __name__)
ver = "2021-01-14"


@DailyReport.route("/", methods=["GET"])
@login_required
def list_item():
    # if session.get("token") is None:
    #     return redirect("/login")
    if request.args.get("set_date") is None:
        current_time = datetime.date.today().isoformat()
    else:
        current_time = request.args.get("set_date")
    get_item_list = query_data(current_time)
    current_user = session.get("name")
    current_department = session.get("department")
    logger.info("User " + current_user + " loads the item list of " + current_time)
    return render_template("/DailyReport/list_item.html", current_time=current_time, item_list=get_item_list,
                           current_user=current_user, current_department=current_department, ver=ver)


@DailyReport.route("/add_item")
@login_required
def add_content_page():
    # if session.get("name") is None:
    #     return redirect("/login")
    current_time = datetime.date.today().isoformat()
    current_user = session.get("name")
    current_department = session.get("department")
    return render_template("/DailyReport/add_item.html", current_time=current_time, current_user=current_user,
                           current_department=current_department, ver=ver)


@DailyReport.route("/modify", methods=["POST"])
@login_required
def modify():
    # if session.get("name") is None:
    #     abort(400)
    form_data = json.loads(request.get_data().decode("utf-8"))
    form_data["content"] = form_data["content"].replace("\n", "<br>")
    form_data["operator"] = form_data["operator"].replace("\n", "<br>")
    form_data["remark"] = form_data["remark"].replace("\n", "<br>")
    form_data["content"] = form_data["content"].replace("\t", "")
    form_data["operator"] = form_data["operator"].replace("\t", "")
    form_data["remark"] = form_data["remark"].replace("\t", "")
    form_data["department"] = form_data["department"].replace("\n", "")
    form_data["department"] = form_data["department"].replace("\t", "")
    form_data["department"] = form_data["department"].replace(" ", "")
    ret = modify_content(form_data)
    if ret == 1:
        logger.info("User " + session.get("name") + " submit modified items")
        return jsonify({"status": 200, "message": "success"})
    else:
        return jsonify({"status": 400, "message": ret})


@DailyReport.route("/del_item", methods=["POST"])
@login_required
def del_item():
    # if session.get("name") is None:
    #     abort(400)
    form_data = json.loads(request.get_data().decode("utf-8"))
    ret = delete_item(form_data)
    if ret == 1:
        logger.info("User " + session.get("name") + " delete items")
        return jsonify({"status": 200, "message": "success"})
    else:
        return jsonify({"status": 400, "message": ret})


@DailyReport.route("/add_new_content", methods=["POST"])
@login_required
def add_new_content():
    # if session.get("name") is None:
    #     abort(400)
    list_form_data = json.loads(request.get_data().decode("utf-8"))
    for form_data in list_form_data:
        form_data["content"] = form_data["content"].replace("\n", "<br>")
        form_data["operator"] = form_data["operator"].replace("\n", "<br>")
        form_data["remark"] = form_data["remark"].replace("\n", "<br>")
        form_data["content"] = form_data["content"].replace("\t", "")
        form_data["operator"] = form_data["operator"].replace("\t", "")
        form_data["remark"] = form_data["remark"].replace("\t", "")
        form_data["uploader"] = session.get("name")
        form_data["department"] = session.get("department")
    ret = create_new_item(list_form_data)
    if ret == 1:
        logger.info("User " + session.get("name") + " add new items")
        return jsonify({"status": 200, "message": "success", "url": "/DailyReport"})
    else:
        return jsonify({"status": 400, "message": ret})


@DailyReport.route("/check_item", methods=["POST"])
@login_required
@authority_required("综合管理部")
def check_item():
    # if session.get("department") != "综合管理部":
    #     abort(400)
    list_form_data = json.loads(request.get_data().decode("utf-8"))
    current_user = session.get("name")
    if list_form_data["type"] == "first_check":
        ret = submit_first_check(list_form_data["check_id"], current_user)
        if ret == 1:
            logger.info("User " + session.get("name") + " submit first_check")
            return jsonify({"status": 200, "message": "success"})
        else:
            return jsonify({"status": 400, "message": ret})
    elif list_form_data["type"] == "double_check":
        ret = submit_double_check(list_form_data["check_id"], current_user)
        if ret == 1:
            logger.info("User " + session.get("name") + " submit double_check")
            return jsonify({"status": 200, "message": "success"})
        else:
            return jsonify({"status": 400, "message": ret})
    else:
        return jsonify({"status": 400, "message": "Bad Request"})


@DailyReport.route("/ExportFile", methods=["POST"])
@login_required
@authority_required("综合管理部")
def get_excel():
    # if session.get("department") != "综合管理部":
    #     abort(400)
    timestamp = request.form.get("timestamp")
    user = session.get("name")
    ret = write_to_workbook(query_data(timestamp), user, timestamp)
    return send_from_directory(r"DailyReport/ExportFile", filename=ret, as_attachment=True)


@DailyReport.route("/SendMessage", methods=["GET", "POST"])
@login_required
@authority_required("综合管理部")
def send_message():
    # if session.get("department") != "综合管理部":
    #     abort(400)
    if request.method == "GET":
        ret = query_mobile()
        return render_template("/DailyReport/send_message.html", user_list=ret)
    elif request.method == "POST":
        form_data = json.loads(request.get_data().decode("utf-8"))
        phone_number_list = form_data[0]
        if len(form_data) > 1:
            for i in range(1, len(form_data)):
                phone_number_list = phone_number_list + ", " + form_data[i]
        payload = {"cid": MessageSetting["cid"], "pass": MessageSetting["pass"],
                   "content": MessageSetting["content"], "mobile": phone_number_list}
        ret = requests.get(MessageSetting["target_url"], params=payload)
        if ret.status_code == 200:
            if ret.json()["status"] == '0':
                logger.info("User " + session.get("name") + " send prompt message to " +
                            phone_number_list)
                return jsonify({"status": 200, "message": "success"})
            else:
                logger.info("User " + session.get("name") + " send prompt message failed, error:" +
                            ret.json()["error"])
                return jsonify({"status": 400, "message": "发送失败"})
        else:
            logger.info("User " + session.get("name") + " send prompt message failed, error: network or server error")
            return jsonify({"status": 400, "message": "发送失败"})


@DailyReport.route("/readme")
def show_readme():
    return render_template("/DailyReport/readme.html")
