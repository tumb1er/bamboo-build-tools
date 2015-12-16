# coding: utf-8
from bamboo.helpers import parse_config, tuple_version, cerr
import os
import sys
from subprocess import Popen, PIPE


class GitError(Exception):
    pass


class GitHelper(object):
    """ Работа с JIRA-задачами в SVN."""
    FIRST_VERSION = "0.0.0"
    commit_message_filename = 'commit-message.txt'
    smart_commits = (
        (r'\+(review\s[A-Z]+-CR(-[\d]+)?)', r'\1'),
        (r'#(developed|reviewed)', r'\1'),
        (r'@(\w+)', r'\1'),
    )

    def __init__(self, project_key, configfile='bamboo.cfg'):
        self.project_key = project_key
        self.remote_name = "origin"
        self.branches_to_delete = []
        self.repo_url = 'https://y.rutube.ru/vrepo/'
        parse_config(self, configfile)

    def rc_tag(self, version, build_number):
        """ название тега для релиз кандидата """
        return "{version}-{build_number}".format(
            version=version, build_number=build_number)

    def release_tag(self, version):
        """ название тега для финального релиза """
        return version

    def git(self, args, quiet=False):
        if not isinstance(args, tuple):
            args = tuple(args)
        if not quiet:
            cerr('git ' + ' '.join(
                '"%s"' % a if ' ' in a else a for a in args))
        args = (
            ('/usr/bin/env', 'git')
            + args
        )
        p = Popen(args, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            cerr(stderr)
            raise GitError()
        return stdout

    @staticmethod
    def _calc_version(version, previous=True):
        version = tuple_version(version)
        if version <= tuple_version(GitHelper.FIRST_VERSION):
            raise GitError("Invalid vesion number %s" % version)

        if previous:
            operator = lambda a: a - 1
        else:
            operator = lambda a: a + 1

        new_version = list(reversed(version))
        for i, n in enumerate(new_version):
            if n > 0:
                new_version[i] = operator(n)
                break

        return ".".join(str(i) for i in reversed(new_version))

    def previous_version(self, version):
        """ Возвращает предыдущую версию для релиза.
        Например, для релиза 1.0.0 - предыдущая версия 0.0.0
                             1.2.1 - 1.2.0
                             1.2.2 - 1.2.1
                             1.1.0 - 1.0.0
        """
        return self._calc_version(version)

    def next_version(self, version):
        """ Возвращает следующую версию для релиза.
        Например, для релиза 1.0.0 - 2.0.0
                             1.2.1 - 1.2.2
                             1.2.2 - 1.2.3
                             1.1.0 - 1.2.0
        """
        return self._calc_version(version, previous=False)

    def check_version(self, version):
        """ Проверяет, что мы можем собирать указанную версию релиза.
        Например, мы не можем собирать мажор 3.0.0 пока ещё не закрыт мажор
        2.0.0 или когда уже началась сборка мажора 4.0.0

        :param version: версия для проверки
        """
        cerr("Checking version %s before release" % version)
        # не можем собрать тег, если текущая версия уже зарелизена
        if self.find_tags(self.release_tag(version)):
            raise GitError("Cannot add features to %s version because it has "
                           "already released" % version)

        prev_version = self.previous_version(version)
        # Не можем создать релиз, если ещё не зарелизена окончательно предыдущая
        # версия (та, на основе которой мы создаем стейбл), за исключением
        # случаев, если это вообще первая версия
        if (prev_version != GitHelper.FIRST_VERSION and
                not self.find_tags(self.release_tag(prev_version))):
            raise GitError("Cannot create %s release because previous "
                           "%s release does not exist" % (version, prev_version))

        next_version = self.next_version(version)
        # Если для следующей версии (той, что использует тот же стейбл)
        # была уже хоть одна сборка - не можем создать релиз
        if self.find_tags(self.rc_tag(next_version, "*")):
            raise GitError("Cannot create %s release because %s release "
                           "already started" % (version, next_version))
        cerr("Checking complete")

    def is_minor_release(self, version):
        """ Определеяет минорный ли это релиз.
        """
        return tuple_version(version)[1:] > (0, 0)

    def get_stable_branch(self, version):
        """ Возвращает название ветки для сборки релиза
        """
        version = tuple_version(version)

        if not self.is_minor_release(version):
            return "master"
        if version[-1] == 0:
            return "minor/%d.x" % version[0]
        else:
            return "minor/%d.%d.x" % version[:2]

    def get_or_create_stable(self, version, task, interactive=False):
        """ Проверяет наличие или создает ветку, в которую будем собирать
        изменения

        :return: Название ветки стейбла
        """
        branch = self.get_stable_branch(version)

        if not self.git(("branch", "--list", branch)):
            remote_branch = "%s/%s" % (self.remote_name, branch)
            if self.git(("branch", "-r", "--list", remote_branch)):
                # если на сервере уже есть ветка, то будем использовать ей
                start_point = remote_branch
                cerr("Checkout release branch %s for version %s" % (branch, version))
            else:
                # иначе создадим ветку из релиза предыдущей версии
                start_point = self.release_tag(self.previous_version(version))
                cerr("Create release branch %s for version %s" % (branch, version))
            import ipdb; ipdb.set_trace()
            self.git(("checkout", "-b", branch, start_point))

        return branch

    def merge_tasks(self, task_key, tasks, stable_branch):
        """ Мержит задачу из ветки в нужный релиз-репозиторий
        """
        if not tasks:
            raise ValueError('No tasks requested')

        commit_msg = '%s merge tasks %%s' % task_key

        for task in tasks:
            self.checkout(task.key)
            self.checkout(stable_branch)
            # мержим ветку в стейбл
            self.git(("merge", "--no-ff", task.key, "-m", commit_msg % task.key))
            # удаляем ветку сразу после мержа
            self.delete_branch(task.key)

    def find_tags(self, pattern):
        """ Находит все теги для указанного шаблона
        """
        stdout = self.git(("tag", "-l", pattern))
        return stdout.split()

    def get_current_build_number(self, version):
        """ Возвращает текущий номер сборки
        """
        pattern = self.rc_tag(version, "*")
        # текущий - это последний + 1
        tags = [t.replace(pattern, "") for t in self.find_tags(pattern)]
        number_tags = sorted((t for t in tags if t.isdigit()), key=int)
        return int(number_tags[-1]) + 1 if number_tags else 1

    def release_candidate(self, version):
        """ Помечает тегом релиз кандидата коммит текущий коммит.
        """
        tag = self.rc_tag(version, self.get_current_build_number(version))
        self.git(("tag", tag))
        return tag

    def release(self, version, build_number):
        """ Помечает релиз-тегом указанный билд.
        """
        rc_tag = self.rc_tag(version, self.get_current_build_number(version))
        tag = self.release_tag(version)
        self.git(("tag", tag, rc_tag))
        return tag

    def clone(self, repo_url, path):
        """ Клонирует репозиторий по указанному пути
        """
        self.git(("clone", repo_url, path))

    def checkout(self, branch):
        """ Делает checkout указанной ветки
        """
        self.git(("checkout", branch))

    def push(self):
        """ Отправляет изменения на удаленный сервер, включая все теги и
        удаление веток, если нужно
        """
        self.git(("push", "--all"))
        self.git(("push", "--tags"))
        for branch in self.branches_to_delete:
            self.delete_remote_branch(branch)
        self.branches_to_delete = []

    def delete_branch(self, branch, deffer_remote=True):
        """ Удаляет ветку в локальном репе и запоминает, что её
        """
        self.git(("branch", "-d", branch))
        if deffer_remote:
            self.branches_to_delete.append(branch)
        else:
            self.delete_remote_branch(branch)

    def delete_remote_branch(self, branch):
        """ Удаляет ветку в удаленном репозитории
        """
        self.git(("push", self.remote_name, "--delete", branch))