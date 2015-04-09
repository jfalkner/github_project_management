ASSIGNEE = 'Assignee'
CLOSED = 'Closed'
COMMENTS = 'Comments'
CREATED = 'Created'
GROUPING_LABELS = 'Grouping Labels'
GROUPING_TITLE = 'Grouping Title'
ISSUE = 'Issue'
LABELS = 'Labels'
LATEST_COMMENT = 'Latest Comment'
MILESTONE = 'Milestone'
PULL_REQUEST = 'Pull Request'
RECENT_COMMENTS = 'Recent Comments'
REPO_USER = 'Repo User'
REPO_NAME = 'Repo Name'
STATE = 'State'
TEAM_VOTES = 'Team Votes'
TITLE = 'Title'
UPDATED = 'Updated'
URL = 'URL'
VOTES = 'Votes'

HEADER = [
    TITLE,
    MILESTONE,
    GROUPING_LABELS,
    LABELS,
    PULL_REQUEST,
    ASSIGNEE,
    URL,
    CREATED,
    LATEST_COMMENT,
    VOTES,
    TEAM_VOTES,
]

# Non-header fields. Useful for deriving custom extra columns in code that uses
# this API.
BODY = 'body'
