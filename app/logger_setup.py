'''
logger_setup.py customizes the app's logging module. Each time an event is
logged the logger checks the level of the event (eg. debug, warning, info...).
If the event is above the approved threshold then it goes through. The handlers
do the same thing; they output to a file/shell if the event level is above their
threshold.

:Example:

        >>> from website import logger
        >>> logger.info('event', foo='bar')

**Levels**:
        - logger.debug('For debugging purposes')
        - logger.info('An event occured, for example a database update')
        - logger.warning('Rare situation')
        - logger.error('Something went wrong')
        - logger.critical('Very very bad')

You can build a log incrementally as so:

        >>> log = logger.new(date='now')
        >>> log = log.bind(weather='rainy')
        >>> log.info('user logged in', user='John')
'''

import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
import pytz

from flask import session
from structlog import wrap_logger
from structlog.processors import JSONRenderer

from app import app

# Set the logging level
app.logger.setLevel(app.config['LOG_LEVEL'])

tz = pytz.timezone(app.config['TIMEZONE'])

def add_fields(_, level, event_dict):
    ''' Add custom fields to each record. '''
    now = dt.datetime.now()
    event_dict['timestamp'] = tz.localize(now, True).astimezone(pytz.utc).isoformat()
    event_dict['session_id'] = session.get('session_id')
    event_dict['level'] = level
    return event_dict

# Add a handler to write log messages to a file
if app.config.get('LOG_FILE'):
    file_handler = RotatingFileHandler(app.config['LOG_FILENAME'],
                                       app.config['LOG_MAXBYTES'],
                                       app.config['LOG_BACKUPS'],
                                       mode='a',
                                       encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

# Wrap the application logger with structlog to format the output
logger = wrap_logger(
    app.logger,
    processors=[
        add_fields,
        JSONRenderer(indent=None)
    ]
)