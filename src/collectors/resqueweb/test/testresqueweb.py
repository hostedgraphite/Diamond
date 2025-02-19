#!/usr/bin/python3
# coding=utf-8
##########################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from test import Mock
from test import patch

from diamond.collector import Collector
from diamond.pycompat import URLOPEN
from resqueweb import ResqueWebCollector

##########################################################################


class TestResqueWebCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('ResqueWebCollector', {
            'interval': 10
        })

        self.collector = ResqueWebCollector(config, None)

    def test_import(self):
        self.assertTrue(ResqueWebCollector)

    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        patch_urlopen = patch(URLOPEN, Mock(
            return_value=self.getFixture('stats.txt')))

        patch_urlopen.start()
        self.collector.collect()
        patch_urlopen.stop()

        metrics = {
            'pending.current': 2,
            'processed.total': 11686516,
            'failed.total': 38667,
            'workers.current': 9,
            'working.current': 2,
            'queue.low.current': 4,
            'queue.mail.current': 3,
            'queue.realtime.current': 9,
            'queue.normal.current': 1,
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @patch.object(Collector, 'publish')
    def test_should_fail_gracefully(self, publish_mock):
        patch_urlopen = patch(URLOPEN, Mock(
            return_value=self.getFixture('stats_blank.txt')))

        patch_urlopen.start()
        self.collector.collect()
        patch_urlopen.stop()

        self.assertPublishedMany(publish_mock, {})


##########################################################################
if __name__ == "__main__":
    unittest.main()
