import os
import shutil
import sys
import click

from yaml_storage import YAMLStorage
from tinydb import TinyDB, Query
from git import Repo, GitCommandError, RemoteProgress

class MPMMetadata:
    """
    Contains the path, storage type, and default table name for
    the internal database.
    """
    def __init__(self, filepath, storage, table_name, gitignore_name):
        self.filepath = filepath
        self.storage = storage
        self.table_name = table_name
        self.gitignore_name = gitignore_name

def is_local_commit_helper(repo, reference):
    """
    Tests if a branch or sha is local.
    """
    if not repo.git.execute(['git', 'branch', '-r', '--contains', reference]):
        return True
    for head in repo.heads:
        if reference == head.name:
            return True

def checkout_helper(remote_url, reference, path):
    """
    Checkout helper used by the install and update commands.
    Uses GitPython to clone and checkout a git repo from
    a given URL and remote reference (SHA). Before checking out
    a fetch is issued on all remote upstream branches to ensure
    the latest changes are downloaded.
    """
    if not os.path.exists(os.path.join(path, '.git')):
        repo = Repo.clone_from(remote_url, path)
    else:
        repo = Repo(path)

    repo.git.execute(['git', 'fetch', '--all', '-v'])

    if is_local_commit_helper(repo, reference):
        click.echo(('\nWARNING: Your reference is being set to a local branch or commit.\n'
                    'If you check-in a yaml file containing a local reference,\n'
                    'it will not be properly resolved when someone reloads the\n'
                    'yaml file with a fresh clone of the repo. It is suggested you\n'
                    'only commit local references if you are creating a draft commit.\n'))
    repo.git.checkout(reference)

def yaml_to_path_helper(yaml_path):
    """
    Replace forward slashes with current OS path separater.
    """
    return yaml_path.replace('/', os.path.sep)

def path_to_yaml_helper(yaml_path):
    """
    Replace current OS path separater with forward slashes.
    """
    return yaml_path.replace(os.path.sep, '/')

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

def add_to_gitignore_helper(gitignore_filename, entry_string):
    """
    Checks if the entry_string exists in gitignore. If it
    doesn't, this function will add it.
    """
    entry_forward_slash = path_to_yaml_helper(entry_string).strip('/') + '/'
    create_gitignore_entry = False
    with open(gitignore_filename, 'r') as gitignore_file:
        if entry_forward_slash not in gitignore_file.read():
            create_gitignore_entry = True
    # Add path to .gitignore
    if create_gitignore_entry:
        with open(gitignore_filename, 'a+') as gitignore_file:
            gitignore_file.write('\n' + entry_forward_slash)

def mpm_init(ctx, db_table='mpm', db_path='.mpm/', db_filename='mpm-db.yml', db_storage=YAMLStorage, gitignore='.gitignore'):
    """
    Initialize the mpm database. Called on every command
    issued with mpm. If the file does not already exist,
    create it. Save the database information in the DBWrapper
    class, to be passed to the other commands.
    """
    if not os.path.exists(db_path):
        os.mkdir(db_path)
    db_filepath = os.path.join(db_path, db_filename)

    # Create files if they don't already exist
    with TinyDB(db_filepath, storage=db_storage, default_table=db_table):
        pass
    with open(gitignore, 'a+'):
        pass

    add_to_gitignore_helper(gitignore, db_path)

    ctx.obj = MPMMetadata(db_filepath, db_storage, db_table, gitignore)
    return ctx.obj

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
        full_path = os.path.join(directory, module_name)
        add_to_gitignore_helper(db.gitignore_name, full_path)
        full_path = full_path.strip(os.path.sep)
        new_db_entry = {'name': module_name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}
        if db_entry and os.path.exists(os.path.join(yaml_to_path_helper(db_entry['path']), '.git')):
            click.echo('Already Installed! If you wish to update the branch/reference, use the update command.')
        elif db_entry and not os.path.exists(os.path.join(yaml_to_path_helper(db_entry['path']), '.git')):
            click.echo('Folder missing, reinstalling ' + module_name + '...')
            checkout_helper(remote_url, reference, full_path)
            mpm_db.update(new_db_entry, module.name == module_name)
        else:
            click.echo('Installing ' + module_name + '...')
            checkout_helper(remote_url, reference, full_path)
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
            full_path = yaml_to_path_helper(db_entry['path'])
            if os.path.exists(full_path):
                shutil.rmtree(full_path, onerror=onerror_helper)
            mpm_db.remove(module.name == module_name)
            click.echo('Uninstall complete!')
        else:
            click.echo('Nothing to uninstall!')


def mpm_update(db, module_name, reference, directory):
    """
    Update a module's git reference and update the database entry.
    Additionally, the directory of the module can be moved if
    a new directory is entered.
    If no module is found in the database, nothing is updated.
    """
    with TinyDB(db.filepath, storage=db.storage, default_table=db.table_name) as mpm_db:
        module = Query()
        item = mpm_db.get(module.name == module_name)
        if item:
            if not reference:
                # Pull up to latest commit on active branch
                reference = item['reference']
            click.echo('Updating ' + module_name + '...')
            checkout_helper(item['remote_url'], reference, yaml_to_path_helper(item['path']))
            mpm_db.update({'reference': reference}, module.name == module_name)
            click.echo('Module reference updated!')

            if directory:
                new_path = os.path.join(directory, module_name)
                if new_path != yaml_to_path_helper(item['path']):
                    if not os.path.exists(directory):
                        os.mkdir(directory)
                    os.rename(yaml_to_path_helper(item['path']), new_path)
                    mpm_db.update({'path': path_to_yaml_helper(new_path)}, module.name == module_name)
                    click.echo('Module directory updated!')
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
                    directory = yaml_to_path_helper(item['path']).split(os.path.sep)[-2]
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

def mpm_convert(db, filename, product, hard):
    """
    Gets existing git submodules from the repository, adds them to
    the working database, then freezes to an output file. If the hard
    option is used, mpm will use GitPython to remove all the submodules
    from git in favour of managing them via mpm instead.
    """
    if os.path.isfile(os.path.join(os.getcwd(), '.gitmodules')):
        submodules = Repo(os.getcwd()).submodules
        if submodules:
            click.echo('Converting all git submodules to mpm modules...')
            modules = []
            for submodule in submodules:
                name = os.path.basename(submodule.path)
                directory = submodule.path.split(name)[0].strip(os.path.sep)
                remote_url = submodule.url
                reference = str(submodule.module().head.commit)
                mpm_install(db, remote_url, reference, directory, name)
                if hard:
                    # move the file so GitPython doesn't delete it from the filsystem
                    os.rename(directory, 'mpm_tmp_mv' + directory)
                    submodule.remove(configuration=True)
                    os.rename('mpm_tmp_mv' + directory, directory)

            mpm_freeze(db, filename, product)
            click.echo('Convert complete!')
        else:
            click.echo('Nothing to convert!')
    else:
        click.echo('No .gitmodules exists!')

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
