# coding=utf-8

"""
Collect HAProxy Stats

#### Dependencies

 * urlparse
"""

import re
import base64
import csv
import socket
import diamond.collector
import diamond.pycompat
from diamond.pycompat import Request


class HAProxyCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(HAProxyCollector, self).get_default_config_help()
        config_help.update({
            'method': "Method to use for data collection. Possible values: " +
                      "http, unix",
            'url': "Url to stats in csv format",
            'user': "Username",
            'pass': "Password",
            'sock': "Path to admin UNIX-domain socket",
            'ignore_servers': "Ignore servers, just collect frontend and " +
                              "backend stats",
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(HAProxyCollector, self).get_default_config()
        config.update({
            'method':           'http',
            'path':             'haproxy',
            'url':              'http://localhost/haproxy?stats;csv',
            'user':             'admin',
            'pass':             'password',
            'sock':             '/var/run/haproxy.sock',
            'ignore_servers':   False,
        })
        return config

    def _get_config_value(self, section, key):
        if section:
            if section not in self.config:
                self.log.error("Error: Config section '%s' not found", section)
                return None
            return self.config[section].get(key, self.config[key])
        else:
            return self.config[key]

    def http_get_csv_data(self, section=None):
        """
        Request stats from HAProxy Server
        """
        metrics = []
        req = Request(self._get_config_value(section, 'url'))
        try:
            handle = diamond.pycompat.urlopen(req)
            data = []
            for line in handle.readlines():
                data.append(line.decode())

            return data
        except Exception as e:
            if not hasattr(e, 'code') or e.code != 401:
                self.log.error("Error retrieving HAProxy stats. %s", e)
                return metrics

            # get the www-authenticate line from the headers
            # which has the authentication scheme and realm in it
            authline = e.headers['www-authenticate']

            # this regular expression is used to extract scheme and realm
            authre = (r'''(?:\s*www-authenticate\s*:)?\s*''' +
                      r'''(\w*)\s+realm=['"]([^'"]+)['"]''')
            authobj = re.compile(authre, re.IGNORECASE)
            matchobj = authobj.match(authline)
            if not matchobj:
                # if the authline isn't matched by the regular expression
                # then something is wrong
                self.log.error('The authentication header is malformed.')
                return metrics

            scheme = matchobj.group(1)
            # here we've extracted the scheme
            # and the realm from the header
            if scheme.lower() != 'basic':
                self.log.error('Invalid authentication scheme.')
                return metrics

            auth_header = '%s:%s' % (
                self._get_config_value(section, 'user'),
                self._get_config_value(section, 'pass')
            )
            base64string = base64.b64encode(auth_header.encode()).decode()
            req.add_header("Authorization", 'Basic %s' % base64string)
            try:
                handle = diamond.pycompat.urlopen(req)
                data = []
                for line in handle.readlines():
                    data.append(line.decode())

                return data
            except IOError as e:
                # here we shouldn't fail if the USER/PASS is right
                self.log.error("Error retrieving HAProxy stats. " +
                               "(Invalid username or password?) %s", e)
                return metrics

    def unix_get_csv_data(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        data = str()

        try:
            sock.connect(self.config['sock'])
            sock.send(b'show stat\n')
            while 1:
                buf = sock.recv(4096).decode()
                if not buf:
                    break
                data += buf
        except socket.error as e:
            self.log.error("Error retrieving HAProxy stats. %s", e)
            return []

        return data.strip().split('\n')

    def _generate_headings(self, row):
        headings = {}
        for index, heading in enumerate(row):
            headings[index] = self._sanitize(heading)
        return headings

    def _collect(self, section=None):
        """
        Collect HAProxy Stats
        """
        if self.config['method'] == 'http':
            csv_data = self.http_get_csv_data(section)
        elif self.config['method'] == 'unix':
            csv_data = self.unix_get_csv_data()
        else:
            self.log.error("Unknown collection method: %s",
                           self.config['method'])
            csv_data = []

        data = list(csv.reader(csv_data))
        headings = self._generate_headings(data[0])
        section_name = section and self._sanitize(section.lower()) + '.' or ''

        for row in data:
            if ((self._get_config_value(section, 'ignore_servers') and
                 row[1].lower() not in ['frontend', 'backend'])):
                continue

            part_one = self._sanitize(row[0].lower())
            part_two = self._sanitize(row[1].lower())
            metric_name = '%s%s.%s' % (section_name, part_one, part_two)

            for index, metric_string in enumerate(row):
                try:
                    metric_value = float(metric_string)
                except ValueError:
                    continue

                stat_name = '%s.%s' % (metric_name, headings[index])
                self.publish(stat_name, metric_value, metric_type='GAUGE')

    def collect(self):
        if 'servers' in self.config:
            if isinstance(self.config['servers'], list):
                for serv in self.config['servers']:
                    self._collect(serv)
            else:
                self._collect(self.config['servers'])
        else:
            self._collect()

    def _sanitize(self, s):
        """Sanitize the name of a metric to remove unwanted chars
        """
        return re.sub(r'[^\w-]', '_', s)
