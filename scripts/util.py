import datetime as dt
import time

from termcolor import colored


def notify(message, color, start_time):
    now = dt.timedelta(seconds=time.time() - start_time)
    print(colored('{} - {}'.format(now, message), color))
