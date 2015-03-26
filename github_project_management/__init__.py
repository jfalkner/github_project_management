import github3

from github_project_management import constants as GPMC


def list_projects(
    gh_user,
    gh_password,
    gh_api_url,
    repos,
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
                                      labels='curation'):

            row = {}
            row[GPMC.TITLE] = issue.title
            row[GPMC.ASSIGNEE] = issue.assignee.login if issue.assignee else None
            row[GPMC.CREATED] = issue.created_at
            url = gh_api_url + '/' + repo_user + '/' + repo_name + '/issues/' + str(issue.number)
            row[GPMC.URL] = url
            row[GPMC.VOTES] = 0
            row[GPMC.TEAM_VOTES] = 0

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
            GPMC.ASSIGNEE: row[GPMC.ASSIGNEE],
            GPMC.URL: url,
            GPMC.CREATED: date_format(row[GPMC.CREATED]),
            GPMC.LATEST_COMMENT: date_format(row[GPMC.LATEST_COMMENT]),
            GPMC.VOTES: vote_tally.get(url, 0),
            GPMC.TEAM_VOTES: team_vote_tally.get(url, 0),
        }
