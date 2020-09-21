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

key = ''
secret = ''
endpoint = 'https://api.us2.sumologic.com/api'
source_collector_name = 'test_collector_01'
target_collector_names = ['test_collector_02', 'test_collector_03']

sumo_org = SumoLogic(key, secret, endpoint=endpoint)
source_collector = sumo_org.get_collector_by_name(source_collector_name)
sources_to_copy = sumo_org.get_sources_sync(source_collector['collector']['id'])
for  target_collector_name in target_collector_names:
    target_collector = sumo_org.get_collector_by_name(target_collector_name)
    target_collector_id = target_collector['collector']['id']
    for source_to_copy in sources_to_copy:
        if 'id' in source_to_copy:
             del source_to_copy['id']
        source = {}
        source['source'] = source_to_copy
        sumo_org.create_source(target_collector_id, source)

