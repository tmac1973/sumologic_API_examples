# MIT License
#
# Copyright (c) 2020 Timothy MacDonald
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from modules.sumologic import SumoLogic
from time import time

key = ''
secret = ''
endpoint = 'https://api.us2.sumologic.com/api'

namelist = ['kali']
min_collector_dead_time_hours = 1440  #default 1440 hours or 60 days
min_collector_dead_time_milliseconds = min_collector_dead_time_hours * 60 * 60 * 1000
current_time_milliseconds = int(time() * 1000)

sumo_org = SumoLogic(key, secret, endpoint=endpoint)
collectors = sumo_org.get_collectors_sync()
for collector in collectors:
    timedelta = int(current_time_milliseconds) - int(collector['lastSeenAlive'])

    if (collector['alive'] == False) and (timedelta > min_collector_dead_time_milliseconds):
        for name in namelist:
            if name in collector['name']:
                print("Deleting collector " + str(collector['name']))
                sumo_org.delete_collector(collector['id'])
