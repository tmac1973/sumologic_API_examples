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


# This script takes a Sumo Logic content folder and downloads the content to the local hard drive

import json
from modules.sumologic import SumoLogic
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


def process_arguments():
    parser = argparse.ArgumentParser(description='Download the contents of a Sumo Logic folder.')
    parser.add_argument('-key', required=True, help='The API key for the org')
    parser.add_argument('-secret', required=True, help='The API secret for the org')
    parser.add_argument('-deployment', required=True, help='The deployment for the org (e.g. us2, ca, dub, etc.)')
    parser.add_argument('-sourceFolder', required=True, help='The Sumo Logic folder containing the content. Should start with "/Library"')
    parser.add_argument('-savePath', required=True, help='The local filesystem path to save the content to.')
    parser.add_argument('-adminMode', help='Whether to use adminmode when creating searches (required to read from Sumo folders other than your own.)', action='store_true')
    args = parser.parse_args()
    return args


def main():
    arguments = process_arguments()
    sumo_org = SumoLogic(str(arguments.key), str(arguments.secret), endpoint=endpoint_lookup(str(arguments.deployment)))
    sumo_folder = sumo_org.get_content_by_path(arguments.sourceFolder, adminmode=arguments.adminMode)
    sumo_folder_id = sumo_folder['id']
    sumo_folder_contents = sumo_org.get_folder(sumo_folder_id, adminmode=arguments.adminMode)['children']
    for content in sumo_folder_contents:
        content_export = sumo_org.export_content_job_sync(content['id'], adminmode=arguments.adminMode)
        file_name = f"{arguments.savePath}/{content['name']}.json"
        print(f'Writing file:{file_name}')
        with open(file_name, 'w') as f:
            json.dump(content_export, f)


if __name__ == "__main__":
    main()