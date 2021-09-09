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
import csv
import sys
import pathlib
from modules.sumologic import SumoLogic
from logzero import logger
from typing import Union
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED, as_completed
import logzero
import argparse
from urllib.parse import quote


def endpoint(deployment):
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


def export_content(key: str,
                   secret: str,
                   endpoint: str,
                   path_to_content: str) -> Union[dict, bool]:
    try:
        sumo = SumoLogic(key, secret, endpoint=endpoint)
        content_item = sumo.get_content_by_path(path_to_content)
        content_item_name = content_item['name']
        content_item_id = content_item['id']
        logger.info('Exporting {} with id {}'.format(content_item_name, content_item_id))
        exported_content = sumo.export_content_job_sync(content_item_id, adminmode=True)
        logger.info('Export of {} successful.'.format(content_item_name))
        return exported_content

    except Exception as e:
        logger.debug('Failed content export ERROR: {}'.format(e))
        return False


def get_users_and_roles(org_name, org_id, key, secret, api_endpoint):
    try:
        sumo = SumoLogic(key, secret, endpoint=api_endpoint)
        roles = sumo.get_roles_sync()
        users = sumo.get_users_sync()

        return {'org': org_name,
                'org_id': org_id,
                'endpoint': api_endpoint,
                'status': 'SUCCESS',
                'line_number': None,
                'exception': None}

    except Exception as e:
        _, _, tb = sys.exc_info()
        lineno = tb.tb_lineno
        return {'org': org_name,
                'org_id': org_id,
                'endpoint': api_endpoint,
                'status': 'FAIL',
                'line_number': lineno,
                'exception': str(e)}

def read_org_list_csv(file_path: str) -> list:

    csv_file_path = pathlib.Path(file_path)
    org_list = []
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            org_list.append(row)
    return org_list

def process_arguments():
    parser = argparse.ArgumentParser(description='Generate an Excel spreadsheet containing a list of users and their role memberships')
    parser.add_argument('-orgFile', required=True, help='The csv file that contains a list of orgs with this header: orgName,orgID,deployment,key,secret')
    args = parser.parse_args()
    return args


def parallel_runner(org_list, destination_folder, content):

    threads = []
    # The max workers is set to 10 because the Sumo API rate limits with more than 10 concurrent connections
    with ThreadPoolExecutor(max_workers=10) as executor:
        for org in org_list:
            logger.info('Submitting content deploy thread for {}'.format(org['orgName']))
            threads.append(executor.submit(
                import_and_share_content,
                org['orgName'],
                org['orgID'],
                org['key'],
                org['secret'],
                endpoint(org['deployment']),
                destination_folder,
                content))
        #wait(threads, timeout=None, return_when=ALL_COMPLETED)
        for thread in as_completed(threads):
            logger.info(thread.result())


# This was for testing. Left in for posterity.
def serial_runner(org_list, destination_folder, content):

    for org in org_list:
        logger.info('Deploying content to  {}'.format(org['orgName']))
        result = import_and_share_content(org['orgName'],
                                          org['orgID'],
                                          org['key'],
                                          org['secret'],
                                          endpoint(org['deployment']),
                                          destination_folder,
                                          content)
        logger.info(json.dumps(result, indent=4))


def main():

    logzero.logfile('role_membership_audit.log')
    arguments = process_arguments()
    org_list = read_org_list_csv(arguments.orgFile)
    #serial_runner(org_list, arguments.destPath, content)
    parallel_runner(org_list, arguments.destPath, content)


if __name__ == "__main__":
    main()

