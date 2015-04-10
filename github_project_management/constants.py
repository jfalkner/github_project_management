ASSIGNEE = 'Assignee'
CLOSED = 'Closed'
COMMENTS = 'Comments'
CREATED = 'Created'
GROUPING_LABELS = 'Grouping Labels'
GROUPING_TITLE = 'Grouping Title'
ISSUE = 'Issue'
ISSUE_NUMBER = 'Number'
LABELS = 'Labels'
LATEST_COMMENT = 'Latest Comment'
MILESTONE = 'Milestone'
PULL_REQUEST = 'Pull Request'
RECENT_COMMENTS = 'Recent Comments'
REPO_NAME = 'Repo Name'
REPO_USER = 'Repo User'
STATE = 'State'
TEAM_VOTES = 'Team Votes'
TITLE = 'Title'
UPDATED = 'Updated'
URL = 'URL'
VOTES = 'Votes'

HEADER = [
    TITLE,
    MILESTONE,
    GROUPING_TITLE,
    LABELS,
    PULL_REQUEST,
    ASSIGNEE,
    URL,
    CREATED,
    UPDATED,
    CLOSED,
    COMMENTS,
    RECENT_COMMENTS,
    LATEST_COMMENT,
    VOTES,
    TEAM_VOTES,
]

# Non-header fields. Useful for deriving custom extra columns in code that uses
# this API.
BODY = 'body'
