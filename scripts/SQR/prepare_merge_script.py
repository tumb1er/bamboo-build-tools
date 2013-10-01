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

rx = "[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+-[[:digit:]]+"
srx = "s/\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)-\([0-9]*\)/\\\\1_\\\\2_\\\\3-\\\\4/g"
for stable, versions in merge_plan.items():
    stable_dir = 'stable-%s' % stable
    c.write("cd %s\n" % stable_dir)
    c.write("svn ci -F commit-message.txt\n")
    for v in versions.keys():
        int_task = integration_tasks[version]
        plan_name = int_task.split('-')[0] + '-INT'
        c.write("svn-release -t %s %s %s 2>&1 "
                "| grep Copying | awk '{ print \$4 }' "
                """| awk -F / '{print \$7"-"\$8}' >build.txt\n""" % (svn_root, int_task, v))
        c.write("cat build.txt\n")
        c.write("export PACKAGE=%s-\`cat build.txt\`\n" % package)
        c.write("ln -sf /data/settings_local_squirrel.py ../settings_local.py\n")
        c.write("gmake build-packages\n")
        c.write("export VERSION=\`cat build.txt\`\n")
        c.write('echo "Built \$VERSION " > build-message.txt\n')
        c.write('echo "%s/%s-test.php?release=tags-release-\$VERSION" | sed -e "%s" >> build-message.txt\n'
                % ('http://y.rutube.ru/deploy', package, srx))
        c.write('echo "Commenting \$BUILD_KEY"\n')
        c.write('build-comment -c /data/bamboo.cfg %s-\$BUILD_NUMBER -F build-message.txt\n' % plan_name)
    c.write('cd ..\n')
c.close()
