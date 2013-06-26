# coding: utf-8

# $Id: $


import os.path
import re
from subprocess import Popen, PIPE
import sys
from bamboo.helpers import cout, cerr


class SVNError(Exception):
    pass


class SVNHelper(object):
    """ Работа с JIRA-задачами в SVN."""

    def __init__(self, project_key, configfile='bamboo.cfg'):
        self.project_key = project_key
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
        sys.stderr.writelines('=' * 40 + '\n')
        p = Popen(args, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode
