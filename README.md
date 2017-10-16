# MPM
A basic package manager for git written in python 2.7. To provide a simpler approach to including nested submodules in large projects.

## REQUIREMENTS

MPM uses the `git` executable via the `GitPython` package. It must be installed on the system in your `PATH` environment variable.
See https://github.com/gitpython-developers/GitPython README.md for more details on which versions of `Git` are required.

## INSTALL

If you have cloned the repo the first thing you must do is install the requirements with pip:

    pip install -r requirements.txt

MPM uses setuptools for ease of use on all platforms (Windows, Linux, OSX). To set up, navigate to the folder where you cloned MPM, and run:

    pip install --editable .

Voila! Now MPM should be accessible on the command line simply by running:

    mpm --help

## COMMANDS

```
Usage: mpm [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  freeze     Save installed modules to a yaml file.
  install    Retrieve and install a module.
  load       Load and install modules from a yaml file.
  purge      Uninstall all modules.
  show       Print out the currently installed modules.
  uninstall  Uninstall a module.
  update     Update a modules reference.


Usage: mpm convert [OPTIONS] FILENAME

  Gets existing git submodules from the repository, adds them to the
  working set, then freezes to an output file.

Options:
  -p, --product TEXT  The configuration name to save the modules to.
                      [default: _default]
  -h, --hard          Removes existing git submodules from the repository.
                      Use this option if you are committing to use mpm to
                      manage all the modules for your repo.
  --help              Show this message and exit.


Usage: mpm freeze [OPTIONS] FILENAME

  Save installed modules to a yaml file.

Options:
  -p, --product TEXT  [default: _default]
  --help              Show this message and exit.


Usage: mpm install [OPTIONS] REMOTE_URL

  Retrieve and install a module.

Options:
  -r, --reference TEXT  The upstream remote SHA of the module you want to
                        checkout.  [default: remotes/origin/master]
  -d, --directory TEXT  Select the folder to install the module in.
                        [default: modules]
  -n, --name TEXT       Customize the folder name of the module. Useful in
                        the event of name collisions. If no name is included,
                        the name will be extracted from the remote URL.
  --help                Show this message and exit.


Usage: mpm load [OPTIONS] FILENAME

  Load and install modules from a yaml file.

Options:
  -p, --product TEXT  [default: _default]
  --help              Show this message and exit.


Usage: mpm purge [OPTIONS]

  Uninstall all modules.

Options:
  --help  Show this message and exit.


Usage: mpm show [OPTIONS]

  Print out the currently installed modules.

Options:
  --help  Show this message and exit.


Usage: mpm uninstall [OPTIONS] MODULE_NAME

  Uninstall a module.

Options:
  --help  Show this message and exit.


Usage: mpm update [OPTIONS] MODULE_NAME REFERENCE

  Update a modules reference.

Options:
  --help  Show this message and exit.
```

## EXAMPLES

Before you begin, it is recommended that you add `.mpm/` to your project's .gitignore. This folder contains the mpm working module database, but should not be checked in to your project. The `freeze` command saves a separate YAML file that can be checked in.

### Installing A Module

We can install modules using the remote URL of the repo:

    mpm install https://github.com/bitcoin/bitcoin.git -d my_modules -n BTC -r remotes/origin/master

    mpm install git@github.com:reactjs/redux.git -r 6fdcc8c

### Freezing A Module Set

A working set of installed submodules can be saved to a YAML file, and that file can be checked in with your project:

    mpm freeze package.dev.yaml

The output yaml file:

```
_default:
  1:
    name: BTC
    path: my_modules/BTC
    reference: remotes/origin/master
    remote_url: https://github.com/bitcoin/bitcoin.git
  2:
    name: redux
    path: modules/redux
    reference: master
    remote_url: git@github.com:reactjs/redux.git

```

Additionally, you can save a different configuration to the same YAML file using a different 'product' code. First, let us install an extra module for the second product.

    mpm install https://github.com/pallets/click.git

The new product configuration can be saved to the same YAML file with the `-p` option as so:

    mpm freeze package.dev.yaml -p other_config

Updated output:

```
_default:
  1:
    name: BTC
    path: my_modules/BTC
    reference: remotes/origin/master
    remote_url: https://github.com/bitcoin/bitcoin.git
  2:
    name: redux
    path: modules/redux
    reference: master
    remote_url: git@github.com:reactjs/redux.git
other_config:
  1:
    name: BTC
    path: my_modules/BTC
    reference: remotes/origin/master
    remote_url: https://github.com/bitcoin/bitcoin.git
  2:
    name: redux
    path: modules/redux
    reference: master
    remote_url: git@github.com:reactjs/redux.git
  3:
    name: click
    path: modules/click
    reference: remotes/origin/master
    remote_url: https://github.com/pallets/click.git
```

### Loading A Module Set

A set of modules can be loaded and installed from a YAML file:

    mpm load package.dev.yaml

Or with a different product code:

    mpm load package.dev.yaml -p other_config


### Converting Existing Projects To MPM

The `convert` command allows porting projects with existing git submodules over to the mpm method. `convert` is a composition of other commands, which will first get all your repository's submodules, issue `install` commands to enter them into the working module set, and finally issue a `freeze` command to write out the new yaml configuration file.

    mpm convert package.yaml -p new_mpm_product

The `-h` or `--hard` command line option provides the ability to remove a submodule from the git repository. Use this option if you are fully committing to using mpm in your project over traditional git submodules.

    mpm convert package.yaml -p new_mpm_product --hard

## CAVEATS

### Module Names

Currently, modules are indexed by their name that was selected at install time. The whole point of this is to have MPM act more like a package manager, rather than having to type out the full path or url of the module. If you have a name conflict with an existing module, you must install the new module under a different name. To do this with the `install` command, use the `-n` option.

### References: Branches vs SHA1's

For projects that require cloning latest version of a module during development, it is suggested to use a remote branch as the module install reference. This means every time you issue an `update`, `load` or `install` command, the latest commit for that branch will be pulled.

Local branches are allowed in a `freeze` yaml file, but are discouraged because the reference will fail to resolve on a fresh clone and `load` of the repo. Please do not merge any yaml files containing local references to your upstream repository.

When a project becomes feature complete or frozen, it is suggested to `update` your submodule using a specific SHA-1 reference, to ensure that whenever the project is cloned and the yaml is loaded in the future, the right commits from your modules are pulled in.
