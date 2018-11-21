#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
--- 
author: 
  - "Peter Hudec (@hudecof)"
description: 
  - "Module manages filesystem quotas"
module: quota
notes: 
  - "for getting quota is C(quota) tool used"
  - "for setting quota is  C(setquota) tool used"
options: 
  blocks_hard: 
    description: 
      - "number of 1k blocks to set hard quota (integer of floating)"
      - "could contain opional +/- at the begining"
      - "could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T"
      - "block size is 1024, 1Kb = 1, 1M = 1024k = 1024"
    required: false
  blocks_soft: 
    description: 
      - "number of 1k blocks to set soft quota (integer of floating)"
      - "could contain opional +/- at the begining"
      - "could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T"
      - "block size is 1024, 1Kb = 1, 1M = 1024k = 1024"
    required: false
  filesystem: 
    description: 
      - "filesystem path to get/set quota"
    required: true
  inodes_hard: 
    description: 
      - "number of inodes  to set hard quota (integer of floating)"
      - "could contain opional +/- at the begining"
      - "could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T"
    required: false
  inodes_soft: 
    description: 
      - "number of inodes  to set hard quota (integer of floating)"
      - "could contain opional +/- at the begining"
      - "could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T"
    required: false
  name: 
    description: 
      - "name of the group or user to get/set quota"
    required: true
  type: 
    choices: 
      - user
      - group
    description: 
      - "define type of quota to set"
      - "default value is C(user)"
    required: false
short_description: "Managing system quotas"
version_added: "2.5"

'''

EXAMPLES = '''
# get qo
- name: Test with a message
  quota:
    name: user
    type: user
    filesystem: /dev/sdb1


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


def get_quota_quota(module):
    """ get quota for user and given filesystem

    **quota** is used for retrieving the data. 

    Args:
        module: AnsibleModule object

    Returns:
        dictionary: containing the current quota setting and usage

            {
                'blocks_soft': <int>,
                'blocks_hard': <int>,
                'blocks_current': <int>,
                'blocks_grace': <str>,
                'inodes_soft': <int>,
                'inodes_hard': <int>,
                'inodes_current': <int>,
                'inodes_grace': <str>,
            }

        the value 0 for **soft**, **hard** means quota is not in set

        **grace ** is the relative time in string format. If empty, grace is not in use.


    """
    def get_token(line, length):
        """ get token feom string with given minimum lenght without spaces

        Args:
            line: arbitrary string
            length: minimum length string

        Returns:
            token: given token or empty string
            line: new line without the token and separator
        """
        if line is None:
            return('', None)
        if len(line) == 0:
            return('','')

        token = line[:length]
        line = line[length:]
        if len(line) and line[0] == ' ':
            return(token.strip(), line[1:])

        space = line.split(' ', 1)
        token = "{}{}".format(token, space[0])
        if len(space) > 1:
            line = space[1]
        return(token.strip(), line)


    cmd = [module.get_bin_path('quota', True)]
    cmd.append('-l')
    if module.params['type'] == 'user':
        cmd.append('-u')
    else:
        cmd.append('-g')
    cmd.append(module.params['name'])
    cmd = [str(x) for x in cmd]
    rc, out, err = module.run_command(cmd)

    # quota command retuend non zero value on quota exceeded
#    if rc != 0:
#        module.fail_json(msg="geting quota failed", rc=rc, err=err)

    result = {
        'blocks_soft': '0',
        'blocks_hard': '0',
        'blocks_current': '0',
        'blocks_grace': '',
        'inodes_soft': '0',
        'inodes_hard': '0',
        'inodes_current': '0',
        'inodes_grace': '',
    }

    for line in out.split('\n'):
        line = line.strip()
        # get filesystem
        module.debug("line: %s" % line)
        (value, line) = get_token(line, 1)
        module.debug("value %s" % value)

        if value != module.params['filesystem']:
            continue
        #for blocks %7s%c %6s %7s %7s
        (value, line) = get_token(line, 8)
        result['blocks_current'] = value
        (value, line) = get_token(line, 6)
        result['blocks_hard'] = value
        (value, line) = get_token(line, 7)
        result['blocks_soft'] = value
        (value, line) = get_token(line, 7)
        result['blocks_grace'] = value
        if result['blocks_current'][-1] == '*':
            result['blocks_current'] = result['blocks_current'][:-1]

        #for inodes %7s%c %6s %7s %7s
        (value, line) = get_token(line, 8)
        result['inodes_current'] = value
        (value, line) = get_token(line, 6)
        result['inodes_hard'] = value
        (value, line) = get_token(line, 7)
        result['inodes_soft'] = value
        (value, line) = get_token(line, 7)
        result['inodes_grace'] = value
        if result['inodes_current'][-1] == '*':
            result['inodes_current'] = result['inodes_current'][:-1]
        break
    return result


