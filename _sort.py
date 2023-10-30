import os
import yaml
from collections import defaultdict
import pprint

# TODO: map each node to its "site" and then look for network/host addrs based on that

XT = "/etc/sysconfig/network-scripts/ifcfg-"
sites_opts = ["eth0", "bond0", "br0"]
subnets = defaultdict()

for file in os.listdir("./sites"):
  with open(f'./sites/{file}', "r") as stream:
    try: 
      data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
      print(file)
      print(f'!!! ERROR {exc} ERROR !!!')
      exit(0)

  subnets[file] = defaultdict()
  for t in sites_opts:
    try:
      subnets[file][t] = list(data["file"][f'{XT}{t}']["content"]["0701"].keys())[0].split("=")[1]
    except KeyError as err:
      try:
        if data["file"][f'{XT}{t}']["content"]["0700"]:
          subnets[file][t] = list(data["file"][f'{XT}{t}']["content"]["0700"].keys())[0].split("=")[1]
      except KeyError as err:
        pass

pprint.pprint(subnets)

#####

SKIP = { "spaldingwcic0.chtc.wisc.edu.yaml", "unl-svc-1.facility.path-cc.io.yaml",
         "path-ap2001.chtc.wisc.edu.yaml", "glidein-cm3000.chtc.wisc.edu.yaml"}
nodes_mp = {"vxlan123": ["0601", "1200"],
            "eth0": ["0600", "0601"],
            "eth1": ["0600", "0601"],
            "bond0": ["0601"],
            "ib0": ["0602"],
            "br0": ["0601"]}

for file in os.listdir("./nodes"):
  if file in SKIP:
    continue
  
  # checking if file is good to parse
  with open(f'./nodes/{file}', "r") as stream:
    try: 
      data = yaml.safe_load(stream)
      print(f'---{file.split(".")[0]}---')
    except yaml.YAMLError as exc:
      print(file)
      print(f'!!! ERROR {exc} ERROR !!!')
      exit(0)

    #########
    ## BMC ##
    #########
    # TODO: looks like it will always be same xxx.xxx.xxx.??? so this might be subnet issue
    if "bmc" in data.keys():
      print(f'BMC Networks:')
      print(f'    {data["bmc"]["lan"]["ip_address"]}')
      if "default_gateway_ip" in data["bmc"]["lan"].keys():
        print(f'    {data["bmc"]["lan"]["default_gateway_ip"]}')

    ##########
    ## DATA ##
    ##########
    print(f'Data Networks:')

    ### CENTOS7 ###
    if "network" in data.keys():
      if "default_gateway" in data["network"]:
        print(f'    {data["network"]["default_gateway"]}')
      if "bridge_static" in data["network"]:
        print(f'    {data["network"]["bridge_static"]["br0"]["ipaddress"]}')
      continue

    ### CENTOS8 ###    
    if "file" in data.keys():
      for k, vs in nodes_mp.items():
        for v in vs:
          # using a try-except instead of nested ifs to check if the specific yaml field containing
          # the IP address exists in the current file
          try:
            if (ip := data["file"][f'{XT}{k}']["content"][v]) != False:
              if v == "1200" and k == "vxlan123":
                print(f'    {list(ip.keys())[1].split("=")[1]}')
              else:
                print(f'    {list(ip.keys())[0].split("=")[1]}')

          except KeyError as err:
            pass
