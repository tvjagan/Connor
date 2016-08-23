from __future__ import print_function, absolute_import, division

from datetime import datetime
import getpass
import itertools
import logging
import socket
import sys

def zrange(*args):
    try:
        return xrange(*args)
    except NameError:
        return range(*args)

def iter_map(*args):
    try:
        return itertools.imap(*args)
    except AttributeError:
        return map(*args)


class UsageError(Exception):
    '''Raised for malformed command or invalid arguments.'''
    def __init__(self, msg, *args):
        super(UsageError, self).__init__(msg, *args)

class CountingGenerator(object):
    def __init__(self):
        self.item_count = 0

    def count(self, generator):
        for i in generator:
            self.item_count += 1
            yield i

class FilteredGenerator(object):
    '''Applies filters to a base collection yielding the item and its filter'''
    def __init__(self, filter_dict):
        '''
        Args:
            filter_dict (dict): key = filter name, value = function that
                that accepts an item and returns true is that item should
                be excluded. For example: {"div by 2": lambda x: x % 2 == 0}
        '''
        self._filters = sorted(filter_dict.items(), key=lambda x: x[0])
#         self._filter_stats = defaultdict(int)
#         self.total_included = 0
#         self.total_excluded = 0

    def filter(self, base_collection):
        '''Yields subset of base_collection/generator based on filters.'''
        for item in base_collection:
            excluded = []
            for (name, exclude) in self._filters:
                if exclude(item):
                    excluded.append(name)
            if excluded:
                filter_value = ";".join(excluded)
#                 self._filter_stats[filter_value] += 1
#                 self.total_excluded += 1
            else:
                filter_value = None
#                 self.total_included += 1
            yield item, filter_value

#     @property
#     def filter_stats(self):
#         '''Returns an immutable ordered dict of filter:counts; when an item
#         would be filtered by multiple filters, all are listed in alpha order;
#         the dict itself is ordered by descending count, filter name.
#         '''
#         return OrderedDict(sorted(self._filter_stats.items(),
#                                    key=lambda x: (-1 * x[1], x[0])))


class Logger(object):
    _DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    _FILE_LOG_FORMAT = ('%(asctime)s|%(levelname)s|%(start_time)s|%(host)s|'
                        '%(user)s|%(message)s')
    _CONSOLE_LOG_FORMAT = '%(asctime)s|%(levelname)s|%(message)s'

    def __init__(self, args, console_stream=None):
        self._verbose = args.verbose
        self._log_filename = args.log_file
        if console_stream:
            self._console_stream = console_stream
        else:
            self._console_stream = sys.stderr
        user = getpass.getuser()
        host = socket.gethostname()
        start_time = datetime.now().strftime(Logger._DATE_FORMAT)
        self._logging_dict = {'user': user,
                              'host': host,
                              'start_time' : start_time}
        logging.basicConfig(format=Logger._FILE_LOG_FORMAT,
                            level="DEBUG",
                            datefmt=Logger._DATE_FORMAT,
                            filename=self._log_filename)
        self._file_logger = logging
        self.warning_occurred = False

    def _print(self, level, message, args):
        now = datetime.now().strftime(Logger._DATE_FORMAT)
        print(Logger._CONSOLE_LOG_FORMAT % {'asctime': now,
                                            'levelname': level,
                                            'message': self._format(message,
                                                                    args)},
              file=self._console_stream)
        self._console_stream.flush()

    @staticmethod
    def _format(message, args):
        try:
            log_message = message.format(*[i for i in args])
        except IndexError as err:
            log_message = ("Malformed log message ({}: {})"
                           "|{}|{}").format(type(err).__name__,
                                            err,
                                            message,
                                            [str(i) for i in args])
        return log_message

    def debug(self, message, *args):
        if self._verbose:
            self._print("DEBUG", message, args)
        self._file_logger.debug(self._format(message, args),
                               extra=self._logging_dict)

    def error(self, message, *args):
        self._print("ERROR", message, args)
        self._file_logger.error(self._format(message, args),
                               extra=self._logging_dict)

    def info(self, message, *args):
        self._print("INFO", message, args)
        self._file_logger.info(self._format(message, args),
                              extra=self._logging_dict)

    def warning(self, message, *args):
        self._print("WARNING", message, args)
        self._file_logger.warning(self._format(message, args),
                                 extra=self._logging_dict)
        self.warning_occurred = True
