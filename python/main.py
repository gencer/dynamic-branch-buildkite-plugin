#!/usr/bin/env python
import os
import json
import yaml
import sys

def shell_condition(statement: str):
  return os.system('if ' + statement + ' then; exit 0; else; exit 1; fi') == 0

def evaluate_elif(dynamic_branch: dict, executed_branch: dict):
  if 'elif' not in dynamic_branch.keys():
    return False
  for elif_branch in dynamic_branch['elif']:
    if shell_condition(elif_branch['condition']):
      del elif_branch['condition']
      executed_branch = elif_branch
      return True
      
  return False

def evaluate_if_else(dynamic_branch: dict):
  branch = { 'steps':[] }
  if shell_condition(dynamic_branch['if']['condition']):
    del dynamic_branch['if']['condition']
    return dynamic_branch['if']
  if evaluate_elif(dynamic_branch, branch):
    return branch
  if 'else' in dynamic_branch.keys():
    branch = dynamic_branch['else']
  return branch
  
def evaluate_switch_case(dynamic_branch: dict):
  branch = { 'steps':[] }
  switch_val = dynamic_branch['switch']
  if switch_val in dynamic_branch['case'].keys():
    branch = dynamic_branch['case'][switch_val]
  elif 'default' in dynamic_branch['case'].keys():
    branch = dynamic_branch['case']['default']
  return branch

def find_plugin_in_list(plugins: list):
  for element in plugins:
    key = list(element.keys())[0]
    if 'dynamic-branch' in key:
      return element[key]
  sys.exit("Could not find the plugin in BUILDKITE_PLUGINS")

def main():
  plugins = json.loads(os.environ.get('BUILDKITE_PLUGINS'))

  if not isinstance(plugins,list):
    sys.exit("Please use the new plugin definition format detailed in https://buildkite.com/changelog/45-updated-syntax-for-using-plugins-in-your-pipeline-yaml")

  dynamic_branch = find_plugin_in_list(plugins)

  if 'switch' in dynamic_branch.keys():
    branch = evaluate_switch_case(dynamic_branch)
  else:
    branch = evaluate_if_else(dynamic_branch)

  command = ''
  if 'env' in branch.keys():
    for key in branch['env']:
      command += 'export {ENV}=\"{VALUE}\"; '.format(ENV=key, VALUE=branch['env'][key])

  if 'steps' in branch.keys():
    if 'TMP' in os.environ:
      file_path = os.environ['TMP'] + "/executed_branch.yaml" 
    else:
      file_path = os.environ['TMPDIR='] + "/executed_branch.yaml"
       
    with open(file_path, "w") as yaml_file:
      yaml_file.write(yaml.safe_dump(branch))
    command += 'envsubst < \'{PATH}\' | buildkite-agent pipeline upload && rm \'{PATH}\''.format(PATH=file_path)
  else:
    command += 'echo \"Warning: No steps found\";'

  # eval command in environment to inject env vars into the current BK step
  print(command)

if __name__ == "__main__":
    main()
