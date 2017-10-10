from setuptools import setup

setup(
    name='mpm',
    version='0.1',
    py_modules=['mpm'],
    install_requires=[
        'click',
        'gitpython',
        'pyyaml',
        'tinydb',
    ],
    entry_points='''
        [console_scripts]
        mpm=mpm:cli
    ''',
)
