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
misc_addrs = set()
misc_ctr = 0

count_primary = 0
for n in nodes:
  msk_var = None
  if n[-4] in mp.keys():
    msk_var = mp[n[-4]]
  elif "spark" in n:      # sparks are all in the WID
    msk_var = mp["0"]
  elif "syra" in n:
    msk_var = "path_syra"
  elif "syrb" in n:
    msk_var = "path_syrb" # TODO: double check syrb is using syrb or cs2360?
  elif "fiu" in n:
    msk_var = "path_fiu"
  elif "unl" in n:
    msk_var = "path_unl"
  # doesn't work for some reason?
  # elif "wisc" in n:
  #   msk_var = mp["2"]
  # elif n in {"osg-cpu-22", "osg-cpu-23", "osg-cpu-24", "osg-cpu-31",
  #            "osg-cpu-32", "osg-cpu-33", "osg-cpu-34", "osg-cpu-41",
  #            "osg-cpu-42", "osg-cpu-43", "osg-cpu-44", "osg-cpu-51",
  #            "osg-cpu-52", "osg-cpu-53", "osg-cpu-54"}:
  #   msk_var = mp["2"]
  elif n in {
    "e121",
    "e122",
    "e123",
    "e124",
    "e125",
    "e126",
    "e127",
    "e129",
    "e133",
    "e134",
    "e135",
    "e136",
    "e137",
    "e138",
    "e139",
    "e142",
    "e143",
    "e144",
    "e145",
    "e147",
    "e148",
    "e149",
    "e380",
    "e381",
    "e382",
    "e383",
    "e416",
    "e417",
    "e418",
    "e457"}:
    msk_var = mp["0"]
  elif n in {
    "e263",
    "e265",
    "e267",
    "e268",
    "e269",
    "e270",
    "e271",
    "e273",
    "e274",
    "e275",
    "e276",
    "e277",
    "e278",
    "e279",
    "e280",
    "e289",
    "e296",
    "e297",
    "e301",
    "e302",
    "e303",
    "e304",
    "e305",
    "e306",
    "e307",
    "e308",
    "e309",
    "e310",
    "e311",
    "e312",
    "e313",
    "e314",
    "e316",
    "e317",
    "e318",
    "e320",
    "e321",
    "e322",
    "e323",
    "e324",
    "e325",
    "e326",
    "e327",
    "e328",
    "e329",
    "e330",
    "e331",
    "e334",
    "e335",
    "e340",
    "e341",
    "e342",
    "e343",
    "e344",
    "e345",
    "e346",
    "e347",
    "e348",
    "e349",
    "e355",
    "e359",
    "e365",
    "e369",
    "e370",
    "e371",
    "e372",
    "e374",
    "e376",
    "e378",
    "e379",
    "e561"}:
    msk_var = mp["2"]
  else:
    misc_ctr += 1
    # print(n)
    if "primary" in nodes[n]:
      for addr in nodes[n]["primary"]:
        misc_addrs.add(addr)
    if "bmc" in nodes[n]:
      for addr in nodes[n]["bmc"]:
        misc_addrs.add(addr)
    continue

  msk = sites[msk_var]
  counted_primary = False
  # TODO: fix path_fiu not having a primary subnet mask
  if nodes[n]["primary"] and "primary" in msk.keys():
    for V in nodes[n]["primary"]:
      adr = V
      net, _ = get_addresses_from_subnet_mask(adr, msk["primary"])
      net = binary_to_value_ip(net)
      final_sites[msk["primary"]][net].add(adr)

    count_primary += 1
    counted_primary = True

  if "bmc" in nodes[n] and nodes[n]["bmc"]:
    for V in nodes[n]["bmc"]:
      # adr = nodes[n]["bmc"][0]
      adr = V
      net, _ = get_addresses_from_subnet_mask(adr, msk["bmc"])
      net = binary_to_value_ip(net)
      final_sites[msk["bmc"]][net].add(adr)

    if not counted_primary:
      count_primary += 1

tot = 0
for k in final_sites.keys():
  for v in final_sites[k].keys():
    tot += len(final_sites[k][v])
# how are we losing data?
print(len(nodes), count_primary + misc_ctr, tot + len(misc_addrs))
pprint.pprint(misc_addrs)

# Formatting output based on user arguments
args = parser.parse_args()
if args.subnet:
  arg_host = args.subnet[0]

  for subnet in final_sites:
    for h in final_sites[subnet]:
      if h == arg_host:
        if args.first:
          display_unused_ips(final_sites, subnet, arg_host, misc_addrs, first=True)
          exit(0)

        display_unused_ips(final_sites, subnet, arg_host, misc_addrs)
        exit(0)
  
  # If user specified invalid host address, that issue gets caught after checking all hosts
  exit("Couldn't find that host address.") 

tot = 0

for subnet in final_sites:
    for host in final_sites[subnet]:
      if args.first:
        display_unused_ips(final_sites, subnet, host, misc_addrs, first=True)
        exit(0)
      
      tot += display_unused_ips(final_sites, subnet, host, misc_addrs, count_used=True)

print(tot)