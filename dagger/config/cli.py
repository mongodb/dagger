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
