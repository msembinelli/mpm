import click
import os
import shutil
import sys
import hashlib

from yaml_storage import YAMLStorage
from tinydb import TinyDB, Query
from git import Repo, GitCommandError

class DBWrapper:
    def __init__(self, filepath, storage):
        self.filepath = filepath
        self.storage = storage

pass_db = click.make_pass_decorator(DBWrapper)

@click.group(chain=True)
@click.pass_context
def cli(ctx):
    """
    A basic package manager for git written in python.
    To provide a simpler approach to including duplicate
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

@cli.command(help='Retrieve and install a package or submodule.')
@click.option('-u', '--url', help='The upstream remote URL of the package or submodule.', required=True)
@click.option('-r', '--ref', default='HEAD', help='The upstream remote SHA of the package or submodule you want to checkout.')
@click.option('-p', '--path', default='./', help='Select the folder to install the package or submodule in.')
#@click.option('-s', '--save', nargs=2, default={'file': package.yaml, 'product': 'default'}, help='Save the package or submodule reference to an mpm yaml configuration file.')
@pass_db
def install(db, url, ref, path):
    full_path = os.path.abspath(os.path.join(os.getcwd(), path)).strip('/')
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
            if not db_obj.search(module.reference == key):
                db_obj.insert({'reference_md5': key, 'data': {'url': url, 'ref': ref, 'path': full_path}})
                click.echo('Install Complete!')
    except GitCommandError as msg:
        print(msg)
    except OSError as msg:
        print(msg)

def onerror(func, path, exc_info):
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
@cli.command(help='Uninstall a package or submodule.')
@click.option('-p', '--path', default='./', help='Select the folder to uninstall the package or submodule from.')
@pass_db
def uninstall(db, path):
    full_path = os.path.abspath(os.path.join(os.getcwd(), path)).strip('/')
    if os.path.exists(full_path):
        with TinyDB(db.filepath, storage=db.storage) as db_obj:
            module = Query()
            key = str(hashlib.md5(full_path.encode('utf-8')).hexdigest())
            if db_obj.search(module.reference_md5 == key):
                shutil.rmtree(full_path, onerror=onerror)
                db_obj.remove(module.reference_md5 == key)
                click.echo('Uninstall Complete!')
    else:
        click.echo('Nothing to delete.')

#@cli.command(help='Save the currently installed packages or submodule references to the mpm configuration file.')
#@click.option('-f', '--file', default='package.yaml', type=click.File(mode='w'), help='Select the configuration YAML file to save the package or submodule reference to.')
#@click.option('-p', '--product', default='default', help='Select the product you want to save the reference to, within a configuration file. The product can be used to manage different configuration versions or variations within one configuration file.')
#def save(dict, file, product):
#    click.echo(dict.url)
#    click.echo(file)
#    click.echo(product)
