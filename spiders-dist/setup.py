from setuptools import setup, find_packages
# logging.basicConfig(level=logging.INFO)
# http://python-packaging-user-guide.readthedocs.io/en/latest/distributing/?highlight=package_data#package-data
# http://pythonhosted.org/setuptools/setuptools.html#including-data-files


with open('requirements.txt') as file:
    requirements = file.read().splitlines()

setup(
    # Application name:
    name='spiders',

    # Version number (initial):
    version='17.03.02.dev1',

    # Application author details:
    author='Viktor Tsymbalyuk',
    author_email='viktor.tsymbalyuk@gmail.com',

    # Packages
    # packages=['',
    #           # '',
    #           # 'mongo_collector',
    #           # 'spiders',
    #           # 'simple_encrypt_import',
    #           # 'tools'
    #           ],

    packages = find_packages(exclude=('tests',)),
    # package_dir = {'': 'src'},

    # Details
    url='https://github.com/victron/finance_ua/',

    #
    # license="LICENSE.txt",
    # description="Useful towel-related stuff.",

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    # or in requirements.txt
    install_requires = requirements,
    # install_requires=['falcon',
    #                   'pymongo',
    #                   'PyYAML',
    #
    #                   'pytz',
    #                   'requests',
    #                   'pycrypto',
    #                   'beautifulsoup4',
    #                   # 'apscheduler',
    #
    #                   'uwsgi',
    #                   # 'pandas'
    #                   ],
    # install in bin script to start flask web server
    # entry_points={
    #     'console_scripts': [
    #         'flask=app.run_flask:main',
    #         'curs_auto = mongo_collector.auto_update:main',
    #         # 'flask2=flask.fcgi'
    #     ],
    # },

    # This tells setuptools to install any data files it finds in your packages.
    # The data files must be specified via the distutils’ MANIFEST.in file
    include_package_data=True,

    # package_data={
    #     'spiders.simple_encrypt_import': ['secret_data.pye'],
    #     'app.templates': ['*.html'],
    #     'app.static': ['*'],
    # },
    # scripts=['bin/spiders', ],

    data_files=[
        ('.spiders', ['./config/uwsgi.ini',
                      'config/logging.yml'
                      ]),
        ('bin', ['bin/geckodriver',
                 'bin/chromedriver']),
        # ('.curs', ['config']),
        # ('/etc/init.d', ['init-script'])
                ]
)