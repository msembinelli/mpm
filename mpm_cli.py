import click

from mpm import DBWrapper, mpm_init, mpm_install, mpm_uninstall, mpm_freeze

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
@click.option('-s', '--save', nargs=2, default={'file': 'package.yaml', 'product': 'default'}, help='Save the package or submodule reference to an mpm yaml configuration file.')
@pass_db
def install(db, remote_url, reference, directory, name, update, save):
    mpm_install(db, remote_url, reference, directory, name, update, save)

@cli.command(help='Uninstall a module.')
@click.argument('module_name', required=True)
@pass_db
def uninstall(db, module_name):
    mpm_uninstall(db, module_name)

@cli.command(help='Save installed modules to a yml file.')
@click.argument('yaml_file', required=True, type=click.File(mode='w'))
@click.option('-prd', '--product', default='default', help='Select the product you want to save the reference to, within a configuration file. The product can be used to manage different configuration versions or variations within one configuration file.')
@pass_db
def freeze(db, yaml_file, product):
    mpm_freeze(db, yaml_file, product)

@cli.command(help='Print out the currently installed modules.')
@pass_db
def show(db):
    mpm_show(db)