def get_quota_quotatool(module):
    """ get quota for user and given filesystem

    **quotatool** is used for retrieving the data. 

    In **quotatool** version **1.4.12** is bug, which makes this function unusable. It's fixed in next release.
    See https://github.com/ekenberg/quotatool/issues/7. For example **Debian 9** is using this version.

    Args:
        module: AnsibleModule object

    Returns:
        dictionary: containing the current quota setting and usage

            {
                'blocks_soft': <int>,
                'blocks_hard': <int>,
                'blocks_current': <int>,
                'blocks_grace': <str>,
                'inodes_soft': <int>,
                'inodes_hard': <int>,
                'inodes_current': <int>,
                'inodes_grace': <str>,
            }

        the value 0 for **soft**, **hard** means quota is not in set

        **grace ** is the number of seconds from now until the grace time ends. May be negative =
              time already passed. When quota is not passed, grace is zero


    """

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
        'blocks_soft': '0',
        'blocks_hard': '0',
        'blocks_current': '0',
        'blocks_grace': '',
        'inodes_soft': '0',
        'inodes_hard': '0',
        'inodes_current': '0',
        'inodes_grace': '',
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
        result['blocks_grace'] = tokens[5]
        result['inodes_current'] = tokens[6]
        result['inodes_soft'] = tokens[7]
        result['inodes_hard'] = tokens[8]
        result['inodes_grace'] = tokens[9]
        break

    return result

def set_quota_quotatool(module, quota):

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

def set_quota_setquota(module, quota):

    cmd = [module.get_bin_path('setquota', True)]
    if module.params['type'] == 'user':
        cmd.append('-u')
    else:
        cmd.append('-g')
    cmd.append(module.params['name'])
    cmd.append(quota['blocks_hard'])
    cmd.append(quota['blocks_soft'])
    cmd.append(quota['inodes_hard'])
    cmd.append(quota['inodes_soft'])
    cmd.append(module.params['filesystem'])

    cmd = [str(x) for x in cmd]
    rc, out, err = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg="seting quota failed", rc=rc, err=err)


def convert_number(match, multiplier, base):
    if match.group(1) is not None:
        return match.group(0)
    if match.group(3) is None:
        return match.group(0)
    number = float(match.group(2))
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
        type=dict(default='user', choices=['user', 'group'], required=False),
        name=dict(type='str', required=True),
        blocks_soft=dict(type='str', required=False),
        blocks_hard=dict(type='str', required=False),
        inodes_soft=dict(type='str', required=False),
        inodes_hard=dict(type='str', required=False),
        filesystem=dict(type='str', required=True)
    )

    result = dict(
        changed=False,
        message='',
        report_only=True
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

    #quotas = get_quota_quotatool(module)
    quotas = get_quota_quota(module)
    quotas['blocks_changed'] = False
    quotas['inodes_changed'] = False

    for item in ('blocks_soft', 'blocks_hard'):
        if module.params[item] is None:
            # quotas[item] = None   # needed for quotatool
            continue
        result['report_only'] = False
        if  module.params[item] != quotas[item]:
            result['changed'] = True
            quotas['blocks_changed'] = True
            quotas[item] = module.params[item]

    for item in ('inodes_soft', 'inodes_hard'):
        if module.params[item] is None:
            # quotas[item] = None   # needed for quotatool
            continue
        result['report_only'] = False
        if  module.params[item] != quotas[item]:
            result['changed'] = True
            quotas['inodes_changed'] = True
            quotas[item] = module.params[item]

    for item in ('blocks_soft', 'blocks_hard', 'blocks_current', 'inodes_soft', 'inodes_hard', 'inodes_current'):
        quotas[item] = int(quotas[item])

    result.update(quotas)
    if module.check_mode:
        result['message'] = 'in check mode, current quota usage is reported'
        module.exit_json(**result)

    if result['report_only']:
        result['message'] = 'quota usage reported'
        module.exit_json(**result)

    result.pop('blocks_grace', None)
    result.pop('inodes_grace', None)
    result['message'] = 'quota not changed'
    if result['changed']:
        #set_quota_quotatool(module, quotas)
        result['message'] = 'quota updated'
        set_quota_setquota(module, quotas)
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()