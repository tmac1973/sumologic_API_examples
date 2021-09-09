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


def process_arguments():
    parser = argparse.ArgumentParser(description='Find scheduled searches last modified by a disabled user and re-import to target directory.')
    parser.add_argument('-key', required=True, help='The API key for the source org')
    parser.add_argument('-secret', required=True, help='The API secret for the source org')
    parser.add_argument('-deployment', required=True, help='The deployment for the source org (e.g. us2, ca, dub, etc.')
    parser.add_argument('-userEmail', required=True, help='The email of the disabled user.')
    parser.add_argument('-destPath', required=True, help='The destination path for the content (e.g. /Library/Admin Recommended/fixed_alerts')
    parser.add_argument('-delete', required=False, action="store_true", help='Use this flag to also delete the original saved search after re-import.')
    args = parser.parse_args()
    return args


# The following function will recursively walk the Admin Recommended dir and find all searches last modified by
# the given user_id. It returns a list of item ids. These may or not be scheduled searches.
def find_orphaned_content(user_id, folder_id, sumo):
    orphaned_content = []
    if folder_id is None:
        folder = sumo.get_admin_folder_sync(adminmode=True)
    else:
        folder = sumo.get_folder(folder_id, adminmode=True)

    for child in folder['children']:
        if child['itemType'] == 'Folder':
            orphaned_content = orphaned_content + find_orphaned_content(user_id, child['id'], sumo)
        elif child['itemType'] == 'Search' and child['modifiedBy'] == user_id:
            orphaned_content.append(child['id'])

    return orphaned_content




def main():

    logzero.logfile('fix_orphaned_scheduled_searches.log')
    arguments = process_arguments()
    try:
        sumo = SumoLogic(arguments.key, arguments.secret, endpoint=endpoint(arguments.deployment))
        users = sumo.get_users_sync()
        user_id = None
        for user in users:
            if user['email'] == arguments.userEmail:
                user_id = user['id']
                break

        dest_folder_id = sumo.get_content_by_path(arguments.destPath, adminmode=True)['id']

        if user_id:
            content_ids = find_orphaned_content(user_id, None, sumo)
            for content_id in content_ids:
                content = sumo.export_content_job_sync(content_id, adminmode=True)
                # Check if this is a scheduled search (as opposed to just a search)
                if content['searchSchedule']:
                    logger.info(f'Found scheduled search: {content["name"]} Copying.')
                    sumo.import_content_job_sync(dest_folder_id, content, adminmode=True)
                    if arguments.delete:
                        logger.info(f'Copy complete. Deleting {content["name"]} from original location.')
                        sumo.delete_content_job_sync(content_id, adminmode=True)


        else:
            logger.info("User not found. Exiting.")
    except Exception as e:
        _, _, tb = sys.exc_info()
        lineno = tb.tb_lineno
        logger.info(f"Something went wrong on line {lineno}: {str(e)}")




if __name__ == "__main__":
    main()
