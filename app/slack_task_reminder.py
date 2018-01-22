#!/usr/bin/python
from slackclient import SlackClient
import json

class SlackTaskReminder(object):
	def __init__(self, token):
		self._sc = SlackClient(token)
		self.name = "task_reminder"
		
	def list_users(self):
		return self._sc.api_call(
			"users.list"
		)["members"]
	
	def send_message(self, channel_id, attachment):
		attachments = []
		attachments.append(attachment)
		return self._sc.api_call(
			"chat.postMessage",
			channel=channel_id,
			text="*Task requires your attention!!!*",
			attachments = json.dumps(attachments),
			username=self.name
		)