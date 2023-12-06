"""
Subnet mask and IP address calculations/conversions
"""


def get_addresses_from_subnet_mask(addr: str, mask: str) -> tuple:
  """
  Calculates network and host addresses using subnet masks and node IP addresses.

  Parameters
  ----------
  addr : str
    node IP address
  mask : str
    subnet mask

  Returns
  -------
  tuple
    tuple in the form of (network, host) addresses after applying subnet mask
  """
  _addr = list(map(int, addr.split(".")))
  _mask = list(map(int, mask.split(".")))
  pos = []
  neg = []
  
  for i in range(4):
    ba = bin(_addr[i])[2:].zfill(8)
    bm = bin(_mask[i])[2:].zfill(8)

    for j in range(min(len(ba), len(bm))):
      if bm[j] == "1":
        pos.append(ba[j])
        neg.append("0")
      else:
        pos.append("0")
        neg.append(ba[j])

    pos.append(".")
    neg.append(".")
  
  return (''.join(pos[:-1]), ''.join(neg[:-1]))


def binary_to_value_ip(ip: str) -> str:
  """
  Converts IP from binary string to integer string.

  Parameters
  ----------
  ip : str
    binary representation of address, (with or without "." separators)

  Returns
  -------
  str
    integer representation of address
  """
  res = []
  if "." in ip:
    for v in ip.split("."):
      res.append(str(int(v, 2)))
      res.append(".")
  else:
    for v in range(4):
      res.append(str(int(ip[v*8:(v+1)*8], 2)))
      res.append(".")
  return ''.join(res[:-1])


def count_ones_bits(ip: str) -> int:
  """
  Counts the numbers of ones bits in the IP.

  Parameters
  ----------
  ip : str
    integer representation of address

  Returns
  -------
  int
    number of ones bits
  """
  bits = 0
  for v in ip.split("."):
    for b in bin(int(v))[2:]:
      if b == "1":
        bits += 1
  return bits


def construct_ip(host: str, bits: int) -> list:
  """
  Constructs all valid ip addresses from the HOST address with BITS variable bits.

  Parameters
  ----------
  host : str
    string representation of integer-based address
  bits : int
    integer representing how many bits are available to be changed

  Returns
  -------
  list
    list of all possible ips
  """
  ips = []
  pre = [bin(int(p))[2:].zfill(8) for p in host.split(".")]
  bin_hst = ''.join(pre)[:bits] # binary prefix of address based on host

  # cycle through every possible bit combination and append to prefix
  for n in range(2 ** (32 - bits)): 
    x = f'{bin_hst}{bin(n)[2:].zfill(32 - bits)}'
    ips.append(binary_to_value_ip(x))
  return ips