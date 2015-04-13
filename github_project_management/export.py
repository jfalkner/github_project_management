from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import date
import pytz

import github3

from github_project_management import constants as GPMC
from github_project_management import list_issues
from github_project_management import milestone_url


def export(
    gh_user,
    gh_password,
    gh_api_url,
    configs,
    # Defaults: only display the GH issue and format dates in ISO style.
    date_format=lambda x: x.strftime('%Y-%m-%d')):

    # Track all issues in the timeframe.
    tz = pytz.timezone('US/Pacific')
    today = tz.localize(datetime.today())
    recent_end_date = today - timedelta(seconds=(today.hour * 60 * 60 + today.minute * 60 + today.second), microseconds=today.microsecond)
    recent_start_date = recent_end_date - timedelta(days=6)


    # Iterate through all the issues that match the configs.
    from collections import defaultdict
    key2projects = defaultdict(list)
    rows = []
    for row in list_issues(gh_user, gh_password, gh_api_url, configs, recent_start_date, recent_end_date):
        key = (row[GPMC.REPO_USER], row[GPMC.REPO_NAME], row[GPMC.ISSUE_NUMBER])
        # Only keep one copy of the row's data. Issues can be in multiple groups.
        if row[GPMC.ISSUE_NUMBER] not in key2projects:
            rows.append(row)
        # Keep track of all groups that the issue was part of.
        if row[GPMC.GROUPING_TITLE]:
            key2projects[key].append(row[GPMC.GROUPING_TITLE])


    import csv

    from github_project_management.constants import HEADER

    filename = 'projects.csv'
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for row in rows:
            key = (row[GPMC.REPO_USER], row[GPMC.REPO_NAME], row[GPMC.ISSUE_NUMBER])
            row[GPMC.GROUPING_TITLE] = ','.join(key2projects[key])
            try:
                writer.writerow([row.get(col, None) for col in HEADER])
            except Exception as ex:
                print row
                print ex




def main():
    """Runs the weekly update code

    Optional parameters. Will be prompted for unless set.

      -gh_user = GitHub login name. Can also set as env variable of same name.
      -gh_pass = GitHub password. Can also set as env variable of same name.

    Required parameters.

      -gh_api = GitHub URL for the enterprise instance being used.
      -template = Markdown template for the weekly.
      -config = JSON formatted configuration.

    """
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-gh_user', action="store", dest='gh_user', help='GitHub login name. Can also set as env variable of same name.')
    parser.add_argument('-gh_pass', action="store", dest='gh_pass', help='GitHub password. Can also set as env variable of same name.')
    parser.add_argument('-gh_api', action="store", dest='gh_api', help='GitHub URL for the enterprise instance being used.')
    parser.add_argument('-config', action="store", dest='config', help='JSON formatted configuration.')

    args = parser.parse_args(sys.argv[1:])
    print "Running weekly code"

    # Expected arguments.
    gh_user = None
    if args.gh_user:
        gh_user = args.gh_user
    elif 'gh_user' in sys.env:
        gh_user = sys.env['gh_user']
    else:
        gh_user = raw_input('GitHub login:')

    gh_pass = None
    if args.gh_pass:
        gh_pass = args.gh_pass
    elif 'gh_pass' in sys.env:
        gh_pass = sys.env['gh_pass']
    else:
        gh_pass = getpass('GitHub password:')

    gh_api = args.gh_api

    # Parse all the other config from the JSON. Should have the template in there too.
    import json
    config_json = None
    with open(args.config, 'r') as jf:
        config_json = json.load(jf)

    configs = config_json['projects']

    # Run the weekly update.
    export(
        gh_user,
        gh_pass,
        gh_api,
        configs)


if __name__ == "__main__":
    main()
