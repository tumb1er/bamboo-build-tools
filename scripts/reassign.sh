#!/bin/sh

#
# Переводит задачи обратно на их исполнителей
#
echo "Transitioning tasks..."
cat collected-tasks.txt |xargs -n 1 -I {} task-transition -c /data/bamboo.cfg {} integrated
echo "Assigning tasks..."
cat assignees.txt |xargs -n 2 -I {} echo task-assign -c /data/bamboo.cfg {} | sh