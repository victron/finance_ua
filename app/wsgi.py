# test uwsgi
# https://www.digitalocean.com/community/tutorials/how-to-deploy-python-wsgi-applications-using-uwsgi-web-server-with-nginx
# uwsgi --socket 127.0.0.1:8080 --protocol=http -w wsgi
# uwsgi -s /tmp/uwsgi.sock --module /var/www/test.py --callable myapp
# uwsgi -s /tmp/uwsgi.sock -w app:app

def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["Hello!"]
