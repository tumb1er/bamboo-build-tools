# coding: utf-8

# $Id: $


import os.path
import re
from subprocess import Popen, PIPE
import sys
from bamboo.helpers import cout, cerr, query_yes_no


class SVNError(Exception):
    pass


class SVNHelper(object):
    """ Работа с JIRA-задачами в SVN."""

    stable_dir = 'branches/stable'

    def __init__(self, project_key, configfile='bamboo.cfg', root='^'):
        self.project_key = project_key
        self.project_root = root
        self.parse_config(configfile)

    def parse_config(self, configfile):
        filename = os.path.abspath(configfile)
        if os.path.exists(filename) and os.path.isfile(filename):
            config_locals = {}
            execfile(filename, locals=config_locals)
            self.__dict__.update(config_locals)

    def log_tasks(self, revision, branch='^/trunk'):
        args = (
            'log',
        )
        if revision:
            args += (
                '-r',
                '%s:HEAD' % revision,
            )
        args += (branch,)
        cerr("Running svn client")
        stdout, stderr, return_code = self.execute(args)
        cerr("Collecting tasks")
        if return_code != 0:
            raise SVNError(stderr)

        tasks = dict()
        last_rev = None
        for line in stdout.splitlines():
            m = re.match(r'^r([\d]+) \|', line)
            if m:
                last_rev = int(m.group(1))
                continue
            m = re.match(r'^%s-([\d]+)' % self.project_key, line)
            if not m:
                continue
            task = int(m.group(1))
            tasks.setdefault(task, [])
            tasks[task].append(last_rev)
        return tasks

    def print_logged_tasks(self, tasks):
        task_keys = sorted(tasks.keys())
        cout("collected:", ','.join('%s-%s' % (self.project_key, t)
                                    for t in task_keys))
        cout()
        for task in task_keys:
            revisions = map(str, sorted(tasks[task]))
            cout('%s-%s: %s' % (self.project_key, task, ','.join(revisions)))

    def execute(self, args):
        args = ('/usr/bin/env', 'svn') + args
        sys.stderr.write(' '.join(args[1:]) + '\n')
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def create_stable(self, stable, task, branch=None, interactive=False):
        stable_path = os.path.join(self.project_root, self.stable_dir, stable)
        args = ('info', stable_path)
        cerr("Checking stable existance")
        stdout, stderr, return_code = self.execute(args)
        if return_code == 0:
            cerr("Stable already exists")
            return
        parts = stable.split('.')
        if parts[1] == 'x':
            source = os.path.join(self.project_root, 'trunk')
            cerr("Major stable %s assumed created from %s" % (stable, source))
        elif parts[2] == 'x':
            source = os.path.join(self.project_root, self.stable_dir,
                                  '%s.x' % parts[0])
            cerr("Minor stable %s assumed created from %s" % (stable, source))
        else:
            source = os.path.join(self.project_root, self.stable_dir,
                                  '%s.%s.x' % (parts[0], parts[1]))
            cerr("Sub-minor stable %s assumed created from %s" % (
                stable, source))
        if not source.endswith('trunk'):
            cerr("Checking source existance")
            args = ('info', source)
            stdout, stderr, return_code = self.execute(args)
            if return_code != 0:
                raise ValueError("Source for stable does not exists")

        args = (
            'cp',
            source,
            stable_path,
            '-m',
            '"%s - create stable %s"' % (task, stable)
        )
        if interactive:
            cerr('SVN command:')
            cerr('svn ' + ' '.join(args))
            do = query_yes_no('commit?', default='yes')
            if not do:
                cerr('Aborted')
                sys.exit(0)
        cerr("Copying files to stable dir")
        self.execute(args)


