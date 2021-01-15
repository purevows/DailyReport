FROM python:latest

MAINTAINER gzlujiantao

COPY requirements.txt ./
# COPY DailyReport.ini ./
# COPY server ./server

RUN ["/bin/bash", "-c", "useradd -u 1000 -m -s /bin/bash dockeruser"]
RUN ["/bin/bash", "-c", "pip install --no-cache-dir -r requirements.txt"]

WORKDIR /usr/src/app

# VOLUME /usr/src/app/serverlog /usr/src/app/server/DailyReport/ExportFile
VOLUME /usr/src/app

USER dockeruser

EXPOSE 8000

CMD ["/bin/bash", "-c", "uwsgi --ini DailyReport.ini 1>serverlog/server.log 2>&1"]
