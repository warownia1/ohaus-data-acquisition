import logging
import re
from configparser import ConfigParser

import serial
import numpy
import itertools
import time

from collections import deque
from threading import Lock, Thread, Event


class SerialTimeoutException(Exception):
    pass


class DataCollectionNotRunningException(Exception):
    pass


BYTESIZES = {
    '5': serial.FIVEBITS,
    '6': serial.SIXBITS,
    '7': serial.SEVENBITS,
    '8': serial.EIGHTBITS
}

PARITIES = {
    'NONE': serial.PARITY_NONE,
    'EVEN': serial.PARITY_EVEN,
    'ODD': serial.PARITY_ODD
}

STOPBITS = {
    '1': serial.STOPBITS_ONE,
    '1.5': serial.STOPBITS_ONE_POINT_FIVE,
    '2': serial.STOPBITS_TWO
}


def load_config(file):
    if isinstance(file, str):
        with open(file) as f:
            return load_config(f)
    conf = ConfigParser()
    conf.read_file(file)
    return {
        'port': conf.get('connection', 'port'),
        'baudrate': conf.getint('connection', 'baudrate'),
        'bytesize': BYTESIZES[conf.get('connection', 'bytesize')],
        'parity': PARITIES[conf.get('connection', 'parity')],
        'stopbits': STOPBITS[conf.get('connection', 'stopbits')],
        'timeout': conf.getint('connection', 'timeout'),
        'xonxoff': conf.getboolean('connection', 'xonxoff')
    }


class CollectorThread(Thread):

    _count = itertools.count()
    _data_pattern = re.compile(rb'\s*(-?\d+\.\d+) g')

    def __init__(self, conn, interval=0.5):
        super().__init__(name=self.generate_name())
        self._interval = interval
        self._running_evt = Event()
        self._break_evt = Event()
        self._serial = conn
        self._exceptions = deque()
        self._last_value = 0.0
        self._data = numpy.zeros(1000)
        self._len = 0

    def interrupt(self):
        self._break_evt.set()
        self._running_evt.set()

    def pause(self):
        self._running_evt.clear()

    def resume(self):
        self._serial.flushInput()
        self._running_evt.set()

    def run(self):
        last_time = time.time()
        try:
            self._serial.flushInput()
            self._running_evt.set()
            while self._running_evt.wait() and not self._break_evt.is_set():
                # fixme: readline blocks and there is no way to unlock it
                line = self._serial.readline()
                match = self._data_pattern.match(line)
                if match is None:
                    logging.warning('"%s" does not match the pattern' % line)
                    continue
                self._last_value = float(match.group(1))
                current_time = time.time()
                if last_time + self._interval <= current_time:
                    last_time += (
                        ((current_time - last_time) // self._interval + 1)
                        * self._interval
                    )
                    self._data[self._len] = self._last_value
                    self._len += 1
                    # double the size of the array when limit reached
                    if self._len == self._data.size:
                        self._data = numpy.resize(self._data, self._len * 2)
        except Exception as e:
            self._running_evt.clear()
            self._exceptions.append(e)
            logging.exception('Collector loop interrupted')

    def get_mean(self):
        return numpy.mean(self.data) if self.len >= 1 else 0.0

    def get_std(self):
        if self.len >= 1:
            return numpy.std(self.data)
        else:
            return float('nan')

    @property
    def last_value(self):
        return self._last_value

    @property
    def data(self):
        return self._data[:self._len]

    @property
    def len(self):
        return self._len

    def is_running(self):
        return self._running_evt.is_set()

    @classmethod
    def generate_name(cls):
        return 'CollectorThread %u' % next(cls._count)


class DataAcquisition:

    def __init__(self):
        self._serial = serial.Serial(**load_config('./config.cfg'))
        self._collector_thread = None
        self._restart_lock = Lock()

    def start(self):
        """
        Start running data collection thread. If there is a collection thread
        currently running, it's stopped. Serial connection is re-opened, input
        flushed and all values re-set.
        New collection thread is deployed in the end.
        """
        with self._restart_lock:
            if self._collector_thread:
                self.reset()
            while not self._serial.isOpen():
                try:
                    self._serial.open()
                except serial.serialutil.SerialException:
                    logging.warning(
                        'Attempt to open the port failed, retrying...')
            self._collector_thread = CollectorThread(conn=self._serial)
            self._collector_thread.start()

    def reset(self):
        """
        Stops current data collection and dispose the thread.
        """
        self._collector_thread.interrupt()
        self._collector_thread.join()
        self._collector_thread = None

    def close(self):
        """
        Close currently opened serial port.
        """
        self._serial.close()

    def __getattr__(self, item):
        """
        Gives easy access to the selected elements of the collector thread.
        """
        if item in {'pause', 'resume', 'get_mean', 'get_std',
                    'last_value', 'data', 'len'}:
            if self._collector_thread is None:
                raise DataCollectionNotRunningException
            else:
                return getattr(self._collector_thread, item)
        raise AttributeError("'%s' object has no attribute '%s'" %
                             (self.__class__.__name__, item))
