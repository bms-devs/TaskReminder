FROM python:3.7-rc-slim-stretch

MAINTAINER "Maciej Dłuś" maciej.dlus@bms.com.pl

COPY app/get_redmine_tasks.py /opt/task_reminder/
COPY app/polish_holidays.py /opt/task_reminder/
COPY app/slack_task_reminder.py /opt/task_reminder/
COPY app/task_reminder.py /opt/task_reminder/

RUN python -m pip install python-redmine
RUN python -m pip install unidecode
RUN python -m pip install slackclient
RUN python -m pip install python-dateutil

VOLUME ["/opt/task_reminder/conf/"]
COPY app/task_reminder_config.json /opt/task_reminder/conf/
COPY app/user_config.json /opt/task_reminder/conf/

RUN mkdir /opt/task_reminder/log/
WORKDIR /opt/task_reminder/

VOLUME ["/opt/task_reminder/log/"]

CMD ["python","task_reminder.py","conf/user_config.json","conf/task_reminder_config.json","log"]
