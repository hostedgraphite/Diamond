#!/usr/bin/python3
# coding=utf-8
###############################################################################

from netappDisk import netappDisk

from test import CollectorTestCase
from test import get_collector_config
from test import unittest


###############################################################################

class TestnetappDisk(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('netappDisk', {
        })
        self.collector = netappDisk(config, None)

    def test_import(self):
        self.assertTrue(netappDisk)


###############################################################################
if __name__ == "__main__":
    unittest.main()
