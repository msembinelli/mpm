# MPM
A basic package manager for git written in python. To provide a simpler approach to including nested submodules in large projects.

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
