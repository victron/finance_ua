# FIN UA
### installation
1. `python3.5 setup.py sdist` **to prepare dist package from sources**
2. install on machine
    * **python3.5**

    `sudo add-apt-repository ppa:fkrull/deadsnakes`

    `sudo apt-get update`

    `sudo apt-get install python3.5`

    `sudo apt-get install python3.5-dev`

    * **install mongodb**
    `sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927`

    `echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list`

    `sudo apt-get update`

    `sudo apt-get install -y mongodb-org`

    * **to start / stop mongod - use upstart**

        `/etc/init.d/mongod`

    * **install virtual environment**

    `wget https://bootstrap.pypa.io/get-pip.py`

    `python3.5 -m venv  --without-pip flask` - create folder 'flask' with virtualenv

    `cd flask; source bin/activate` - activate venv

    `python3.5 get-pip.py` - install pip in invironment

    * **install application**

    `pip install curs-XX.XX.XX.XXXXX.tar.gz`
    it compiler **uwsgi** and **pycrypto** from sources (python3.5-dev)

3. * **start mongod**

        `sudo /etc/init.d/mongod start`

   * **configure nginx and uwsgi**
        * prety working config copied by `pip install` in `.curs` folder.
        need to move in `/etc/nginx/nginx.conf`
        * copy into `/var/www/curs/static/` static files from `app\static`
        * working **uwsgi** config in `.curs` folder, too.
        installed ` bin/uwsgi_start.sh` will find it.
   * **start nginx and uwsgi**
        * `sudo service nginx start`
        * `bin/uwsgi_start.sh`



