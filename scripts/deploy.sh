#!/bin/sh

project=${bamboo.ProjectName}
release=${bamboo.deploy.release}
force_stop=${bamboo.ForceStop}

echo "PROJECT: $project"
echo "FORCE STOP: $force_stop"
echo "RELEASE: $release"

cd /data

# Проверяем наличие директории с раскатываемым релизом
if [ -d $release ]; then
    # смотрим, какой релиз активен
    current=`readlink /data/$project`
    if [ $current == '/data/$release' ]; then
        # активен текущий релиз
        if [ $force_stop == 'true' ]; then
            # предварительно останавливаем перекатываемый сервис
            sudo /usr/local/etc/rc.d/$project stop
        else
            # падаем с ошибкой, если нельзя стопить сервис на время раскатки
            echo 'Release is active' >&2
            exit -1
        fi
    fi
    # очищаем директорию с раскатываем релизом
    rm -rf /data/$release
fi

# распаковываем пакет
tar xzof $release.tgz
cd $release

# выполняем Makefile для развертывания виртуального окружения
gmake -e VENV_DIR=virtualenv all

# стопаем предыдущую версию
sudo /usr/local/etc/rc.d/$project stop
# переключаем симлинк на новую версию
[ -d /data/yast ] && rm /data/$project
ln -sf /data/$release /data/$project
# стартуем новую версию
sudo /usr/local/etc/rc.d/$project start

# пишем номер раскатанной версии в файл /data/version.txt
version=`echo $release|awk -F \- '{ print $2"-"$3; }'`
echo $version>/data/version.txt