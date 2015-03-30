from collections import Counter
from datetime import datetime
import pytz

import github3

from github_project_management import constants as GPMC


def weekly(
    gh_user,
    gh_password,
    gh_api_url,
    repos,
    labels,
    date_format=lambda x: x.strftime('%Y-%m-%d')):

    # Login to the GH enterprise server.
    gh = github3.github.GitHubEnterprise(gh_api_url)
    gh.login(gh_user, gh_password)


    # Track all issues in the timeframe.
    tz = pytz.timezone('US/Pacific')
    start_date = tz.localize(datetime.strptime('2015-03-30', '%Y-%m-%d'))
    end_date = tz.localize(datetime.strptime('2015-04-05', '%Y-%m-%d'))
#    start_date = tz.localize(datetime.strptime('2015-03-23', '%Y-%m-%d'))
#    end_date = tz.localize(datetime.strptime('2015-03-29', '%Y-%m-%d'))

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
            if issue.closed_at and issue.closed_at < start_date:
                continue
            if issue.created_at > end_date:
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
                if com.updated_at < start_date:
                    continue
                if com.created_at > end_date:
                    continue

                # keeping based on created_at has the downside that updates will mutate the data.
                if com.created_at > start_date and com.created_at <= end_date:
                    comments.append({
                        'body': com.body,
                        'created': com.created_at,
                        'user': com.user.login,
                    })
            row['comments'] = comments

            # don't show this issues if there were no comments.
            if len(comments) > 0 or (issue.updated_at <= end_date and issue.updated_at >= start_date):
                # display the results.
                rows.append(row)

    # Make the weekly title. Use it for a unique check.
    def suffix(d):
        return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

    def custom_strftime(format, t):
        return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

    title = "%s Weekly %s - %s" % (
                   'Curation',
                   custom_strftime('%b {S}', start_date),
                   custom_strftime('%b {S}', end_date))

    print title
    # Nate the point of this issue.
    print '@dev/curators @dev/pgms @dev/genomics\n'

    print 'This is the Curation weekly GitHub issue. The purpose of it is to summarize needing work and related discussions. GitHub is used because it is the primary tool Counsyl engineers use to track work and report progress.\n'

    print 'You can find out more about [Curation here](https://docs.google.com/a/counsyl.com/document/d/1Sv-8omVeYK5F5mywlrkMbtCqzITf4XSvoK-bEnidtA4/edit?usp=sharing). More information about the weekly, monthly and project management process in [here](https://docs.google.com/a/counsyl.com/document/d/1k2Qrqk-hPJKmLh_JZsiYFr7lh6s3Qc9lTABTxiUvARI/edit?usp=sharing).\n'

    rows = sorted(rows, key=lambda x: len(x['comments']), reverse=True)
    print '### Active this week\n'
    open_issues = [row for row in rows if issue['state'] == 'open']
    for issue in open_issues:
        print '- %d comment%s: [%s](%s)' % (
            len(issue['comments']),
            's' if len(issue['comments']) > 1 else '',
            issue[GPMC.TITLE],
            issue[GPMC.URL])
    if not open_issues:
        print "- No comments in issues labeled 'curation' this week"

    print '\n### Closed this week\n'
    closed_issues = [row for row in rows if issue['state'] != 'open']
    for issue in closed_issues:
        print '- %d comment%s: [%s](%s)' % (
            len(issue['comments']),
            's' if len(issue['comments']) > 1 else '',
            issue[GPMC.TITLE],
            issue[GPMC.URL])
    if not closed_issues:
        print '- No issues closed this week.'

    print '\n### Milestones'
    print '\nThese are groups of tickets related to a specific project. Misc inactive tickets are binned in the "Curation Backlog" milestone. This list is intended to help summarize the [full set of tickets open for Curation](https://github.counsyl.com/dev/website/labels/curation).\n'
    for (title, url), count in Counter(milestones).most_common():
        if title:
            print '- %d open issue%s: [%s](%s)' % (count, 's' if count > 1 else '', title, url)
        else:
            print '- %d open issue%s assigned to a milestone' % (count, "s aren't" if count > 1 else " isn't")


#    # Flatten out all comments.
#    for issue in rows:
#        print '-', issue['state'], issue[GPMC.TITLE]
#        comments = issue['comments']
#        sorted(comments, key=lambda x: x['created'])
#        for comment in comments:
#            print '  -', comment['created'], comment['user'], comment['body']

    import ipdb; ipdb.set_trace()

    # Flatten and render last weeks remaining issues.
    open_issues = []
    for uoi in all_open_issues.iterkeys():
        open_issues += list(all_open_issues[uoi])
    all_issues = issues_to_markdown(open_issues)

    body = self.body.encode('ascii', 'ignore').format(
        active_issues=issues_to_markdown(active_issues).encode('ascii', 'ignore'),
        closed_issues=closed_issues.encode('ascii', 'ignore'))


    if test:
        print('### Test Mode. Not posting to GH ###')
        print(title)
        print(body)
        return

    # Search for a GH issue that already has this title. If exists, reuse it.
    repo = gh.repository(self.weekly_gh_user, self.weekly_gh_repo)
    weekly_issue = None
    for issue in repo.iter_issues():
        if issue.title == title:
            weekly_issue = issue
    # If weekly issue doesn't exist, make it.
    if not weekly_issue:
        weekly_issue = repo.create_issue(
            title,
            body=body,
            assignee=self.weekly_user,
            labels=self.weekly_labels)
        if not weekly_issue:
            raise ValueException("Can't find or create weekly issue.")
        else:
            logger.info('Lazy made GH issue #%d as weekly.' % weekly_issue.number)
    # If the issue exists, update it.
    else:
        if weekly_issue.is_closed():
            weekly_issue.reopen()
        weekly_issue.edit(
            title,
            body)
        logger.info('Updated: (%s, %s) #%d' % (user, repo, weekly_issue.number))
