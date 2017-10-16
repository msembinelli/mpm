from setuptools import setup

setup(
    name='mpm',
    version='0.2',
    py_modules=['mpm_cli', 'mpm', 'yaml_storage'],
    test_suite='tests',
    install_requires=[
        'click',
        'gitpython',
        'pyyaml',
        'tinydb',
    ],
    entry_points='''
        [console_scripts]
        mpm=mpm_cli:cli
    ''',
)
