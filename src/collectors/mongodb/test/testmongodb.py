#!/usr/bin/python3
# coding=utf-8
##########################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from test import run_only
from test import MagicMock
from test import patch
from test import call

from diamond.collector import Collector
from mongodb import MongoDBCollector
from collections import defaultdict

try:
    import json
except ImportError:
    import simplejson as json

try:
    long
except NameError:
    long = int


def run_only_if_pymongo_is_available(func):
    try:
        import pymongo
    except ImportError:
        pymongo = None

    return run_only(func, lambda: pymongo is not None)


class TestMongoDBCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('MongoDBCollector', {
            'host': 'localhost:27017',
            'databases': '^db'
        })
        self.collector = MongoDBCollector(config, None)
        self.connection = MagicMock()

    def test_import(self):
        self.assertTrue(MongoDBCollector)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_nested_keys_for_server_stats(self,
                                                         publish_mock,
                                                         connector_mock):
        data = {'more_keys': {'nested_key': 1}, 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection.db.command.assert_called_once_with('serverStatus')
        self.assertPublishedMany(publish_mock, {
            'more_keys.nested_key': 1,
            'key': 2
        })

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_nested_keys_for_db_stats(self,
                                                     publish_mock,
                                                     connector_mock):
        data = {'db_keys': {'db_nested_key': 1}, 'dbkey': 2, 'dbstring': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection['db1'].command.assert_called_once_with('dbStats')
        metrics = {
            'db_keys.db_nested_key': 1,
            'dbkey': 2
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_stats_with_long_type(self,
                                                 publish_mock,
                                                 connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection.db.command.assert_called_once_with('serverStatus')
        self.assertPublishedMany(publish_mock, {
            'more_keys': 1,
            'key': 2
        })

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_ignore_unneeded_databases(self,
                                              publish_mock,
                                              connector_mock):
        self._annotate_connection(connector_mock, {})

        self.collector.collect()

        assert call('baddb') not in self.connection.__getitem__.call_args_list

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_ignore_unneeded_collections(self,
                                                publish_mock,
                                                connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.connection['db1'].collection_names.return_value = ['collection1',
                                                                'tmp.mr.tmp1']
        self.connection['db1'].command.return_value = {'key': 2,
                                                       'string': 'str'}

        self.collector.collect()

        self.connection.db.command.assert_called_once_with('serverStatus')
        self.connection['db1'].collection_names.assert_called_once_with()
        self.connection['db1'].command.assert_any_call('dbStats')
        self.connection['db1'].command.assert_any_call('collstats',
                                                       'collection1')
        assert call('collstats', 'tmp.mr.tmp1') not in self.connection['db1'].command.call_args_list  # NOQA
        metrics = {
            'databases.db1.collection1.key': 2,
        }

        self.assertPublishedMany(publish_mock, metrics)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_ignore_replset_status_if_disabled(self,
                                                      publish_mock,
                                                      connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()
        assert call('replsetSetGetStatus') not in \
            self.connection.admin.command.method_calls

    def _annotate_connection(self, connector_mock, data):
        connector_mock.return_value = self.connection
        self.connection.db.command.return_value = data
        self.connection.database_names.return_value = ['db1', 'baddb']

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_keys_from_real_server_stats(self,
                                                        publish_mock,
                                                        connector_mock):
        data = json.load(self.getFixture('real_serverStatus_response.json'))
        self._annotate_connection(connector_mock, data)

        self.collector.collect()
        self.connection.db.command.assert_called_with('serverStatus')

        # check for multiple datapoints per metric
        # should not happen, but it did (once), so lets check it
        datapoints_per_metric = defaultdict(int)
        for c in publish_mock.call_args_list:
            m = c[0][0]
            datapoints_per_metric[m] += 1
        dupes = [m for m, n in datapoints_per_metric.items() if n > 1]
        self.assertEqual(len(dupes), 0,
                         'BUG: 1+ point for same metric received: %s' %
                         ', '.join(dupes))

        # just a few samples
        expected_calls = [
            call('opcounters.query', 125030709),
            call('opcountersRepl.insert', 7465),
            call('extra_info.heap_usage_bytes', 801236248),
            call('metrics.document.returned', 536691431),
            call('metrics.commands.saslContinue.total', 1400470),
            call('wiredTiger.thread.yield.page_acquire_time_sleeping_(usecs)',
                 3022511),
            call('opcounters_per_sec.query', 0, instance=None,
                 metric_type='COUNTER', precision=0, raw_value=125030709),
        ]

        publish_mock.assert_has_calls(expected_calls, any_order=True)


class TestMongoMultiHostDBCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('MongoDBCollector', {
            'hosts': ['localhost:27017', 'localhost:27057'],
            'databases': '^db',
        })
        self.collector = MongoDBCollector(config, None)
        self.connection = MagicMock()

    def test_import(self):
        self.assertTrue(MongoDBCollector)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_nested_keys_for_server_stats(self,
                                                         publish_mock,
                                                         connector_mock):
        data = {'more_keys': {'nested_key': 1}, 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection.db.command.assert_called_with('serverStatus')
        self.assertPublishedMany(publish_mock, {
            'localhost_27017.more_keys.nested_key': 1,
            'localhost_27057.more_keys.nested_key': 1,
            'localhost_27017.key': 2,
            'localhost_27057.key': 2
        })

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_nested_keys_for_db_stats(self,
                                                     publish_mock,
                                                     connector_mock):
        data = {'db_keys': {'db_nested_key': 1}, 'dbkey': 2, 'dbstring': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection['db1'].command.assert_called_with('dbStats')
        metrics = {
            'localhost_27017.db_keys.db_nested_key': 1,
            'localhost_27057.db_keys.db_nested_key': 1,
            'localhost_27017.dbkey': 2,
            'localhost_27057.dbkey': 2
        }

        self.setDocExample(collector=self.collector.__class__.__name__,
                           metrics=metrics,
                           defaultpath=self.collector.config['path'])
        self.assertPublishedMany(publish_mock, metrics)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_stats_with_long_type(self,
                                                 publish_mock,
                                                 connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection.db.command.assert_called_with('serverStatus')
        self.assertPublishedMany(publish_mock, {
            'localhost_27017.more_keys': 1,
            'localhost_27057.more_keys': 1,
            'localhost_27017.key': 2,
            'localhost_27057.key': 2
        })

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_ignore_unneeded_databases(self,
                                              publish_mock,
                                              connector_mock):
        self._annotate_connection(connector_mock, {})

        self.collector.collect()

        assert call('baddb') not in self.connection.__getitem__.call_args_list

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_ignore_unneeded_collections(self,
                                                publish_mock,
                                                connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.connection['db1'].collection_names.return_value = ['collection1',
                                                                'tmp.mr.tmp1']
        self.connection['db1'].command.return_value = {'key': 2,
                                                       'string': 'str'}

        self.collector.collect()

        self.connection.db.command.assert_called_with('serverStatus')
        self.connection['db1'].collection_names.assert_called_with()
        self.connection['db1'].command.assert_any_call('dbStats')
        self.connection['db1'].command.assert_any_call('collstats',
                                                       'collection1')
        assert call('collstats', 'tmp.mr.tmp1') not in self.connection['db1'].command.call_args_list  # NOQA
        metrics = {
            'localhost_27017.databases.db1.collection1.key': 2,
            'localhost_27057.databases.db1.collection1.key': 2,
        }

        self.assertPublishedMany(publish_mock, metrics)

    def _annotate_connection(self, connector_mock, data):
        connector_mock.return_value = self.connection
        self.connection.db.command.return_value = data
        self.connection.database_names.return_value = ['db1', 'baddb']


class TestMongoDBCollectorWithReplica(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('MongoDBCollector', {
            'host': 'localhost:27017',
            'databases': '^db',
            'replica': True
        })
        self.collector = MongoDBCollector(config, None)
        self.connection = MagicMock()

    def test_import(self):
        self.assertTrue(MongoDBCollector)

    @run_only_if_pymongo_is_available
    @patch('pymongo.MongoClient')
    @patch.object(Collector, 'publish')
    def test_should_publish_replset_status_if_enabled(self,
                                                      publish_mock,
                                                      connector_mock):
        data = {'more_keys': long(1), 'key': 2, 'string': 'str'}
        self._annotate_connection(connector_mock, data)

        self.collector.collect()

        self.connection.admin.command.assert_called_once_with(
            'replSetGetStatus')

    def _annotate_connection(self, connector_mock, data):
        connector_mock.return_value = self.connection
        self.connection.db.command.return_value = data
        self.connection.database_names.return_value = ['db1', 'baddb']


##########################################################################
if __name__ == "__main__":
    unittest.main()
