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

    `python3.5 get-pip.py`

    `python3.5 -m venv  --without-pip flask` - create folder 'flask' with virtualenv



