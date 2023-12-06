"""
Deals with scraping and formatting information from yaml files.
"""

import glob
import yaml
from collections import defaultdict

XT = "/etc/sysconfig/network-scripts/ifcfg-"
SKIP = {
  "spaldingwcic0.chtc.wisc.edu.yaml", # some issue with printing out an ip addr...?
  "path-ap2001.chtc.wisc.edu.yaml", # there's a '\t' which throws on line125, col11
  "glidein-cm3000.chtc.wisc.edu.yaml" # has unknown char on line28, col55
} 
nodes_mp = {
  "vxlan123": ["0601", "1200"],
  "eth0": ["0600", "0601"],
  "eth1": ["0600", "0601"],
  "bond0": ["0601"],
  "ib0": ["0602"],
  "br0": ["0601"]
}


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


def get_subnets() -> dict:
  """
  Scrapes subnet masks from each file in the "sites" directory.

  Returns
  -------
  dict
    dictionary mapping each file in "sites" to corresponding subnet masks for each connection type 
  """
  subnets = defaultdict()

  for file in glob.glob("./sites/*.yaml"):
    data = get_yaml_file(file)
    f = file.split("/")[2].split(".")[0]
    subnets[f] = defaultdict()
  
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
        subnets[f][t] = list(mask)[0].split("=")[1]

  return subnets


def get_nodes() -> dict:
  """
  Scrapes primary and BMC NIC IP address information from each file in the "nodes" directory.

  Returns
  -------
  dict
    nested dictionary mapping file names to another dictionary, which stores primary/BMC IP 
    addresses in string format
  """
  addrs = defaultdict()

  for file in glob.glob("./nodes/*.yaml"):
    f = file.split("/")[2]
    if f in SKIP:
      continue

    f = f.split(".")[0]
    data = get_yaml_file(file)
    addrs[f] = defaultdict()

    if "bmc" in data.keys():
      addrs[f]["bmc"] = get_bmc_addrs(data)
    addrs[f]["primary"] = get_primary_addrs(data)
  
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
  if "default_gateway_ip" in node["bmc"]["lan"].keys():
    return [
      node["bmc"]["lan"]["ip_address"], 
      node["bmc"]["lan"]["default_gateway_ip"]
    ]
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
    # TODO: this causes error, there's no subnet mask
    # if "default_gateway" in node["network"]:
    #   addrs.append(node["network"]["default_gateway"])
    if "bridge_static" in node["network"]:
      addrs.append(["br0", node["network"]["bridge_static"]["br0"]["ipaddress"]])

  ### CENTOS8 ###    
  elif "file" in node.keys():
    for k, vs in nodes_mp.items():
      for v in vs:
        # using a try-except instead of nested ifs to check if the specific yaml field containing
        # the IP address exists in the current file
        try:
          if (ip := node["file"][f'{XT}{k}']["content"][v]) != False:
            if v == "1200" and k == "vxlan123":
              addrs.append([k, list(ip.keys())[1].split("=")[1]])
            else:
              addrs.append([k, list(ip.keys())[0].split("=")[1]])

        except KeyError:
          pass
  
  return addrs