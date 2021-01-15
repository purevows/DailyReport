from flask import Flask, redirect, request, session, send_from_directory
from plugin import flask_config, logger
from DailyReport.DailyReport import DailyReport
import json
import os
import requests

web_type = "development"  # development or production
app = Flask(__name__)
app.config.from_object(flask_config[web_type])
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.register_blueprint(DailyReport, url_prefix="/DailyReport")


@app.route("/favicon.ico")
def get_favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                               "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET"])
def login():
    if request.method == "GET":
        token = request.args.get("token")
        if token is None:
            # The request is from user
            if session.get("token") is not None:
                # web server has session
                sso_url = flask_config[web_type].sso_url
                sso_headers = {"Content-Type": "application/json", "Token": session["token"]}
                sso_request_data = {"AppServer": 1001}
                sso_response = requests.post(sso_url + "/login", data=json.dumps(sso_request_data), headers=sso_headers)
                logger.info("Send token:" + session["token"])
                ret = json.loads(sso_response.text)
                if ret["retCode"] == 1:
                    # correct token, login success.
                    logger.info("Login success:" + session["username"] + " from " + request.remote_addr)
                    return redirect("/DailyReport")
                else:
                    if ret["retCode"] == 4:
                        logger.info("Can't match token, login needed:" + session["username"])
                    else:
                        logger.info("Unknown Error:" + session["username"])
                    session.clear()
                    return redirect(sso_url + "/login?AppServer=" + flask_config[web_type].local_url
                                    + "&srv_path=login")
            else:
                # web server doesn't have session
                return redirect(flask_config[web_type].sso_url + "/login?AppServer=" + flask_config[web_type].local_url
                                + "&srv_path=login")
        else:
            # The request is from SSO
            sso_url = flask_config[web_type].sso_url
            sso_headers = {"Content-Type": "application/json", "Token": token}
            sso_request_data = {"AppServer": 1001}
            sso_response = requests.post(sso_url + "/login", data=json.dumps(sso_request_data), headers=sso_headers)
            logger.info("Send token:" + token)
            ret = json.loads(sso_response.text)
            if ret["retCode"] == 1:
                # correct token, login success.
                if (ret["department"] == "规划与建设管理部") | (ret["department"] == "建设公司"):
                    session["department"] = "规划与建设管理部（建设公司）"
                elif (ret["department"] == "资产运营部") | (ret["department"] == "置业公司"):
                    session["department"] = "资产运营部（置业公司）"
                else:
                    session["department"] = ret["department"]
                session["token"] = token
                session["name"] = ret["name"]
                session["username"] = ret["username"]
                logger.info("Login success:" + session["username"] + " from " + request.remote_addr)
                return redirect("/DailyReport")
            else:
                if ret["retCode"] == 4:
                    logger.info("Can't match token, login needed.")
                else:
                    logger.info("Internal Server Error")
                session.clear()
                return redirect(sso_url + "/login?AppServer=" + flask_config[web_type].local_url + "&srv_path=login")


@app.route("/logout")
def logout():
    sso_url = flask_config[web_type].sso_url
    token = session.get("token")
    if token is None:
        return redirect(sso_url + "/login?AppServer=" + flask_config[web_type].local_url + "&srv_path=login")
    session.clear()
    return redirect(sso_url + "/logout?AppServer=" + flask_config[web_type].local_url)


if __name__ == '__main__':
    app.run()
