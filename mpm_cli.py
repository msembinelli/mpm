import click

from mpm import MPMMetadata, mpm_init, mpm_install, mpm_uninstall, mpm_update, mpm_load, mpm_freeze, mpm_purge, mpm_convert, mpm_show

pass_db = click.make_pass_decorator(MPMMetadata)

@click.group()
@click.pass_context
def cli(ctx):
    mpm_init(ctx)

@cli.command(help='Retrieve and install a module.')
@click.argument('remote_url', required=True)
@click.option('-r', '--reference', show_default=True, default='remotes/origin/master', help='The upstream remote SHA of the module you want to checkout.')
@click.option('-d', '--directory', show_default=True, default='modules', help='Select the folder to install the module in.')
@click.option('-n', '--name', show_default=True, default=None, help='Customize the folder name of the module. Useful in the event of name collisions. If no name is included, the name will be extracted from the remote URL.')
@pass_db
def install(db, remote_url, reference, directory, name):
    mpm_install(db, remote_url, reference, directory, name)

@cli.command(help='Uninstall a module.')
@click.argument('module_name', required=True)
@pass_db
def uninstall(db, module_name):
    mpm_uninstall(db, module_name)

@cli.command(help='Update a modules reference or install path.')
@click.argument('module_name', required=True)
@click.option('-r', '--reference', show_default=True, default=None, help='The upstream remote SHA of the module you want to checkout.')
@click.option('-d', '--directory', show_default=True, default=None, help='Select the folder to move the module to.')
@pass_db
def update(db, module_name, reference, directory):
    mpm_update(db, module_name, reference, directory)

@cli.command(help='Load and install modules from a yaml file.')
@click.argument('filename', default='package.yaml', required=True)
@click.option('-p', '--product', show_default=True, default='_default', help='The configuration name to load the modules from.')
@pass_db
def load(db, filename, product):
    mpm_load(db, filename, product)

@cli.command(help='Save installed modules to a yaml file.')
@click.argument('filename', default='package.yaml', required=True)
@click.option('-p', '--product', show_default=True, default='_default', help='The configuration name to save the modules to.')
@pass_db
def freeze(db, filename, product):
    mpm_freeze(db, filename, product)

@cli.command(help='Uninstall all modules.')
@pass_db
def purge(db):
    mpm_purge(db)

@cli.command(help='Gets existing git submodules from the repository, adds them to the working set, then freezes to an output file.')
@click.argument('filename', default='package.yaml', required=True)
@click.option('-p', '--product', show_default=True, default='_default', help='The configuration name to save the modules to.')
@click.option('-h', '--hard', is_flag=True, help='Removes existing git submodules from the repository. Use this option if you are committing to use mpm to manage all the modules for your repo.')
@pass_db
def convert(db, filename, product, hard):
    mpm_convert(db, filename, product, hard)

@cli.command(help='Print out the currently installed modules.')
@pass_db
def show(db):
    mpm_show(db)
