#!/usr/bin/python3
# coding=utf-8
##########################################################################

import configobj

import diamond.handler.riemann as mod
from diamond.metric import Metric
from test import Mock
from test import patch
from test import run_only
from test import unittest

try:
    from riemann_client.client import Client

    riemann_client = True
except ImportError:
    riemann_client = None


def run_only_if_riemann_client_is_available(func):
    return run_only(func, lambda: riemann_client is not None)


def fake_connect(self):
    # used for 'we can connect' tests
    self.transport = Mock()


class TestRiemannHandler(unittest.TestCase):

    def setUp(self):
        self.__connect_method = mod.RiemannHandler
        mod.RiemannHandler._connect = fake_connect

    def tearDown(self):
        # restore the override
        mod.RiemannHandler._connect = self.__connect_method

    @run_only_if_riemann_client_is_available
    @patch('riemann_client.transport.TCPTransport.connect', Mock())
    @patch('riemann_client.client.Client.send_event', Mock())
    def test_metric_to_riemann_event(self):
        config = configobj.ConfigObj()
        config['host'] = 'localhost'
        config['port'] = 5555
        handler = mod.RiemannHandler(config)

        metric = Metric('servers.com.example.www.cpu.total.idle',
                        0,
                        timestamp=1234567,
                        host='com.example.www')

        handler.process(metric)

        for call in handler.client.send_event.mock_calls:
            event = Client.create_dict(call[1][0])

            self.assertEqual(event, {
                'host': u'com.example.www',
                'service': u'servers.cpu.total.idle',
                'time': 1234567,
                'metric_f': 0.0,
            })


##########################################################################
if __name__ == "__main__":
    unittest.main()
