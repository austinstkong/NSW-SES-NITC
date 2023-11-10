from datetime import datetime
import pytz

def sydney_time_now():
    utc_now = datetime.utcnow()
    sydney_tz = pytz.timezone('Australia/Sydney')
    sydney_now = utc_now.replace(tzinfo=pytz.utc).astimezone(sydney_tz)
    return sydney_now
