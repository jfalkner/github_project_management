Github Project Management
===

If you work with engineering teams that rely on GitHub and you have to help
do project management, this tool is likely helpful. It gives a simple way to
export the full list of current GitHub projects based on labels.

- [Why make this project?](#why-make-this-project)
- [Installation](#installation)
- [Example](#example)

This code is maintained by Jayson Falkner (jfalkner@gmail.com). Please file
ideas for improvements in the [issues section](https://github.com/jfalkner/github_project_management/issues) of this repo.

Why make this project?
---

This code came from a need to help coordinate between user groups and
engineering resources. The complexity of existing tools and confusion around 
how projects were prioritized lead to this. The goal was to keep things simple
and focused on two main goals.

1. Better engage users to both use GitHub and note what work they think is 
   most important.

2. Expose to engineers what users want in the place they already track work.
   This is a convenient conversation starter about what work will get done and
   when.

There are many caveats in project management. The intention here is not to
claim that this tool is the one end-all, best way to track work. Nor is this
some sort of objective metric that can magically rank all projects by
importance. This also isn't something new that engineers have to learn that
deviates from their existing GitHub-based workflows.

I'll argue that the hardest part of project management is the following:

> Have an recurring dialog between who needs the work and who will do the work. 
> Focus this dialog on clarifying needs and expectations. Don't rely on a tool
> to do this for you.

This project helps streamline the above task by letting the key discussion of
what work is needed and why focus on exactly that. You've got a list of 
projects. Stick to discussing it and what items will be done in the near future
and when. Is your item not on the list? Learn some GitHub and make sure it is 
there next time.

A danger of recurring meetings is that people will sometimes wait on doing work
until the next meeting. There is no need to only run this tool monthly or 
whenever the meeting occurs. Typical use is to run this at least daily. 
Keeping the project request list in a place engineers can see also helps with
related discussions about work and urgent or ad-hoc prioritization.

Installing
---

Install the code with the following.

```
pip install github_project_management
```

You will likely also need these dependencies.

```
pip install github3.py
pip install uritemplate.py
```

Example Code
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

