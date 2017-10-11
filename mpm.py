import os
import shutil
import sys
import hashlib
import click

from yaml_storage import YAMLStorage
from tinydb import TinyDB, Query
from git import Repo, GitCommandError

class DBWrapper:
    def __init__(self, filepath, storage):
        self.filepath = filepath
        self.storage = storage

def mpm_init(ctx):
    """
    A basic package manager for git written in python.
    To provide a simpler approach to including nested
    submodules in large projects.
    """
    db_path = os.path.join(os.getcwd(), '.mpm/')
    if not os.path.exists(db_path):
        os.mkdir(db_path)
    db_filepath = os.path.join(db_path, 'mpm-db.yml')
    with open(db_filepath, 'a'):
        with TinyDB(db_filepath, storage=YAMLStorage) as db:
            pass
    ctx.obj = DBWrapper(db_filepath, YAMLStorage)

def mpm_install(db, url, ref, path):
    repo_name = os.path.basename(url).split('.git')[0]
    full_path = os.path.abspath(os.path.join(os.getcwd(), os.path.join(path, repo_name))).strip('/')
    if not os.path.exists(os.path.join(full_path, '.git')):
        Repo.clone_from(url, full_path)
    repo = Repo(full_path)
    for remote in repo.remotes:
        remote.fetch()
    try:
        commit_string = 'mpm-checkout-' + ref
        branch = repo.create_head(commit_string, ref)
        branch.checkout()
        with TinyDB(db.filepath, storage=db.storage) as db_obj:
            module = Query()
            key = str(hashlib.md5(full_path.encode('utf-8')).hexdigest())
            if db_obj.search(module.reference_md5 == key):
                click.echo('Already Installed!')
            else:
                db_obj.insert({'reference_md5': key, 'data': {'name': repo_name, 'url': url, 'ref': ref, 'path': full_path}})
                click.echo('Install Complete!')
    except GitCommandError as msg:
        print(msg)
    except OSError as msg:
        print(msg)

def mpm_uninstall(db, path):
    full_path = os.path.abspath(os.path.join(os.getcwd(), path)).strip('/')
    if os.path.exists(full_path):
        with TinyDB(db.filepath, storage=db.storage) as db_obj:
            module = Query()
            key = str(hashlib.md5(full_path.encode('utf-8')).hexdigest())
            if db_obj.search(module.reference_md5 == key):
                shutil.rmtree(full_path, onerror=onerror_helper)
                db_obj.remove(module.reference_md5 == key)
                click.echo('Uninstall Complete!')
    else:
        click.echo('Nothing to delete.')

def onerror_helper(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def mpm_freeze(db, file, product):
    pass

def mpm_show(db):
    pass
