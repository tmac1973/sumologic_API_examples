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

import json
import csv
import pathlib
from modules.sumologic import SumoLogic

key = ''
secret = ''
endpoint = 'https://api.us2.sumologic.com/api'
# This CSV file should have columns named "First", "Last", "Email"
csv_file_string = pathlib.Path('/path/to/some/file.csv')

sumo = SumoLogic(key, secret, endpoint=endpoint)
# Later when we create users we have to define their role by id, so we're getting that here for the administrator role
# and adding it to a list called role_ids
existing_roles = sumo.get_roles_sync()
for existing_role in existing_roles:
    if existing_role['name'] == 'Administrator':
        role_ids = [existing_role['id']]
        break

# We need to make sure we don't add anyone that already exists, so get a list of current users..
existing_users = sumo.get_users_sync()

# Open up the csv...
with open(csv_file_string) as csv_file:
    data = csv.DictReader(csv_file)
    for row in data:
        user_found = False
        # iterate through each existing user and compare the the csv entry we are trying to add...
        for existing_user in existing_users:
            if row['Email'] == existing_user['email']:
                user_found = True
                print('Skipping user {} {} with email {}. User already exists.'.format(row['First'], row['Last'], row['Email']))
                break
        # if it exists already skip it
        # otherwise add it
        if not user_found:
            try:
                print('Adding user {} {} with email {}'.format(row['First'], row['Last'], row['Email']))
                sumo.create_user(row['First'], row['Last'], row['Email'], role_ids)
            except Exception as e:
                print('Failed to add user {} {} with email {}'.format(row['First'], row['Last'], row['Email']))
                print(e)








