#!/usr/bin/python3
# coding=utf-8
##########################################################################

from test import patch, unittest
import configobj
import gzip
import contextlib
from io import BytesIO
from diamond.pycompat import HTTPError
from diamond.metric import Metric
from diamond.handler.tsdb import TSDBHandler


class FakeUrlopenResponse:
    def getcode(self):
        return 200

    def read(self):
        return 'contents'


class FakeUrlopen:
    def __call__(self, *args, **kwargs):
        return FakeUrlopenResponse()


@patch('diamond.handler.tsdb.urlopen', new_callable=FakeUrlopen)
@patch('diamond.handler.tsdb.Request')
class TestTSDBdHandler(unittest.TestCase):

    def setUp(self):
        self.url = 'http://127.0.0.1:4242/api/put'

    def decompress(self, input):
        infile = BytesIO()
        infile.write(input)
        infile.seek(0)
        with contextlib.closing(gzip.GzipFile(fileobj=infile, mode="r")) as f:
            f.rewind()
            out = f.read()
            return out.decode()

    def test_HTTPError(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        header = {'Content-Type': 'application/json'}
        exception = HTTPError(url=self.url, code=404, msg="Error",
                                      hdrs=header, fp=None)
        handler.side_effect = exception
        handler.process(metric)

    def test_single_metric(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        body = '[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname"}, "metric": "cpu.cpu_count"}]'
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_compression(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['compression'] = 1
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        body = '[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname"}, "metric": "cpu.cpu_count"}]'
        passed_headers = mock_urlopen.call_args[0][2]
        passed_body = mock_urlopen.call_args[0][1]
        assert passed_headers['Content-Encoding'] == 'gzip'
        assert passed_headers['Content-Type'] == 'application/json'
        assert self.decompress(passed_body) == body

    def test_user_password(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['user'] = 'John Doe'
        config['password'] = '123456789'
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        body = '[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname"}, "metric": "cpu.cpu_count"}]'
        header = {'Content-Type': 'application/json',
                  'Authorization': 'Basic Sm9obiBEb2U6MTIzNDU2Nzg5'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_batch(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['batch'] = 2
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        metric2 = Metric('servers.myhostname.cpu.cpu_time',
                         123, raw_value=456, timestamp=5678910,
                         host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        handler.process(metric2)
        body = ('[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname"}, "metric": "cpu.cpu_count"}, '
                '{"timestamp": 5678910, "value": 123, "tags": {"hostname": "myhostname"}, "metric": "cpu.cpu_time"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_tags(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = 'tag1=tagv1 tag2=tagv2'
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, '
                '"tags": {"hostname": "myhostname", "tag1": "tagv1", "tag2": "tagv2"}, "metric": "cpu.cpu_count"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_prefix(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['prefix'] = 'diamond'
        metric = Metric('servers.myhostname.cpu.cpu_count',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')
        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname"}, '
                '"metric": "diamond.cpu.cpu_count"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_cpu_metrics_taghandling_default(self, mock_urlopen, mock_request):
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.cpu.cpu0.user',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, '
                '"tags": {"hostname": "myhostname", "cpuId": "cpu0", "myFirstTag": "myValue"}, "metric": "cpu.user"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_cpu_metrics_taghandling_0(self, mock_urlopen, mock_request):
        """
        deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.cpu.cpu0.user',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, '
                '"metric": "cpu.cpu0.user"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_cpu_metrics_taghandling_default2(self, mock_urlopen, mock_request):
        """
        aggregate default
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.cpu.total.user',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        assert not mock_urlopen.called, "should not process"

    def test_cpu_metrics_taghandling_1(self, mock_urlopen, mock_request):
        """
        aggregate deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.cpu.total.user',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, '
                '"tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, "metric": "cpu.total.user"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_cpu_metrics_taghandling_2(self, mock_urlopen, mock_request):
        """
        aggregate deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = True
        config['skipAggregates'] = False

        metric = Metric('servers.myhostname.cpu.total.user',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, '
                '"tags": {"hostname": "myhostname", "cpuId": "total", "myFirstTag": "myValue"}, '
                '"metric": "cpu.user"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_haproxy_metrics_default(self, mock_urlopen, mock_request):
        """
        taghandling default
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.haproxy.SOME-BACKEND.SOME-SERVER.'
                        'bin',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, "tags": {'
                '"hostname": "myhostname", "server": "SOME-SERVER", '
                '"backend": "SOME-BACKEND", "myFirstTag": "myValue"}, '
                '"metric": "haproxy.bin"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_haproxy_metrics(self, mock_urlopen, mock_request):
        """
        taghandling deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.haproxy.SOME-BACKEND.SOME-SERVER.'
                        'bin',
                        123, raw_value=123, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 123, "tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, '
                '"metric": "haproxy.SOME-BACKEND.SOME-SERVER.bin"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_diskspace_metrics_default(self, mock_urlopen, mock_request):
        """
        taghandling default
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.diskspace.MOUNT_POINT.byte_percent'
                        'free',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ( '[{"timestamp": 1234567, "value": 80, '
                 '"tags": {"hostname": "myhostname", "mountpoint": "MOUNT_POINT", "myFirstTag": "myValue"}, '
                 '"metric": "diskspace.byte_percentfree"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_diskspace_metrics(self, mock_urlopen, mock_request):
        """
        taghandling deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.diskspace.MOUNT_POINT.byte_'
                        'percentfree',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 80, "tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, '
                '"metric": "diskspace.MOUNT_POINT.byte_percentfree"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_iostat_metrics_default(self, mock_urlopen, mock_request):
        """
        taghandling default
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.iostat.DEV.io_in_progress',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 80, '
                '"tags": {"hostname": "myhostname", "device": "DEV", "myFirstTag": "myValue"}, '
                '"metric": "iostat.io_in_progress"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_iostat_metrics(self, mock_urlopen, mock_request):
        """
        taghandling deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.iostat.DEV.io_in_progress',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 80, "tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, '
                '"metric": "iostat.DEV.io_in_progress"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_network_metrics_default(self, mock_urlopen, mock_request):
        """
        taghandling default
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']

        metric = Metric('servers.myhostname.network.IF.rx_packets',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 80, '
                '"tags": {"hostname": "myhostname", "interface": "IF", "myFirstTag": "myValue"}, '
                '"metric": "network.rx_packets"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)

    def test_network_metrics(self, mock_urlopen, mock_request):
        """
        taghandling deactivate
        """
        config = configobj.ConfigObj()
        config['host'] = '127.0.0.1'
        config['port'] = '4242'
        config['tags'] = ['myFirstTag=myValue']
        config['cleanMetrics'] = False

        metric = Metric('servers.myhostname.network.IF.rx_packets',
                        80, raw_value=80, timestamp=1234567,
                        host='myhostname', metric_type='GAUGE')

        handler = TSDBHandler(config)
        handler.process(metric)
        body = ('[{"timestamp": 1234567, "value": 80, "tags": {"hostname": "myhostname", "myFirstTag": "myValue"}, '
                '"metric": "network.IF.rx_packets"}]')
        header = {'Content-Type': 'application/json'}
        mock_urlopen.assert_called_with(self.url, body, header)
