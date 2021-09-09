# MIT License
#
# Copyright (c) 2021 Timothy MacDonald
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

import time
import datetime
import os
from modules.sumologic import SumoLogic

# lookup the API endpoint URL using the Sumo deployment name
def endpoint_lookup(deployment):
    # there are duplicates here because most deployments have 2 names
    endpoints = {'prod': 'https://api.sumologic.com/api',
                 'us1': 'https://api.sumologic.com/api',
                 'us2': 'https://api.us2.sumologic.com/api',
                 'eu': 'https://api.eu.sumologic.com/api',
                 'dub': 'https://api.eu.sumologic.com/api',
                 'ca': 'https://api.ca.sumologic.com/api',
                 'mon': 'https://api.ca.sumologic.com/api',
                 'de': 'https://api.de.sumologic.com/api',
                 'fra': 'https://api.de.sumologic.com/api',
                 'au': 'https://api.au.sumologic.com/api',
                 'syd': 'https://api.au.sumologic.com/api',
                 'jp': 'https://api.jp.sumologic.com/api',
                 'tky': 'https://api.jp.sumologic.com/api',
                 'in': 'https://api.in.sumologic.com/api',
                 'mum': 'https://api.in.sumologic.com/api',
                 'fed': 'https://api.fed.sumologic.com/api',
                 }
    return endpoints[str(deployment).lower()]


def download_and_write(start_time: datetime.datetime,
                       end_time: datetime.datetime,
                       query: str,
                       filename: str,
                       access_id: str,
                       access_key: str,
                       api_endpoint: str):
    # create an instance of the Sumo Logic SDK
    sumo = SumoLogic(access_id, access_key, endpoint=api_endpoint)
    start_time_ISO = start_time.isoformat()
    end_time_ISO = end_time.isoformat()

    try:
        sumo = SumoLogic(access_id, access_key, endpoint=api_endpoint)
        job_start_time = time.perf_counter()
        searchjob = sumo.search_job(query, fromTime=start_time_ISO, toTime=end_time_ISO)
        status = sumo.search_job_status(searchjob)
        nummessages = status['messageCount']
        while status['state'] != 'DONE GATHERING RESULTS':
            if status['state'] == 'CANCELLED':
                break
            status = sumo.search_job_status(searchjob)
            nummessages = status['messageCount']
            print(f"Search job running. Current result count is {nummessages}")
            time.sleep(2)
        if status['state'] == 'DONE GATHERING RESULTS':
            job_finish_time = time.perf_counter()
            iterations = nummessages // 10000 + 1

            with open(filename, 'a') as f:
                for iteration in range(1, iterations + 1):
                    print(f"Downloading and writing result block {iteration}/{iterations}")
                    messages = sumo.search_job_messages(searchjob, limit=10000,
                                                    offset=((iteration - 1) * 10000))
                    for message in messages['messages']:
                        f.write(message['map']['_raw'])
                        f.write('\n')
            download_finish_time = time.perf_counter()
            print(f"Search job took {job_finish_time - job_start_time:0.4f} seconds to complete.")
            print(f"Data download took {download_finish_time - job_finish_time:0.4f} seconds.")
            
        else:
            print(f"looks like something went wrong:{status['state']}")
    except Exception as e:
        print(str(e))


def main():
    query = "*"
    filename = "logs.txt"
    access_id = ""
    access_key = ""
    endpoint = endpoint_lookup('us2')

    # datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0)
    start_time = datetime.datetime(2021, 7, 10, minute=0, hour=0, second=0)
    stop_time = datetime.datetime(2021, 7, 14, minute=0, hour=0, second=0)

    #  remove previous file if it exists
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            print("Error while deleting file ", filename)

    download_and_write(start_time, stop_time, query, filename, access_id, access_key, endpoint)


if __name__ == "__main__":
    main()
