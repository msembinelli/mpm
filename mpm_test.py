import unittest
import os
import shutil
import stat

from mpm import MPMMetadata, mpm_init, mpm_purge, mpm_install, mpm_uninstall, mpm_update, mpm_load, mpm_freeze, mpm_purge, mpm_convert, mpm_show
from mpm_helpers import clone_and_checkout_helper, clone_helper, checkout_helper, yaml_to_path_helper, path_to_yaml_helper, onerror_helper, remove_from_gitignore_helper, add_to_gitignore_helper, is_local_commit_helper, with_open_or_create_tinydb_helper, with_open_or_create_file_helper, create_directory_helper
from mpm_yaml_storage import YAMLStorage
from tinydb import TinyDB, Query
from git import Repo, GitCommandError

class HelperObject(object):
    pass

class TestHelpers(unittest.TestCase):
    def test_is_local_commit_helper_not_local(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        ref = '2dc33423188a7e06fa6e9725a0a74059b009ff6a'
        clone_helper(url, path)
        repo = Repo(path)
        self.assertFalse(is_local_commit_helper(repo, '2dc3342318'))
        repo.close()
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_is_local_commit_helper_is_local(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        ref = '2dc33423188a7e06fa6e9725a0a74059b009ff6a'
        clone_helper(url, path)
        repo = Repo(path)
        branch = repo.create_head('test_branch', '2dc33423188a7e06fa6e9725a0a74059b009ff6a')
        self.assertTrue(is_local_commit_helper(repo, 'test_branch'))
        repo.git.checkout('test_branch')
        new_path = os.path.join(path, 'test_module')
        os.mkdir(new_path)
        repo.index.add(['test_module'])
        repo.index.commit("Added a new folder test")
        self.assertTrue(is_local_commit_helper(repo, 'test_branch'))
        repo.close()
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_clone_helper_should_clone(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        clone_helper(url, path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.exists(os.path.join(path, '.git')))
        # Try cloning again
        clone_helper(url, path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.exists(os.path.join(path, '.git')))
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_clone_helper_should_not_clone(self):
        path = os.path.join('test', 'test')
        # Bad URL
        url = 'https://github.com/fake/repo/repo123456789.git'
        self.assertRaises(GitCommandError, clone_helper, url, path)
        self.assertFalse(os.path.exists(path))
        self.assertFalse(os.path.exists(os.path.join(path, '.git')))
        self.assertRaises(TypeError, clone_helper, url, None)
        self.assertRaises(TypeError, clone_helper, None, path)

    def test_checkout_helper_should_checkout(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        ref = '2dc33423188a7e06fa6e9725a0a74059b009ff6a'
        clone_helper(url, path)
        checkout_helper(path, ref)
        repo = Repo(path)
        self.assertEqual(repo.head.commit.hexsha, ref)
        repo.close()
        repo = Repo(path)
        branch = repo.create_head('test', '2dc33423188a7e06fa6e9725a0a74059b009ff6a')
        checkout_helper(path, 'test')
        repo.close()
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_checkout_helper_should_not_checkout(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        ref = '123456789'
        clone_helper(url, path)
        self.assertRaises(GitCommandError, checkout_helper, path, ref)
        self.assertRaises(TypeError, checkout_helper, None, '2dc3342')
        self.assertRaises(TypeError, checkout_helper, path, None)
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_clone_and_checkout_helper_should_clone_and_checkout(self):
        path = os.path.join('test', 'broker')
        url = 'https://github.com/msembinelli/broker.git'
        ref = '2dc33423188a7e06fa6e9725a0a74059b009ff6a'
        clone_and_checkout_helper(url, ref, path)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.exists(os.path.join(path, '.git')))
        repo = Repo(path)
        self.assertEqual(repo.head.commit.hexsha, ref)
        repo.close()
        shutil.rmtree(path, onerror=onerror_helper)
        os.rmdir('test')

    def test_yaml_to_path_helper(self):
        yaml_path = '/test/folder'
        expected_path = os.path.sep + 'test' + os.path.sep + 'folder'
        self.assertEqual(expected_path, yaml_to_path_helper(yaml_path))

    def test_path_to_yaml_helper(self):
        path = os.path.sep + 'test' + os.path.sep + 'folder'
        expected_yaml_path = '/test/folder'
        self.assertEqual(expected_yaml_path, path_to_yaml_helper(path))

    def test_add_to_gitignore_helper(self):
        self.assertTrue(add_to_gitignore_helper('.gitignore', 'test/path'))
        remove_from_gitignore_helper('.gitignore', 'test/path')

    def test_add_to_gitignore_helper_already_added(self):
        add_to_gitignore_helper('.gitignore', 'test/path')
        self.assertFalse(add_to_gitignore_helper('.gitignore', 'test/path'))

    def test_remove_from_gitignore_helper(self):
        add_to_gitignore_helper('.gitignore', 'test/path')
        self.assertTrue(remove_from_gitignore_helper('.gitignore', 'test/path'))

    def test_remove_from_gitignore_helper_already_removed(self):
        self.assertFalse(remove_from_gitignore_helper('.gitignore', 'test/path'))

    def test_with_open_or_create_tinydb_helper_should_create_db(self):
        path = os.getcwd()
        filepath = os.path.join(path, 'test-db.yaml')
        with_open_or_create_tinydb_helper(filepath, YAMLStorage)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(filepath))
        os.remove(filepath)

    def test_with_open_or_create_tinydb_helper_should_not_create_db(self):
        path = os.getcwd()
        filepath = os.path.join(path, 'test-db.yaml')
        self.assertRaises(TypeError, with_open_or_create_tinydb_helper, filepath, None)
        self.assertRaises(TypeError, with_open_or_create_tinydb_helper, None, YAMLStorage)
        self.assertRaises(IOError, with_open_or_create_tinydb_helper, '.', YAMLStorage)

    def test_with_open_or_create_file_helper_should_create_file(self):
        path = os.getcwd()
        filepath = os.path.join(path, 'file.txt')
        with_open_or_create_file_helper(filepath, 'a+')
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(filepath))
        with_open_or_create_file_helper(filepath, 'r+')
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(filepath))
        os.remove(filepath)

    def test_with_open_or_create_file_helper_should_not_create_file(self):
        path = os.getcwd()
        filepath = os.path.join(path, 'file.txt')
        self.assertRaises(TypeError, with_open_or_create_file_helper, filepath, None)
        self.assertRaises(TypeError, with_open_or_create_file_helper, None, 'r+')
        self.assertRaises(IOError, with_open_or_create_file_helper, '.', 'r+')

    def test_create_directory_helper_should_create_directory(self):
        path = os.path.join(os.getcwd(), 'test')
        create_directory_helper(path)
        self.assertTrue(os.path.exists(path))
        os.rmdir(path)

    def test_create_directory_helper_should_not_create_directory(self):
        self.assertRaises(TypeError, create_directory_helper, None)

    def test_onerror_helper_should_delete_file(self):
        path = 'tmp'
        create_directory_helper(path)
        filepath = os.path.join(path, 'file.txt')
        with_open_or_create_file_helper(filepath, 'a+')
        os.chmod(filepath, stat.S_IREAD)
        onerror_helper(os.remove, filepath, 'test')
        self.assertFalse(os.path.isfile(filepath))
        shutil.rmtree(path, onerror=onerror_helper)

    def test_onerror_helper_should_not_delete_file(self):
        path = 'tmp'
        create_directory_helper(path)
        filepath = os.path.join(path, 'file.txt')
        with_open_or_create_file_helper(filepath, 'a+')
        self.assertRaises(IOError, onerror_helper, os.remove, filepath, 'test exception message')
        shutil.rmtree(path, onerror=onerror_helper)

class TestInit(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.context.obj = None
        self.db_table = 'aaa'
        self.db_path = '.aaa/'
        self.db_filename = 'aaa-db.yml'
        self.db_filepath = os.path.join(self.db_path, self.db_filename)
        self.db_storage = YAMLStorage
        self.gitignore = '.gitignore-test'

    def tearDown(self):
        shutil.rmtree(self.db_path)
        os.remove(self.gitignore)

    def test_init_should_init(self):
        expected_metadata_object = MPMMetadata(self.db_filepath, self.db_storage, self.db_table, self.gitignore)
        output_metadata_object = mpm_init(self.context, self.db_table, self.db_path, self.db_filename, self.db_storage, self.gitignore)

        self.assertTrue(os.path.exists(self.db_path))
        self.assertTrue(os.path.exists(self.gitignore))
        self.assertTrue(os.path.isfile(self.db_filepath))
        self.assertEqual(expected_metadata_object.filepath, output_metadata_object.filepath)
        self.assertEqual(expected_metadata_object.storage, output_metadata_object.storage)
        self.assertEqual(expected_metadata_object.table_name, output_metadata_object.table_name)
        with open(self.gitignore, 'r') as gitignore_file:
            self.assertTrue(self.db_path in gitignore_file.read())
        with open(self.db_filepath, 'r') as database_file:
            self.assertTrue(self.db_table in database_file.read())

class TestInstall(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)

    def tearDown(self):
        shutil.rmtree('.mpm', onerror=onerror_helper)

    def test_install_defaults(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        mpm_install(self.db, remote_url, reference, directory, None)

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertEqual(db_entry, expected_db_entry)

        self.assertTrue(os.path.exists(directory))
        self.assertTrue(os.path.exists(full_path))
        shutil.rmtree(directory, onerror=onerror_helper)
        remove_from_gitignore_helper('.gitignore', full_path)

    def test_install_custom_name(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker-test'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        mpm_install(self.db, remote_url, reference, directory, name)

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertEqual(db_entry, expected_db_entry)

        self.assertTrue(os.path.exists(directory))
        self.assertTrue(os.path.exists(full_path))
        shutil.rmtree(directory, onerror=onerror_helper)
        remove_from_gitignore_helper('.gitignore', full_path)

    def test_install_already_installed(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        mpm_install(self.db, remote_url, reference, directory, None)
        mpm_install(self.db, remote_url, reference, directory, None)

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertEqual(db_entry, expected_db_entry)

        self.assertTrue(os.path.exists(directory))
        self.assertTrue(os.path.exists(full_path))
        shutil.rmtree(directory, onerror=onerror_helper)
        remove_from_gitignore_helper('.gitignore', full_path)

    def test_install_reinstall(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        mpm_install(self.db, remote_url, reference, directory, None)
        shutil.rmtree(directory, onerror=onerror_helper)
        self.assertFalse(os.path.exists(full_path))
        mpm_install(self.db, remote_url, reference, directory, None)

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertEqual(db_entry, expected_db_entry)

        self.assertTrue(os.path.exists(directory))
        self.assertTrue(os.path.exists(full_path))
        shutil.rmtree(directory, onerror=onerror_helper)
        remove_from_gitignore_helper('.gitignore', full_path)

    def test_install_bad_parameters(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        self.assertRaises(Exception, mpm_install, None, remote_url, reference, directory, None)
        self.assertRaises(Exception, mpm_install, self.db, None, reference, directory, None)
        self.assertRaises(Exception, mpm_install, self.db, remote_url, None, directory, None)
        self.assertRaises(Exception, mpm_install, self.db, remote_url, reference, None, None)

class TestUninstall(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)

    def tearDown(self):
        shutil.rmtree('.mpm', onerror=onerror_helper)

    def test_uninstall_defaults(self):
        remote_url = 'https://github.com/msembinelli/broker.git'
        reference = 'remotes/origin/master'
        directory = 'modules'
        name = 'broker'
        full_path = os.path.join(directory, name)
        expected_db_entry = {'name': name, 'remote_url': remote_url, 'reference': reference, 'path': path_to_yaml_helper(full_path)}

        mpm_install(self.db, remote_url, reference, directory, None)
        mpm_uninstall(self.db, name)
        self.assertFalse(os.path.exists(full_path))

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertIsNone(db_entry)
            self.assertEqual([], mpm_db.all())

    def test_uninstall_nothing_to_uninstall(self):
        name = 'broker'
        mpm_uninstall(self.db, name)

        with TinyDB(self.db.filepath, storage=self.db.storage, default_table=self.db.table_name) as mpm_db:
            module = Query()
            db_entry = mpm_db.get(module.name == name)
            self.assertIsNone(db_entry)
            self.assertEqual([], mpm_db.all())

    def test_uninstall_bad_parameters(self):
        name = 'broker'
        self.assertRaises(Exception, mpm_uninstall, None, name)

class TestUpdate(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)
        self.remote_url = 'https://github.com/msembinelli/broker.git'
        self.reference = 'remotes/origin/master'
        self.directory = 'modules'
        self.name = 'broker'
        self.full_path = os.path.join(self.directory, self.name)
        mpm_install(self.db, self.remote_url, self.reference, self.directory, None)

    def tearDown(self):
        mpm_uninstall(self.db, self.name)
        shutil.rmtree('.mpm', onerror=onerror_helper)

    def test_update_new_reference(self):
        new_ref = '2dc33423188a7e06fa6e9725a0a74059b009ff6a'
        mpm_update(self.db, self.name, new_ref, None)
        repo = Repo(self.full_path)
        self.assertEqual(repo.head.commit.hexsha, new_ref)
        repo.close()

    def test_update_new_directory(self):
        new_directory = 'modules-test'
        mpm_update(self.db, self.name, None, new_directory)
        self.assertTrue(os.path.exists(os.path.join(new_directory, self.name)))
        repo = Repo(os.path.join(new_directory, self.name))
        self.assertIsNotNone(repo)
        repo.close()

    def test_update_no_module(self):
        self.assertIsNone(mpm_update(self.db, 'broker-test', self.reference, self.directory))

    def test_update_bad_parameters(self):
        self.assertRaises(Exception, mpm_update, None, self.name, self.reference, self.directory)

class TestConvert(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)
        self.remote_url = 'https://github.com/msembinelli/test-mpm-with-submodule.git'
        self.reference = 'remotes/origin/master'
        self.directory = 'modules'
        self.name = 'test-mpm-with-submodule'
        self.full_path = os.path.join(self.directory, self.name)
        mpm_install(self.db, self.remote_url, self.reference, self.directory, None)

    def tearDown(self):
        mpm_uninstall(self.db, self.name)

    def test_convert_hard(self):
        filename = 'convert-test.yaml'
        product = '_default'
        expected_module_name = 'broker'
        dir_before = os.getcwd()
        os.chdir(self.full_path)
        context = HelperObject()
        new_db = mpm_init(context)
        mpm_convert(new_db, filename, product, True)
        self.assertTrue(os.path.isfile(filename))
        with TinyDB(filename, storage=YAMLStorage) as db:
            module = Query()
            db_entry = db.get(module.name == expected_module_name)
            self.assertIsNotNone(db_entry)
        with open('.gitmodules', 'r') as gitmodules:
            self.assertTrue(expected_module_name not in gitmodules.read())
        os.chdir(dir_before)

    def test_convert_soft(self):
        filename = 'convert-test.yaml'
        product = '_default'
        expected_module_name = 'broker'
        dir_before = os.getcwd()
        os.chdir(self.full_path)
        context = HelperObject()
        new_db = mpm_init(context)
        mpm_convert(new_db, filename, product, False)
        self.assertTrue(os.path.isfile(filename))
        with TinyDB(filename, storage=YAMLStorage) as db:
            module = Query()
            db_entry = db.get(module.name == expected_module_name)
            self.assertIsNotNone(db_entry)
        with open('.gitmodules', 'r') as gitmodules:
            self.assertTrue(expected_module_name in gitmodules.read())
        os.chdir(dir_before)

class TestShow(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)
        self.remote_url = 'https://github.com/msembinelli/broker.git'
        self.reference = 'remotes/origin/master'
        self.directory = 'modules'
        self.name = 'broker'

    def tearDown(self):
        shutil.rmtree('.mpm', onerror=onerror_helper)

    def test_show(self):
        name = 'broker'
        mpm_install(self.db, self.remote_url, self.reference, self.directory, None)
        mpm_show(self.db)
        mpm_uninstall(self.db, name)

    def test_show_no_modules(self):
        mpm_show(self.db)

    def test_show_bad_parameters(self):
        self.assertRaises(AttributeError, mpm_show, None)

if __name__ == '__main__':
    unittest.main()
