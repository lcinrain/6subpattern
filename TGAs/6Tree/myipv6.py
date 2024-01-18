import ipaddress
import time


def compressed(hextets):
    best_doublecolon_start = -1
    best_doublecolon_len = 0
    doublecolon_start = -1
    doublecolon_len = 0
    for index, hextet in enumerate(hextets):
        if hextet == '0':
            doublecolon_len += 1
            if doublecolon_start == -1:
                # Start of a sequence of zeros.
                doublecolon_start = index
            if doublecolon_len > best_doublecolon_len:
                # This is the longest sequence of zeros so far.
                best_doublecolon_len = doublecolon_len
                best_doublecolon_start = doublecolon_start
        else:
            doublecolon_len = 0
            doublecolon_start = -1

    if best_doublecolon_len > 1:
        best_doublecolon_end = (best_doublecolon_start +
                                best_doublecolon_len)
        # For zeros at the end of the address.
        if best_doublecolon_end == len(hextets):
            hextets += ['']
        hextets[best_doublecolon_start:best_doublecolon_end] = ['']
        # For zeros at the beginning of the address.
        if best_doublecolon_start == 0:
            hextets = [''] + hextets
    return hextets

def hexstr2ipv6(hex_str):
    '''
    Parameters:
        - hex_str: str. full IPv6 str withOUT ':' among nybbles, e.g. 20010db8000000000000000000000000
    Returns:
        compressed IPv6 addresses: str.  e.g.  2001:db8:: 
    '''
    hextets = ['%x' % int(hex_str[x:x+4], 16) for x in range(0, 32, 4)]
    a= compressed(hextets)
    return ':'.join(a)

def hexstr2ipv6_depressed(ip:str,compressed:bool=True):
    '''
Parameters:
    ip - full IPv6 str withOUT ':' among nybbles, e.g. 20010db8000000000000000000000000
    
    compressed - whether to return a compressed IPv6 address

Returns:
    full IPv6 str WITH ':', e.g. 2001:0db8:0000:0000:0000:0000:0000:0000 or 2001:db8:: if parameter 'compressed' set True
'''
    ipv6 = []
    for i in range(0,8):
        ip = ip.strip('\n')
        ipv6.append(ip[i*4:(i+1)*4])
    ipv6 = ':'.join(ipv6)
    if compressed:
        return ipaddress.IPv6Address(ipv6).compressed
    return ipv6

def ipv62hexstr(ip:str):
    '''
2001:db8:: to 20010db8000000000000000000000000
'''
    #return ipaddress.IPv6Address(ip).exploded.replace(':','')
    return ipv6explod(ip)



def is_in_network(ip:str, ip_network:str):
    '''
    Parameters:

    ip: str ipv6 e.g. 2001:db8::

    ip_network: str, format ipv6/mask e.g. 2001:db8::/32

    Returns:

    bool, True or False

    e.g. 2001:db8:: is in 2001:db8::/32 return True, or return False
    '''
    ip = ipv6explod(ip)
    ip_int = int(ip,16)
    ip_network_addr, mask = ip_network.split('/')
    ip_network_addr = ipv6explod(ip_network_addr)
    ip_network_addr_int = int(ip_network_addr,16)
    mask = int(mask)
    mask_str = '1'*mask + (128-mask)*'0'
    mask_int = int(mask_str,2)
    if ip_int&mask_int == ip_network_addr_int&mask_int:
        return True
    else:
        return False

def is_in_network2(ip:str, ip_network:str):
    ipexploded = ipv6explod(ip)
    ip_network_addr, plen = ip_network.split('/')
    plen = int(plen)
    ip_network_addr_exploded = ipv6explod(ip_network_addr)
    hex_num = int(plen/4)
    if ipexploded[:hex_num]!=ip_network_addr_exploded[:hex_num]: return False
    hex_mask_len = plen%4
    mask_str = '1'*hex_mask_len + (4-hex_mask_len)*'0'
    mask_int = int(mask_str,2)
    hex_ipexplded = int(ipexploded[hex_num],16)
    hex_networkipexploded = int(ip_network_addr_exploded[hex_num],16)
    if hex_ipexplded&mask_int==hex_networkipexploded&mask_int:
        return True
    return False 

def is_subnetof(subnet:str, supernet:str):
    '''
    if parameter subnet is the subnet of the paremeter supernent Return True, else Return False
    '''
    subnetwork_ip, subprefix = subnet.split('/')
    supernetwok_ip, superifix = supernet.split('/')
    if int(subprefix) <= int(superifix):
        return False
    else:
        if subnetwork_ip == supernetwok_ip: return True
        return is_in_network2(subnetwork_ip,supernet)

