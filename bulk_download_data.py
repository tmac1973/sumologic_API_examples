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

import json
import sys
import pathlib
import datetime
from modules.sumologic import SumoLogic
from logzero import logger
from typing import Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import logzero
import argparse


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
                       source_category: str,
                       access_id: str,
                       access_key: str,
                       api_endpoint: str) -> Union[dict, bool]:
    # create an instance of the Sumo Logic SDK
    sumo = SumoLogic(access_id, access_key, endpoint=api_endpoint)
    start_time_ISO = start_time.isoformat()
    end_time_ISO = end_time.isoformat()

    try:
        # execute the query
        query = f'_sourceCategory={str(source_category)}'
        messages = sumo.search_job_messages_sync(query,
                                             fromTime=start_time_ISO,
                                             toTime=end_time_ISO,
                                             timeZone='UTC')
        # we're about to write this to a file. We need a filename that doesn't have slashes in it
        sanitized_source_category = source_category.replace('/', '-')
        filename = f'{sanitized_source_category}-{start_time_ISO}-{end_time_ISO}.log'
        # the logs variable has a bunch of extra stuff in it. We're just interested in the raw logs data so
        # write that to a text file line by line
        if len(messages) > 0:
            with open(filename, 'w') as f:
                for message in messages:
                    f.write(message['map']['_raw'])
                    f.write('\n')
        # since we're multi-threaded we need to return status explicitly
        return {'query': query,
                'start': str(start_time_ISO),
                'end': str(end_time_ISO),
                'endpoint': api_endpoint,
                'num_results': len(messages),
                'status': 'SUCCESS',
                'line_number': None,
                'exception': None}
    # since we're multi-threaded we need to return status explicitly, especially if there's an issue
    except Exception as e:
        _, _, tb = sys.exc_info()
        lineno = tb.tb_lineno
        return {'query': query,
                'start': str(start_time_ISO),
                'end': str(end_time_ISO),
                'endpoint': api_endpoint,
                'num_messages': None,
                'status': 'FAIL',
                'line_number': lineno,
                'exception': str(e)}


def read_text_file(file_path_string: str) -> list:
    file_path = pathlib.Path(file_path_string)
    with open(file_path, 'r') as f:
        content = f.readlines()
    content = [line.strip() for line in content]
    return content


def process_arguments():
    parser = argparse.ArgumentParser(description='Download data between a range of datas for a selection of source categories.')
    parser.add_argument('-key', required=True, help='The API key for the org')
    parser.add_argument('-secret', required=True, help='The API secret for the org')
    parser.add_argument('-deployment', required=True, help='The deployment for the org (e.g. us2, ca, dub, etc.)')
    parser.add_argument('-startDate', required=True, help='The start date. YYYY-MM-DD')
    parser.add_argument('-endDate', required=True, help='The end date YYYY-MM-DD')
    parser.add_argument('-increment', required=True, help='The time increment, in hours')
    parser.add_argument('-categoryFile', required=True, help='File that contains a list of source categories, one per line.')
    args = parser.parse_args()
    return args


def parallel_runner(category_list, start_time, end_time, time_delta, api_key, api_secret, endpoint):

    threads = []
    # The max workers is set to 10 because the Sumo API rate limits with more than 10 concurrent connections
    current_start_time = start_time
    with ThreadPoolExecutor(max_workers=10) as executor:
        while end_time > current_start_time:
            for category in category_list:
                logger.info(f'Submitting search job for {category} starting at {current_start_time} ending at {current_start_time + time_delta}')
                threads.append(executor.submit(
                    download_and_write,
                    current_start_time,
                    current_start_time + time_delta,
                    category,
                    api_key,
                    api_secret,
                    endpoint
                    ))
            current_start_time = current_start_time + time_delta
    for thread in as_completed(threads):
        logger.info(json.dumps(thread.result()))

# This function isn't called but I left it in for troubleshooting and educational purposes
def serial_runner(category_list, start_time, end_time, time_delta, api_key, api_secret, endpoint):

    # The max workers is set to 10 because the Sumo API rate limits with more than 10 concurrent connections
    current_start_time = start_time
    while end_time > current_start_time:
        for category in category_list:
            logger.info(f'Submitting search job for {category} starting at {current_start_time} ending at {current_start_time + time_delta - datetime.timedelta(milliseconds=1)}')
            result = download_and_write(
                current_start_time,
                current_start_time + time_delta,
                category,
                api_key,
                api_secret,
                endpoint
                )
            logger.info(result)
        current_start_time = current_start_time + time_delta


def main():

    logzero.logfile('bulk_download_data.log')
    arguments = process_arguments()
    source_categories = read_text_file(arguments.categoryFile)
    start_time = datetime.datetime.strptime(arguments.startDate, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = datetime.datetime.strptime(arguments.endDate, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
    time_delta = datetime.timedelta(hours=int(arguments.increment))
    parallel_runner(source_categories,
                    start_time,
                    end_time,
                    time_delta,
                    str(arguments.key),
                    str(arguments.secret),
                    endpoint_lookup(str(arguments.deployment)))
    # serial_runner(source_categories,
    #                 start_time,
    #                 end_time,
    #                 time_delta,
    #                 str(arguments.key),
    #                 str(arguments.secret),
    #                 endpoint_lookup(str(arguments.deployment)))


if __name__ == "__main__":
    main()

