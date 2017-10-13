import click

from mpm import DBWrapper, mpm_init, mpm_install, mpm_uninstall, mpm_load, mpm_freeze, mpm_purge, mpm_show

pass_db = click.make_pass_decorator(DBWrapper)

@click.group()
@click.pass_context
def cli(ctx):
    mpm_init(ctx)

@cli.command(help='Retrieve and install a module.')
@click.argument('remote_url', required=True)
@click.option('-r', '--reference', default='remotes/origin/master', help='The upstream remote SHA of the module you want to checkout.')
@click.option('-d', '--directory', default='modules', help='Select the folder to install the module in.')
@click.option('-n', '--name', default=None, help='Customize the folder name of the module. Useful in the event of name collisions. If no name is included, the name will be extracted from the remote URL.')
@click.option('-u', '--update', is_flag=True, help='Update the reference of an existing module.')
@pass_db
def install(db, remote_url, reference, directory, name, update):
    mpm_install(db, remote_url, reference, directory, name, update)

@cli.command(help='Uninstall a module.')
@click.argument('module_name', required=True)
@pass_db
def uninstall(db, module_name):
    mpm_uninstall(db, module_name)

@cli.command(help='Load and install modules from a yaml file.')
@click.argument('filename', default='package.yaml')
@click.option('-p', '--product', default='_default')
@pass_db
def load(db, filename, product):
    mpm_load(db, filename, product)

@cli.command(help='Save installed modules to a yaml file.')
@click.argument('filename', default='package.yaml')
@click.option('-p', '--product', default='_default')
@pass_db
def freeze(db, filename, product):
    mpm_freeze(db, filename, product)

@cli.command(help='Uninstall all the modules.')
@pass_db
def purge(db):
    mpm_purge(db)

@cli.command(help='Print out the currently installed modules.')
@pass_db
def show(db):
    mpm_show(db)
