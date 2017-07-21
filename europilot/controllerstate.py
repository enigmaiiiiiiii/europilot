import sys
from subprocess import PIPE, Popen
from threading import Thread
from Queue import Queue
import json
from collections import OrderedDict


class ControllerOutput(object):
    """
    Reads stdout from G27.py, to get the controller event outputs without
    blocking.
    """
    def __init__(self):
        ON_POSIX = 'posix' in sys.builtin_module_names
        # use unbuffered output, since stdout will be generally small
        # https://stackoverflow.com/questions/1410849/bypassing-buffering-of-subprocess-output-with-popen-in-c-or-python
        self.p = Popen(['python', '-u', 'g27.py'], bufsize=0, stdout=PIPE,
                       close_fds=ON_POSIX)
        self.q = Queue()
        self.t = Thread(target=self.__enqueue_output,
                        args=(self.p, self.q))
        self.t.daemon = True  # thread dies with program

    def start(self):
        self.t.start()

    def __enqueue_output(self, process, queue):
        """Insert stdout into queue"""
        for line in iter(process.stdout.readline, ''):
            print("line: %s" % line)
            queue.put(line)

        process.stdout.close()

    def get_output(self):
        """Append all of the items in the queue
            >>> c.get_output()
            >>> ['wheel-axis  256', 'wheel-axis  252', 'wheel-axis  244']
        """
        message = []
        for _ in range(0, self.q.qsize()):
            message.append(self.q.get().strip())
        return message


class ControllerState(object):
    """
    Holds the latest value of each of the controller output value.
        >>> c = ControllerState()
        >>> c.start()
        >>> c.get_state()
        OrderedDict([('wheel-axis', '1012'), ('clutch', '-27865'),...]
    """
    def __init__(self):
        self.output = ControllerOutput()
        self.state = self.__init_dict()

    def start(self):
        self.output.start()

    def __init_dict(self):
        """Initialize the values for each of the controller output"""
        d = OrderedDict()
        d['wheel-axis'] = 0
        d['clutch'] = -32767
        d['brake'] = -32767
        d['gas'] = -32767
        d['paddle-left'] = 0
        d['paddle-right'] = 0
        d['wheel-button-left-1'] = 0
        d['wheel-button-left-2'] = 0
        d['wheel-button-left-3'] = 0
        d['wheel-button-right-1'] = 0
        d['wheel-button-right-2'] = 0
        d['wheel-button-right-3'] = 0
        d['shifter-button-left'] = 0
        d['shifter-button-right'] = 0
        d['shifter-button-up'] = 0
        d['shifter-button-down'] = 0
        d['dpad-left/right'] = 0
        d['dpad-up/down'] = 0
        d['shifter-button-1'] = 0
        d['shifter-button-2'] = 0
        d['shifter-button-3'] = 0
        d['shifter-button-4'] = 0
        d['gear-1'] = 0
        d['gear-2'] = 0
        d['gear-3'] = 0
        d['gear-4'] = 0
        d['gear-5'] = 0
        d['gear-6'] = 0
        d['gear-R'] = 0

        return d

    def __update_state(self):
        """Update ControllerState with the latest controller data"""
        o = self.output.get_output()
        # iterate through all of the stdout from beginning to end.
        for msg in o:
            msg = msg.split(' ')
            k, v = msg[0], msg[1]
            if k in self.state:
                self.state[k] = v

    def get_state(self):
        """returns the latest state"""
        self.__update_state()
        return self.state

    def get_state_json(self):
        """returns the latest state in json format"""
        self.__update_state()
        j = json.dumps(self.state)
        return j
