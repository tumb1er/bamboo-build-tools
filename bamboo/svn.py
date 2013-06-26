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
    commit_message_filename = 'commit-message.txt'

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
        args = ('log',)
        if revision:
            args += ('-r', '%s:HEAD' % revision)
        else:
            args += ('-l', '100')
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
            m = re.match(r'^%s-([\d]+) (.*)' % self.project_key, line)
            if not m:
                continue
            task = int(m.group(1))
            message = m.group(2)
            tasks.setdefault(task, [])
            tasks[task].append((last_rev, message))
        return tasks

    def print_logged_tasks(self, tasks):
        task_keys = sorted(tasks.keys())
        cout("collected:", ','.join('%s-%s' % (self.project_key, t)
                                    for t in task_keys))
        cout()
        for task in task_keys:
            revisions = map(lambda item: str(item[0]), sorted(tasks[task]))
            cout('%s-%s: %s' % (self.project_key, task, ','.join(revisions)))

    def execute(self, args, quiet=False):
        args = ('/usr/bin/env', 'svn') + args
        if not quiet:
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
        if branch:
            cerr('Source overriden from command line: %s' % branch)
            source = branch
        if not source.endswith('trunk'):
            cerr("Checking source existance")
            args = ('info', source)
            stdout, stderr, return_code = self.execute(args)
            if return_code != 0:
                raise SVNError("Source for stable does not exists")

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
            if not query_yes_no('commit?', default='yes'):
                cerr('Aborted')
                sys.exit(0)
        cerr("Copying files to stable dir")
        stdout, stderr, return_code = self.execute(args)
        if return_code != 0:
            raise SVNError(stderr)

    def merge_tasks(self, task_key, tasks, branch='trunk', interactive=False):
        if not tasks:
            raise ValueError('No tasks requested')
        cerr('Cleaning working copy')
        args = ('revert', '-R', '.')
        stdout, stderr, return_code = self.execute(args)
        if return_code != 0:
            raise SVNError(stderr)
        cerr('Updating from SVN')
        args = ('up',)
        stdout, stderr, return_code = self.execute(args)
        if return_code != 0:
            raise SVNError(stderr)
        with open(self.commit_message_filename, 'w+') as commit_msg_file:
            commit_msg_file.write(
                '%s merge tasks %s\n' % (task_key, ','.join(tasks)))
            source = os.path.join(self.project_root, branch)
            commit_msg_file.write('Request revisions from %s:\n' % source)
            logged = self.log_tasks(None, branch=source)
            collected = ['%s-%s' % (self.project_key, t) for t in logged.keys()]
            not_found = set(tasks) - set(collected)
            if not_found:
                cerr('These tasks not found in SVN log:', ','.join(not_found))
                cerr('collected tasks:', ','.join(collected))
                raise SVNError('not all tasks collected')
            cerr('Merging with svn merge --non-interactive -c $REV')
            revisions = []
            for t, revs in logged.items():
                for r, msg in revs:
                    revisions.append((r, t, msg))
            revisions = sorted(revisions, key=lambda item: item[0])
            for r, t, msg in revisions:
                jira_task = '%s-%s' %(self.project_key, t)
                if jira_task not in tasks:
                    continue
                commit_msg_file.write(
                    'r%s %s %s\n' % (r, jira_task, msg))

                args = ('merge', '--non-interactive', '-c', 'r%s' % r, source)
                self.execute(args, quiet=True)
            commit_msg_file.flush()
            commit_msg_file.seek(0)
            merged = []
            for line in commit_msg_file.readlines():
                m = re.match(r'^r[\d]+ ([A-Z]+-[\d]+)', line)
                if not m:
                    continue
                merged.append(m.group(1))
            not_merged = set(tasks) - set(merged)
            if not_merged:
                cerr('These tasks not merged:', ','.join(not_merged))
                cerr('Merged tasks:', ','.join(merged))
                raise SVNError('not all tasks merged')

        cerr('Checking merge result')
        args = ('st',)
        stdout, stderr, return_code = self.execute(args)
        for line in stdout.splitlines():
            if 'C' in line[:8]:
                raise SVNError('Conflict found')
        if return_code != 0:
            raise SVNError(stderr)

        args = ('ci', '-F', self.commit_message_filename)
        if interactive:
            cerr('SVN command:')
            cerr('svn ' + ' '.join(args))
            if not query_yes_no('commit?', default='yes'):
                cerr('Aborted')
                sys.exit(0)
        cerr("Committing merge to SVN")
        stdout, stderr, return_code = self.execute(args)
        if return_code != 0:
            raise SVNError(stderr)



