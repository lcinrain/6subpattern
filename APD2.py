from myio import read_big_file,write_list2file
from myipv6 import ipv62hexstr,hexstr2ipv6
from cfg import HEX_STR
import random
import queue
from collections import defaultdict
import time
import subprocess
def get_currentime():
    ctime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return f'[{ctime}]    '
def read_prefixes():
    prefixes = []
    file_name = './routeview/all-prefixes.txt'
    for line in read_big_file(file_name)[6:]:
        prefix = line.split('\t')[0]
        prefixes.append(prefix)
    return prefixes

def generate_postprefix(postprefix_len:int):
    postprefix_list = []
    for _ in range(postprefix_len):
        random_nibble_index = random.randint(0,15)
        random_nibble = HEX_STR[random_nibble_index]
        postprefix_list.append(random_nibble)
    postprefix = ''.join(postprefix_list)
    return postprefix

def generate_subprefixes(prefix):
    generated_addrs_exploded = []

    ip,plen = prefix.split('/')

    ipv6_exploded = ipv62hexstr(ip)
    prefix_nibble_len = int(int(plen)/4)
    prefix_ = ipv6_exploded[:prefix_nibble_len]
    postprefix_0 = ipv6_exploded[prefix_nibble_len+1:]
    subprefixes = []
    subprefix_addr_exploded_list = []
    for j in HEX_STR:
        subprefix = prefix_+j
        subprefixes.append(subprefix)
        subprefix_addr_exploded = subprefix+postprefix_0
        subprefix_addr_exploded_list.append(subprefix_addr_exploded)
    
    postprefix_len = 32-prefix_nibble_len-1
    
    for subprefix in subprefixes:
        postprefix = generate_postprefix(postprefix_len)
        generated_ipv6_exploded = subprefix+postprefix
        generated_addrs_exploded.append(generated_ipv6_exploded)

    subprefix_len = int(plen)+4
    subprefixes = []
    for addr_exploded in subprefix_addr_exploded_list:
        addr = hexstr2ipv6(addr_exploded)
        subprefix_str = f'{addr}/{subprefix_len}'
        subprefixes.append(subprefix_str)

    subprefix_addrs = [hexstr2ipv6(x) for x in generated_addrs_exploded]
    return subprefixes,subprefix_addrs

def execute(prefix):
    pass

if __name__ == '__main__':

    prefix_subprefixes_dict = defaultdict(set)
    fw_target = open('./target.txt','w',newline='\n')
    fw_aliased = open('./aliased_prefix.txt','w',newline='\n')
    fw_nonaliased = open('./nonaliased_prefix.txt','w',newline='\n')
    q = queue.Queue()
    for x in read_prefixes():
        q.put(x)
    all_addrs = []
    while not q.empty():
        prefix = q.get()
        
        subprefixes,generated_subprefix_addr = generate_subprefixes(prefix)
        fw_target.writelines([x+'\n' for x in generated_subprefix_addr])
        #response_addrs,_ = scan(generated_subprefix_addr,redis_connection)
        write_list2file(generated_subprefix_addr,'./tmp.txt')
        cmd = f"sudo zmap --ipv6-source-ip=240d:c000:2023:ba01:0:9af8:f599:93f2 --ipv6-target-file=tmp.txt -M icmp6_echoscan -B 10M -q -o out.txt"

        subprocess.call(cmd,shell=True,stdout=subprocess.PIPE) 
        response_addrs = read_big_file('./out.txt')
        if not response_addrs:
            fw_nonaliased.write(prefix+'\n')
            print(get_currentime(),prefix,'is not aliased')
            continue
        if len(response_addrs) == 16:
            fw_aliased.write(prefix+'\n')
            print(get_currentime(),prefix,'is aliased')
            continue
        for res_addr in response_addrs:
            index = generated_subprefix_addr.index(res_addr)
            candidate_alised_prefix = subprefixes[index]
            subprefix_len = candidate_alised_prefix.split('/')[-1]
            if int(subprefix_len)<112:
                q.put(candidate_alised_prefix)
            
        

    fw_target.close()
    fw_aliased.close()
    fw_nonaliased.close()

