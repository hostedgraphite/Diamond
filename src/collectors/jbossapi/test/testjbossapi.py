#!/usr/bin/python3
# coding=utf-8
###############################################################################

from jbossapi import JbossApiCollector

from test import CollectorTestCase
from test import get_collector_config
from test import unittest


###############################################################################

class TestJbossApiCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('JbossApiCollector', {
        })
        self.collector = JbossApiCollector(config, None)

    def test_import(self):
        self.assertTrue(JbossApiCollector)


###############################################################################
if __name__ == "__main__":
    unittest.main()
