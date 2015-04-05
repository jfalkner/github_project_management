Github Project Management
===

If you work with engineering teams that rely on GitHub and you have to help do project management, these tools are likely helpful. You'll find here a tool that makes weekly summaries of active GitHub issuese and a way to export the full list of current GitHub projects based on labels.

- [Why make this project?](#why-make-this-project)
- [Installing](#installing)
- [Example Code](#example-code)
  - [Weekly GitHub summary](#weekly-summary)
  - [CSV Export of all open issues](#csv-export)

This code is maintained by Jayson Falkner (jfalkner@gmail.com). Please file
ideas for improvements in the [issues section](https://github.com/jfalkner/github_project_management/issues) of this repo.

Why make this project?
---

This code came from a need to help better communicate between user groups, engineering resources, management and execs. GitHub is great for tracking source-code changes and the work queue of related engineering tasks. It also allows for direct user participation in discussions. A challenge is that not everyone has the time or interest to follow all GitHub chatter. It is also challenging to know what a team is actively working. Fortunatley, GitHub has a great API that you can use to interact with the it and export any desired inforimation. The goal of this work is to provide a few easy to use tools that enable a project manager to wrangle GitHub issues and focus on related communication with users, devs, and execs.

Here are the tools. No need to be a programmer. If you have a GitHub login, you should be set.

1. [Weekly activity summary](), including manually curated "executive summary" style comments. Useful to quickly see what is going on during the week and bubble up communication appropriately.

2. [Export the list of open GitHub issues as a spreadsheet](). This includes key information that make it easier to see milestone groupings, find stale tickets, and also see what issues that users and team leads have voted most imported. This is useful all the time, and particulary monthly planning and prioritization reviews. 


There are many caveats in project management. The intention here is not to claim that this tool is the one end-all, best way to track work. Nor does the spreadsheet export have some sort of objective metric that can magically rank all projects by importance. These tools are mostly intended to let project managers better automate common GitHub issue wrangling tasks and help entice users to more directly use GitHub.

A final note. A downside of recurring meetings is that people will sometimes wait on doing work until the next meeting. There is no need to only run these tools weekly, monthly or whenever respective meetings occur. The author has these tools running on a 15 minute cron task. It is helpful to have this information available all the time so that user needs are exposed as soon as possible for potential ad-hoc prioritization.

Installing
---

Install the code with the following.

```
pip install github_project_management
```

You must also have the [github3.py](https://github3py.readthedocs.org/en/master/index.html) installed.

```
pip install github3.py
pip install uritemplate.py
```


Weekly Summary
---

The following code will generate a GitHub issue that summarizes activity for the week. It purposely relies on GitHub labels because it is common to have many different teams creating issues in the same repository(ies). It is easy to edit and maintain labels. If you can keep them up to date, then the code below will give a weekly summary.

Here is an example of the summary.

![Weekly Summary]()

The three sections are as follows:

- Executive Summary. This is a copy of all comments in the issue's thread that start with "Executive Summary:". The intention is that a project manager or anyone else can help type short summaries of important events during the week. Each comment triggers a GitHub e-mail, which is helpful for those that want immediate updates. The final list of comments is ideal for copying to a weekly style e-mail that summarizes work.
- Active. All issues and PRs that have had at least one comment this week. Sorted by the number of comments for the week.
- Closed. All issues and PRs that were closed this week. Sorted by the number of comments for the week.
- Milestones. All open milestones for issues included in the weekly summary. A way to see higher-level grouping of issues.

Creating the weekly summary is straight-forward. Use GitHub as normal and maintain a label for the group on all issues. For example, imagine the summary is for a Curation group and the label "curation" is tagged on all issues and PRs. The following Python script will make the weekly issue.

```python
from github_project_management.weekly import weekly
from github_project_management.utils import save_as_csv

# Secret auth info. Not smart to hardcode it here, but can be practical.
gh_user = 'jayson'
gh_pass = 'fake_password'
gh_api = 'https://github.my_company.com'

# What repositories to scan for GH issues.
repos = [
    ('dev', 'website')
]

# Only tickets with these labels will be considered.
labels = [
    'curation',
]

# Arbitrary group name that'll appear in the weekly tickets.
group_name = 'Curation'

weekly(
    gh_user,
    gh_pass,
    gh_api,
    repos,
    labels,
    group_name,
    test=False)
```

You'll need to also make a template for the issue. This is how you customize the issue's description to include links and relevant information for your group. The template is just a markdown file that you make next to the script. Below is an example.

```md
@dev/curators @dev/pgms @dev/genomics

This is the curation weekly GitHub issue. The purpose of it is to summarize needing work and related discussions. GitHub is used because it is the primary tool Counsyl engineers use to track work and report progress.

You can find out more about [curation here](https://docs.google.com/a/my_company/document/d/.../edit?usp=sharing). More information about the weekly, monthly and project management process in [here](https://docs.google.com/a/my_company/document/d/.../edit?usp=sharing).

<a name="summary"></a>
### Executive Summary

{executive}

<a name="active"></a>
### Active this week

{active}

<a name="closed"></a>
### Closed this week

{closed}

<a name="milestones"></a>
### Milestones

These are groups of tickets related to a specific project. misc inactive tickets are binned in the "Curation Backlog" milestone. this list is intended to help summarize the [full set of tickets open for curation](https://github.counsyl.com/dev/website/labels/curation). 

{milestones}
```

Finally, to run the script and it'll automatically create or update the weekly issue as needed.

```bash
python run_weekly.py
```

The above script will also automatically close out last week's issue, if it exists. You don't have to do any extra GitHub ticket wrangling outside of maintaining labels and ensuring that issues exist for all needed work, assuming you run this scripy at least weekly (much more often is recommended).


Export the list of open GitHub issues as a spreadsheet
---

Here is a full example.

>WIP: Need to improve.

>- Show making up some GH issues in this repo
>- Show setting the config and the full script
>- Show the output CSV

For example, try running the code below.

```python
from github_project_management import list_projects
from github_project_management.utils import save_as_csv

# Basic GH auth info.
gh_user = 'jfalkner'
gh_pass = 'fake_password'
gh_api = 'https://github.fake_company.com'

# Repositories to scan for issues.
repos = [
    ('jfalkner', 'github_project_management')
]

# Labels to use. Issues without one of these labels will be ignored.
labels = ['curation']

# Users that are able to vote.
users = [
    'jfalkner',
    'mona',
    'mleggett',
]

# Team leads that can cast votes for the team.
team_leads = [
    'jfalkner',
]

save_as_csv(
    list_projects(
        gh_user,
        gh_pass,
        gh_api,
        repos,
        labels,
        users,
        team_leads),
    'projects.csv')
```

It'll export a spreadsheet similar to the following.

![Example Spreadsheet](images/example_spreadsheet.png)

Notice that the spreadsheet isn't just titles and links. It also tallies up
votes from users and team leads. This allows you to engage user groups to use 
GitHub, clarify what is needed, then bring that to a reoccuring project
planning need with engineering resources. For example, this is currently used
as the basis of a monthly refresh and refocus on needed work.
