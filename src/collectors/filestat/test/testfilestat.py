#!/usr/bin/python3
# coding=utf-8
##########################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from test import Mock
from test import patch
from test import StringIO
from test import BUILTIN_OPEN

from diamond.collector import Collector
from filestat import FilestatCollector

##########################################################################


class TestFilestatCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('FilestatCollector', {
            'interval': 10
        })

        self.collector = FilestatCollector(config, None)

    def test_import(self):
        self.assertTrue(FilestatCollector)

    @patch(BUILTIN_OPEN)
    @patch('os.access', Mock(return_value=True))
    @patch.object(Collector, 'publish')
    def test_should_open_proc_sys_fs_file_nr(self, publish_mock, open_mock):
        open_mock.return_value = StringIO('')
        self.collector.collect()
        open_mock.assert_called_once_with('/proc/sys/fs/file-nr')

    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        FilestatCollector.PROC = self.getFixturePath('proc_sys_fs_file-nr')
        self.collector.collect()

        metrics = {
            'assigned': 576,
            'unused': 0,
            'max': 4835852
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)


##########################################################################
if __name__ == "__main__":
    unittest.main()
