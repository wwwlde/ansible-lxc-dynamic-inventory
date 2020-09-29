#!/usr/bin/env python3

import os
import sys
import json
import warnings

from pylxd import Client

def get_container_group(obj):
    if 'user.ansible.group' in obj.expanded_config:
        return [obj.expanded_config['user.ansible.group']]
    else:
        return []

def get_container_ip(obj):
    return obj.state().network['eth0']['addresses'][0]['address']

def build_dict():
    """Returns a dictionary keyed to the defined LXC groups. All
    containers, including the ones not in any group, are included in the
    "all" group."""

    crt = os.environ.get('HOME') + '/.config/lxc/client.crt'
    key = os.environ.get('HOME') + '/.config/lxc/client.key'

    client = Client(endpoint='https://u0156.sysenv.priv:8443', verify=False, cert=(crt, key))
    data = client.containers.all()
    # Enumerate all containers, and list the groups they are in. Also,
    # implicitly add every container to the 'all' group.
    containers = dict([(c.name, ['all'] + get_container_group(c)) for c in data])

    # Extract the groups, flatten the list, and remove duplicates
    groups = set(sum([g for g in containers.values()], []))
    hostvars = { '_meta': { 'hostvars': { c.name: {'ansible_host': get_container_ip(c) } for c in data } } }

    # Create a dictionary for each group (including the 'all' group)
    inventory = dict([(g, {'hosts': [k for k, v in containers.items() if g in v],
                      'vars': {'ansible_user': 'ubuntu'} }) for g in groups])

    result = dict()
    result.update(hostvars)
    result.update(inventory)

    return result

def main(argv):

    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    if len(argv) == 2 and argv[1] == '--list':
        result = build_dict()
        print(json.dumps(result, sort_keys=True, indent=4))
    elif len(argv) == 3 and argv[1] == '--host':
        print(json.dumps({"_meta": {"hostvars": {}}}, sort_keys=True, indent=4))
    else:
        print("Need an argument, either --list or --host <host>", file=sys.stderr)

if __name__ == '__main__':
    main(sys.argv)
