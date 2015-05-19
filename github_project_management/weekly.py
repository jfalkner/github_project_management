from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import date
import pytz

import github3

from github_project_management import constants as GPMC
from github_project_management import list_issues
from github_project_management import milestone_url


def weekly(
    gh_user,
    gh_password,
    gh_api_url,
    weekly_config,
    configs,
    group_name,
    template,
    # Defaults: only display the GH issue and format dates in ISO style.
    test=True,
    date_format=lambda x: x.strftime('%Y-%m-%d')):

    # Make sure that a template can be parsed.
    body_template = 'No file found for %s' % template
    if template:
        with open(template, 'r') as tf:
            body_template = tf.read()

    # Track all issues in the timeframe.
    tz = pytz.timezone('US/Pacific')
    today = tz.localize(datetime.today())
    today -= timedelta(seconds=(today.hour * 60 * 60 + today.minute * 60 + today.second), microseconds=today.microsecond)
    current_week_monday = today - timedelta(days=today.weekday())
    current_week_sunday = current_week_monday + timedelta(days=6)


    # make the weekly title. use it for a unique check.
    def suffix(d):
        return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

    def custom_strftime(format, t):
        return t.strftime(format).replace('{s}', str(t.day) + suffix(t.day))

    def make_title(name, start_date, end_date):
        return "%s Weekly %s - %s" % (
                   name,
                   custom_strftime('%b {s}', start_date),
                   custom_strftime('%b {s}', end_date))

    current_week_title = make_title(group_name, current_week_monday, current_week_sunday)


    # Iterate through all the issues that match the configs.
    milestones = []
    rows = []

    for row in list_issues(gh_user, gh_password, gh_api_url, configs, current_week_monday, current_week_sunday):
        issue = row[GPMC.ISSUE]

        # Track all milestones with at least one open ticket.
        if issue.state == 'open':
            if issue.milestone:
                milestones.append((issue.milestone.title,
                                   milestone_url(gh_api_url, row[GPMC.REPO_USER], row[GPMC.REPO_NAME], issue.milestone.title)))
            else:
                milestones.append((None, None))

        # Skip if the create or close date doesn't make sense given the time range.
        if issue.closed_at and issue.closed_at < current_week_monday:
            continue
        if issue.created_at > current_week_sunday:
            continue

        # Only show issues in the weekly that have had recent comments.
        if row[GPMC.RECENT_COMMENTS] or issue.created_at > current_week_sunday:
            rows.append(row)


    # Find this week's weekly and also auto-close all old weeklies.
    weekly_labels = weekly_config['labels']
    weekly_repo_user = weekly_config['repo_user']
    weekly_repo_name = weekly_config['repo_name']
    weekly_issue = None
    for row in list_issues(gh_user, gh_password, gh_api_url, [weekly_config], current_week_monday, current_week_sunday):
        issue = row[GPMC.ISSUE]

        # Track if this week or last week's issue exists.
        if issue.title == current_week_title:
            weekly_issue = issue
        else:
            if not issue.is_closed():
                if not test:
                    print 'Closed old weekly: (%s, %s) #%d' % (weekly_repo_user, weekly_repo_name, issue.number)
                    issue.close()
                else:
                    print 'Test mode. Would have closed old weekly: (%s, %s) #%d' % (weekly_repo_user, weekly_repo_name, issue.number)


    # Build up the body of the current Weekly GH issue.
    # First show the executive summary.
    executive_summary_comments = []
    if weekly_issue:
        for com in weekly_issue.iter_comments():
            if com.body and com.body.startswith('Executive Summary:'):
                executive_summary_comments.append(com.body[len('Executive Summary:'):])
    executive_body = ''
    if not executive_summary_comments:
        executive_body += '- No executive summary comments.\n'
    else:
        for esc in executive_summary_comments:
            executive_body += '- %s\n' % esc

    rows = sorted(rows, key=lambda x: x[GPMC.RECENT_COMMENTS], reverse=True)


    # Group all issues by the set of labels.
    from collections import OrderedDict
    config_tuples = [
        (config.get('title', None),
         (config.get('labels', None),
          config.get('link', None),
          config.get('description', None))) for config in configs]
    title2meta = OrderedDict(config_tuples)
    title2issues = {}
    for title in title2meta.iterkeys():
        title2issues[title] = []
    for row in rows:
        title2issues[row[GPMC.GROUPING_TITLE]].append(row)

    projects_body = ''
    for title, (lables, link, description) in title2meta.iteritems():
        # Make the per-project header.
        if not title:
            title = 'All Issues'
        if link:
            projects_body += '\n<hr/>\n#### [%s](%s)\n' % (title, link)
        else:
            projects_body += '\n<hr/>\n#### %s\n' % title
        if description:
            projects_body += '%s\n' % description

        # Show all active GH issues as a list sorted by most comments.
        open_issues = [row for row in rows if row[GPMC.STATE] == 'open' and row[GPMC.GROUPING_TITLE] == title]
        if open_issues:
            projects_body += '\n##### Active this week\n'
            for issue in open_issues:
                num_comments = issue[GPMC.RECENT_COMMENTS]
                if num_comments:
                    projects_body += '- %d comment%s: [%s](%s)\n' % (
                        num_comments,
                        's' if num_comments > 1 else '',
                        issue[GPMC.TITLE],
                        issue[GPMC.URL])
                else:
                    projects_body += '- New issue: [%s](%s)\n' % (
                        issue[GPMC.TITLE],
                        issue[GPMC.URL])

        # Show all closed GH issues as a list sorted by most comments.
        closed_issues = [row for row in rows if row[GPMC.STATE] != 'open' and row[GPMC.GROUPING_TITLE] == title]
        if closed_issues:
            projects_body += '\n##### Closed this week\n'
            for issue in closed_issues:
                projects_body += '- %d comment%s: [%s](%s)\n' % (
                    issue[GPMC.RECENT_COMMENTS],
                    's' if issue[GPMC.RECENT_COMMENTS] > 1 else '',
                    issue[GPMC.TITLE],
                    issue[GPMC.URL])

        if not open_issues and not closed_issues:
            projects_body += "- No comment activity this week.\n"

    milestone_body = ''
    for (title, url), count in Counter(milestones).most_common():
        if title:
            milestone_body += '- %d open issue%s: [%s](%s)\n' % (count, 's' if count > 1 else '', title, url)
        else:
            milestone_body += '- %d open issue%s assigned to a milestone\n' % (count, "s aren't" if count > 1 else " isn't")

    body = body_template.format(
        executive=executive_body.encode('utf-8').strip(),
        projects=projects_body.encode('utf-8').strip(),
        milestones=milestone_body.encode('utf-8').strip())


    # Always run in test mode by default.
    if test:
        print('### Test Mode. Not posting to GH ###')
        print(current_week_title)
        print(body)
        return



    if not weekly_issue:
        # Login to the GH enterprise server.
        gh = github3.github.GitHubEnterprise(gh_api_url)
        gh.login(gh_user, gh_password)
        repo = gh.repository(weekly_repo_user, weekly_repo_name)

        print 'Making new issue'
        weekly_issue = repo.create_issue(
            current_week_title,
            body=body,
            assignee=gh_user,
            labels=weekly_labels)
        if not weekly_issue:
            raise ValueException("Can't find or create weekly issue.")
        else:
            print 'Lazy made GH issue #%d as weekly.' % weekly_issue.number
    # If the issue exists, update it.
    else:
        if weekly_issue.is_closed():
            weekly_issue.reopen()
        weekly_issue.edit(
            current_week_title,
            body,
            assignee=gh_user,
            labels=weekly_labels)
        print 'Updated: %s/%s#%d' % (weekly_repo_user, weekly_repo_name, weekly_issue.number)


def main():
    """Runs the weekly update code

    Optional parameters. Will be prompted for unless set.

      -gh_user = GitHub login name. Can also set as env variable of same name.
      -gh_pass = GitHub password. Can also set as env variable of same name.
      -test = True will display the final markdown. False posts to GitHub and closes old weekly issues.

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
    parser.add_argument('-template', action="store", dest='template', help='Markdown template for the weekly.')
    parser.add_argument('-config', action="store", dest='config', help='JSON formatted configuration.')
    parser.add_argument('--test', dest='test', action='store_true')

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

    weekly_config = config_json['weekly_config']
    configs = config_json['projects']
    group_name = config_json['group_name']
    # Allow overriding of the template. Fall back on assuming it is in the JSON.
    if args.template:
        template = args.template
    else:
        template = config_json['template']

    # Run the weekly update.
    weekly(
        gh_user,
        gh_pass,
        gh_api,
        weekly_config,
        configs,
        group_name,
        template=template,
        test= True if args.test else False)


if __name__ == "__main__":
    main()
