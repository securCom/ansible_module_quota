#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: quota

short_description: Managing system quotas

version_added: "2.5"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Peter Hudec (peter.hudec@securcom.me)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

import re
import math
from ansible.module_utils.basic import AnsibleModule

RE_BLOCK_VALUE=re.compile('^(\+|-)?([0-9]+)([KMGT]b?)?$')
RE_INODE_VALUE=re.compile('^(\+|-)?([0-9]+)([KMGT]b?)?$')


def get_quota(module):

    cmd = [module.get_bin_path('quotatool', True)]
    cmd.append('-d')
    if module.params['type'] == 'user':
        cmd.append('-u')
    else:
        cmd.append('-g')
    cmd.append(module.params['name'])
    cmd.append(module.params['filesystem'])
    cmd = [str(x) for x in cmd]
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg="geting quota failed", rc=rc, err=err)

    result = {
        'blocks_soft': 0,
        'blocks_hard': 0,
        'blocks_current': 0,
        'blocks_grade': 0,
        'inodes_soft': 0,
        'inodes_hard': 0,
        'inodes_current': 0,
        'inodes_grace': 0,
    }

    for line in out.split('\n'):
        line = line.strip()
        tokens = line.split(' ')
        if len(tokens) != 10:
            continue
        if tokens[1] != module.params['filesystem']:
            continue
        result['blocks_current'] = tokens[2]
        result['blocks_soft'] = tokens[3]
        result['blocks_hard'] = tokens[4]
        result['blocks_grade'] = tokens[5]
        result['inodes_current'] = tokens[6]
        result['inodes_soft'] = tokens[7]
        result['inodes_hard'] = tokens[8]
        result['inodes_grade'] = tokens[9]
        break

    return result

def set_quota(module, quota):

    def run(module, quota_type, hard=None, soft=None):
        cmd = [module.get_bin_path('quotatool', True)]
        if module.params['type'] == 'user':
            cmd.append('-u')
        else:
            cmd.append('-g')
        cmd.append(module.params['name'])
        cmd.append(quota_type)
        if hard:
            cmd.append('-l')
            cmd.append(hard)
        if soft:
            cmd.append('-q')
            cmd.append(soft)
        cmd.append(module.params['filesystem'])
        cmd = [str(x) for x in cmd]
        rc, out, err = module.run_command(cmd)

        if rc != 0:
            module.fail_json(msg="seting quota failed", rc=rc, err=err)

    if quota['blocks_changed']:
        run(module, '-b', quota['blocks_hard'], quota['blocks_soft'])

    if quota['inodes_changed']:
        run(module, '-i', quota['inodes_hard'], quota['inodes_soft'])

def convert_number(match, multiplier, base):
    if match.group(1) is not None:
        return match.group(0)
    if match.group(3) is None:
        return match.group(0)
    number = int(match.group(2))
    if 'K' in match.group(3):
        number = number*math.pow(multiplier,1-base)
    if 'M' in match.group(3):
        number = number*math.pow(multiplier,2-base)
    if 'G' in match.group(3):
        number = number*math.pow(multiplier,3-base)
    if 'T' in match.group(3):
        number = number*math.pow(multiplier,4-base)

    return str(int(number))

def main():
    module_args = dict(
        type=dict(default='user', choices=['user', 'group']),
        name=dict(type='str', required=True),
        blocks_soft=dict(type='str', required=False),
        blocks_hard=dict(type='str', required=False),
        inodes_soft=dict(type='str', required=False),
        inodes_hard=dict(type='str', required=False),
        filesystem=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True)

    for item in ('blocks_soft', 'blocks_hard'):
        if module.params[item] is None:
            continue
        m = RE_BLOCK_VALUE.match(module.params[item])
        if m is None:
            module.fail_json(msg='unsuported value in %s' % item)
        module.params[item] = convert_number(m, 1024, 1)

    for item in ('inodes_soft', 'inodes_hard'):
        if module.params[item] is None:
            continue
        m = RE_INODE_VALUE.match(module.params[item])
        if m is None:
            module.fail_json(msg='unsuported value in %s' % item)
        module.params[item] = convert_number(m, 1000, 0)

    quotas = get_quota(module)
    quotas['blocks_changed'] = False
    quotas['inodes_changed'] = False
    result.update(quotas)

    for item in ('blocks_soft', 'blocks_hard'):
        if module.params[item] is None:
            quotas[item] = None
            continue
        if  module.params[item] != quotas[item]:
            result['changed'] = True
            quotas['blocks_changed'] = True
            quotas[item] = module.params[item]

    for item in ('inodes_soft', 'inodes_hard'):
        if module.params[item] is None:
            quotas[item] = None
            continue
        if  module.params[item] != quotas[item]:
            result['changed'] = True
            quotas['inodes_changed'] = True
            quotas[item] = module.params[item]

    if module.check_mode:
        module.exit_json(**result)

    if result['changed']:
        set_quota(module, quotas)

    
    module.exit_json(**result)

if __name__ == '__main__':
    main()