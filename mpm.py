import click
import os
import shutil
from git import Repo, GitCommandError

@click.group(chain=True)
@click.pass_context
def cli(ctx):
    """
    A basic package manager for git written in python.
    To provide a simpler approach to including duplicate
    submodules in large projects.
    """
    click.echo('mpm - A basic package manager for git submodules written in python.')

@cli.command(help='Retrieve and install a package or submodule.')
@click.option('-u', '--url', help='The upstream remote URL of the package or submodule.', required=True)
@click.option('-s', '--sha', default='HEAD', help='The upstream remote SHA of the package or submodule you want to checkout.')
@click.option('-p', '--path', default='./', help='Select the folder to install the package or submodule in.')
@click.pass_context
def install(ctx, url, sha, path):
    if not os.path.exists(os.path.join(path, '.git')):
        Repo.clone_from(url, path)
    repo = Repo(path)
    for remote in repo.remotes:
        remote.fetch()
    try:
        commit_string = 'mpm-checkout-' + sha
        branch = repo.create_head(commit_string, sha)
        branch.checkout()
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
@click.pass_context
def uninstall(ctx, path):
    if os.path.exists(os.path.join(path, '.git')):
        if click.prompt('''Type 'DELETE '''+ path +'''' to continue''') == 'DELETE ' + path:
            shutil.rmtree(path, onerror=onerror)
    else:
        click.echo('Nothing to delete.')
    if not os.listdir(os.path.join(path, '../')):
        os.rmdir(os.path.join(path, '../'))
        
#@cli.command(help='Save the package or submodule reference to the mpm configuration file.')
#@click.option('-f', '--file', default='package.yaml', type=click.File(mode='w'), help='Select the configuration YAML file to save the package or submodule reference to.')
#@click.option('-p', '--product', default='default', help='Select the product you want to save the reference to, within a configuration file. The product can be used to manage different configuration versions or variations within one configuration file.')
#def save(dict, file, product):
#    click.echo(dict.url)
#    click.echo(file)
#    click.echo(product)
