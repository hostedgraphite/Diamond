# coding=utf-8

"""
Collects stats from bind 9.5's statistics server

#### Dependencies

 * [bind 9.5](http://www.isc.org/software/bind/new-features/9.5)
    configured with libxml2 and statistics-channels

"""

import diamond.collector
import diamond.pycompat
import xml.etree.cElementTree as ElementTree


class BindCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(BindCollector, self).get_default_config_help()
        config_help.update({
            'host': "",
            'port': "",
            'publish': "Available stats:\n" +
            " - resolver (Per-view resolver and cache statistics)\n" +
            " - server (Incoming requests and their answers)\n" +
            " - zonemgmt (Zone management requests/responses)\n" +
            " - sockets (Socket statistics)\n" +
            " - memory (Global memory usage)\n",
            'publish_view_bind': "",
            'publish_view_meta': "",
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(BindCollector, self).get_default_config()
        config.update({
            'host': 'localhost',
            'port': 8080,
            'path': 'bind',
            # Available stats:
            # - resolver (Per-view resolver and cache statistics)
            # - server (Incoming requests and their answers)
            # - zonemgmt (Requests/responses related to zone management)
            # - sockets (Socket statistics)
            # - memory (Global memory usage)
            'publish': [
                'resolver',
                'server',
                'zonemgmt',
                'sockets',
                'memory',
            ],
            # By default we don't publish these special views
            'publish_view_bind': False,
            'publish_view_meta': False,
        })
        return config

    def clean_counter(self, name, value):
        value = self.derivative(name, value)
        if value < 0:
            value = 0
        self.publish(name, value)

    def collect(self):
        try:
            req = diamond.pycompat.urlopen('http://%s:%d/' % (
                self.config['host'], int(self.config['port'])))
        except Exception as e:
            self.log.error('Couldnt connect to bind: %s', e)
            return {}

        tree = ElementTree.fromstring(req.read())

        if not tree:
            raise ValueError("Corrupt XML file, no statistics found")

        root = tree

        if 'resolver' in self.config['publish']:
            for view in root.findall('views/view'):
                name = view.attrib.get('name')
                if name == '_bind' and not self.config['publish_view_bind']:
                    continue
                if name == '_meta' and not self.config['publish_view_meta']:
                    continue
                nzones = len(view.findall('zones/zone'))
                self.publish('view.%s.zones' % name, nzones)
                for counter in view.findall('rdtype'):
                    self.clean_counter(
                        'view.%s.query.%s' % (name,
                                              counter.find('name').text),
                        int(counter.find('counter').text)
                    )
                for counter in view.findall('counters[@type="resstats"]/counter'):
                    self.clean_counter(
                        'view.%s.resstat.%s' % (
                            name,
                            counter.attrib.get('name')
                        ),
                        int(counter.text)
                    )
                for counter in view.findall('cache/rrset'):
                    self.clean_counter(
                        'view.%s.cache.%s' % (
                            name, counter.find('name').text.replace('!',
                                                                    'NOT_')),
                        int(counter.find('counter').text)
                    )

        if 'server' in self.config['publish']:
            for counter in root.findall('server/counters[@type="opcode"]/counter'):
                self.clean_counter(
                    'requests.%s' % counter.attrib.get('name'),
                    int(counter.text)
                )
            for counter in root.findall('server/counters[@type="resqtype"]/counter'):
                self.clean_counter(
                    'queries.%s' % counter.attrib.get('name'),
                    int(counter.text)
                )
            for counter in root.findall('server/counters[@type="nsstat"]/counter'):
                self.clean_counter(
                    'nsstat.%s' % counter.attrib.get('name'),
                    int(counter.text)
                )

        if 'zonemgmt' in self.config['publish']:
            for counter in root.findall('server/counters[@type="zonestat"]/counter'):
                self.clean_counter(
                    'zonestat.%s' % counter.attrib.get('name'),
                    int(counter.text)
                )

        if 'sockets' in self.config['publish']:
            for counter in root.findall('server/counters[@type="sockstat"]/counter'):
                self.clean_counter(
                    'sockstat.%s' % counter.attrib.get('name'),
                    int(counter.text)
                )

        if 'memory' in self.config['publish']:
            for counter in list(root.find('memory/summary')):
                self.publish(
                    'memory.%s' % counter.tag,
                    int(counter.text)
                )
