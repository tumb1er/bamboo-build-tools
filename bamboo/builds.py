# coding: utf-8

# $Id: $
from copy import copy
import json
from jira.client import JIRA, translate_resource_args
from jira.utils import raise_on_error
from bamboo.helpers import parse_config


class Bamboo(JIRA):

    def __init__(self, server=None, options=None, basic_auth=None, oauth=None,
                 validate=None, async=False, logging=True, max_retries=3):
        headers = copy(JIRA.DEFAULT_OPTIONS['headers'])
        headers.update({'Accept': 'application/json'})
        options = options or {}
        options.setdefault('headers', {})
        options['headers'].update(headers)
        super(Bamboo, self).__init__(server, options, basic_auth, oauth,
                                     validate, async, logging, max_retries)

    def server_info(self):
        info = self._get_json('info')
        info['versionNumbers'] = info['version'].split('.')
        return info


class Builds(object):
    def __init__(self, configfile='bamboo.cfg'):
        self.jira_user = 'stikhonov'
        self.jira_password = '3P2Qsd4f'
        self.server_name = 'http://bamboo.rutube.ru:8085'
        parse_config(self, configfile)
        self.jira = Bamboo(server=self.server_name,
                           options={'rest_api_version': '1.0'},
                           basic_auth=(self.jira_user, self.jira_password))

    @translate_resource_args
    def add_comment(self, build, body):
        data = {
            'author': self.jira_user,
            'content': body
        }
        url = self.jira._get_url('result/' + build + '/comment')
        r = self.jira._session.post(url, headers={'content-type':'application/json'}, data=json.dumps(data))
        raise_on_error(r)

    @translate_resource_args
    def run_plan(self, plan, **extra_variables):
        params = None
        if extra_variables:
            params = {}
            for k, v in extra_variables.items():
                params['bamboo.variable.%s' % k] = v
        url = self.jira._get_url('queue/%s' % plan)
        print "POST %s" % url
        r = self.jira._session.post(url, headers={'content-type':'application/json'},
                                    params=params, data=json.dumps({}))
        raise_on_error(r)
