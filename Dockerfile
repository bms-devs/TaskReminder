FROM 3.7.0a3-alpine3.7

RUN mkdir /opt/task_reminder

ADD app /opt/task_reminder/bin

