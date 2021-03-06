from setuptools import setup, find_packages
# http://python-packaging-user-guide.readthedocs.io/en/latest/distributing/?highlight=package_data#package-data
# http://pythonhosted.org/setuptools/setuptools.html#including-data-files

with open('requirements.txt') as file:
    requirements = file.read().splitlines()

setup(
    # Application name:
    name='curs',

    # Version number (initial):
    version='17.3.8.dev1',

    # Application author details:
    author='Viktor Tsymbalyuk',
    author_email='viktor.tsymbalyuk@gmail.com',

    # Packages
    # packages=['app',
    #           'mongo_collector',
    #           'spiders',
    #           'spiders.simple_encrypt_import',
    #           'tools'],
    packages=find_packages(exclude=('tests',)),


    # Details
    url='https://github.com/victron/finance_ua/',

    #
    # license="LICENSE.txt",
    # description="Useful towel-related stuff.",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    # install_requires=['flask',
    #                   'flask-wtf',
    #                   'flask-login',
    #                   'pymongo',
    #                   'PyYAML',
    #
    #                   'pytz',
    #                   'requests',
    #                   'pycrypto',
    #                   'beautifulsoup4',
    #                   'apscheduler',
    #
    #                   'uwsgi',
    #                   'pandas'
    #                   ],
    install_requires=requirements,
    # install in bin script to start flask web server
    entry_points={
        'console_scripts': [
            'curs=curs.run_flask:main',
            # 'curs_auto = mongo_collector.auto_update:main',
            # 'flask2=flask.fcgi'
        ],
    },

    # This tells setuptools to install any data files it finds in your packages. The data files must be specified via the distutils’ MANIFEST.in file
    include_package_data=True,

    # package_data={
    #     'spiders.simple_encrypt_import': ['secret_data.pye'],
    #     'app.templates': ['*.html'],
    #     'app.static': ['*'],
    # },
    ##################
    # ready scripts
    #################
    scripts=['bin/curs', ],
##############################
    data_files=[
        ('.curs', ['config/flask.cfg', 'config/nginx.conf', 'config/uwsgi.ini', 'config/logging.yml']),
        # ('logs', ['logs/curs.log']),
        # ('.curs', ['config']),
        # ('/etc/init.d', ['init-script'])
                ]
)