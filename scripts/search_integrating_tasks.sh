#!/bin/sh
# Ищет в JIRA задачи по текущему проекту
# По-умолчанию ищет задачи типа Development/Bug Ticket/Subtask
# находящиеся в статусе Integrating
#
# Сохраняет задачи в collected-tasks.txt
# а их исполнителей в assignees.txt
#
# Переставляет задачи на JIRA-пользователя, осуществляющего сборку


PROJECT_KEY=`echo $BUILD_KEY|awk '{split($0,a,"-"); print a[1]}'`
task-search $PROJECT_KEY -c /data/bamboo.cfg > collected-tasks.txt
echo "Collected tasks:"
echo "================"
cat collected-tasks.txt
cat >assignees.txt
echo "Saving assignees..."
cat collected-tasks.txt | xargs -n 1 -I {} sh -c 'USER=`task-assign -c /data/bamboo.cfg {}`; echo {} $USER >>assignees.txt'
echo "Assigning to me..."
cat collected-tasks.txt | xargs -n 1 task-assign -c /data/bamboo.cfg -m
echo ===[DONE]===