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

def mpm_init(ctx):
    """
    Initialize the mpm database. Called on every command
    issued with mpm. If the file does not already exist,
    create it. Save the database information in the DBWrapper
    class, to be passed to the other commands.
    """
    db_path = os.path.join(os.getcwd(), '.mpm/')
    if not os.path.exists(db_path):
        os.mkdir(db_path)
    db_filepath = os.path.join(db_path, 'mpm-db.yml')
    if not os.path.isfile(db_filepath):
        with open(db_filepath, 'a'):
            pass
    ctx.obj = DBWrapper(db_filepath, YAMLStorage, 'mpm')

def mpm_install(db, remote_url, reference, directory, name):
    """
    Install a module with GitPython using the reference,
    remote_url, directory, and path parameters, then create
    a database entry. If the module already exists in the
    database and the filesystem, do nothing. If the module
    exists in the database but not on the filesytem, reinstall
    the module.
    """
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        if not name:
            # Use the default module name
            module_name = os.path.basename(remote_url).split('.git')[0]
        else:
            # Use the user provided module name
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
    """
    Uninstall a module by name and remove the database entry.
    If no module is found in the database, nothing is uninstalled.
    """
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
    """
    Update a module's git reference and update the database entry.
    If no module is found in the database, nothing is updated.
    """
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

def mpm_load(db, filename, product):
    """
    Installs a module set from a previously created yaml
    file and updates the database. The product string specifies
    which configuration to load within the yaml file, as multiple
    products can be supported per file. If the product does not
    exist in the file, nothing will be loaded.
    """
    if os.path.exists(filename):
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
    else:
        click.echo('File not found!')

def mpm_freeze(db, filename, product):
    """
    Saves the current working module set in the database to an
    output yaml file. The product string specifies which configuration
    to save to within the yaml file, as multiple products can be
    supported per file. If no modules are installed, nothing will be
    frozen.
    """
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
    """
    Deletes all the currently installed modules from the database
    and file system. If the database is empty, nothing will be purged.
    """
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
    """
    Displays all currently installed modules in the database.
    """
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
