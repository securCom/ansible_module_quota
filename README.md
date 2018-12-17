# Module: quota

Manages filesystem quotas using **quota** and **setquota** tools

# Requirements

quota utilities need to be installed on the target system

# Notes

Tested only on **CentOS 7** and ** Debian 9**. 

Use at your own risk.


## RedHat based distros

    yum install -y quota
    
## Debian based distros

    apt install quota
    
# Variables

Detailed description is in the modules file, just brief

* `blocks_hard` 
  * number of 1k blocks to set hard quota (integer of floating)
  * could contain opional +/- at the begining
  * could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T
  * block size is 1024, 1Kb = 1, 1M = 1024k = 1024
  *  required: false
 
* `blocks_soft`
  * number of 1k blocks to set soft quota (integer of floating)
  * could contain opional +/- at the begining
  * could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T
  * block size is 1024, 1Kb = 1, 1M = 1024k = 1024
  * required: false

 
* `filesystem`
  * filesystem path to get/set quota
   * required: true
  
* `inodes_hard`
  * number of inodes  to set hard quota (integer of floating)
  * could contain opional +/- at the begining
  * could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T
  * required: false

 * `inodes_soft` 
   * number of inodes  to set hard quota (integer of floating)
   * could contain opional +/- at the begining
   * could be followed by modifiers: Kb, Mb, Gb, Tb, K, M, G, T
   * required: false
  
* `name`
  * name of the group or user to get/set quota"
  * required: true
  * values: [user, group]

  
# Example Playbook

## import

At thos moment thismodule is no tin **galaxy.ansible.com**, so import need to be a littbe bit tweaked.
Put this into `requirements.yml`

    - src: https://github.com/securCom/ansible_module_quota
      name: securcom.module_quota


## get actual quota

To get actual quota omit all **hard**/**soft** parameters.

    - hosts: servers
      roles:
         - { role: securcom.module_quota }
      tasks:
        - name: get quota
          quota:
            name: user
            type: user
            filesystem: /dev/sdb1
          register: quota

## set quota

    - hosts: servers
      roles:
         - { role: securcom.module_quota }
      tasks:
        - name: get quota
          quota:
            name: user
            type: user
            filesystem: /dev/sdb1
            blocks_hard: 2K


# License

GPLv3

# Author Information

- Peter Hudec (@hudecof)
