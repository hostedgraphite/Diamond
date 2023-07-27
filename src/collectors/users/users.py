# coding=utf-8

"""
Collects the number of users logged in and shells per user

#### Dependencies

 * [pyutmp](http://software.clapper.org/pyutmp/)
or
 * [utmp] (https://pypi.org/project/utmp/)

"""

import diamond.collector

try:
    from pyutmp import UtmpFile
except ImportError:
    UtmpFile = None
try:
    from utmp import reader
except ImportError:
    reader = None


class UsersCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        """
        Returns the default collector help text
        """
        config_help = super(UsersCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(UsersCollector, self).get_default_config()
        config.update({
            'path': 'users',
            'utmp': None,
        })
        return config

    def collect(self):
        if UtmpFile is None and reader is None:
            self.log.error('Unable to import either pyutmp or utmp')
            return False

        metrics = {'total': 0}

        if UtmpFile:
            for utmp in UtmpFile(path=self.config['utmp']):
                if utmp.ut_user_process:
                    metrics[utmp.ut_user] = metrics.get(utmp.ut_user, 0) + 1
                    metrics['total'] = metrics['total'] + 1

        if reader:
            with open(self.config['utmp'], 'rb') as fd:
                buf = fd.read()
                for entry in reader.read(buf):
                    if entry.type == reader.UTmpRecordType.user_process:
                        metrics[entry.user] = metrics.get(entry.user, 0) + 1
                        metrics['total'] = metrics['total'] + 1

        for metric_name in metrics.keys():
            self.publish(metric_name, metrics[metric_name])

        return True
