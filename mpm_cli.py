import click

from mpm import DBWrapper, mpm_init, mpm_install, mpm_uninstall, mpm_freeze

pass_db = click.make_pass_decorator(DBWrapper)

@click.group(chain=True)
@click.pass_context
def cli(ctx):
    mpm_init(ctx)

@cli.command(help='Retrieve and install a module.')
@click.option('-u', '--url', help='The upstream remote URL of the module.', required=True)
@click.option('-r', '--ref', default='remotes/origin/master', help='The upstream remote SHA of the module you want to checkout.')
@click.option('-p', '--path', default='modules', help='Select the folder to install the module in.')
#@click.option('-s', '--save', nargs=2, default={'file': package.yaml, 'product': 'default'}, help='Save the package or submodule reference to an mpm yaml configuration file.')
@pass_db
def install(db, url, ref, path):
    mpm_install(db, url, ref, path)

@cli.command(help='Uninstall a module.')
@click.option('-p', '--path', default='./', help='Select the folder to uninstall the module from.')
@pass_db
def uninstall(db, path):
    mpm_uninstall(db, path)

@cli.command(help='Save installed modules to a yml file.')
@click.option('-f', '--file', default='package.yaml', type=click.File(mode='w'), help='Select the configuration YAML file to save the module reference to.')
@click.option('-p', '--product', default='default', help='Select the product you want to save the reference to, within a configuration file. The product can be used to manage different configuration versions or variations within one configuration file.')
@pass_db
def freeze(db, file, product):
    mpm_freeze(db)

@cli.command(help='Print out the currently installed modules.')
@pass_db
def show(db):
    mpm_show(db)
