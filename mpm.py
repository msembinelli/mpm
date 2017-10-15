import os
import shutil
import sys
import click

from yaml_storage import YAMLStorage
from tinydb import TinyDB, Query
from git import Repo, GitCommandError

class DBWrapper:
    def __init__(self, filepath, storage, table_name):
        self.filepath = filepath
        self.storage = storage
        self.table_name = table_name

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
    if not os.path.isfile(db_filepath):
        with open(db_filepath, 'a'):
            pass
    ctx.obj = DBWrapper(db_filepath, YAMLStorage, 'mpm')

def checkout_helper(remote_url, path, reference):
    if not os.path.exists(os.path.join(path, '.git')):
        Repo.clone_from(remote_url, path)
    repo = Repo(path)
    for remote in repo.remotes:
        remote.fetch()
    try:
        commit_string = 'mpm-' + reference
        branch = repo.create_head(commit_string, reference)
        branch.checkout()
    except GitCommandError as msg:
        print(msg)
    except OSError as msg:
        print(msg)

def mpm_install(db, remote_url, reference, directory, name):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        if not name:
            module_name = os.path.basename(remote_url).split('.git')[0]
        else:
            module_name = name

        module = Query()
        db_entry = mpm_db.get(module.name == module_name)
        full_path = os.path.join(directory, module_name).strip('/')
        new_db_entry = {'name': module_name, 'remote_url': remote_url, 'reference': reference, 'path': full_path.replace(os.path.sep, '/')}
        if db_entry and os.path.exists(os.path.join(db_entry['path'].replace('/', os.path.sep), '.git')):
            click.echo('Already Installed! If you wish to update the branch/reference, use the update command.')
        elif db_entry and not os.path.exists(os.path.join(db_entry['path'].replace('/', os.path.sep), '.git')):
            click.echo('Folder missing, reinstalling ' + module_name + '...')
            checkout_helper(remote_url, full_path, reference)
            mpm_db.update(new_db_entry, module.name == module_name)
        else:
            click.echo('Installing ' + module_name + '...')
            checkout_helper(remote_url, full_path, reference)
            mpm_db.insert(new_db_entry)
            click.echo('Install complete!')

def mpm_uninstall(db, module_name):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        module = Query()
        db_entry = mpm_db.get(module.name == module_name)
        if db_entry:
            click.echo('Uninstalling ' + module_name + '...')
            full_path = db_entry['path'].replace('/', os.path.sep)
            if os.path.exists(full_path):
                shutil.rmtree(full_path, onerror=onerror_helper)
            mpm_db.remove(module.name == module_name)
            click.echo('Uninstall complete!')
        else:
            click.echo('Nothing to uninstall!')


def mpm_update(db, module_name, reference):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        module = Query()
        item = mpm_db.get(module.name == module_name)
        if item:
            click.echo('Updating ' + module_name + '...')
            mpm_db.update({'reference': reference}, module.name == module_name)
            checkout_helper(item['remote_url'], item['path'], reference)
            click.echo('Module reference updated!')
        else:
            click.echo('Module not found!')


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

def mpm_load(db, filename, product):
    with TinyDB(filename, storage=db.storage, default_table=product) as load_db:
        if load_db.all():
            click.echo('Loading modules from file: ' + filename + '...')
            for item in load_db.all():
                name = item['name']
                directory = item['path'].replace('/', os.path.sep).split(os.path.sep)[-2]
                mpm_install(db, item['remote_url'], item['reference'], directory, name)
        else:
            load_db.purge_table(product)
            click.echo('Nothing to load!')
            return

        click.echo('Load complete!')

def mpm_freeze(db, filename, product):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        if not os.path.isfile(filename):
            with open(filename, 'a'):
                pass

        if mpm_db.all():
            click.echo('Freezing installed modules to file... ' + filename)
            with TinyDB(filename, storage=db.storage, default_table=product) as save_db:
                    for item in mpm_db.all():
                        if item not in save_db.table(product):
                            save_db.table(product).insert(item)
        else:
            click.echo('Nothing to freeze!')
            return

        click.echo('Freeze complete!')

def mpm_purge(db):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        if mpm_db.all():
            click.echo('Purging all modules...')
            for item in mpm_db.all():
                mpm_uninstall(db, item['name'])
        else:
            click.echo('Nothing to purge!')
            return

        click.echo('Purging complete!')

def mpm_show(db):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        if mpm_db.all():
            click.echo('\nmodules installed')
        else:
            click.echo('\nno modules installed')

        for entry in mpm_db.all():
            click.echo('-------------------------------------')
            click.echo('name - {}'.format(entry['name']))
            click.echo('url  - {}'.format(entry['remote_url']))
            click.echo('ref  - {}'.format(entry['reference']))
            click.echo('path - {}'.format(entry['path']))
