import os
import sys
import logging

import libgiza.config


logger = logging.getLogger('dagger.config.cli')

if sys.version_info >= (3, 0):
    basestring = str


class DaggerCliConfig(libgiza.config.ConfigurationBase):
    # the function attribute is used by argh in its dispatching.
    @property
    def function(self):
        return self.state['_entry_point']

    @function.setter
    def function(self, value):
        if callable(value):
            self.state['_entry_point'] = value
        else:
            raise TypeError

    def get_function(self):
        return self.state['_entry_point']

    # set logging level to increase or decrease logging verbosity
    @property
    def level(self):
        if 'level' not in self.state:
            return 'info'

        return self.state['level']

    @level.setter
    def level(self, value):
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }

        if value not in levels:
            value = 'info'

        logging.basicConfig()
        root_logger = logging.getLogger()

        root_logger.setLevel(levels[value])
        self.state['level'] = value

    @property
    def path(self):
        if 'path' in self.state:
            return self.state['path']
        else:
            raise KeyError("Path is not set")

    @path.setter
    def path(self, value):
        if isinstance(value, basestring):
            if os.path.isfile(value):
                self.state['path'] = value
            else:
                raise ValueError("Path must be a valid file")
        else:
            raise TypeError("Path must be a string corresponding to a file name")












