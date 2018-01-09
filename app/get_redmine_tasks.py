#!/usr/bin/python3
import sys
import unidecode
from redminelib import Redmine

class RedmineLister:
	def __init__(self, username, password):
		self.url = "https://redmine.bms.com.pl"
		self.username = username
		self.password = password
	
	def get_redmine(self):
		return Redmine(self.url, username=self.username, password=self.password, requests={'verify': False})
	
	def get_statuses(self):
		result = {}
		for i in self.get_redmine().issue_status.all():
			result[i.id] = i
		return result
	
	def get_for_project(self, project_name):
		redmine = self.get_redmine()
		project = redmine.project.get(project_name)
		result = {}
		for i in project.issues:
			iss = redmine.issue.get(i.id, include='journals')
			if not hasattr(iss, "assigned_to"):
				assigned_to = iss.author.id
			else:
				assigned_to = iss.assigned_to.id
			assigned_to = redmine.user.get(assigned_to)
			if "login" in assigned_to._decoded_attrs:
				name = assigned_to._decoded_attrs["login"]
			else:
				name = unidecode.unidecode(assigned_to.firstname.strip().lower()) + "." + unidecode.unidecode(assigned_to.lastname.strip().lower())
			if not name in result:
				result[name] = []
			result[name].append(iss)
		return result

def print_usage():
	print("USAGE: get_redmine_tasks.py USERNAME PASSWORD PROJECT_NAME")
			
def main():
	if len(sys.argv) < 3:
		print_usage()
		sys.exit(1)
	else:
		lister = RedmineLister(sys.argv[1], sys.argv[2])
		print(lister.get_for_project(sys.argv[3]).items())

if __name__ == "__main__":
	main()