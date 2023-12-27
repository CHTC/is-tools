from _file import *
from _sort import *
from _show import *
import pprint
import time
import argparse

# User input logic -- exiting if input is invalid or prompting for help
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-s', '--subnet',
  nargs='*',
  help='specify a subnet to find an available ip address in'
)
parser.add_argument('-f', '--first',
  action='store_true',
  help='gets the first available ip address (use -fs to find first available address in specified subnet)'
)


# Scraping information from node files and finding subnet mask and host addresses
s = time.time()

nodes = get_nodes()
sites = get_subnets()
final_sites = defaultdict(lambda: defaultdict(set))
mp = {
  "0": "wid",
  "1": "cs_b240",
  "2": "cs_2360",
  "3": "cs_3370a",
  "4": "oneneck"
}

# count_primary_processed = 0
# count_primary = 0
for n in nodes:
  # if nodes[n]["primary"]:
    # count_primary += 1

  if n[-4] in mp.keys():
    if nodes[n]["primary"]:
      msk_key = nodes[n]["primary"][0][0]
      adr = nodes[n]["primary"][0][1]
      msk = sites[mp[n[-4]]][msk_key]
      net, _ = get_addresses_from_subnet_mask(adr, msk)
      net = binary_to_value_ip(net)

      # final_sites[msk][net] = final_sites[msk].get(net, set()).add(adr)
      final_sites[msk][net].add(adr)
      # count_primary_processed += 1

      if "bmc" in nodes[n] and nodes[n]["bmc"]:
        adr = nodes[n]["bmc"][0]
        net, _ = get_addresses_from_subnet_mask(adr, msk)
        net = binary_to_value_ip(net)
        # final_sites[msk][net] = final_sites[msk].get(net, set()).update(adr)
        final_sites[msk][net].add(adr)


# how are we losing data?
# print(len(nodes), count_primary, count_primary_processed)
# pprint.pprint(final_sites)
        

# Formatting output based on user arguments
args = parser.parse_args()
if args.subnet:
  arg_host = args.subnet[0]

  for subnet in final_sites:
    for h in final_sites[subnet]:
      if h == arg_host:
        if args.first:
          display_unused_ips(final_sites, subnet, arg_host, first=True)
          exit(0)

        display_unused_ips(final_sites, subnet, arg_host)
        exit(0)
  
  # If user specified invalid host address, that issue gets caught after checking all hosts
  exit("Couldn't find that host address.") 

for subnet in final_sites:
    for host in final_sites[subnet]:
      if args.first:
        display_unused_ips(final_sites, subnet, host, first=True)
        exit(0)
      
      display_unused_ips(final_sites, subnet, host)