def ipseg2str(ipseglist:list):
    strlist = []
    for ipseg in ipseglist:
        hexstr = (4-len(ipseg))*'0'+ipseg
        strlist.append(hexstr)
    return ''.join(strlist)


def compressedipv6exploded(parts_list:list):
    '''
    explode ipv6 str with '::' in it. parts_list = ipv6.split('::')
    '''
    part1, part2 = parts_list
    part1_list = part1.split(':') if part1 else []
    part2_list = part2.split(':') if part2 else []
    middle0str = '0000'*(8-len(part1_list)-len(part2_list))
    ipv6_exploded = ipseg2str(part1_list)+middle0str+ipseg2str(part2_list)
    return ipv6_exploded

def ipv6explod(ipv6:str):
    ipv6exploded = ''
    if '::' in ipv6:
        ipv6exploded = compressedipv6exploded(ipv6.split('::'))
    else:
        ipv6exploded = ipseg2str(ipv6.split(':'))
    return ipv6exploded

def ipv62dec(ipv6:str):
    '''
    convert IPv6 address to decimal format
    '''
    ipv6exploded = ipv6explod(ipv6)
    return int(ipv6exploded,16)

def get_4len_prefix(prefix_len:int):
    '''
    return prefix length larger to the next multiple of 4. e.g. input 23 return 24
    '''
    a = prefix_len%4
    if a ==0: 
        return prefix_len
    else:
        return 4*(int(prefix_len/4)+1)

def get_4subnetworks(network:str,compressed=False):
    '''
    given a network prefix, return its subnetworks of prefix length =n*4, n=1,2,3,4..32. 
    e.g. input 2001:dc00::/23, 24 return ['2001:dc00::/24','2001:dd00::/24']
    '''
    network_ip,plen = network.split('/')
    plen = int(plen)
    mask_1 = plen%4
    if mask_1==0: 
        if compressed: 
            return [network]
        else:
            return [ipv6explod(network_ip)+'/'+str(plen)]
    network_ip_exploded = ipv6explod(network_ip)
    index = int(plen/4)
    new_plen = str((index+1)*4)
    part1 = network_ip_exploded[:index]
    charx = network_ip_exploded[index]
    # the count of bit 1 in mask
    
    mask = '1'*mask_1+'0'*(4-mask_1)
    mask = int(mask,2)
    start_num = int(charx,16)&mask
    subnet_num = 2**(4-mask_1)
    char_list = []
    for i in range(0,subnet_num):
        subnet_char_int = start_num+i
        if subnet_char_int >= 16:
            print(' error in get_subnetwork.')
            exit(-1)
        subnet_char_x = hex(subnet_char_int).replace('0x','')
        char_list.append(subnet_char_x)
    prefix_list = [part1+x for x in char_list]
    networks_ip = [x + (32-index-1)*'0' for x in prefix_list]
    if compressed:
        networks_ip = list(map(hexstr2ipv6,networks_ip))
    networks = [x+'/'+new_plen for x in networks_ip]
    return networks


def test_ipv6explode():
    '''
    test which is faster. the former used the around 1/10 time by testing 8.9M addresses
    '''
    f = open('hitlist/20221029/responsive-addresses20221029.txt')
    l = []
    for line in f:
        ipv6 = line.strip('\n')
        l.append(ipv6)
    s = time.time()
    for ipv6 in l:
        ipv6explod(ipv6)
    print(time.time()-s)
    s = time.time()
    for ipv6 in l:
        ipaddress.ip_address(ipv6).exploded
    print(time.time()-s)


if __name__ == '__main__':
    a=get_4subnetworks('2a0e:a180::/29')
    print(a)
    c = ipaddress.ip_network('2a0e:a180::/29').subnets(new_prefix=32)
    print(list(c))
    a=get_4subnetworks('2a0e:a184::/30')
    print(a)
    # a = '2001:d800::/21'
    # c = ipaddress.ip_network(a).subnets(new_prefix=24)
    # print(list(c))
    # b=get_4subnetworks(a)
    # print(b)
    # a = '2001:dc00::/22'
    # c = ipaddress.ip_network(a).subnets(new_prefix=24)
    # print(list(c))
    # b=get_4subnetworks(a)
    # print(b)
    # a = '2001:dc00::/23'
    # c = ipaddress.ip_network(a).subnets(new_prefix=24)
    # print(list(c))
    # b=get_4subnetworks(a)
    # print(b)
    # c = '2001:db8::/56'
    # b = '2001:db8::/32'
    # b = '2001:270:f000::/36' 
    # c = '2001:270:fa62:203:233:89:128:0/127'
    # a=is_subnetof(c,b)
    # print(a)