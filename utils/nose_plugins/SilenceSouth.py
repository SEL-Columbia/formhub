from nose.plugins import Plugin

import logging


class SilenceSouth(Plugin):
    south_logging_level = logging.ERROR

    def configure(self, options, conf):
        super(SilenceSouth, self).configure(options, conf)
        logging.getLogger('south').setLevel(self.south_logging_level)
