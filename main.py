from _file import *
from _sort import *
from _show import *
import pprint
import sys
import time


# User input logic -- exiting if input is invalid or prompting for help
if len(sys.argv) > 1:
  if sys.argv[1] in {"-h", "--help"}:
    print("HELP MANUAL")
    exit(0)
  if sys.argv[1] not in {"-s", "--subnet"}:
    exit("Usage: python3 main.py -s [HOST]")
  else:
    if len(sys.argv) == 2:
      exit("Please specify host address.")


# Scraping information from node files and finding subnet mask and host addresses
s = time.time()

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

      final_sites[msk][net] = final_sites[msk].get(net, []) + [adr]
      # count_primary_processed += 1

      if "bmc" in nodes[n] and nodes[n]["bmc"]:
        adr = nodes[n]["bmc"][0]
        net, _ = get_addresses_from_subnet_mask(adr, msk)
        net = binary_to_value_ip(net)
        final_sites[msk][net] = final_sites[msk].get(net, []) + [adr]

# how are we losing data?
# print(len(nodes), count_primary, count_primary_processed)
# pprint.pprint(final_sites)


# Displaying all available IPs or just subnet IPs based on what user specified
if len(sys.argv) > 1:
  arg_host = sys.argv[2]

  for subnet in final_sites:
    for h in final_sites[subnet]:
      if h == arg_host:
        display_unused_ips(final_sites, subnet, arg_host)
        print(time.ctime() - s)
        exit(0)
  
  # If user specified invalid host address, that issue gets caught after checking all hosts
  exit("Couldn't find that host address.") 

else:
  for subnet in final_sites:
    for host in final_sites[subnet]:
      display_unused_ips(final_sites, subnet, host)

print(time.time() - s)