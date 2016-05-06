#!/bin/sh
# start uwsgi for nginx
# config for nginx in .curs
# cd flask
# source bin/activate
cd flask
bin/uwsgi --ini .curs/uwsgi.ini
sleep 3
master=`cat /tmp/uwsgi.pid`
echo "master process on $master"
echo "---------------"
echo "use:"
echo "kill -HUP [PID] gracefully reloads the workers and the application
SIGINT -INT and SIGQUIT -QUIT kills all the workers immediately"

