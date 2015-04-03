from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import date
import pytz

import github3

from github_project_management import constants as GPMC


def weekly(
    gh_user,
    gh_password,
    gh_api_url,
    repos,
    labels,
    group_name,
    # Defaults: only display the GH issue and format dates in ISO style.
    test=True,
    date_format=lambda x: x.strftime('%Y-%m-%d'),
    template='template.md'):

    # Make sure that a template can be parsed.
    body_template = 'No file found for %s' % template
    if template:
        with open(template, 'r') as tf:
            body_template = tf.read()

    # Add the weekly label for the Weeklies.
    weekly_labels = labels + ['Weekly']

    # Login to the GH enterprise server.
    gh = github3.github.GitHubEnterprise(gh_api_url)
    gh.login(gh_user, gh_password)


    # Track all issues in the timeframe.
    tz = pytz.timezone('US/Pacific')
    today = tz.localize(datetime.today())
    today -= timedelta(seconds=(today.hour * 60 * 60 + today.minute * 60 + today.second), microseconds=today.microsecond)
    current_week_monday = today - timedelta(days=today.weekday())
    current_week_sunday = current_week_monday + timedelta(days=6)
    last_week_monday = current_week_monday - timedelta(days=7)
    last_week_sunday = current_week_sunday - timedelta(days=7)


    milestones = []

    rows = []
    for repo_user, repo_name in repos:
        repo = gh.repository(repo_user, repo_name)
        for issue in repo.iter_issues(state='all', labels=','.join(labels)):
            print 'Checking issue:', issue.state, issue.title

            # Track all milestones with at least one open ticket.
            if issue.state == 'open':
                if issue.milestone:
                    milestone_url = gh_api_url + '/' + repo_user + '/' + repo_name + '/milestones/' + str(issue.milestone.title)
                    milestones.append((issue.milestone.title, milestone_url))
                else:
                    milestones.append((None, None))

            # Skip if the create or close date doesn't make sense given the time range.
            if issue.closed_at and issue.closed_at < current_week_monday:
                continue
            if issue.created_at > current_week_sunday:
                continue

            row = {}
            row['state'] = issue.state
            row[GPMC.TITLE] = issue.title
            row[GPMC.ASSIGNEE] = issue.assignee.login if issue.assignee else None
            row[GPMC.CREATED] = issue.created_at
            url = gh_api_url + '/' + repo_user + '/' + repo_name + '/issues/' + str(issue.number)
            row[GPMC.URL] = url
            row[GPMC.MILESTONE] = issue.milestone.title if issue.milestone else None


            # extra info that may not appear in columns.
            row[GPMC.BODY] = issue.body

            # iterate through all of the comments.
            ruoi, roi = issue.repository
            uoi = issue.assignee.login if issue.assignee else 'not assigned'

            comments = []
            for com in issue.iter_comments():
                # skip comments note in the time range of ineterest.
                if com.updated_at < current_week_monday:
                    continue
                if com.created_at > current_week_sunday:
                    continue

                # keeping based on created_at has the downside that updates will mutate the data.
                if com.created_at > current_week_monday and com.created_at <= current_week_sunday:
                    comments.append({
                        'body': com.body,
                        'created': com.created_at,
                        'user': com.user.login,
                    })
            row['comments'] = comments

            # don't show this issues if there were no comments.
            if len(comments) > 0 or (issue.created_at <= current_week_sunday and issue.created_at >= current_week_monday):
                # display the results.
                rows.append(row)

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
    last_week_title = make_title(group_name, last_week_monday, last_week_sunday)

    # Search for a GH issue that already has this title. If exists, reuse it.
    print "Searching for this and last week's issues"
    repo = gh.repository(repo_user, repo_name)
    weekly_issue = None
    last_weekly_issue = None
    for issue in repo.iter_issues(state='all', labels=','.join(labels)):
        if issue.title == current_week_title:
            weekly_issue = issue
        if issue.title == last_week_title:
            last_weekly_issue = issue
    # If weekly issue doesn't exist, make it.
    print "  Found this week's issue: %s" % (weekly_issue)
    print "  Found last week's issue: %s" % (last_weekly_issue)
    print current_week_title

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

    rows = sorted(rows, key=lambda x: len(x['comments']), reverse=True)

    # Show all active GH issues as a list sorted by most comments.
    active_body = ''
    open_issues = [row for row in rows if row['state'] == 'open']
    for issue in open_issues:
        num_comments = len(issue['comments'])
        if num_comments:
            active_body += '- %d comment%s: [%s](%s)\n' % (
                num_comments,
                's' if num_comments > 1 else '',
                issue[GPMC.TITLE],
                issue[GPMC.URL])
        else:
            active_body += '- New issue: [%s](%s)\n' % (
                issue[GPMC.TITLE],
                issue[GPMC.URL])
    if not open_issues:
        active_body += "- No comments in issues labeled 'curation' this week\n"

    # Show all closed GH issues as a list sorted by most comments.
    closed_body = ''
    closed_issues = [row for row in rows if row['state'] != 'open']
    for issue in closed_issues:
        closed_body += '- %d comment%s: [%s](%s)\n' % (
            len(issue['comments']),
            's' if len(issue['comments']) > 1 else '',
            issue[GPMC.TITLE],
            issue[GPMC.URL])
    if not closed_issues:
        closed_body += '- No issues closed this week.\n'

    milestone_body = ''
    for (title, url), count in Counter(milestones).most_common():
        if title:
            milestone_body += '- %d open issue%s: [%s](%s)\n' % (count, 's' if count > 1 else '', title, url)
        else:
            milestone_body += '- %d open issue%s assigned to a milestone\n' % (count, "s aren't" if count > 1 else " isn't")

    body = body_template.format(
        executive=executive_body,
        active=active_body,
        closed=closed_body,
        milestones=milestone_body)


    # Always run in test mode by default.
    if test:
        print('### Test Mode. Not posting to GH ###')
        print(current_week_title)
        print(body)
        return


    if not weekly_issue:
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
        print 'Updated: (%s, %s) #%d' % (gh_user, repo, weekly_issue.number)
    # Make sure that last week's issue is closed.
    if last_weekly_issue and not last_weekly_issue.is_closed():
        last_weekly_issue.close()
        print 'Closed old weekly: (%s, %s) #%d' % (gh_user, repo, last_weekly_issue.number)
