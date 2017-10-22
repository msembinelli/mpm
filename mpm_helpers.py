import os
import click

from git import Repo
from tinydb import TinyDB

def is_local_commit_helper(repo, reference):
    """
    Tests if a branch or sha is local.
    """
    if not repo.git.execute(['git', 'branch', '-r', '--contains', reference]):
        return True
    for head in repo.heads:
        if reference == head.name:
            return True
    return False

def clone_helper(remote_url, path):
    """
    Clone helper used by the install and update commands.
    Uses GitPython to clone a git repo from a given URL.
    If a repo at the given path already exists, it won't be
    recloned. Returns the repo object.
    """
    if not path:
        raise TypeError("path cannot be NoneType.")
    if not remote_url:
        raise TypeError("remote_url cannot be NoneType.")

    if not os.path.exists(os.path.join(path, '.git')):
        repo = Repo.clone_from(remote_url, path)
    else:
        repo = Repo(path)
    repo.close()

def checkout_helper(path, reference):
    """
    Checkout helper used by the install and update commands.
    Uses GitPython to checkout a git repo from a given remote
    reference (SHA or remote). Before checking out a fetch is issued on
    all remote upstream branches to ensure the latest changes
    are downloaded.
    """
    if not path:
        raise TypeError("path cannot be NoneType.")
    repo = Repo(path)
    repo.git.execute(['git', 'fetch', '--all', '-v'])

    if is_local_commit_helper(repo, reference):
        click.echo(('\nWARNING: Your reference is being set to a local branch or commit.\n'
                    'If you check-in a yaml file containing a local reference,\n'
                    'it will not be properly resolved when someone reloads the\n'
                    'yaml file with a fresh clone of the repo. It is suggested you\n'
                    'only commit local references if you are creating a draft commit.\n'))
    repo.git.checkout(reference)
    repo.close()

def clone_and_checkout_helper(remote_url, reference, path):
    """
    Clones and checks out a repo at the given url and reference
    to the provided path. Calls the checkout and clone helpers.
    """
    clone_helper(remote_url, path)
    checkout_helper(path, reference)


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
        raise IOError(exc_info)

def add_to_gitignore_helper(gitignore_filename, entry_string):
    """
    Checks if the entry_string exists in gitignore. If it
    doesn't, this function will add it.
    """
    entry_forward_slash = path_to_yaml_helper(entry_string).strip('/') + '/'
    create_gitignore_entry = False
    added = False
    with open(gitignore_filename, 'r+') as gitignore_file:
        if entry_forward_slash not in gitignore_file.read():
            create_gitignore_entry = True
    # Add path to .gitignore
    if create_gitignore_entry:
        with open(gitignore_filename, 'a+') as gitignore_file:
            gitignore_file.write(entry_forward_slash + '\n')
            added = True
    return added

def remove_from_gitignore_helper(gitignore_filename, entry_string):
    """
    Checks if the entry_string exists in gitignore. If it
    doesn't, this function will delete it.
    """
    entry_forward_slash = path_to_yaml_helper(entry_string).strip('/') + '/'
    lines = None
    removed = False
    with open(gitignore_filename, 'r') as gitignore_file:
        lines = gitignore_file.readlines()
    # Remove item from .gitignore
    with open(gitignore_filename, 'w') as gitignore_file:
        for line in lines:
            if line != entry_forward_slash + '\n':
                gitignore_file.write(line)
            else:
                removed = True
    return removed

def with_open_or_create_tinydb_helper(filepath, storage, table='_default'):
    """
    Open and or create the tinydb file with the input filepath,
    storage type, and default_table.
    """
    with TinyDB(filepath, storage=storage, default_table=table):
        pass

def with_open_or_create_file_helper(filepath, mode):
    """
    Open and or create the file with the input filepath,
    and mode.
    """
    with open(filepath, mode):
        pass

def create_directory_helper(path):
    """
    If the path does not exist, create the directory.
    """
    if not os.path.exists(path):
        os.mkdir(path)
