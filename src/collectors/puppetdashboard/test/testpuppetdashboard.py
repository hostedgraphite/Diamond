#!/usr/bin/python3
# coding=utf-8
##########################################################################

from puppetdashboard import PuppetDashboardCollector

from diamond.collector import Collector
from diamond.pycompat import URLOPEN
from test import CollectorTestCase
from test import Mock
from test import get_collector_config
from test import patch
from test import unittest


##########################################################################


class TestPuppetDashboardCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('PuppetDashboardCollector', {
            'interval': 10
        })

        self.collector = PuppetDashboardCollector(config, None)

    def test_import(self):
        self.assertTrue(PuppetDashboardCollector)

    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        patch_urlopen = patch(URLOPEN, Mock(
            return_value=self.getFixture('index.html')))

        patch_urlopen.start()
        self.collector.collect()
        patch_urlopen.stop()

        metrics = {
            'unresponsive': 3,
            'pending': 0,
            'changed': 10,
            'unchanged': 4,
            'unreported': 0,
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @patch.object(Collector, 'publish')
    def test_should_fail_gracefully(self, publish_mock):
        patch_urlopen = patch(URLOPEN, Mock(
            return_value=self.getFixture('index.blank')))

        patch_urlopen.start()
        self.collector.collect()
        patch_urlopen.stop()

        self.assertPublishedMany(publish_mock, {})


##########################################################################
if __name__ == "__main__":
    unittest.main()
