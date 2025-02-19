#!/usr/bin/python3
# coding=utf-8
##########################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from test import run_only
from test import Mock
from test import patch
from test import BUILTIN_OPEN

from diamond.collector import Collector
from diskspace import DiskSpaceCollector

##########################################################################


class TestDiskSpaceCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('DiskSpaceCollector', {
            'interval': 10,
            'byte_unit': ['gigabyte'],
            'exclude_filters': [
                '^/export/home',
            ]
        })

        self.collector = DiskSpaceCollector(config, None)

    def test_import(self):
        self.assertTrue(DiskSpaceCollector)

    def run_collection(self, statvfs_mock, os_major, os_minor):
        os_stat_mock = patch('os.stat')
        os_path_isdir_mock = patch('os.path.isdir', Mock(return_value=False))
        open_mock = patch(BUILTIN_OPEN,
                          Mock(return_value=self.getFixture('proc_mounts')))
        os_statvfs_mock = patch('os.statvfs', Mock(return_value=statvfs_mock))

        os_stat_mock.start()
        os_path_isdir_mock.start()
        open_mock.start()
        os_statvfs_mock.start()
        self.collector.collect()
        os_stat_mock.stop()
        os_path_isdir_mock.stop()
        open_mock.stop()
        os_statvfs_mock.stop()

    @patch('os.access', Mock(return_value=True))
    def test_get_file_systems(self):
        result = None

        os_stat_mock = patch('os.stat')
        os_realpath_mock = patch('os.path.realpath')
        open_mock = patch(BUILTIN_OPEN,
                          Mock(return_value=self.getFixture('proc_mounts')))

        stat_mock = os_stat_mock.start()
        stat_mock.return_value.st_dev = 42

        realpath_mock = os_realpath_mock.start()
        realpath_mock.return_value = '/dev/sda1'

        omock = open_mock.start()

        result = self.collector.get_file_systems()
        os_stat_mock.stop()
        os_realpath_mock.stop()
        open_mock.stop()

        stat_mock.assert_called_once_with('/')
        realpath_mock.assert_called_once_with(
            '/dev/disk/by-uuid/81969733-a724-4651-9cf5-64970f86daba')

        self.assertEqual(result, {
            42: {
                'device':
                '/dev/sda1',
                'fs_type': 'ext3',
                'mount_point': '/'}
        })

        omock.assert_called_once_with('/proc/mounts')
        return result

    @patch('os.access', Mock(return_value=True))
    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        statvfs_mock = Mock()
        statvfs_mock.f_bsize = 1048576
        statvfs_mock.f_frsize = 4096
        statvfs_mock.f_blocks = 360540255
        statvfs_mock.f_bfree = 285953527
        statvfs_mock.f_bavail = 267639130
        statvfs_mock.f_files = 91578368
        statvfs_mock.f_ffree = 91229495
        statvfs_mock.f_favail = 91229495
        statvfs_mock.f_flag = 4096
        statvfs_mock.f_namemax = 255

        self.run_collection(statvfs_mock, 9, 0)

        metrics = {
            'root.gigabyte_used': (284.525, 2),
            'root.gigabyte_free': (1090.826, 2),
            'root.gigabyte_avail': (1020.962, 2),
            'root.inodes_used': 348873,
            'root.inodes_free': 91229495,
            'root.inodes_avail': 91229495,
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @patch('os.access', Mock(return_value=True))
    @patch.object(Collector, 'publish')
    def test_should_work_with_tmpfs(self, publish_mock):
        config = get_collector_config('DiskSpaceCollector', {
            'interval': 10,
            'byte_unit': ['gigabyte'],
            'exclude_filters': [],
            'filesystems': 'tmpfs',
            'exclude_filters': '^/sys'
        })

        self.collector = DiskSpaceCollector(config, None)
        statvfs_mock = Mock()
        statvfs_mock.f_bsize = 4096
        statvfs_mock.f_frsize = 4096
        statvfs_mock.f_blocks = 360540255
        statvfs_mock.f_bfree = 285953527
        statvfs_mock.f_bavail = 267639130
        statvfs_mock.f_files = 91578368
        statvfs_mock.f_ffree = 91229495
        statvfs_mock.f_favail = 91229495
        statvfs_mock.f_flag = 4096
        statvfs_mock.f_namemax = 255

        self.run_collection(statvfs_mock, 4, 0)

        metrics = {
            'tmp.gigabyte_used': (284.525, 2),
            'tmp.gigabyte_free': (1090.826, 2),
            'tmp.gigabyte_avail': (1020.962, 2),
            'tmp.inodes_used': 348873,
            'tmp.inodes_free': 91229495,
            'tmp.inodes_avail': 91229495,
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @patch('os.access', Mock(return_value=True))
    @patch.object(Collector, 'publish')
    def test_should_work_in_system_directories(self, publish_mock):
        config = get_collector_config('DiskSpaceCollector', {
            'interval': 10,
            'byte_unit': ['gigabyte'],
            'exclude_filters': [],
            'filesystems': 'tmpfs',
            'exclude_filters': '^/tmp'
        })

        self.collector = DiskSpaceCollector(config, None)
        statvfs_mock = Mock()
        statvfs_mock.f_bsize = 4096
        statvfs_mock.f_frsize = 4096
        statvfs_mock.f_blocks = 360540255
        statvfs_mock.f_bfree = 285953527
        statvfs_mock.f_bavail = 267639130
        statvfs_mock.f_files = 91578368
        statvfs_mock.f_ffree = 91229495
        statvfs_mock.f_favail = 91229495
        statvfs_mock.f_flag = 4096
        statvfs_mock.f_namemax = 255

        self.run_collection(statvfs_mock, 4, 0)

        metrics = {
            '_sys_fs_cgroup.gigabyte_used': (284.525, 2),
            '_sys_fs_cgroup.gigabyte_free': (1090.826, 2),
            '_sys_fs_cgroup.gigabyte_avail': (1020.962, 2),
            '_sys_fs_cgroup.inodes_used': 348873,
            '_sys_fs_cgroup.inodes_free': 91229495,
            '_sys_fs_cgroup.inodes_avail': 91229495,
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)


##########################################################################
if __name__ == "__main__":
    unittest.main()
