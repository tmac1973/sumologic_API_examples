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


# This script takes a folder full of saved searches and converts them to scheduled searches with email alerts
# The default in the script is to setup real time searches but you can modify the JSON to define some other schedule
# This script does not recurse folders.

import json
from modules.sumologic import SumoLogic
import argparse


def return_real_time_schedule():
    return json.loads("""
     {
        "cronExpression": "17 * * * * ? *",
        "displayableTimeRange": "-15m",
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
                "relativeTime": "-15m",
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
    }""")


def return_every_15_schedule():
    return json.loads("""
        {
            "cronExpression": "0 0/15 * * * ? *",
            "displayableTimeRange": "-15m",
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
                    "relativeTime": "-15m",
                    "type": "RelativeTimeRangeBoundary"
                },
                "to": null,
                "type": "BeginBoundedTimeRange"
            },
            "scheduleType": "15Minutes",
            "threshold": {
                "count": 0,
                "operator": "gt",
                "thresholdType": "group"
            },
            "timeZone": "America/Chicago"
        }
""")


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


def process_arguments():
    parser = argparse.ArgumentParser(description='Transform a folder full of saved searches into scheduled searches.')
    parser.add_argument('-key', required=True, help='The API key for the org')
    parser.add_argument('-secret', required=True, help='The API secret for the org')
    parser.add_argument('-deployment', required=True, help='The deployment for the org (e.g. us2, ca, dub, etc.)')
    parser.add_argument('-sourceFolder', required=True, help='The folder containing the saved searches"')
    parser.add_argument('-destFolder', required=True, help='The location to put the scheduled searches. Should start with "/Library"')
    parser.add_argument('-email',required=True, help='The email address to receive the alerts"' )
    parser.add_argument('-adminMode', help='Whether to use adminmode when creating searches (required to write to folders other than your own.)', action='store_true')
    args = parser.parse_args()
    return args


def main():
    arguments = process_arguments()
    sumo_org = SumoLogic(str(arguments.key), str(arguments.secret), endpoint=endpoint_lookup(str(arguments.deployment)))
    saved_searches_folder = sumo_org.get_content_by_path(arguments.sourceFolder, adminmode=arguments.adminMode)
    saved_searches_folder_id = saved_searches_folder['id']
    saved_searches_folder_contents = sumo_org.get_folder(saved_searches_folder_id, adminmode=arguments.adminMode)['children']
    dest_folder = sumo_org.get_content_by_path(arguments.destFolder, adminmode=arguments.adminMode)
    dest_folder_id = dest_folder['id']
    for saved_search in saved_searches_folder_contents:
        if saved_search['itemType'] == 'Search':
            saved_search_content = sumo_org.export_content_job_sync(saved_search['id'], adminmode=arguments.adminMode)
            if 'type' in saved_search_content and saved_search_content['type'] == 'SavedSearchWithScheduleSyncDefinition':
                saved_search_content['searchSchedule'] = return_real_time_schedule()
                #saved_search_content['searchSchedule'] = return_every_15_schedule()
                saved_search_content['searchSchedule']['notification']['toList'].append(str(arguments.email))
                print(f'Creating scheduled search for: {saved_search_content["name"]}')
                sumo_org.import_content_job_sync(dest_folder_id, saved_search_content)


if __name__ == "__main__":
    main()