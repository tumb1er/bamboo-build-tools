# coding: utf-8

# Готовит bash-скрипт для осуществления сборки релиза
#
# На вход получает следующие файлы:
#   merge-plan.json: словарь {Stable -> {Version -> [task-list]}}
#   integration-tasks.json: словарь {Version -> int-task-key}
#
# На выходе скрипт merge.sh
#

import os
import shutil
import json

f = open('merge-plan.json', 'r')
merge_plan = json.load(f)
f.close()
f = open('integration-tasks.json', 'r')
integration_tasks = json.load(f)
f.close()
package = os.environ['bamboo_Package']
svn_root = os.environ['SVN_ROOT'].replace('/trunk', '')
c = open('merge.sh', 'w')
stable_root = os.path.join(svn_root, 'branches/stable')
for stable, versions in merge_plan.items():
    stable_path = os.path.join(stable_root, stable)
    stable_dir = 'stable-%s' % stable
    try:
        shutil.rmtree(stable_dir)
    except OSError:
        pass
    checked_out = False
    for version, tasks in versions.items():
        int_task = integration_tasks[version]
        if not checked_out:
            c.write("svn-create-stable -t %s %s %s\n" % (svn_root, int_task, stable))
            c.write("svn co %s %s\n" % (stable_path, stable_dir))
            c.write("cd %s\n" % stable_dir)
            checked_out = True
        c.write("yes no | svn-merge-tasks -t %s -i %s %s || exit 252\n" % (svn_root, int_task,
            ' '.join(tasks)))
    c.write("cd ..\n")

rx = "[[:alnum:]]+-[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+-[[:digit:]]+"

for stable, versions in merge_plan.items():
    stable_dir = 'stable-%s' % stable
    c.write("cd %s\n" % stable_dir)
    c.write("svn ci -F commit-message.txt\n")
    for v in versions.keys():
        int_task = integration_tasks[version]
        c.write("svn-release -t %s %s %s\n" % (svn_root, int_task, v))
        c.write("svn-build -t %s %s-%s2>&1 | tail -n1 "
                "| awk -F '/' '{ print $3 }' | "
                "egrep -o '%s' > build.txt\n" %(svn_root, package, v, rx))
        c.write("export VERSION=`cat build.txt`\n")
        c.write('echo "Built $VERSION " > build-message.txt\n"')
        c.write('echo "%s/%s-test.php?release=$VERSION" >> build-message.txt\n'
                % ('http://y.rutube.ru/deploy', package))
        c.write('build-comment $BUILD_KEY -F build-message.txt\n')
    c.write('cd ..\n')
c.close()