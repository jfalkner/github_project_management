import github3

from github_project_management import constants as GPMC


def milestone_url(gh_api_url, repo_user, repo_name, milestone_title):
    return gh_api_url + '/' + repo_user + '/' + repo_name + '/milestones/' + str(milestone_title)


def list_issues(
    gh_user,
    gh_password,
    gh_api_url,
    configs,
    recent_start_date,
    recent_end_date):

    # Login to the GH enterprise server.
    gh = github3.github.GitHubEnterprise(gh_api_url)
    gh.login(gh_user, gh_password)

    def get_or_error(name):
        if name not in config:
            raise ValueError("Must provide a 'repo_user' in each config. Found %s" % config)
        return config[name]


    for config in configs:

        # Check that the config is valid.
        repo_user = get_or_error('repo_user')
        repo_name = get_or_error('repo_name')
        title = config.get('title', None)
        labels = config.get('labels', None)
        desc = config.get('description', None)
        link = config.get('link', None)
        # Ensure no extra keys.
        expected_keys = {'repo_user', 'repo_name', 'labels', 'description', 'link', 'title'}
        for key in config.iterkeys():
            if key not in expected_keys:
                raise ValueError("Unexpected key-value pair (%s, %s). Only valid keys are %s" % (key, config[key], expected_keys))


        repo = gh.repository(repo_user, repo_name)
        # GitHub caps these at 100. Need to loop to get them all.
        issues_found = 100
        last_date = '1900-01-01'
        while issues_found == 100:
            issues_found = 0
            for issue in repo.iter_issues(state='all', labels=labels, sort='updated', direction='asc', since=last_date):
                last_date = issue.updated_at
                issues_found += 1

                labels_set = set(labels)
                issue_labels_set = {label.name for label in issue.labels}
                if not labels_set.issubset(issue_labels_set):
                    #print 'Skipping %s labels  %s because subset of %s' % (issue.title, labels_set, issue_labels_set)
                    continue

                row = {}
                row[GPMC.ISSUE] = issue
                row[GPMC.STATE] = issue.state
                row[GPMC.TITLE] = issue.title
                row[GPMC.ASSIGNEE] = issue.assignee.login if issue.assignee else None
                row[GPMC.CREATED] = issue.created_at
                row[GPMC.CLOSED] = issue.closed_at
                row[GPMC.UPDATED] = issue.updated_at
                row[GPMC.REPO_USER] = repo_user
                row[GPMC.REPO_NAME] = repo_name
                row[GPMC.ISSUE_NUMBER] = issue.number
                url = gh_api_url + '/' + repo_user + '/' + repo_name + '/issues/' + str(issue.number)
                row[GPMC.URL] = url
                row[GPMC.MILESTONE] = issue.milestone.title if issue.milestone else None

                row[GPMC.PULL_REQUEST] = True if issue.pull_request else False
                row[GPMC.LABELS] = ','.join([label.name for label in issue.labels])
                row[GPMC.GROUPING_TITLE] = title.encode('utf-8').strip() if title else title
                row[GPMC.GROUPING_LABELS] = labels

                # extra info that may not appear in columns.
                row[GPMC.BODY] = issue.body.encode('utf-8').strip() if issue.body else issue.body

                row[GPMC.COMMENTS] = issue.comments

                comments = []
                for com in issue.iter_comments():
                    # skip comments note in the time range of ineterest.
                    if com.updated_at < recent_start_date:
                        continue
                    if com.created_at > recent_end_date:
                        continue

                    # keeping based on created_at has the downside that updates will mutate the data.
                    if com.created_at > recent_start_date and com.created_at <= recent_end_date:
                        comments.append({
                            'body': com.body,
                            'created': com.created_at,
                            'user': com.user.login,
                        })
                row[GPMC.RECENT_COMMENTS] = len(comments)

                yield row


def list_projects(
    gh_user,
    gh_password,
    gh_api_url,
    repos,
    labels,
    users=None,
    team_leads=None,
    date_format=lambda x: x.strftime('%Y-%m-%d')):

    # Login to the GH enterprise server.
    gh = github3.github.GitHubEnterprise(gh_api_url)
    gh.login(gh_user, gh_password)

    # Track votes across all issues.
    votes = {}
    team_votes = {}

    def track_vote(votes, com, issue):
        """Used to track user or team votes"""
        latest_vote = votes.get(com.user.login, None)
        if latest_vote:
            vote_issue, vote_date = latest_vote
            if vote_date < com.updated_at:
                votes[com.user.login] = (issue, com.updated_at)
        else:
            votes[com.user.login] = (issue, com.updated_at)

    rows = []
    for repo_user, repo_name in repos:
        repo = gh.repository(repo_user, repo_name)
        for issue in repo.iter_issues(state='open',
                                      labels=','.join(labels)):

            row = {}
            row[GPMC.TITLE] = issue.title
            row[GPMC.ASSIGNEE] = issue.assignee.login if issue.assignee else None
            row[GPMC.CREATED] = issue.created_at
            url = gh_api_url + '/' + repo_user + '/' + repo_name + '/issues/' + str(issue.number)
            row[GPMC.URL] = url
            row[GPMC.VOTES] = 0
            row[GPMC.TEAM_VOTES] = 0
            row[GPMC.MILESTONE] = issue.milestone.title if issue.milestone else None

            # Extra info that may not appear in columns.
            row[GPMC.BODY] = issue.body

            # Iterate through all of the comments.
            ruoi, roi = issue.repository
            uoi = issue.assignee.login if issue.assignee else 'Not Assigned'
            latest_comment = row[GPMC.CREATED]
            for com in issue.iter_comments():
                # Track the latest comment.
                if not latest_comment or com.updated_at >= latest_comment:
                    latest_comment = com.updated_at
                # Make sure the latest vote is recorded. Only one vote per user counts.
                if '+1' in com.body:
                    track_vote(votes, com, url)
                    if com.user.login in team_leads:
                        track_vote(team_votes, com, url)
            row[GPMC.LATEST_COMMENT] = latest_comment

            # Display the results.
            rows.append(row)


    # User votes. One time tally.
    vote_tally = {}
    for issue, _ in votes.itervalues():
        vote_tally[issue] = vote_tally.get(issue, 0) + 1
    # Team votes. One time tally.
    team_vote_tally = {}
    for issue, _ in team_votes.itervalues():
        team_vote_tally[issue] = team_vote_tally.get(issue, 0) + 1

    # Yeild all the final results.
    for row in rows:
        url = row[GPMC.URL]
        yield {
            GPMC.TITLE: row[GPMC.TITLE],
            GPMC.MILESTONE: row[GPMC.MILESTONE],
            GPMC.ASSIGNEE: row[GPMC.ASSIGNEE],
            GPMC.URL: url,
            GPMC.CREATED: date_format(row[GPMC.CREATED]),
            GPMC.LATEST_COMMENT: date_format(row[GPMC.LATEST_COMMENT]),
            GPMC.VOTES: vote_tally.get(url, 0),
            GPMC.TEAM_VOTES: team_vote_tally.get(url, 0),
            # Non-header fields.
            GPMC.BODY: GPMC.BODY,
        }
