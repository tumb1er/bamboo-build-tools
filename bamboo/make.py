# coding: utf-8

# $Id: $
import os.path
from bamboo.helpers import cerr


class MakeRunner(object):
    """ Запускает make с параметрами на основе конфига:

    # списки имен файлов зависимостей pip по типам
    requires = {
        'DEPLOY': ('requires.part1.txt', 'requires.part2.txt'),
        'DEVEL': ('requires.dev.txt'),
        'TEST': ('requires.test.txt')
    }

    # список подключаемых файлов проекта для make
    include = ('include1.mk', 'include2.mk')

    # список дополнительных целей make, выполняемых после раскатки
    extra_targets = {
        'PRODUCTION': (),
        'DEVEL': (),
        'TEST': (),
    }
    """

    test_tools = (
        'nose',
        'coverage',
        'unittest-xml-reporting',
        'django_nose'
    )

    def parse_config(self, configfile):
        filename = os.path.abspath(configfile)
        if os.path.exists(filename) and os.path.isfile(filename):
            config_locals = {}
            execfile(filename, locals=config_locals)
            self.__dict__.update(config_locals)

    def __init__(self, project_name, configfile='bamboo.cfg', sources=None,
                 local_venv=False, gmake=False):
        self.requires = {}
        self.make = 'gmake' if gmake else 'make'
        self.include = ()
        self.extra_targets = {}

        self.parse_config(configfile)

        self.project_name = project_name
        self.makefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'Makefile')
        self.sources = sources
        self.local_venv = local_venv

    def insert_requires(self, make_args, requires_type, requires_var):
        requires = self.requires.get(requires_type, ())
        if requires:
            make_args += (
                '-e',
                '%s="%s"' % (requires_var, ' '.join(requires))
            )
        return make_args

    def insert_include(self, make_args):
        if self.include:
            make_args += (
                '-e',
                'PROJECT_MK="%s"' % ' '.join(self.include)
            )
        return make_args

    def insert_targets(self, make_args, target_type, target_var):
        targets = self.extra_targets.get(target_type, ())
        if targets:
            make_args += (
                '-e',
                'POST_DEPLOY_%s_TARGETS="%s"' % (target_var, ' '.join(targets))
            )
        return make_args

    def make_args(self, target):
        make_args = (
            self.make,
            target,
            '-f',
            self.makefile,
            '-e',
            'PROJECT_NAME=%s' % self.project_name,
        )
        if self.sources:
            make_args += ('-e', 'SOURCES_DIR="%s"' % self.sources)
        if self.local_venv:
            make_args += ('-e', 'VENV_DIR=./virtualenv')
        return make_args

    def install_production(self):
        make_args = self.make_args('deploy-admin')
        make_args = self.insert_include(make_args)
        make_args = self.insert_requires(make_args, 'DEPLOY', 'REQUIRES')
        make_args = self.insert_targets(make_args, 'PRODUCTION', 'ADMIN')
        self.execute_make(make_args)

    def install_devel(self):
        make_args = self.make_args('deploy-devel')
        make_args = self.insert_include(make_args)
        make_args = self.insert_requires(make_args, 'DEPLOY', 'REQUIRES')
        make_args = self.insert_requires(make_args, 'DEVEL', 'REQUIRES_DEV')
        make_args = self.insert_targets(make_args, 'DEVEL', 'DEVEL')
        self.execute_make(make_args)

    def execute_make(self, make_args):
        cerr(' '.join(make_args))
        cerr('=' * 40)
        os.execv('/usr/bin/env', (self.make,) + make_args)

    def install_test(self):
        make_args = self.make_args('deploy-test')
        make_args = self.insert_include(make_args)
        make_args = self.insert_requires(make_args, 'DEPLOY', 'REQUIRES')
        make_args = self.insert_requires(make_args, 'TEST', 'REQUIRES_TEST')
        make_args = self.insert_targets(make_args, 'TEST', 'TEST')
        self.execute_make(make_args)

    def install_test_tools(self):
        args = (
            'env',
            'pip',
            'install',
        ) + self.test_tools
        os.execv('/usr/bin/env', args)

    def run_django_tests(self, coverage=False):
        make_args = self.make_args('test-django')
        if coverage:
            make_args += ('-e', 'WITH_COVERAGE=true')
        self.execute_make(make_args)

