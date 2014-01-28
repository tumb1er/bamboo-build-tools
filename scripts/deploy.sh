#!/bin/sh
cd /data
[ -d deploy_tmp ] && rm -rf deploy_tmp
mkdir deploy_tmp
project=yast
release=${bamboo.deploy.release}
force_stop=${bamboo.ForceStop}
echo "FORCE STOP: $force_stop"
tar xzof $release.tgz -C deploy_tmp
version=`echo $release|awk -F \- '{ print $2"-"$3; }'`

echo "RELEASE: $release"
if [ -d $release ]; then
    current=`readlink /data/$project`
    if [ $current == '/data/$release' ]; then
        if [ $force_stop == 'true' ]; then
            sudo /usr/local/etc/rc.d/$project stop
        else
            echo 'Release is active' >&2
            exit -1
        fi
    fi
    rm -rf /data/$release
fi


mv deploy_tmp/$release .
cd $release
gmake -e VENV_DIR=virtualenv all
[ -d /data/yast ] && rm /data/$project
sudo /usr/local/etc/rc.d/$project stop
ln -sf /data/$release /data/$project
sudo /usr/local/etc/rc.d/$project start
echo $version>/data/version.txt