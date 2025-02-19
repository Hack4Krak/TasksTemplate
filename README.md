# Hack4Krak Tasks Template

![Issues](https://img.shields.io/github/issues-raw/Hack4Krak/TasksTemplate?color=0096FF&label=issues&style=for-the-badge)
![Pull Requests](https://img.shields.io/github/issues-pr-raw/Hack4Krak/TasksTemplate?color=0096FF&label=PRs&style=for-the-badge)
![Contributors](https://img.shields.io/github/contributors/Hack4Krak/TasksTemplate?color=0096FF&label=contributors&style=for-the-badge)
![Lines](https://img.shields.io/endpoint?url=https://ghloc.vercel.app/api/Hack4Krak/TasksTemplate/badge?style=flat&logoColor=white&color=0096FF&style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/Hack4Krak/TasksTemplate?color=0096FF&label=last%20commit&style=for-the-badge)

This repository provides a template for creating task definitions for Hack4Krak events.
It is parsed directly by [our website](https://github.com/Hack4Krak/Hack4KrakSite/) to display detailed information about specific Capture the Flag (CTF) challenges.

The repository includes basic tools for verifying, parsing, and task creation.

> [!IMPORTANT]
> Workflows by default don't run on pull request from forks on private repositories. To enable them edit your organization settings.
> Refer to [GitHub documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#enabling-workflows-for-forks-of-private-repositories) for more information.

For more information check out [our documentation](docs/)!

## Development
*Required only for running Hack4Krak Toolbox*

### 1. Download all required dependencies
```shell
uv sync
```

### 2. Run CLI
```shell
uv run toolbox 
```

## Architecture
- [tasks/](tasks/) - configuration for all tasks
- [config/](config/) - configuration for the specific CTF event
- [toolbox/](toolbox/) - our custom CLI for working with this repository
- [docs/](docs/) - documentation

## Stats

![Repobeats analytics image](https://repobeats.axiom.co/api/embed/302c940507d69624923aea749c322661176bed1b.svg "Repobeats analytics image")
