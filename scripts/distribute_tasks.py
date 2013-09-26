# coding: utf-8

# Распределяет задачи по stable
#
# На вход получает файл collected-tasks.txt
# Дампит в JSON следующие файлы
#   merge-plan.json: словарь {Stable -> {Version -> [task-list]}}
#   integration-tasks.json: словарь {Version -> int-task-key}


import sys
import os
import json
from pprint import pprint
from bamboo.tasks import Tasks
from bamboo.helpers import get_stable, cerr

project_key = os.environ['BUILD_KEY'].split('-')[0]
print "Project key:", project_key
jira = Tasks(configfile='/data/bamboo.cfg')
with open('collected-tasks.txt', 'r') as f:
    all_stables = dict()
    version_int_tasks = dict()
    for line in f.readlines():
        task_key = line.strip()
        versions = jira.get_versions(task_key)
        stables = {v: get_stable(v) for v in versions}
        if len(set(stables.values()))!=len(versions):
            cerr('Incorrect versions and stables for %s' % task_key)
            cerr('Versions: %s' % ', '.join('%s: %s' % (k, v) for k, v in stables.items()))
            sys.exit(-1)
        for v, s in stables.items():
            all_stables.setdefault(s, {})
            all_stables[s].setdefault(v, [])
            all_stables[s][v].append(task_key)
            version_int_tasks[v] = None
print "Merging plan:"
pprint(all_stables)
plan = open('merge-plan.json', 'w')
json.dump(all_stables, plan)
plan.close()
for v in version_int_tasks.keys():
    tasks = jira.search_tasks(
        project_key, 
        issue_type="Intergration Ticket", 
        release=v)
    if not tasks:
        cerr('No integration ticket for %s' % v)
        sys.exit(-2)
    version_int_tasks[v] = tasks[0].key
print "Integration tickets:"
pprint(version_int_tasks)    
tasks = open('integration-tasks.json', 'w')
json.dump(version_int_tasks, tasks)
plan.close()

