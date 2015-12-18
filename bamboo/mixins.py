# coding: utf-8
import os
import sys
from subprocess import Popen, PIPE

from bamboo.helpers import cerr, query_yes_no


class BuildMixin(object):
    """ Миксин с функциями сборки проектов
    """
    repo_url = 'https://y.rutube.ru/vrepo/'

    def tar(self, archive, chdir, folder, quiet=False):
        args = ('/usr/bin/env', 'tar', 'czf', archive, '-C', chdir, folder)
        return self.execute(args, quiet)

    def execute(self, args, quiet=False):
        if not quiet:
            sys.stderr.write(' '.join(
                '"%s"' % a if ' ' in a else a for a in args[1:]) + '\n')
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        return stdout, stderr, p.returncode

    def upload(self, source, destination, quiet=False, interactive=False):
        args = ('/usr/bin/env', 'curl', '-T', source, destination)
        cerr("Upload command: %s" % ' '.join(args[1:]))
        if interactive and not query_yes_no('upload file?', default='yes'):
            cerr('Aborted')
            return
        return self.execute(args, quiet)