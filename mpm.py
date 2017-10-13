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

def mpm_install(db, remote_url, reference, directory, name, update):
    if not name:
        repo_name = os.path.basename(remote_url).split('.git')[0]
    else:
        repo_name = name

    click.echo('Installing ' + repo_name + ' ...')

    full_path = os.path.abspath(os.path.join(os.getcwd(), os.path.join(directory, repo_name))).strip('/')
    if not os.path.exists(os.path.join(full_path, '.git')):
        Repo.clone_from(remote_url, full_path)
    repo = Repo(full_path)
    for remote in repo.remotes:
        remote.fetch()
    try:
        commit_string = 'mpm-' + reference
        branch = repo.create_head(commit_string, reference)
        branch.checkout()
        db_entry = {'name': repo_name, 'remote_url': remote_url, 'reference': reference, 'path': full_path.replace(os.path.sep, '/')}
        with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as db_obj:
            module = Query()
            if db_obj.search(module.name == repo_name) and db_obj.all():
                if update:
                    db_obj.update({'reference': reference}, module.name == repo_name)
                    click.echo('Reference Updated!')
                else:
                    click.echo('Already Installed! If you wish to update the branch/reference, use the -u option.')
            else:
                db_obj.insert(db_entry)
                click.echo('Install complete!')
    except GitCommandError as msg:
        print(msg)
    except OSError as msg:
        print(msg)

def mpm_uninstall(db, module_name):
    click.echo('Uninstalling ' + module_name + ' ...')
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as db_obj:
        module = Query()
        [db_entry] = db_obj.search(module.name == module_name)
        full_path = db_entry['path'].replace('/', os.path.sep)
        if db_entry and os.path.exists(full_path):
            shutil.rmtree(full_path, onerror=onerror_helper)
            db_obj.remove(module.name == module_name)
            click.echo('Uninstall complete!')
        else:
            click.echo('Nothing to delete or module not found.')

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
    click.echo('Loading modules from file... ' + filename)
    with TinyDB(filename, storage=db.storage, default_table=product) as load_db:
        for item in load_db.all():
            name = item['name']
            directory = item['path'].replace('/', os.path.sep).split(os.path.sep)[-2]
            mpm_install(db, item['remote_url'], item['reference'], directory, name, True )
    click.echo('Load complete!')

def mpm_freeze(db, filename, product):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as db_obj:
        if not os.path.isfile(filename):
            with open(filename, 'a'):
                pass
        click.echo('Saving modules to file... ' + filename)
        with TinyDB(filename, storage=db.storage, default_table=product) as save_db:
            for item in db_obj.all():
                if item not in save_db.table(product):
                    save_db.table(product).insert(item)
    click.echo('Save complete!')


def mpm_show(db):
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as db_obj:
        if db_obj.all():
            click.echo('\nmodules installed')
        else:
            click.echo('\nno modules installed')
        for entry in db_obj.all():
            click.echo('-------------------------------------')
            click.echo('name - {}'.format(entry['name']))
            click.echo('url  - {}'.format(entry['remote_url']))
            click.echo('ref  - {}'.format(entry['reference']))
            click.echo('path - {}'.format(entry['path']))
