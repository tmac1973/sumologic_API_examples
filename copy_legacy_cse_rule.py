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

# This works for legacy CSE implementations that have a separate API. If your instance has a unified API
# you'll need to modify this script
import json

from modules.sumologic_cse import SumoLogicCSE
import argparse

def process_arguments():
    parser = argparse.ArgumentParser(description="Copy a CSE Rule between orgs")
    parser.add_argument('-sourcekey', required=True, help='API key for the source')
    parser.add_argument('-sourceurl', required=True, help='URL for the source')
    parser.add_argument('-destkey', required=True, help='API key for the destination')
    parser.add_argument('-desturl', required=True, help='URL for the destination')
    parser.add_argument('-rule', required=True, help='The Rule ID')
    args = parser.parse_args()
    return args

def remove_json_keys(json):
    # all of the following keys are part of the rule export but will cause the import to fail
    remove_keys = ['created', 'createdBy', 'contentType', 'deleted', 'id', 'lastUpdated', 'lastUpdatedBy', 'ruleId',
                   'ruleSource', 'ruleType', 'signalCount07d', 'signalCount24h', 'status',
                   'descriptionExpressionOverride', 'entitySelectorsOverride', 'nameExpressionOverride',
                   'scoreMappingOverride', 'summaryExpressionOverride', 'hasOverride', 'nameOverride',
                   'isPrototypeOverride', 'tagsOverride']
    for remove_key in remove_keys:
        if remove_key in json:
            del json[remove_key]
    return {'fields': json}

def main():
    arguments = process_arguments()
    source_cse = SumoLogicCSE(arguments.sourcekey, arguments.sourceurl)
    dest_cse = SumoLogicCSE(arguments.destkey, arguments.desturl)

    exported_rule = source_cse.get_rule(str(arguments.rule))
    #print(f"Exported rule: {json.dumps(exported_rule)}")
    rule_type = exported_rule['ruleType']
    #print(f"Rule type: {rule_type}")
    processed_rule = remove_json_keys(exported_rule)
    if processed_rule['fields']['scoreMapping']['mapping'] is None:
        processed_rule['fields']['scoreMapping']['mapping'] = []
    if rule_type == 'templated match':
        result = dest_cse.create_templated_match_rule(processed_rule)
    elif rule_type == 'match':
        result = dest_cse.create_match_rule(processed_rule)
    elif rule_type == 'chain':
        result = dest_cse.create_chain_rule(processed_rule)
    elif rule_type == 'threshold':
        result = dest_cse.create_threshold_rule(processed_rule)
    elif rule_type == 'aggregation':
        result = dest_cse.create_aggregation_rule(processed_rule)


if __name__ == "__main__":
    main()


