from setuptools import setup

setup(
    name='mpm',
    version='0.1',
    py_modules=['mpm_cli', 'mpm'],
    install_requires=[
        'click',
        'gitpython',
        'pyyaml',
        'tinydb',
    ],
    entry_points='''
        [console_scripts]
        mpm=mpm_cli:init
    ''',
)
