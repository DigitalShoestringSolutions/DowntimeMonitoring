# timestamp.py

# standard imports
import logging
# do we need to use both of the following together?
import time
import datetime

# startup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_timestamp():
    """Get a string containing the current lcoal time in ISO8601 format"""
    __dt = -1 * (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone)
    tz = datetime.timezone(datetime.timedelta(seconds=__dt))
    timestamp = datetime.datetime.now(tz=tz).isoformat()
    logger.debug("retrieved current timestamp as", timestamp)
    return timestamp
