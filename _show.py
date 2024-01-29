"""
Output formatting for display purposes
"""

from _sort import *


def print_nodes(nodes: dict):
  for n in nodes:
    print(f'---{n}---')
    if "bmc" in nodes[n]:
      print(f'BMC Networks:')
      for x in nodes[n]["bmc"]:
        print(f'    {x}')

    print(f'Data Networks:')
    for x in nodes[n]["primary"]:
      print(f'    {x}')


def display_unused_ips(
  nodes: dict, 
  subnet: str, 
  host: str, 
  USED_NODES,
  display_used: bool = False, 
  first: bool = False,
  count_used = False
):
  msk_cnt = count_ones_bits(subnet)
  used, unused = [], []
  for ip in construct_ip(host, msk_cnt):
    if ip in USED_NODES:
      if "128.105.82.93" == ip:
        print('in')

      used.append(ip)
    else:
      if "128.105.82.93" == ip:
        print('out')
      unused.append(ip)

  print(f'Available IPs for {host}/{msk_cnt}')
  for n in unused:
    print(n)
    if first:
      return
  
  if display_used:
    print(f'Used IPs for {host}/{msk_cnt}')
    for n in used:
      print(n)

  if count_used:
    return (len(used))

