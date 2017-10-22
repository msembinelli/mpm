from setuptools import setup

setup(
    name='mpm',
    version='0.2',
    py_modules=['mpm_cli', 'mpm', 'mpm_yaml_storage', 'mpm_helpers'],
    test_suite='mpm_test',
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
