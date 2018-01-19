FROM python:3.7.0a4-windowsservercore-ltsc2016

MAINTAINER "Maciej Dłuś" maciej.dlus@bms.com.pl

RUN python -m pip install python-redmine
RUN python -m pip install unidecode
RUN python -m pip install slackclient
RUN python -m pip install python-dateutil

RUN mkdir C:/task_reminder/conf/
VOLUME ["C:/task_reminder/conf/"]

RUN mkdir C:/task_reminder/log/
VOLUME ["C:/task_reminder/log/"]

WORKDIR C:/task_reminder/

COPY app/get_redmine_tasks.py C:/task_reminder/
COPY app/polish_holidays.py C:/task_reminder/
COPY app/slack_task_reminder.py C:/task_reminder/
COPY app/task_reminder.py C:/task_reminder/

COPY reminder-loop.ps1 C:/task_reminder/

CMD ["powershell", "-File", "reminder-loop.ps1"]
