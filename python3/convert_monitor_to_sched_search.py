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
from modules.sumologic import SumoLogic
from logzero import logger
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import logzero
import argparse

def return_scheduled_search_template():
    return json.loads("""
        {
            "description": "",
            "name": "",
            "search": {
                "byReceiptTime": false,
                "defaultTimeRange": "-5m",
                "parsingMode": "Manual",
                "queryParameters": [],
                "queryText": "",
                "viewName": ""
            },
            "searchSchedule": {
                "cronExpression": "17 * * * * ? *",
                "displayableTimeRange": "-5m",
                "muteErrorEmails": false,
                "notification": {
                    "includeCsvAttachment": false,
                    "includeHistogram": true,
                    "includeQuery": true,
                    "includeResultSet": true,
                    "subjectTemplate": "Search Alert: {{TriggerCondition}} found for {{SearchName}}",
                    "taskType": "EmailSearchNotificationSyncDefinition",
                    "toList": []
                },
                "parameters": [],
                "parseableTimeRange": {
                    "from": {
                        "relativeTime": "-5m",
                        "type": "RelativeTimeRangeBoundary"
                    },
                    "to": null,
                    "type": "BeginBoundedTimeRange"
                },
                "scheduleType": "RealTime",
                "threshold": {
                    "count": 0,
                    "operator": "gt",
                    "thresholdType": "group"
                },
                "timeZone": "America/Chicago"
            },
            "type": "SavedSearchWithScheduleSyncDefinition"
        }""")


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
    return endpoints[deployment]

def operator_lookup(monitor_operator):
    operators = {'GreaterThanOrEqual': 'ge',
                 'LessThanOrEqual': 'le',
                 'LessThan': 'lt',
                 'GreaterThan': 'gt'}
    return operators[monitor_operator]

def process_arguments():
    parser = argparse.ArgumentParser(description='Transform a folder full of log monitors into scheduled searches.')
    parser.add_argument('-key', required=True, help='The API key for the org')
    parser.add_argument('-secret', required=True, help='The API secret for the org')
    parser.add_argument('-deployment', required=True, help='The deployment for the org (e.g. us2, ca, dub, etc.)')
    parser.add_argument('-monitorFolder', required=True, help='The source folder for the log monitors to convert. Should start with "/Monitor"')
    parser.add_argument('-destFolder', required=True, help='The location to put the scheduled searches. Should start with "/Library"')
    parser.add_argument('-adminMode', help='Whether to use adminmode when creating searches (required to write to folders other than your own.)', action='store_true')
    args = parser.parse_args()
    return args


def convert(monitor, scheduled_search_folder_id, sumo_org, adminmode=False):
    try:
        monitor_details = sumo_org.get_monitor(monitor['id'])
        if monitor_details['monitorType'] == 'Logs':
            scheduled_search_template = return_scheduled_search_template()
            scheduled_search_template['name'] = monitor_details['name']
            scheduled_search_template['description'] = monitor_details['description']
            logger.info(f"Creating scheduled search from monitor name: {monitor_details['name']} Query: {monitor_details['queries'][0]['query']}")
            scheduled_search_template['search']['queryText'] = monitor_details['queries'][0]['query']
            scheduled_search_template['searchSchedule']['parseableTimeRange']['relativeTime'] = monitor_details['triggers'][0]['timeRange']
            scheduled_search_template['searchSchedule']['threshold']['count'] = int(monitor_details['triggers'][0]['threshold'])
            scheduled_search_template['searchSchedule']['threshold']['operator'] = operator_lookup(monitor_details['triggers'][0]['thresholdType'])
            for recipient in monitor_details['notifications'][0]['notification']['recipients']:
                scheduled_search_template['searchSchedule']['notification']['toList'].append(recipient)
            results = sumo_org.import_content_job(scheduled_search_folder_id, scheduled_search_template, adminmode=adminmode)
            logger.info(f"Wrote scheduled search {scheduled_search_template['name']}")
            logger.info(f"Disabling monitor: {monitor_details['name']}")
            monitor_details['isDisabled'] = True
            monitor_details['type'] = 'MonitorsLibraryMonitorUpdate'
            sumo_org.update_monitor(monitor['id'], monitor_details)
            logger.info(f"Monitor successfully disabled: {monitor_details['name']}")

            return {'results': results,
                    'status': 'SUCCESS',
                    'line_number': None,
                    'exception': None}

    except Exception as e:
        _, _, tb = sys.exc_info()
        lineno = tb.tb_lineno
        return {'results': None,
                'status': 'FAIL',
                'line_number': lineno,
                'exception': str(e)}


def parallel_runner(monitors, scheduled_search_folder_id, sumo_org, adminmode=False):
    threads = []
    # The max workers is set to 10 because the Sumo API rate limits with more than 10 concurrent connections
    with ThreadPoolExecutor(max_workers=10) as executor:
        for monitor in monitors:
            if monitor['contentType'] == 'Monitor':
                logger.info(f'Submitting convert job for {monitor["name"]}')
                threads.append(executor.submit(
                    convert,
                    monitor,
                    scheduled_search_folder_id,
                    sumo_org,
                    adminmode=adminmode
                    ))
    for thread in as_completed(threads):
        logger.info(json.dumps(thread.result()))


def serial_runner(monitors, scheduled_search_folder_id, sumo_org, adminmode=False):
    for monitor in monitors:
        if monitor['contentType'] == 'Monitor':
            logger.info(f'Submitting convert job for {monitor["name"]}')
            result = convert(
                monitor,
                scheduled_search_folder_id,
                sumo_org,
                adminmode=adminmode
                )
            logger.info(result)


def main():

    logzero.logfile('convert_monitor_to_sched_search.log')
    arguments = process_arguments()
    sumo_org = SumoLogic(str(arguments.key), str(arguments.secret), endpoint=endpoint_lookup(str(arguments.deployment)))
    monitors = sumo_org.get_monitor_by_path(arguments.monitorFolder)
    dest_folder = sumo_org.get_content_by_path(arguments.destFolder, adminmode=arguments.adminMode)
    dest_folder_id = dest_folder['id']
    logger.info(f"Destination folder {arguments.destFolder} has id {dest_folder_id}")
    parallel_runner(monitors['children'], dest_folder_id, sumo_org, adminmode=arguments.adminMode)


if __name__ == "__main__":
    main()