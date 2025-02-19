#!/usr/bin/python3
# coding=utf-8
###############################################################################

from netapp import NetAppCollector

from test import CollectorTestCase
from test import get_collector_config
from test import unittest


###############################################################################

class TestNetAppCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('NetAppCollector', {
        })
        self.collector = NetAppCollector(config, None)

    def test_import(self):
        self.assertTrue(NetAppCollector)


###############################################################################
if __name__ == "__main__":
    unittest.main()
