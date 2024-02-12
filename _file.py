"""
Deals with scraping and formatting information from yaml files.
"""

import glob
import yaml
from collections import defaultdict

# Where to look for IP addresses in the YAML files
nodes_mp = {
  "vxlan123": ["0601", "1200"],
  "eth0": ["0600", "0601", "0604", "0605", "171"],
  "eth1": ["0600", "0601"],
  "eth2": ["0600", "0601"],
  "bond0": ["0601", "110"],
  "ib0": ["0602", "0600"],
  "br0": ["0601"],
  "bond0.5": ["110", "050"]
}
XT = "/etc/sysconfig/network-scripts/ifcfg-"


def get_yaml_file(filepath: str) -> dict:
  """
  Loads yaml file located at FILEPATH.

  Parameters
  ----------
  filepath : str
    where the file is located

  Returns
  -------
  dict
    dictionary representation of yaml file

  Raises
  ------
  YAMLError
    if an issue occurs while parsing the yaml file into a dictionary
  """
  with open(f'{filepath}', "r") as stream:
    try: 
      return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
      exit(f'An error occured in: {filepath}\n{exc}')


def get_subnets(data_directory: str) -> dict:
  """
  Scrapes subnet masks from each file in the "site" directory.

  Returns
  -------
  dict
    dictionary mapping each file to corresponding subnet masks for each connection type 
  """
  subnets = defaultdict(lambda: defaultdict())

  # Opens only YAML files in "site"
  for file in glob.glob(f"{data_directory}/site/*.yaml"):
    data = get_yaml_file(file)
    f = file.split("/")[-1].split(".")[0]
  
    # Getting primary subnet masks
    for t in ["eth0", "bond0", "br0"]: # the other types don't show up or don't have notable info
      mask = ""

      try:
        if (d := data["file"][f'{XT}{t}']["content"]):
          if "0701" in d:
            mask = d["0701"].keys()
          elif "0700" in d and d["0700"]: # can sometimes be false
            mask = d["0700"].keys()
 
      except KeyError:
        pass

      if mask:
        subnets[f]["primary"] = list(mask)[0].split("=")[1]
        break
    
    # Getting BMC subnet masks
    try:
      subnets[f]["bmc"] = data["bmc"]["lan"]["subnet_mask"]
    except KeyError:
      pass

  return subnets


def get_nodes(data_directory: str) -> dict:
  """
  Scrapes primary and BMC NIC IP address information from each file in the "node" directory.

  Returns
  -------
  dict
    nested dictionary mapping file names to another dictionary, which stores primary/BMC IP 
    addresses in string format
  """
  addrs = defaultdict()
  faults = []

  # Opens only YAML files in "node"
  for file in glob.glob(f"{data_directory}/node/*.yaml"):
    with open(file, "r") as stream:
      try: 
        data = yaml.safe_load(stream)
        f = file.split("/")[-1].split(".")[0]
        addrs[f] = defaultdict()

        # Getting BMC and primary addresses from this file
        if "bmc" in data.keys():
          addrs[f]["bmc"] = get_bmc_addrs(data)
        addrs[f]["primary"] = get_primary_addrs(data)

      # Catching errors with reading the YAML files and file formatting
      except yaml.YAMLError as exc:
        faults.append([file, exc])
        continue
      except TypeError as exc:
        faults.append([file, exc])
        continue

  # Prints errors to user if any were found
  if faults:
    print("Found malformed YAML files. List of IP addresses is likely incomplete.")
    for item in faults:
      print(f'{item[0]}: {item[1]}')
     
  return addrs


def get_bmc_addrs(node: dict) -> list:
  """
  Gets IP addresses of BMC NICs from NODE.

  Parameters
  ----------
  node : dict
    dictionary representation of the current node

  Returns
  -------
  list
    list of strings representing IP addresses
  """
  def_gate = False
  ip_addr = False

  if "default_gateway_ip" in node["bmc"]["lan"].keys():
    def_gate = True
  if "ip_address" in node["bmc"]["lan"].keys():
    ip_addr = True
  
  if def_gate and ip_addr:
    return [
      node["bmc"]["lan"]["ip_address"], 
      node["bmc"]["lan"]["default_gateway_ip"]
    ]
  if def_gate:
    return [node["bmc"]["lan"]["default_gateway_ip"]]
  if ip_addr:
    return [node["bmc"]["lan"]["ip_address"]]


def get_primary_addrs(node: dict) -> list:
  """
  Gets IP addresses of primary NICs from NODE.

  Parameters
  ----------
  node : dict
    dictionary representation of the current node

  Returns
  -------
  list
    list of strings representing IP addresses
  """
  addrs = []

  ### CENTOS7 ###
  if "network" in node.keys():
    if "default_gateway" in node["network"]:
      addrs.append(node["network"]["default_gateway"])
    
    if "bridge_static" in node["network"]:
      addrs.append(node["network"]["bridge_static"]["br0"]["ipaddress"])
      if "gateway" in node["network"]["bridge_static"]["br0"] and node["network"]["bridge_static"]["br0"]["gateway"]:
        addrs.append(node["network"]["bridge_static"]["br0"]["gateway"])
    

  ### CENTOS8 ###    
  if "file" in node.keys():
    for k, vs in nodes_mp.items():
      for v in vs:
        # using a try-except instead of nested ifs to check if the specific yaml field containing
        # the IP address exists in the current file
        try:
          if (ips := node["file"][f'{XT}{k}']["content"][v]) != False:
            for ip in ips:
              val = ip.split("=")[1]
              if val != "overwriteme":
                addrs.append(val)

        except KeyError:
          pass
  
  return addrs
