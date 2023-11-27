# TODO: map each node to its "site" and then look for network/host addrs based on that

from _file import *
from _sort import *
import pprint


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


nodes = get_nodes()
sites = get_subnets()
final_sites = defaultdict(defaultdict)
mp = {
  "0": "wid",
  "1": "cs_b240",
  "2": "cs_2360",
  "3": "cs_3370a",
  "4": "oneneck"
}

for n in nodes:
  if n[-4] in mp.keys():
    if nodes[n]["primary"] and nodes[n]["primary"]:
      msk_key = nodes[n]["primary"][0][0]
      adr = nodes[n]["primary"][0][1]
      msk = sites[mp[n[-4]]][msk_key]
      net, hst = get_addresses_from_subnet_mask(adr, msk)
      net = binary_to_value_ip(net)

      final_sites[msk][net] = final_sites[msk].get(net, []) + [adr]
    
pprint.pprint(final_sites)

