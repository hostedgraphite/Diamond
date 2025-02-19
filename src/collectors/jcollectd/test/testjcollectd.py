#!/usr/bin/python3
# coding=utf-8
###############################################################################

from jcollectd import JCollectdCollector, sanitize_word

from test import CollectorTestCase
from test import get_collector_config
from test import unittest


###############################################################################

class TestJCollectdCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('JCollectdCollector', {
        })
        self.collector = JCollectdCollector(config, None)

    def test_import(self):
        self.assertTrue(JCollectdCollector)

    def test_sanitize(self):
        self.assertEqual(sanitize_word('bla'), 'bla')
        self.assertEqual(sanitize_word('bla:'), 'bla')
        self.assertEqual(sanitize_word('foo:bar'), 'foo_bar')
        self.assertEqual(sanitize_word('foo:!bar'), 'foo_bar')
        self.assertEqual(sanitize_word('"ou812"'), 'ou812')
        self.assertEqual(sanitize_word('Aap! N@@t mi_es'), 'Aap_N_t_mi_es')


###############################################################################
if __name__ == "__main__":
    unittest.main()
