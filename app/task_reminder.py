#!/usr/bin/python3
import sys
import datetime
import os
import json
from get_redmine_tasks import RedmineLister
from slack_task_reminder import SlackTaskReminder
from polish_holidays import get_holidays

class TaskWaitingForReaction:
    pass

class TaskReminder(object):
    def __init__(self):
        self.user_config_path = "user_config.json"
        self.task_reminder_config_path = "task_reminder_config.json"
        self.log_dir = "."
        self.user_mapping = None
        self.debug = False

    def is_working_day(self, date):
        if date.weekday() > 4:
            return False
        holidays = get_holidays(date.year).values()
        return not date in holidays

    def get_user_mapping(self):
        if not self.user_mapping:
            self.user_mapping = {}
        if os.path.exists(self.user_config_path):
            with open(self.user_config_path, "r") as cfg:
                self.user_mapping = json.load(cfg)
        return self.user_mapping

    def subtract_dates(self, first_date, second_date):
        if first_date == second_date:
            return 0
        dd = 0
        dir = 1 if first_date < second_date else -1
        while first_date != second_date:
            if self.is_working_day(first_date):
                dd += dir
            first_date += datetime.timedelta(days=dir)
        return dd

    def list_tasks(self, username, password, project):
        result = []
        lister = RedmineLister(username, password)
        for i, k in lister.get_for_project(project["name"]).items():
            for j in k:
                jrnls = list(j.journals)
                if len(jrnls) == 0:
                    date = j.start_date
                else:
                    jrnls.sort(key=lambda x: x.created_on, reverse=True)
                    date = jrnls[-1].created_on.date()
                t = TaskWaitingForReaction()
                t.project = j.project_name
                t.subject = j.subject
                t.assigned_to = i
                t.id = j.id
                t.description = j.description
                t.url = lister.url + "/issues/" + str(t.id)
                if hasattr(j, "due_date") and self.subtract_dates(j.due_date, date) < 0:
                    t.due_date = j.due_date
                    t.elapsed_days = None
                    t.overdue = self.subtract_dates(t.due_date, datetime.date.today())
                    result.append(t)
                elapsed_days = self.subtract_dates(date, datetime.date.today())
                if elapsed_days > project["days_limit"]:
                    t.due_date = None
                    t.elapsed_days = elapsed_days
                    result.append(t)
        return result

    def find_slack_user(self, users, login):
        mapping = self.get_user_mapping()
        if login in mapping:
            login = mapping[login]
        for user in users:
            if user["name"] == login:
                return user

    def run(self):
        with open(self.task_reminder_config_path, "r") as cfg:
            reminder_config = json.load(cfg)
        log_filename = "task_reminder_{dd}.log".format(dd=datetime.datetime.today().strftime('%Y%m%d'))
        with open(os.path.join(self.log_dir, log_filename), "a") as fl:
            if self.is_working_day(datetime.date.today()):
                for project in reminder_config["projects"]:
                    tasks = self.list_tasks(reminder_config["redmine_user"], reminder_config["redmine_password"], project)
                    slack = SlackTaskReminder(reminder_config["slack_token"])
                    users = slack.list_users()
                    for i in tasks:
                        slack_user = self.find_slack_user(users, i.assigned_to)
                        # if i.due_date:
                        #     msg = "Task *" + i.subject + "* is should be finished till " + str(i.due_date) + " - " + i.url
                        # else:
                        #     msg = "Task *" + i.subject + "* is waiting for your reaction for " + str(i.elapsed_days) + " days! - " + i.url
                        if slack_user:
                            print("[{dt}] Sending msg to {user}[{user_id}]: {msg}".format(dt=datetime.datetime.now(), user=slack_user["name"], user_id=slack_user["id"], msg=json.dumps(self.prepare_attachment(i))), file=fl)
                            if not self.debug:
                                print("[{dt}] {response}".format(dt=datetime.datetime.now(), response=slack.send_message(slack_user["id"], self.prepare_attachment(i))), file=fl)
                        else:
                            print("[{dt}] Slack user for {user} was not found".format(dt=datetime.datetime.now(), user=i.assigned_to), file=fl)
            else:
                print("[{dt}] Skipping run in not business day".format(dt=datetime.datetime.now()), file=fl)
        with open(os.path.join(self.log_dir, "last_run.log"), "w") as lr:
            print(str(datetime.datetime.now()), file=lr)

    def prepare_attachment(self, task):
        attachment = {}
        attachment["fields"] = []
        if task.due_date:
            attachment["fallback"] = "Overdue task *" + task.subject + "*, should be finished by " + str(task.due_date) + " - " + task.url
            attachment["pretext"] = "Overdue task"
            attachment["fields"].append({"title":"Overdue", "value": str(task.overdue) + " days", "short":"true"})
        else:
            attachment["fallback"] = "Task *" + task.subject + "* is waiting for your reaction for " + str(task.elapsed_days) + " days! - " + task.url
            attachment["pretext"] = "Neglected task"
            attachment["fields"].append({"title":"Last updated", "value": str(task.elapsed_days) + " days ago", "short":"true"})
        attachment["title"] = task.subject
        attachment["title_link"] = task.url
        attachment["text"] = task.description
        attachment["fields"].append({"title":"Project", "value": task.project, "short":"true"})
        attachment["color"] =  "danger"
        return attachment

def main():
    reminder = TaskReminder()
    if len(sys.argv) > 1:
        reminder.user_config_path = sys.argv[1]
    if len(sys.argv) > 2:
        reminder.task_reminder_config_path = sys.argv[2]
    if len(sys.argv) > 3:
        reminder.log_dir = sys.argv[3]
    if len(sys.argv) > 4:
        reminder.debug = sys.argv[4] == "-debug"
    reminder.run()

if __name__ == "__main__":
    main()
