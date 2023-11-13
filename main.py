# TODO: map each node to its "site" and then look for network/host addrs based on that

from _file import *
from _sort import *
import pprint

# pprint.pprint(_file.get_subnets())
# print(_sort.get_addresses_from_subnet_mask("192.168.123.132", "255.255.255.0"))

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
P = []
M = []
N = []
Q = []
R = []

for n in nodes:
  if n[-4] == "1":
    P.append(n)
  elif n[-4] == "0":
    M.append(n)
  elif n[-4] == "2":
    N.append(n)
  elif n[-4] == "3":
    Q.append(n)
  elif n[-4] == "4":
    R.append(n)
  

sites = get_subnets()
pprint.pprint(sites["cs_2360"])

# for n in P:
#   # print(nodes[n])
#   if nodes[n]["primary"]:
#     msk = nodes[n]["primary"][0][0]
#     adr = nodes[n]["primary"][0][1]
#     x = get_addresses_from_subnet_mask(adr, sites["cs_b240"][msk])
#     print(binary_to_value_ip(x[0]), binary_to_value_ip(x[1]))

# for n in M:
#   # print(nodes[n])
#   if "primary" in nodes[n] and nodes[n]["primary"]:
#     msk = nodes[n]["primary"][0][0]
#     adr = nodes[n]["primary"][0][1]
#     x = get_addresses_from_subnet_mask(adr, sites["wid"][msk])
#     print(binary_to_value_ip(x[0]), binary_to_value_ip(x[1]))

for n in N:
  if "primary" in nodes[n] and nodes[n]["primary"]:
    print(nodes[n])
    msk = nodes[n]["primary"][0][0]
    adr = nodes[n]["primary"][0][1]
    print(msk)
    x = get_addresses_from_subnet_mask(adr, sites["cs_2360"][msk])
    print(binary_to_value_ip(x[0]), binary_to_value_ip(x[1]))



# pprint.pprint(sorted(P))