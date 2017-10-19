import unittest
import os
import shutil
from mpm import MPMMetadata, mpm_init, mpm_purge, mpm_install, mpm_uninstall, mpm_update, mpm_load, mpm_freeze, mpm_purge, mpm_convert, mpm_show, yaml_to_path_helper, path_to_yaml_helper, onerror_helper, remove_from_gitignore_helper, add_to_gitignore_helper
from yaml_storage import YAMLStorage
from tinydb import TinyDB, Query

class HelperObject(object):
    pass

class TestHelpers(unittest.TestCase):
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


class TestInit(unittest.TestCase):
    def test_init_normal_parameters(self):
        self.context = HelperObject()
        self.context.obj = None
        self.db_table = 'aaa'
        self.db_path = '.aaa/'
        self.db_filename = 'aaa-db.yml'
        self.db_filepath = os.path.join(self.db_path, self.db_filename)
        self.db_storage = YAMLStorage
        self.gitignore = '.gitignore-test'
        with open(self.gitignore, 'a+'):
            pass
        metadata_object = MPMMetadata(self.db_filepath, self.db_storage, self.db_table, self.gitignore)

        output_metadata_object = mpm_init(self.context, self.db_table, self.db_path, self.db_filename, self.db_storage, self.gitignore)

        self.assertTrue(os.path.exists(self.db_path))
        self.assertTrue(os.path.exists(self.gitignore))
        self.assertTrue(os.path.isfile(self.db_filepath))
        self.assertEqual(metadata_object.filepath, output_metadata_object.filepath)
        self.assertEqual(metadata_object.storage, output_metadata_object.storage)
        self.assertEqual(metadata_object.table_name, output_metadata_object.table_name)
        with open(self.gitignore, 'r') as gitignore_file:
            self.assertTrue(self.db_path in gitignore_file.read())
        with open(self.db_filepath, 'r') as database_file:
            self.assertTrue(self.db_table in database_file.read())

        shutil.rmtree(self.db_path)
        os.remove(self.gitignore)

class TestInstall(unittest.TestCase):
    def setUp(self):
        self.context = HelperObject()
        self.db = mpm_init(self.context)

    def tearDown(self):
        pass

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
        shutil.rmtree('.mpm', onerror=onerror_helper)
        remove_from_gitignore_helper('.gitignore', full_path)

if __name__ == '__main__':
    unittest.main()
