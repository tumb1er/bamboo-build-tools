# coding: utf-8

# $Id: $
import re

from jira.client import JIRA
from bamboo.helpers import parse_config


class Tasks(object):
    def __init__(self, configfile='bamboo.cfg'):
        self.jira_user = 'bamboo'
        self.jira_password = 'bamboo'
        self.server_name = 'https://jira.rutube.ru'
        parse_config(self, configfile)
        self.jira = JIRA({'server': self.server_name},
                         basic_auth=(self.jira_user, self.jira_password))

    def get_versions(self, task_key):
        self.issue = self.jira.issue(task_key)
        result = []
        for v in self.issue.fields.fixVersions:
            if v.archived or v.released:
                continue
            version = v.name
            if not re.match(r'^[\d]+\.[\d]+\.[\d]+$', version):
                continue
            result.append(version)
        return result

    def get_transitions(self, task_key):
        return self.jira.transitions(task_key)

    def search_tasks(self, project_key, status=None, issue_type=None,
                     assignee=None, release=None):
        query = "project = %s" % project_key
        if isinstance(status, (tuple, list)):
            statuses = ', '.join('"%s"' % s for s in status)
            query += ' AND status IN (%s)' % statuses
        if isinstance(status, str):
            query += ' AND status = "%s"' % status
        if isinstance(issue_type, (tuple, list)):
            types = ', '.join('"%s"' % t for t in issue_type)
            query += ' AND type IN (%s)' % types
        if isinstance(issue_type, str):
            query += ' AND type = "%s"' % issue_type
        if assignee:
            if assignee == 'currentUser()':
                query += ' AND assignee=currentUser()'
            else:
                query += ' AND assignee="%s"' % assignee
        if release:
            query += ' AND fixVersion="%s"' % release
        return self.jira.search_issues(query)

    def transition(self, task_key, transition_id):
        self.jira.transition_issue(task_key, transition_id)

    def assign(self, task_key, assignee):
        self.jira.assign_issue(task_key, assignee)

    def get_assignee(self, task_key):
        issue = self.jira.issue(task_key)
        return issue.fields.assignee.name

    def task_info(self, task_key):
        issue = self.jira.issue(task_key)
        result = (
            ('key', issue.key),
            ('title', issue.fields.summary),
            ('assignee', issue.fields.assignee.name),
            ('status', issue.fields.status.name),
        )
        return result

    def move(self, task_key, transition_name):
        transition_name = transition_name.lower().replace(' ', '-')
        transitions = self.get_transitions(task_key)
        for trans in transitions:
            name = trans['to']['name'].lower().replace(' ', '-')
            if name == transition_name:
                self.transition(task_key, trans['id'])
                return True
        return False
