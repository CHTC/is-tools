"""
Subnet mask calculations
"""


def get_addresses_from_subnet_mask(addr: str, mask: str) -> tuple:
  """
  Returns tuple of (NETWORK, HOST) addresses after applying subnet mask
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