import os
import yaml

ext = "/etc/sysconfig/network-scripts/ifcfg-"
skipped = { "spaldingwcic0.chtc.wisc.edu.yaml", "centos7", "centos8", 
            "unl-svc-1.facility.path-cc.io.yaml", "_sort.py", "_out.txt" }

for file in os.listdir("."):
  if file in skipped:
    continue

  print(f'---{file.split(".")[0]}---')

  with open(file, "r") as stream:
    try: 
      data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
      print(file)
      print(f'!!! ERROR {exc} ERROR !!!')

    ################################################################################################
    # BMC
    if "bmc" in data.keys():
      if "lan" in data["bmc"].keys():
        print(f'BMC Network:')
        print(f'    {data["bmc"]["lan"]["ip_address"]}')
        if "default_gateway_ip" in data["bmc"]["lan"].keys():
          print(f'    {data["bmc"]["lan"]["default_gateway_ip"]}')

    ################################################################################################
    # DATA
    ipaddr = ""

    print(f'Data Networks:')
    ### CENTOS7 ###
    try:
      ipaddr = data["network"]["bridge_static"]["br0"]["ipaddress"]
      # print(f'{file.split(".")[0]} default network (centos7): {ipaddr}')
      # os.rename(file, f'./centos7/{file}')
      print(f'    {ipaddr}')
    except KeyError:
      pass

    try:
      ipaddr = data["network"]["default_gateway"]
      print(f'    {ipaddr}')
    except KeyError:
      pass
      

    ### CENTOS8 ###
    if "file" in data.keys():
      if f"{ext}vxlan123" in data["file"].keys():
        if "content" in data["file"][f"{ext}vxlan123"].keys():
          if "1200" in data["file"][f"{ext}vxlan123"]["content"].keys():
            ipaddr = data["file"][f"{ext}vxlan123"]["content"]["1200"].keys()
            ipaddr = list(ipaddr)[1].split("=")[1]
            # os.rename(file, f'./centos8/vxlan123/{file}')
            # print(f'{file.split(".")[0]} default network (centos8): {ipaddr}')
            print(f'    {ipaddr}')

          if "0601" in data["file"][f"{ext}vxlan123"]["content"].keys():
            ipaddr = data["file"][f"{ext}vxlan123"]["content"]["0601"].keys()
            ipaddr = list(ipaddr)[0].split("=")[1]
            # os.rename(file, f'./centos8/vxlan123/{file}')
            # print(f'{file.split(".")[0]} default network (centos8): {ipaddr}')
            print(f'    {ipaddr}')

    
      if f"{ext}eth0" in data["file"].keys():
        if "content" in data["file"][f"{ext}eth0"].keys():
          if "0601" in data["file"][f"{ext}eth0"]["content"].keys():
            ipaddr = data["file"][f"{ext}eth0"]["content"]["0601"].keys()
            # os.rename(file, f'./centos8/eth0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

          elif "0600" in data["file"][f"{ext}eth0"]["content"].keys():
            ipaddr = data["file"][f"{ext}eth0"]["content"]["0600"].keys()
            # os.rename(file, f'./centos8/eth0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

      if f"{ext}eth1" in data["file"].keys():
        if "content" in data["file"][f"{ext}eth1"].keys():
          if "0601" in data["file"][f"{ext}eth1"]["content"].keys():
            ipaddr = data["file"][f"{ext}eth1"]["content"]["0601"].keys()
            # os.rename(file, f'./centos8/eth0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

          elif "0600" in data["file"][f"{ext}eth1"]["content"].keys():
            ipaddr = data["file"][f"{ext}eth1"]["content"]["0600"].keys()
            # os.rename(file, f'./centos8/eth0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')


      if f"{ext}bond0" in data["file"].keys():
        if "content" in data["file"][f"{ext}bond0"].keys():
          if "0601" in data["file"][f"{ext}bond0"]["content"].keys():
            ipaddr = data["file"][f"{ext}bond0"]["content"]["0601"].keys()
            # os.rename(file, f'./centos8/bond0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

      if f"{ext}ib0" in data["file"].keys():
        if "content" in data["file"][f"{ext}ib0"].keys():
          if "0602" in data["file"][f"{ext}ib0"]["content"].keys():
            ipaddr = data["file"][f"{ext}ib0"]["content"]["0602"].keys()
            # os.rename(file, f'./centos8/ib0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

      if f"{ext}br0" in data["file"].keys():
        if "content" in data["file"][f"{ext}br0"].keys():
          if "0601" in data["file"][f"{ext}br0"]["content"].keys():
            ipaddr = data["file"][f"{ext}br0"]["content"]["0601"].keys()
            # os.rename(file, f'./centos8/br0/{file}')
            ipaddr = list(ipaddr)[0].split("=")[1]
            print(f'    {ipaddr}')

      # if ipaddr:
      #   ipaddr = list(ipaddr)[0].split("=")[1]
        # print(f'{file.split(".")[0]} default network (centos8): {ipaddr}')