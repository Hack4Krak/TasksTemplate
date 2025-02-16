# Tasks structure

All tasks should be defined in `tasks/` directory in separate directory for each task.
Tasks have strictly defined files structure:
- [`config.yaml`](structure/config.md) - task configuration file
- [`docker-compose.yaml`](structure/description.md) - configure deployment (*only for tasks with services*)
- [`description.md`](structure/description.md) - task description file
- [`solution.md`](structure/solution.md) - solution revealed after competition to users
- [`assets/`](structure/assets.md) - directory with task assets
- [`pictures/`](structure/pictures.md) - directory with icon and background pictures
- [`src/`](structure/src.md) - source code for task implementation

Documentation of each part of task structure is available in [documentation structure](structure/) directory.
