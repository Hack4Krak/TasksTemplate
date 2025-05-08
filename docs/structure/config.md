# `config.yaml`
Main configuration file for task. It contains all necessary information about task, like name, flag hash, story etc.

```yaml
$schema: "../schema.json"

# Unique identifier for the task (same as directory name)
id: "simple-task-example"
# Display name for users
name: "Simple Task Example"
# Hashed flag content (without `hack4KrakCTF{}` around)
# For easier development you can use `toolbox hash-flag` script
flag_hash: "1912766d6ba0e50e8b1bacfb51207e83b95b7ac0cd8ce15307cdf4965e7e3f6c"
# Difficulty estimate of the task. 
# It doesn't affect points, it's just suggestion for participants
difficulty_estimation: "easy"
# Task types labels. Labels are used to categorize tasks based on their type.
# Labels are defined in `config/labels.yaml` file.
# Label icons are defined in `config/assets/labels/` file, they should have same name as label id.
labels:
  - "web"


# All assets for tasks have to be registered here
# Please refer to `docs/structure/assets.md` for more information
assets:
  - description: "Hard html game to find button"
    path: "task.html" # Path relative to `assets/`

# Dialogues for task, which will be displayed after clicking on task icon on map
story:
  - title: "Wiedźma"
    message: "Witaj, podróżniku. Co cię sprowadza do mojego domku w lesie?"
  - title: "Podróżnik"
    message: "Omom, ta zielona mikstura. Wygląda dobrze. Mogę ją wypić?"
  - title: "Wiedźma"
    message: "Magia nie jest dla każdego. Czasem lepiej trzymać się z dala od tajemniczych mikstur."

# Configuration related to display of this task on a map
display:
  icon_coordinates:
    x: 24
    y: 20
```