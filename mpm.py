import click
from git import Repo

@click.group(chain=True)
@click.pass_context
def cli(ctx):
    """
    A basic package manager for git written in python.
    To provide a simpler approach to including duplicate
    submodules in large projects.
    """
    click.echo('mpm - A basic package manager for git submodules written in python.')

#'install', help='Retrieve and install a package or submodule.'
@cli.command(help='Retrieve and install a package or submodule.')
@click.option('-u', '--url', help='The upstream remote URL of the package or submodule.', required=True)
@click.option('-s', '--sha', default=None, help='The upstream remote SHA of the package or submodule you want to checkout.')
@click.option('-p', '--path', default='./', help='Select the folder to install the package or submodule in.')
@click.pass_context
def install(ctx, url, sha, path):
    click.echo(url)
    click.echo(sha)
    click.echo(path)
    Repo.clone_from(url, path)
    repo = Repo(path)
    print(repo)

#@cli.command(help='Save the package or submodule reference to the mpm configuration file.')
#@click.option('-f', '--file', default='package.yaml', type=click.File(mode='w'), help='Select the configuration YAML file to save the package or submodule reference to.')
#@click.option('-p', '--product', default='default', help='Select the product you want to save the reference to, within a configuration file. The product can be used to manage different configuration versions or variations within one configuration file.')
#def save(dict, file, product):
#    click.echo(dict.url)
#    click.echo(file)
#    click.echo(product)
