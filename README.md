# Dynamic Branch

In vanilla buildkite, the functionality of the `if` attribute is very limited. Firstly, there isn't a corresponding `else` attribute; as such, one must define both the opposite condition in the else branch like so:
```yaml
- label: branch-one
  if: build.env('CONDITION') == 'some_cond'
  ...

- label: branch-two
  if: build.env('CONDITION') != 'some_cond'
  ...

```
This becomes even more complex when multiple conditions mixing `&&` and `||` are introduced.

To introduce more sophisticated branching control flows it is required to either build a separate pipeline to trigger the right branch or to implement the control flow using dynamic steps. Both of these methods results in scattering the pipeline definitions in multiple files, making the system of piplines difficult to maintain.

This plugin introduces more sophisticated branching patterns in a pipeline by using dynamic steps but localizes the definition of the uploaded step in the same steps definition of the original pipeline. The branch step may be injected into the executing pipeline either before running the current step in the environment hook or in the post-command hook. You can adjust this behaviour by setting `post-command` boolean property of the plugin. 

In addition to branching new steps, this plugin also enables branching environment variables in the executing step. This is useful when the branching condition sets a large number of hard-coded environment variables that will be used by the executing step. For this use-case the `post-command` property must not be set to `true` to allow the environment hook to inject the environment variables (Remember to escape the `$` character in the command step to use this feature).

### Dependency
- Docker

### Environment Hook
The environment hook of this plugin has a dependency on docker. The hooks pulls a lightweight python container (python:3.8-alpine) and installs the required python modules before executing the python code. 

If the `post-command` property is _not_ set to `true`, this hook builds a docker container that launches a python script to parse the switch-case or if-else control flow to select the right branch to upload as the next step of the pipeline. 

If `post-command` is set to `true`, this hook will exit without pulling, building or running any docker containers.

### Post-Command Hook
The post-command hook behaves almost exactly as the environment hook. The only difference being that the environment variables are not inject to this step since it would be redundant as the command step has already occur. When `post-command` is not set to `true` this hook exits without doing anything.

### Switch-Case Example
```yaml
build-step: &build-step
  steps:
  - label: "clone-ci-and-build"
    commands:
    - echo "P4_STREAM is $$P4_STREAM"
    - echo "BUILDER_QUEUE is $$BUILDER_QUEUE"
    agents:
    - "agent_count=1"
    - "capable_of_building=something"
    - "environment=${CI_ENVIRONMENT:-production}"
    - "platform=windows"
    - "queue=$$BUILDER_QUEUE"

steps:
- commands:
  - "echo \"Executing branching...\""
  - "echo \"Exported stream is $$P4_STREAM\""
  - "echo \"Exported queue is $$BUILDER_QUEUE\""
  plugins:
  - BryanJY-Wong/dynamic-branch:
      post-command: true # optional, defaults to false
      switch: ${CI_STREAM:-main}
      case:
        custom:
          <<: *build-step
          env:
            P4_STREAM: ${P4_STREAM:-//game/Playtest}
            BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-15-abcdefg}
        stream_6:
          <<: *build-step
          env:
            P4_STREAM: //game/stream_6
            BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-16-hijklmn}
        default:
          <<: *build-step
          env:
            P4_STREAM: //game/main
            BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-15-nopqrst}
```
### If-Else Example
```yaml
build-step: &build-step
  steps:
  - label: "clone-ci-and-build"
    commands:
    - echo "P4_STREAM is $$P4_STREAM"
    - echo "BUILDER_QUEUE is $$BUILDER_QUEUE"
    agents:
    - "agent_count=1"
    - "capable_of_building=something"
    - "environment=${CI_ENVIRONMENT:-production}"
    - "platform=windows"
    - "queue=$$BUILDER_QUEUE"

steps:
- commands:
  - "echo \"Executing branching...\""
  - "echo \"Exported stream is $$P4_STREAM\""
  - "echo \"Exported queue is $$BUILDER_QUEUE\""
  plugins:
  - BryanJY-Wong/dynamic-branch:
      if: 
        condition: "[[ ${CI_STREAM:-main} == stream_1 ]]"
        <<: *build-step
        env:
          P4_STREAM: //game/stream_1
          BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-16-abcde-1}
      elif: 
      - condition: "[[ ${CI_STREAM:-main} == stream_2 ]]"
        <<: *build-step
        env:
          P4_STREAM: //game/stream_2_minimal
          BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-16-abcde-2}
      - condition: "[[ ${CI_STREAM:-main} == stream_3 ]]"
        <<: *build-step
        env:
          P4_STREAM: //game/final
          BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-16-abcde-3}
      else:
        <<: *build-step
        env:
          P4_STREAM: //game/main
          BUILDER_QUEUE: ${BUILDER_QUEUE:-v4-20-06-15-abcde-4}
```

The `condition` property under `if` and `elif` must be a bash conditional statement as these are evaluated using the `os.system` method in Python.
