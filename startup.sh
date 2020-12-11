#!/bin/bash
nohup pipenv run uwsgi --ini DailyReport.ini 1>serverlog/server.log 2>&1 &
