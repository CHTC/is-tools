from _file import *
from _sort import *
from _show import *
import argparse
import os

# User input logic -- exiting if input is invalid or prompting for help
parser = argparse.ArgumentParser(description='Find available IP addresses.')
parser.add_argument('-s', '--subnet',
  nargs='*',
  help='specify a subnet to find an available ip address in'
)
parser.add_argument('-f', '--first',
  action='store_true',
  help='gets the first available ip address (use -fs to find first available address in specified subnet)'
)


# Scraping information from node and site directories for subnet masks and host addresses
nodes = get_nodes()
subnets = get_subnets()
mask_map = defaultdict(lambda: defaultdict(set))
used_ips_total = set()

# Finding which subnet mask to use based on the symlink that each node file points to
for file in glob.glob("./site_tier_0/*.yaml"):
  try:
    # Set the file's "map" property to the stripped symlink
    nodes[file.split("/")[2].split(".")[0]]["map"] = os.readlink(file).split("/")[2].split(".")[0]
  except:
    # Skip files that are in the site_tier_0 directory but aren't in the nodes dictionary
    # These are usually files that had some kind of formatting error and weren't parsed correctly
    # print(file.split("/")[2].split(".")[0])
    continue
  
# Calculating host and network addresses using assigned subnet masks
for n in nodes:
  # Skip files that are in the nodes dictionary but not in the site_tier_0 directory
  # These are files that don't have symlinks
  if "map" in nodes[n]:
    msk = subnets[nodes[n]["map"]]

    # Check if primary addresses and mask exists
    if "primary" in msk.keys() and "primary" in nodes[n]:
      for adr in nodes[n]["primary"]:        
        net, _ = get_addresses_from_subnet_mask(adr, msk["primary"])
        net = binary_to_value_ip(net)
        mask_map[msk["primary"]][net].add(adr)
        used_ips_total.add(adr)

    # Check if bmc addresses and mask exists
    # All bmc addresses under one node will have the same network address
    if "bmc" in msk.keys() and "bmc" in nodes[n]:
      net, _ = get_addresses_from_subnet_mask(nodes[n]["bmc"][0], msk["bmc"])
      net = binary_to_value_ip(net)
      for adr in nodes[n]["bmc"]:
        mask_map[msk["bmc"]][net].add(adr)
        used_ips_total.add(adr)

  else:
    # print(n)
    continue


# Formatting output based on user arguments
args = parser.parse_args()

# If a subnet was specified
if args.subnet:
  usr_network = args.subnet[0]

  for subnet in mask_map:
    for network in mask_map[subnet]:
      if network == usr_network:
        # Only display first available address
        if args.first:
          display_unused_ips(used_ips_total, subnet, usr_network, first=True)
          exit(0)

        # Otherwise display all available addresses in that network
        display_unused_ips(used_ips_total, subnet, usr_network)
        exit(0)
  
  # If user specified invalid network address, that issue gets caught after checking all networks
  exit("Couldn't find that host address.") 

for subnet in mask_map:
    for network in mask_map[subnet]:
      # Only display first available address
      if args.first:
        display_unused_ips(used_ips_total, subnet, network, first=True)
        exit(0)
      
      display_unused_ips(used_ips_total, subnet, network)
