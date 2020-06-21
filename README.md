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

This plugin introduces more sophisticated branching patterns in a pipeline by using dynamic steps but localizes the definition of the upoloaded step in the same steps definition of the original pipeline. 

### Environment Hook
The environment hook of this plugin has a dependency on `Python` and `pip` to install the `pyyaml` module to parse the python object and generate the branch yaml to be uploaded. This hook launches a python script to parse the switch-case or if-else control flow to select the right branch to upload as the next step of the pipeline which is also defined in the same pipeline file (see example). The python script does not upload the script or inject the environment variables directly, it instead constructs a command that is then evaluated by the shell of the environment hook. This is to allow the environment variables for each branch to be injected into the current step as well as the (branch) uploaded step.

### Command Hook
The command hook is just a simple script that uses `eval` on the commands for the step that uses this plugin. This is to allow the commands to read the environment variables injected by the environment hook for debugging purposes. 

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
