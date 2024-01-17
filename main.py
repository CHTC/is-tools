from _file import *
from _sort import *
from _show import *
import pprint
import time
import argparse
import os

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
nodes = get_nodes()
sites = get_subnets()
final_sites = defaultdict(lambda: defaultdict(set))

for file in glob.glob("./site_tier_0/*.yaml"):
  try:
    nodes[file.split("/")[2].split(".")[0]]["map"] = os.readlink(file).split("/")[2].split(".")[0]
  except:
    # files that are in the site_tier_0 directory but aren't in the nodes dict
    continue
  

for n in nodes:
  if "map" not in nodes[n]:
    # files that are in the nodes dict but aren't in the site_tier_0 directory
    continue

  msk = nodes[n]["map"]
  msk = sites[msk]
  counted_primary = False
  # TODO: fix path_fiu not having a primary subnet mask
  if nodes[n]["primary"] and "primary" in msk.keys():
    for V in nodes[n]["primary"]:
      adr = V
      net, _ = get_addresses_from_subnet_mask(adr, msk["primary"])
      net = binary_to_value_ip(net)
      final_sites[msk["primary"]][net].add(adr)

  if "bmc" in nodes[n] and nodes[n]["bmc"]:
    for V in nodes[n]["bmc"]:
      # adr = nodes[n]["bmc"][0]
      adr = V
      net, _ = get_addresses_from_subnet_mask(adr, msk["bmc"])
      net = binary_to_value_ip(net)
      final_sites[msk["bmc"]][net].add(adr)


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
      
      display_unused_ips(final_sites, subnet, host, count_used=True)