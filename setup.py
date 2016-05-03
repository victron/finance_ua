from setuptools import setup

setup(
    # Application name:
    name='curs',

    # Version number (initial):
    version='16.05.01.dev1',

    # Application author details:
    author='Viktor Tsymbalyuk',
    author_email='viktor.tsymbalyuk@gmail.com',

    # Packages
    packages=['app',
              'mongo_collector',
              'spiders',
              'spiders.simple_encrypt_import'],

    # Include additional files into the package
    # include_package_data=True,

    # Details
    url='https://github.com/victron/finance_ua/',

    #
    # license="LICENSE.txt",
    # description="Useful towel-related stuff.",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=['flask',
                      'flask-wtf',
                      'flask-login',
                      'flask-pymongo',

                      'pytz',
                      'requests',
                      'pycrypto',
                      'beautifulsoup4'



    ],
    entry_points={
        'console_scripts': [
            'flask=app.run_flask:main',
            # 'flask2=flask.fcgi'
        ],
    },

    scripts=['bin/lighttpd.fcgi'],

    package_data={
        'spiders.simple_encrypt_import': ['secret_data.pye'],
    },

    data_files=[('.curs', ['config/flask.cfg']),
                # ('/etc/init.d', ['init-script'])
                ]
)