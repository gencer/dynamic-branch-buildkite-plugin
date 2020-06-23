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
  branch = { }
  if shell_condition(dynamic_branch['if']['condition']):
    del dynamic_branch['if']['condition']
    return dynamic_branch['if']
  if evaluate_elif(dynamic_branch, branch):
    return branch
  if 'else' in dynamic_branch.keys():
    branch = dynamic_branch['else']
  return branch
  
def evaluate_switch_case(dynamic_branch: dict):
  keys = dynamic_branch.keys()
  if 'case' not in keys and 'default' not in keys:
    exit("Missing \'case\' or \'default\' property")

  switch_val = dynamic_branch['switch']
  branch = { }

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
  elif 'if' in dynamic_branch.keys():
    branch = evaluate_if_else(dynamic_branch)
  else:
    exit("Missing \'if\'' or \'switch\' property")

  if 'steps' in branch.keys():
    with open('/bk/executed.steps.yaml', 'w') as the_file:
      the_file.write(yaml.safe_dump(branch))
    print('EXE_BRANCH=\'{HOST_DIR}/executed.steps.yaml\''.format(HOST_DIR=os.environ['BK_DIR']))

  if 'env' in branch.keys():
    for key in branch['env']:
      print('{ENV}=\'{VALUE}\''.format(ENV=key, VALUE=branch['env'][key]))

if __name__ == "__main__":
    main()
