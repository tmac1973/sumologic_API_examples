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
import argparse


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
    parser = argparse.ArgumentParser(description="Populate a user's last name field with their email if it is empty.")
    parser.add_argument('-key', required=True, help='API key ID')
    parser.add_argument('-sec', required=True, help='API key Secret')
    parser.add_argument('-dep', required=True, help='Sumo Logic deployment for your org (prod, us2, eu, dub, ca, de, au, jp, in, fed)')
    args = parser.parse_args()
    return args

def main():
    arguments = process_arguments()
    sumo = SumoLogic(arguments.key, arguments.sec, endpoint=endpoint(arguments.dep))

    users = sumo.get_users_sync()
    for user in users:
        user_id = user['id']
        first_name = user['firstName']
        last_name = user['lastName']
        is_active = user['isActive']
        email = user['email']
        role_ids = user['roleIds']

        if not last_name:
            try:
                last_name = email
                result = sumo.update_user_by_field(user_id, first_name, last_name, is_active, role_ids)
                print(f'Updated user for email: {email}')
            except Exception as e:
                print(f"Something went wrong: {str(e)}")


if __name__ == "__main__":
    main()
