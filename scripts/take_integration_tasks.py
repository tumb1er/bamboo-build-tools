# coding: utf-8

#
# скрипт, переводящий задачи на интеграцию в статус Integrating и на
# пользователя, из-под которого осуществляется сборка
#
# На входе integration-tasks.json
#

import json
from bamboo.tasks import Tasks
from bamboo.helpers import cerr

jira = Tasks(configfile='/data/bamboo.cfg')
f = open('integration-tasks.json', 'r')
integration_tasks = json.load(f)
f.close()

for task_key in integration_tasks.values():
    info = dict(jira.task_info(task_key))
    if info['status'] != 'Integrating':
        cerr('Taking task %s' % task_key)
        transitions = jira.get_transitions(task_key)
        for trans in transitions:
            name = trans['to']['name'].lower().replace(' ', '-')
            print name
            if name == 'integrating':
                print "Transition to %s" % name
                jira.transition(task_key, trans['id'])
    elif info['assignee'] != 'bamboo':
        cerr('Assigning %s to me' % task_key)
        jira.assign(task_key, 'bamboo')
