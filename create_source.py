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
import json

key = ''
secret = ''
endpoint = 'https://api.us2.sumologic.com/api'
collector_name = ''

source = json.loads("""
{"source":{
    "name":"auth",
    "category":"linux/authlog",
    "automaticDateParsing":true,
    "multilineProcessingEnabled":true,
    "useAutolineMatching":true,
    "forceTimeZone":false,
    "filters":[],
    "cutoffTimestamp":1485331200000,
    "encoding":"UTF-8",
    "fields":{},
    "pathExpression":"/var/log/auth*",
    "blacklist":[],
    "sourceType":"LocalFile"
  }}""")
sumo_org = SumoLogic(key, secret, endpoint=endpoint)
source_collector = sumo_org.get_collector_by_name(collector_name)
result = sumo_org.create_source(source_collector['collector']['id'], source)