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
		for i, v in lister.get_for_project(project["name"]).items():
			for j in v:
				jrnls = list(j.journals)
				if len(jrnls) == 0:
					date = j.start_date
				else:
					jrnls.sort(key=lambda x: x.created_on, reverse=True)
					date = jrnls[-1].created_on.date()
				t = TaskWaitingForReaction()
				t.subject = j.subject
				t.assigned_to = i
				t.id = j.id
				t.url = lister.url + "/issues/" + str(t.id)
				if hasattr(j, "due_date") and self.subtract_dates(date, j.due_date) < 0:
					t.due_date = j.due_date
					t.elapsed_days = None
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
			for project in reminder_config["projects"]:
				tasks = self.list_tasks(reminder_config["redmine_user"], reminder_config["redmine_password"], project)
				slack = SlackTaskReminder(reminder_config["slack_token"])
				users = slack.list_users()
				for i in tasks:
					slack_user = self.find_slack_user(users, i.assigned_to)
					if i.due_date:
						msg = "Task *" + i.subject + "* is should be finished till " + str(i.due_date) + " - " + i.url
					else:
						msg = "Task *" + i.subject + "* is waiting for your reaction for " + str(i.elapsed_days) + " days! - " + i.url
					print("[{dt}] Sending msg to {user}[{user_id}]: {msg}".format(dt=datetime.datetime.now(), user=slack_user["name"], user_id=slack_user["id"], msg=msg), file=fl)
					if not self.debug:
						slack.send_message(slack_user["id"], msg)
		with open(os.path.join(self.log_dir, "last_run.log"), "w") as lr:
			print(str(datetime.datetime.now()), file=lr)
	
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