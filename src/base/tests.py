from unittest import TestCase
from unittest.mock import patch

from .tasks import delete_local_file, delete_folder


class BackendTasksTestCase(TestCase):

    @patch('os.remove')
    def test_delete_local_file(self, mock_remove):
        filename = '/path/to/file'
        delete_local_file(filename)
        mock_remove.assert_called_once_with(filename)

    @patch('shutil.rmtree')
    def test_delete_folder(self, mock_rmtree):
        folder = '/path/to/folder'
        delete_folder(folder)
        mock_rmtree.assert_called_once_with(folder)
