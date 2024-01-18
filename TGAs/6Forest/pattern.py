import time
from mytime import get_time_now
from myipv6 import hexstr2ipv6
import json
from collections import Counter
import psutil
import multiprocessing
from myio import read_big_file,write_list2file
import random
import math

HEX_FULL = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

class Pattern():
    patterns = []
    def __init__(self, seeds:list,pattern) -> None:
        self.seed_region = seeds
        self.pattern = pattern
        self.density = len(self.seed_region)/16**self.pattern.count('*')
    @classmethod
    def add_pattern(cls,pattern):
        if not pattern in cls.patterns:
            cls.patterns.append(pattern)

    def add(self,seed) :
        if not seed in self.seed_region:
            seed_region = self.seed_region.copy()
            seed_region.append(seed)
            pattern = get_pattern_simple(seed_region)
            if pattern != self.pattern:
                return seed_region,pattern
            # if = means the seed added will increase the density
            self.seed_region = seed_region
            self.pattern = pattern
            self.density = len(self.seed_region)/16**self.pattern.count('*')
        return [],[]

class Pattern2:
    '''
    work with find_subpattern6
    '''
    def __init__(self, seeds:list,pattern) -> None:
        self.seed_region = seeds
        self.pattern = pattern
        self.free_dimension_count = self.pattern.count('*')
        self.density = len(self.seed_region)/16**self.free_dimension_count

    def add(self,seed) :
        if not seed in self.seed_region:
            seed_region = self.seed_region.copy()
            seed_region.append(seed)
            pattern = get_pattern_simple(seed_region)
            if pattern == self.pattern:
                self.seed_region = seed_region
                self.pattern = pattern
                self.density = len(self.seed_region)/16**self.free_dimension_count


def find_dimension(pattern:str):
    pattern_list = list(pattern)
    fixed_d = []
    free_d = []
    for i in range(0,32):
        if pattern_list[i] == '*':
            free_d.append(i)
        else:
            fixed_d.append(i)

def pattern2ipv6s(pattern:str,start:int=-1,end:int=-1):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = [pattern,]
    count = pattern.count('*')
    l = []
    for i in range(0,count):
        for p in p_l:
            tmp = replace_wildcard(p,start=start,end=end)
            l = l + tmp
        p_l = l
        l = []
    return list(map(hexstr2ipv6,p_l))

def pattern2ipv6s2(pattern:str,start:int,end:int):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = replace_wildcard3(pattern,start,end)
    return list(map(hexstr2ipv6,p_l))

def pattern2ipv6s_simple(pattern:str):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = replace_wildcard_simple(pattern)
    return p_l

def pattern2ipv6s_count(pattern:str,num_generated:int,num_to_generate:int=256):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    freed_num_total = pattern.count('*')
    if num_generated>= 16**freed_num_total: return []
    if num_to_generate >= 16**freed_num_total:
        p_l = replace_wildcard_simple(pattern)
        return list(map(hexstr2ipv6,p_l))

    freed_generated = math.ceil(math.log(num_generated,16)) if num_generated else 0
    freed_2generted = math.ceil(math.log(num_to_generate,16))
    if freed_generated:
        freed_left = freed_num_total - freed_generated - freed_2generted +1
    else:
        freed_left = freed_num_total - freed_2generted 
    if freed_left>0:
        for i in range(0,freed_left):
            pattern = pattern.replace('*','0',1)
    nybbles = []
    for i in range(freed_generated,freed_2generted-1,-1):
        q = int(num_generated/16**i)
        r = num_generated%16**i
        nybbles.append(hex(q).replace('0x',''))
        num_generated = r
    if freed_generated >= freed_num_total:
        nybbles = nybbles[1:]
    for i in nybbles:
        pattern = pattern.replace('*',i,1)

    p_l = replace_wildcard_simple(pattern)

    return list(map(hexstr2ipv6,p_l))

def pattern2ipv6s_6tree(pattern:str,num_addr:int,generated_addr,mode=''):
    '''
    Parameters:
        - num_addr: the number of addr to be generated
        - generated_addr: addr generated last time, to be exclusive from addr generated this time
    '''
    freed = pattern.count('*')
    freed_s = math.ceil(math.log(num_addr,16))
    freed_left = freed - freed_s
    num_generated = 16**freed
    if num_generated-len(generated_addr)<=num_addr or freed_left<=0:
        addrs = pattern2ipv6s_simple(pattern)
        return set(addrs) - set(generated_addr)
    
    if freed<=3:
        addrs = pattern2ipv6s_simple(pattern)
        addr_noduplicate = list(set(addrs)-set(generated_addr))
        indices = random.sample(range(0,len(addr_noduplicate)),num_addr)
        return [addr_noduplicate[i] for i in indices]

    index = 0
    freed_indices = []
    for i in range(0,freed):
        index = pattern.index('*',index)
        freed_indices.append(index)
        index+=1
    multiple = math.ceil(len(generated_addr)/16**freed_s)
    if multiple > 16**freed_left:
        print('error in pattern2ipv6s_6tree',pattern,num_addr,len(generated_addr))
    hex_str = hex(multiple).replace('0x','')
    chars = []
    for i in range(0,freed_left-len(hex_str)):
        chars.append('0')
    for i in list(hex_str):
        chars.append(i)
    for i in chars:
        pattern = pattern.replace('*',i,1)
    addrs = pattern2ipv6s_simple(pattern)
    addr_noduplicate = list(set(addrs)-set(generated_addr))
    return addr_noduplicate



def pattern2ipv6s_conservative(pattern:str,representation:list):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = repalce_wildcard_conservative(pattern,representation)
    return list(map(hexstr2ipv6,p_l))

def replace_wildcard_simple(pattern:str):
    prefix = ''
    prefixes = ['',]
    prefixes_tmp = []
    for h in pattern:
        if h == '*':
            for hex_char in HEX_FULL:
                for prefix in prefixes:
                    prefix+=hex_char
                    prefixes_tmp.append(prefix)
            prefixes = prefixes_tmp
            prefixes_tmp = []
        else:
            for prefix in prefixes:
                prefix+=h
                prefixes_tmp.append(prefix)
            prefixes = prefixes_tmp
            prefixes_tmp = []
    return prefixes

def replace_wildcard3(pattern:str,start=-1,end=-1):
    chars = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
    if start!=-1:
        chars = [hex(x).replace('0x','') for x in range(start,end+1)]
    prefix = ''
    prefixes = ['',]
    prefixes_tmp = []
    for h in pattern:
        if h == '*':
            for hex_char in chars:
                for prefix in prefixes:
                    prefix+=hex_char
                    prefixes_tmp.append(prefix)
            prefixes = prefixes_tmp
            prefixes_tmp = []
        else:
            for prefix in prefixes:
                prefix+=h
                prefixes_tmp.append(prefix)
            prefixes = prefixes_tmp
            prefixes_tmp = []
    return prefixes

def replace_wildcard(pattern_str:str,start:int=-1,end:int=-1):
    '''
    repalce the most left * in pattern with 0-f

    input a pattern with at least one *, return a list with * replaced with 0-f

    this fuction is a component in fuction pattern2ipv6s
    '''
    l = []
    range_ = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
    # if start >=0:
    #     range_ = [hex(x).replace('0x','') for x in range(start,end+1)]
    for hex_char in range_:
        tmp_pattern = pattern_str.replace('*',hex_char,1)
        l.append(tmp_pattern)
    return l


    

def replace_wildcard2(pattern_str:str,wild_card_index:int):
    '''
    this is an alternative of replace_wildcard. 
    '''
    
    prefix = pattern_str[:wild_card_index]
    postfix = pattern_str[wild_card_index+1:]
    l = []
    for hex_char in ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']:
        sub_pattern = ''.join([prefix,hex_char,postfix])
        l.append(sub_pattern)
    return l


def repalce_wildcard_conservative(pattern:str,segments:list):
    '''
    
    Parameters:
        - pattern: str. 32 len hex str.
        - segments: list. e.g. [(index1,range1),(index2,range2)]
    '''
    subpatterns = [pattern,]
    for index, range_ in segments:
        l = []
        for subpattern in subpatterns:
            prefix = subpattern[:index]
            postfix = subpattern[index+1:]
            for hex_char in get_simple_range(range_):
                subpattern_tmp = ''.join([prefix,hex_char,postfix])
                l.append(subpattern_tmp)
        subpatterns = l
    return subpatterns

def get_simple_range(range_:str):
    
    if len(range_) == 2:
        start,end = [int(x,16) for x in list(range_)]
        return [hex(i).replace('0x','') for i in range(start,end+1)]
    elif len(range_) == 4:
        start1,end1,start2,end2 = [int(x,16) for x in list(range_)]
        r1 = [hex(i).replace('0x','') for i in range(start1,end1+1)]
        r2 = [hex(i).replace('0x','') for i in range(start2,end2+1)]
        return r1+r2
    elif range_ == '*':
        return ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
    else:
        print('error in pattern->get_simple_range, range is:',range_)
        exit(-1)
def test_replace_wildcard():
    '''
    to test which is fater.
    replace_wildcard慢于replace_wildcard2,100w次慢0.1s
    '''
    pattern = '200119002100000000000000000*****'
    s= time.time()
    for i in range(0,1000000):
        replace_wildcard(pattern)
    print((time.time()-s)/60)
    s = time.time()
    for i in range(0,1000000):
        replace_wildcard2(pattern,31)
    print((time.time()-s)/60)

def test_find_sub_pattern():

    '''
    this fuction is used to test the subpattern fuction using some instances
    '''
    # instance No. 1
    # seeds = ['1234','1235','1236','2236','3236','3457','3557','3657']
    # sub_patterns = find_sub_pattern(seeds,'****')
    # output {'123*': [0.125, ['1235', '1236']], '*23*': [0.01953125, ['1234', '1235', '1236', '2236', '3236']], '*236': [0.125, ['2236', '3236']], '3***': [0.0009765625, ['3236', '3457', '3557', '3657']], '3*57': [0.125, ['3557', '3657']]}
    
    # instance No. 2
    # seeds = ['24001420100001010000000000000229', '24001420100001010000000000000239']
    # sub_patterns = find_sub_pattern(seeds,'240014201000010100000000000002*9')
    # output {'240014201000010100000000000002*9': [0.125, ['24001420100001010000000000000229', '24001420100001010000000000000239']]}
    
    # instance No. 3
    # seeds = ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32','2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']
    # sub_patterns = find_sub_pattern(seeds,'2a0206b8b0000634022590fffe83****')
    # output
    # 2a0206b8b0000634022590fffe831*** [0.0009765625, ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe831*96 [0.125, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96']]
    # 2a0206b8b0000634022590fffe831**6 [0.0078125, ['2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe832*** [0.00048828125, ['2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60']] 这个里面种子少
    # 2a0206b8b0000634022590fffe832d3* [0.125, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38']]
    # 2a0206b8b0000634022590fffe832d** [0.0078125, ['2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e']]
    # 2a0206b8b0000634022590fffe83*d** [0.0009765625, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe831d96']]
    # 2a0206b8b0000634022590fffe8338*8 [0.125, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8']]
    # 2a0206b8b0000634022590fffe833*** [0.00048828125, ['2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    # 2a0206b8b0000634022590fffe83***8 [0.000732421875, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe832c88']]     
    # new output ,fix bug
    # 2a0206b8b0000634022590fffe831*** [0.0009765625, ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe831*96 [0.125, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96']]
    # 2a0206b8b0000634022590fffe831**6 [0.01171875, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe832*** [0.001220703125, ['2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60']]
    # 2a0206b8b0000634022590fffe832d3* [0.125, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38']]
    # 2a0206b8b0000634022590fffe832d** [0.01171875, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e']]
    # 2a0206b8b0000634022590fffe8338*8 [0.125, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8']]
    # 2a0206b8b0000634022590fffe833*** [0.0009765625, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    
    # instance No4. abnormal detection, abnormal seed 2a0206b8b0000634022590cccc642491 makes the space from 2a0206b8b0000634022590fffe83**** to 2a0206b8b0000634022590**********  result: the space is reduced to ****, the origional space, according to the output. the subpatterns are equal to those without the abnomal seed 2a0206b8b0000634022590cccc642491. Threrefore , we believe the subpattern is able to filter out abnormal seeds.
    # seeds = ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32','2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c','2a0206b8b0000634022590cccc642491']
    # sub_patterns = find_sub_pattern(seeds,'2a0206b8b0000634022590**********')
    # output 
    # 2a0206b8b0000634022590fffe83**** [0.000213623046875, ['2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    # 2a0206b8b0000634022590fffe831*** [0.0009765625, ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe831*96 [0.125, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96']]
    # 2a0206b8b0000634022590fffe831**6 [0.01171875, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe832*** [0.001220703125, ['2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60']]
    # 2a0206b8b0000634022590fffe832d3* [0.125, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38']]
    # 2a0206b8b0000634022590fffe832d** [0.01171875, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e']]
    # 2a0206b8b0000634022590fffe8338*8 [0.125, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8']]
    # 2a0206b8b0000634022590fffe833*** [0.0009765625, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    
    # instance No5. two abnoamal seeds that cannot form a pattern: 2a0206b8b0000634022590cccc642491, 2a0206b8b0000634022590cccc642492. a new subpattern 2a0206b8b0000634022590*f******** occurs according to the output. The fuction find_subpattern do what we what it to do without unexpactation. However, the too large space is what we donont want. The abnormal seeds should be dealed with in space partion and should not be left to the find_subpattern function although this function has the ability to tolerate abnormal seeds in some extent.
    seeds = ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32','2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c','2a0206b8b0000634022590cccc642491','2a0206b8b0000634022590dfab129fff']
    sub_patterns = find_sub_pattern(seeds,'2a0206b8b0000634022590**********')
    # 2a0206b8b0000634022590*f******** [2.1827872842550278e-10, ['2a0206b8b0000634022590dfab129fff', '2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    # 2a0206b8b0000634022590fffe83**** [0.000213623046875, ['2a0206b8b0000634022590fffe830200', '2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6', '2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60', '2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]
    # 2a0206b8b0000634022590fffe831*** [0.0009765625, ['2a0206b8b0000634022590fffe83172a', '2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe831*96 [0.125, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96']]
    # 2a0206b8b0000634022590fffe831**6 [0.01171875, ['2a0206b8b0000634022590fffe831b96', '2a0206b8b0000634022590fffe831d96', '2a0206b8b0000634022590fffe831fc6']]
    # 2a0206b8b0000634022590fffe832*** [0.001220703125, ['2a0206b8b0000634022590fffe832c88', '2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e', '2a0206b8b0000634022590fffe832f60']]
    # 2a0206b8b0000634022590fffe832d3* [0.125, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38']]
    # 2a0206b8b0000634022590fffe832d** [0.01171875, ['2a0206b8b0000634022590fffe832d32', '2a0206b8b0000634022590fffe832d38', '2a0206b8b0000634022590fffe832d7e']]
    # 2a0206b8b0000634022590fffe8338*8 [0.125, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8']]
    # 2a0206b8b0000634022590fffe833*** [0.0009765625, ['2a0206b8b0000634022590fffe8338c8', '2a0206b8b0000634022590fffe8338d8', '2a0206b8b0000634022590fffe833914', '2a0206b8b0000634022590fffe833a7c']]

    for k,v in sub_patterns.items():
        print(k, v)


def find_sub_pattern2(seeds:list):
    '''
    find sub-pattern in seeds, eg. input seeds = ['1234','1235','1236','2236','3236','3457','3557','3657']

    Return potential sub-pattern, using pattern_dict={pattern:[density,[seed region]]}, such as {'123*': [0.125, ['1235', '1236']], '*23*': [0.01953125, ['1234', '1235', '1236', '2236', '3236']], '*236': [0.125, ['2236', '3236']], '3***': [0.0009765625, ['3236', '3457', '3557', '3657']], '3*57': [0.125, ['3557', '3657']]}
    '''
    pattern_found = set()
    pattern_seeds = get_pattern_simple(seeds)
    pattern_found.add(pattern_seeds)
    pattern_dict_return = dict()
    seeds.sort()
    free_dimension = pattern_seeds.count('*')
    initial_density = len(seeds)/16**free_dimension
    pattern_dict_return[pattern_seeds] = [initial_density,seeds]
    for i in range(0,len(seeds)):
        seedi = seeds[i]
        seed_region = [seedi]
        pattern_dict = dict()
        pattern_found_tmp = set()
        for j in range(i+1,len(seeds)):
            seedj = seeds[j]
            new_seeds_region = seed_region.copy()
            new_seeds_region.append(seedj)
            new_pattern = get_pattern_simple(new_seeds_region)
            new_density = get_density(new_seeds_region)
            if new_pattern in pattern_found_tmp:
                old_density, old_region = pattern_dict[new_pattern]
                new_region = old_region.copy()
                new_region.append(seedj)
                new_density = get_density(new_region)
                if new_density>old_density:
                    pattern_dict[new_pattern] = [new_density,new_region]
            else:
                pattern_dict[new_pattern] = [new_density,new_seeds_region]
                pattern_found_tmp.add(new_pattern)


            # if not pattern_dict:
            #     new_region, new_pattern, new_density = combine_seeds(seed_region,seedj)
            #     if new_pattern in pattern_found_tmp:
            #         old_density,old_region = pattern_dict[new_pattern]
            #         if new_density>old_density:
            #             pattern_dict[new_pattern] = [new_density,new_region] 
            #     else:
            #         pattern_dict[new_pattern] = [new_density,new_region]
            #         pattern_found_tmp.add(new_pattern)
            # else:
            #     v_list = list(pattern_dict.values())
            #     for density,region in v_list:
            #         new_region, new_pattern, new_density = combine_seeds(region,seedj)
            #         if new_pattern in pattern_found_tmp:
            #             old_density,old_region = pattern_dict[new_pattern]
            #             if new_density>old_density:
            #                 pattern_dict[new_pattern] = [new_density,new_region] 
            #         else:
            #             pattern_dict[new_pattern] = [new_density,new_region]
            #             pattern_found_tmp.add(new_pattern)  
        for k_pattern, v_list in pattern_dict.items():
            # if k_pattern appears once again, the region is not complete due to break, then contine
            if k_pattern in pattern_found:
                density,region = v_list
                if density<= pattern_dict_return[k_pattern][0]:
                    continue
            density, region = v_list
            if density>=initial_density:
                pattern_found.add(k_pattern)
                pattern_dict_return[k_pattern] = v_list
    return pattern_dict_return
    
    
    
    for start_id in range(0,len(seeds)):
        start_ip = seeds[start_id]
        region = [start_ip,]
        pattern_dict = dict()
        # add the IP down next to the start IP to form a sub-pattern one by one
        flag = 0 # this flag use to break the for index in range()
        for index in range(start_id+1,len(seeds)):
            seed = seeds[index]
            # the first time to form a pattern. at this time the pattern_dict has no item in it
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                if new_pattern in pattern_found:
                    continue
                pattern_dict[new_pattern] = [new_density,new_region]
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_found:
                        flag = 1
                        break
                    pattern_dict[new_pattern] = [new_density, new_region]
            if flag:
                flag = 0
                continue
        # add the IP up next to the start IP to form a sub-pattern one by one
        for index in  reversed(range(0,start_id)):
            seed = seeds[index]
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                if new_pattern in pattern_found:
                    break
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_found:
                        flag = 1
                        break
                    pattern_dict[new_pattern] = [new_density, new_region]
            if flag:
                flag = 0
                break
        for k_pattern, v_list in pattern_dict.items():
            # if k_pattern appears once again, the region is not complete due to break, then contine
            if k_pattern in pattern_found:
                continue
            density, region = v_list
            if density>=initial_density:
                pattern_found.add(k_pattern)
                pattern_dict_return[k_pattern] = v_list
    return pattern_dict_return

def find_sub_pattern3(seeds:list,pattern_seeds=''):
    '''
    find sub-pattern in seeds, eg. input seeds = ['1234','1235','1236','2236','3236','3457','3557','3657']

    Return potential sub-pattern, using pattern_dict={pattern:[density,[seed region]]}, such as {'123*': [0.125, ['1235', '1236']], '*23*': [0.01953125, ['1234', '1235', '1236', '2236', '3236']], '*236': [0.125, ['2236', '3236']], '3***': [0.0009765625, ['3236', '3457', '3557', '3657']], '3*57': [0.125, ['3557', '3657']]}
    '''
    pattern_found = set()
    if not pattern_seeds:
        pattern_seeds = get_pattern_simple(seeds)
    pattern_found.add(pattern_seeds)
    pattern_dict_return = dict()
    
    seeds.sort()
    free_dimension = pattern_seeds.count('*')
    initial_density = len(seeds)/16**free_dimension
    pattern_dict_return[pattern_seeds]=[initial_density,seeds]
    for start_id in range(0,len(seeds)):
        start_ip = seeds[start_id]
        region = [start_ip,]
        pattern_dict = dict()
        # add the IP down next to the start IP to form a sub-pattern one by one
        flag = 0 # this flag use to break the for index in range()
        for index in range(start_id+1,len(seeds)):
            seed = seeds[index]
            # the first time to form a pattern. at this time the pattern_dict has no item in it
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                pattern_dict[new_pattern] = [new_density,new_region]
                if new_pattern in pattern_found:
                    break
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_dict.keys():
                        if pattern_dict[new_pattern][0] > new_density:
                            continue
                    pattern_dict[new_pattern] = [new_density, new_region]
        # add the IP up next to the start IP to form a sub-pattern one by one
        for index in  reversed(range(0,start_id)):
            seed = seeds[index]
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                if new_pattern in pattern_found:
                    break
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_dict.keys():
                        if pattern_dict[new_pattern][0] > new_density:
                            continue
                    pattern_dict[new_pattern] = [new_density, new_region]
        for k_pattern, v_list in pattern_dict.items():
            # if k_pattern appears once again, the region is not complete due to break, then contine
            if k_pattern in pattern_found:
                density,region = v_list
                if density<= pattern_dict_return[k_pattern][0]:
                    continue
            density, region = v_list
            if density>=initial_density:
                pattern_found.add(k_pattern)
                pattern_dict_return[k_pattern] = v_list
    del pattern_dict_return[pattern_seeds]
    return pattern_dict_return

def find_subpattern4(seeds:list,seeds_pattern:str=''):
    patterns = []
    try:
        for i in range(0,len(seeds)):
            for j in range(i+1,len(seeds)):
                start_region = [seeds[i],seeds[j]]
                start_pattern = Pattern(start_region)
                if not start_pattern.pattern in Pattern.patterns:
                    patterns.append(start_pattern)
                    Pattern.add_pattern(start_pattern.pattern) 
                # if start_pattern not in Pattern.patterns:
                #     patterns.append(start_pattern)
                new_patterns = []
                new_regions = []
                for pattern in patterns:
                    new_region,new_pattern = pattern.add(seeds[j])
                    if new_region:
                        if new_pattern not in Pattern.patterns:
                            new_patterns.append(new_pattern)
                            new_regions.append(new_region)
                # if duplicates found in new_patterns
                # if found, select the one which contains the most seeds in new_region
                if len(new_patterns) != len(set(new_patterns)):
                    patterns_, regions_ = select_seed_regions(new_patterns,new_regions)
                    patterns+=[Pattern(x) for x in regions_]
                    map(Pattern.add_pattern,patterns_)
                else:
                    patterns+=[Pattern(x) for x in new_regions]
                    map(Pattern.add_pattern,new_patterns)
    except Exception as e:
        print(e)
        print(i,j)
    if len(patterns)!=len(Pattern.patterns):
        print('len not equal')
        exit(-1)
    if not seeds_pattern:
        seeds_pattern = get_pattern_simple(seeds)
    density = len(seeds)/16**seeds_pattern.count('*')
    return_pattern = []
    for pattern in patterns:
        if pattern.density>density:
            return_pattern.append(pattern)
    return return_pattern

def find_subpattern5(seeds:list,seeds_pattern:str=''):
    '''
    different from find_subpattern4: only preserve patterns with 3*
    '''
    patterns = []
    try:
        for i in range(0,len(seeds)):
            for j in range(i+1,len(seeds)):
                start_region = [seeds[i],seeds[j]]
                pattern_str = get_pattern_simple(start_region)
                if pattern_str.count('*')<=3:

                    start_pattern = Pattern(start_region,pattern_str)
                    if not start_pattern.pattern in Pattern.patterns:
                        patterns.append(start_pattern)
                        Pattern.add_pattern(start_pattern.pattern) 
                # if start_pattern not in Pattern.patterns:
                #     patterns.append(start_pattern)
                new_patterns = []
                new_regions = []
                for pattern in patterns:
                    new_region,new_pattern = pattern.add(seeds[j])
                    if new_pattern.count('*')>3:
                        continue
                    if new_region:
                        if new_pattern not in Pattern.patterns:
                            new_patterns.append(new_pattern)
                            new_regions.append(new_region)
                # if duplicates found in new_patterns
                # if found, select the one which contains the most seeds in new_region
                if len(new_patterns) != len(set(new_patterns)):
                    new_patterns, new_regions = select_seed_regions(new_patterns,new_regions)
                for x,y in zip(new_patterns,new_regions):
                    patterns.append(Pattern(y,x))
                    Pattern.add_pattern(y)
    except Exception as e:
        print(e)
        print(i,j)
    if not seeds_pattern:
        seeds_pattern = get_pattern_simple(seeds)
    density = len(seeds)/16**seeds_pattern.count('*')
    return_pattern = []
    for pattern in patterns:
        if pattern.density>density:
            return_pattern.append(pattern)
    return return_pattern

def process_subpattern5(seeds:list,seeds_pattern:str=''):
    '''
    different from find_subpattern4: only preserve patterns with 3*
    '''
    patterns = []

    for i in range(0,len(seeds)):
        for j in range(i+1,len(seeds)):
            start_region = [seeds[i],seeds[j]]
            pattern_str = get_pattern_simple(start_region)
            if pattern_str.count('*')<=3:

                start_pattern = Pattern(start_region,pattern_str)
                if not start_pattern.pattern in Pattern.patterns:
                    patterns.append(start_pattern)
                    Pattern.add_pattern(start_pattern.pattern) 
            # if start_pattern not in Pattern.patterns:
            #     patterns.append(start_pattern)
            new_patterns = []
            new_regions = []
            for pattern in patterns:
                new_region,new_pattern = pattern.add(seeds[j])
                if new_pattern.count('*')>3:
                    continue
                if new_region:
                    if new_pattern not in Pattern.patterns:
                        new_patterns.append(new_pattern)
                        new_regions.append(new_region)
            # if duplicates found in new_patterns
            # if found, select the one which contains the most seeds in new_region
            if len(new_patterns) != len(set(new_patterns)):
                new_patterns, new_regions = select_seed_regions(new_patterns,new_regions)
            for x,y in zip(new_patterns,new_regions):
                patterns.append(Pattern(y,x))
                Pattern.add_pattern(y)
    if not seeds_pattern:
        seeds_pattern = get_pattern_simple(seeds)
    density = len(seeds)/16**seeds_pattern.count('*')
    return_pattern = []
    for pattern in patterns:
        if pattern.density>density:
            return_pattern.append(pattern)

    tmp_list = []
    for pattern in patterns:
        subpattern = pattern.pattern
        density = pattern.density
        seeds = pattern.seed_region
        tmp_list.append((subpattern,density,seeds))
    tmp_list = sorted(tmp_list, key = lambda x: x[1])
    subpattern_list = []
    for subpattern,density,seeds in tmp_list:
        subpattern_list.append({'subpattern':subpattern,'density':density,'seeds':seeds})
    outjson = {'pattern':seeds_pattern,'subpatterns':subpattern_list}

    fw = open('./seed_region/%s'%seeds_pattern.replace('*','-'),'w')
    json_obj = json.dumps(outjson)
    fw.write(json_obj)
    fw.close()

def find_subpattern6(seeds:list,seeds_pattern:str=''):
    '''
    不同于之前版本：
    1. 仅保留自由维度不大于3的模式
    2. 对任意两个种子生成候选模式，候选模式自由维度不大于3，在向候选模式加入种子时，产生的新模式不再计算，因为新模式会使候选模式空间膨胀
    '''
    patterns = []
    candidate_regions = []
    for i in range(0,len(seeds)):
        for j in range(i+1,len(seeds)):
            start_region = [seeds[i],seeds[j]]
            candidate_regions.append(start_region)
    start_patterns = []
    for region in candidate_regions:
        pattern_str = get_pattern_simple(region)
        if not pattern_str in start_patterns:
            if pattern_str.count('*')<=3:
                start_patterns.append(pattern_str)
                patterns.append(Pattern2(region,pattern_str))
    for seed in seeds:
        for pattern in patterns:
            pattern.add(seed)
    return patterns


def process_find_subpattern6(lines:list,process_index,filename_pattern_jsonout:str,max_freed=3):
    '''
    不同于之前版本：
    1. 仅保留自由维度不大于3的模式
    2. 对任意两个种子生成候选模式，候选模式自由维度不大于3，在向候选模式加入种子时，产生的新模式不再计算，因为新模式会使候选模式空间膨胀
    '''
    filename_jsonout = filename_pattern_jsonout.replace('*',str(process_index))
    loginfo = '[%s] process_find_subpattern6 start. process id: %s. seed region num: %s. output json name %s.'%(get_time_now(),process_index,len(lines),filename_jsonout)
    print(loginfo)
    outjson_list = []
    s = time.time()
    for line in lines:
        seeds_pattern = line[0]
        seeds = line[2]
        if len(seeds) == 1:
            continue
        if seeds_pattern.count('*')==1:
            continue
        patterns = []
        candidate_regions = []
        for i in range(0,len(seeds)):
            for j in range(i+1,len(seeds)):
                start_region = [seeds[i],seeds[j]]
                candidate_regions.append(start_region)
        start_patterns = []
        for region in candidate_regions:
            pattern_str = get_pattern_simple(region)
            if not pattern_str in start_patterns:
                if pattern_str.count('*')<=max_freed:
                    start_patterns.append(pattern_str)
                    patterns.append(Pattern2(region,pattern_str))
        for seed in seeds:
            for pattern in patterns:
                pattern.add(seed)
        
        tmp_list = []
        for pattern in patterns:
            subpattern = pattern.pattern
            density = pattern.density
            seeds = pattern.seed_region
            tmp_list.append((subpattern,density,seeds))
        tmp_list = sorted(tmp_list, key = lambda x: x[1])
        subpattern_list = []
        for subpattern,density,seeds in tmp_list:
            subpattern_list.append({'subpattern':subpattern,'density':density,'seeds':seeds})
        outjson = {'pattern':seeds_pattern,'subpatterns':subpattern_list}
        outjson_list.append(outjson)

    fw = open(filename_jsonout,'w')
    json_obj = json.dumps(outjson_list)
    fw.write(json_obj)
    fw.close()

    loginfo = '[%s] process_find_subpattern6 end. process id: %s. seed region num: %s. output json name %s. time cost: %s.'%(get_time_now(),process_index,len(lines),filename_jsonout,time.time()-s)
    print(loginfo)
    return outjson_list

def select_seed_regions(patterns:list, seed_regions:list):
    '''
    for duplicates in patterns, select most seeds in seed_regions

    Params: patterns and their corresponding seeds (seed_regions)
    '''

    # b = {element1:occur_times, ...}
    b = dict(Counter(patterns))
    return_indexes = []
    for ele, occur_count in b.items():
        if occur_count > 1:
            # duplicate element indexes in patterns
            index_list = []
            index = -1
            for i in range(0,occur_count):
                index = patterns.index(ele, index+1)
                index_list.append(index)
            max_seed_num = -1
            max_index = -1
            for index in index_list:
                if len(seed_regions[index]) > max_seed_num:
                    max_seed_num = len(seed_regions[index])
                    max_index = index
            # index of duplicates with most seeds
            return_indexes.append(max_index)
        else:
            # index of non-duplicates
            return_indexes.append(patterns.index(ele))
    return_regions = []
    return_patterns = []
    for index in return_indexes:
        return_patterns.append(patterns[index])
        return_regions.append(seed_regions[index])
    return return_patterns,return_regions



def find_sub_pattern(seeds:list, pattern_seeds:str):
    '''
    find sub-pattern in seeds, eg. input seeds = ['1234','1235','1236','2236','3236','3457','3557','3657']

    Return potential sub-pattern, using pattern_dict={pattern:[density,[seed region]]}, such as {'123*': [0.125, ['1235', '1236']], '*23*': [0.01953125, ['1234', '1235', '1236', '2236', '3236']], '*236': [0.125, ['2236', '3236']], '3***': [0.0009765625, ['3236', '3457', '3557', '3657']], '3*57': [0.125, ['3557', '3657']]}
    '''
    pattern_found = set()
    pattern_found.add(pattern_seeds)
    pattern_dict_return = dict()
    seeds.sort()
    free_dimension = pattern_seeds.count('*')
    initial_density = len(seeds)/16**free_dimension
    for start_id in range(0,len(seeds)):
        start_ip = seeds[start_id]
        region = [start_ip,]
        pattern_dict = dict()
        # add the IP down next to the start IP to form a sub-pattern one by one
        flag = 0 # this flag use to break the for index in range()
        for index in range(start_id+1,len(seeds)):
            seed = seeds[index]
            # the first time to form a pattern. at this time the pattern_dict has no item in it
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                pattern_dict[new_pattern] = [new_density,new_region]
                if new_pattern in pattern_found:
                    break
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_found:
                        flag = 1
                        break
                    pattern_dict[new_pattern] = [new_density, new_region]
            if flag:
                flag = 0
                break
        # add the IP up next to the start IP to form a sub-pattern one by one
        for index in  reversed(range(0,start_id)):
            seed = seeds[index]
            if not pattern_dict.items():
                new_region, new_pattern, new_density = combine_seeds(region,seed)
                if new_pattern in pattern_found:
                    break
            else:
                v_list = list(pattern_dict.values())
                for density,region in v_list:
                    new_region, new_pattern, new_density = combine_seeds(region,seed)                    
                    if new_pattern in pattern_found:
                        flag = 1
                        break
                    pattern_dict[new_pattern] = [new_density, new_region]
            if flag:
                flag = 0
                break
        for k_pattern, v_list in pattern_dict.items():
            # if k_pattern appears once again, the region is not complete due to break, then contine
            if k_pattern in pattern_found:
                continue
            density, region = v_list
            if density>=initial_density:
                pattern_found.add(k_pattern)
                pattern_dict_return[k_pattern] = v_list
    return pattern_dict_return

def combine_seeds(region:list, ip:str):
    '''
    add the parameter ip to the paremeter region:list to form a new_region, and  then calculate the pattern and the density of the new region, at last return the results 
    '''
    new_region = region.copy()
    new_region.append(ip)
    new_pattern = find_pattern(new_region)
    free_dimension_count = new_pattern.count('*')
    new_density = len(new_region)/16**free_dimension_count
    return new_region, new_pattern, new_density

def get_density(seeds_exploded:list):
    new_pattern = get_pattern_simple(seeds_exploded)
    free_dimension_count = new_pattern.count('*')
    new_density = len(seeds_exploded)/16**free_dimension_count
    return new_density

def get_pattern_simple(hitlist_exploded:list):
    pattern = ['0']*32
    for i in range(0,32):
        col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
        col_i_values = set(col_i_values)
        if len(col_i_values) == 1:
            pattern[i] = col_i_values.pop()
        else:
            pattern[i] = '*'
    return ''.join(pattern)


def find_pattern(seeds:list):
    '''
    input seeds output a pattern

    Example:

    input: ['1234','1234','1236'] return '123*'
    '''
    patterns = []
    row = len(seeds)
    col = len(seeds[0])
    dlist = seeds2double_array(seeds)
    for c in range(0,col):
        col_values = set()
        for r in range(0,row):
            value_rc = dlist[r][c]
            col_values.add(value_rc)
        if len(col_values) > 1:
            patterns.append('*')
        else:
            patterns.append(col_values.pop())
    return ''.join(patterns)

def seeds2double_array(seeds:list):
    '''
    input seeds like ['1234','1235','1246'] return double list like [['1','2','3','4'], ['1','2','3','5'], ['1','2','3','6']]
    '''
    dlist = []
    for seed in seeds:
        dlist.append(list(seed))
    return dlist

def print_subpattern_dict(seeds):
    a = find_sub_pattern3(seeds)
    for pattern,values in a.items():
        density, seeds_ = values
        print(pattern,'#',density)
        print('-'*32)
        for seed in seeds_:
            print(seed)
        print()

def output_subpattern():
    '''
    this function works with find_sub_pattern3
    '''
    inputfile = './seed_region/seed_regions_sp5.256.txt'
    outputfile = inputfile.replace('.txt','.subpattern.txt')
    f = open(inputfile)
    fw = open(outputfile,'w')
    output_list = []
    count=0
    for line in f:
        info = line.strip('\n').split('\t')
        origin_pattern = info[0]
        origin_seeds = info[1:]
        # a = find_sub_pattern3(origin_seeds)
        a = find_sub_pattern3(origin_seeds)
        tmp_list = []
        for subpattern,values in a.items():
            density, seeds = values
            tmp_list.append((subpattern,density,seeds))
        tmp_list = sorted(tmp_list, key = lambda x: x[1])
        subpattern_list = []
        for subpattern,density,seeds in tmp_list:
            subpattern_list.append({'subpattern':subpattern,'density':density,'seeds':seeds})
        output_list.append({'pattern':origin_pattern,'subpatterns':subpattern_list})
        count+=1
        if count >= 1:
            pass
    json_obj = json.dumps(output_list)
    fw.write(json_obj)
    fw.close()

def output_subpattern2():
    '''
    this function works with find_subpattern4,5
    '''
    inputfile = './seed_region/seed_regions_sp5.256.txt'
    outputfile = inputfile.replace('.txt','.subpattern.json')
    f = open(inputfile)
    fw = open(outputfile,'w')
    fw_single = open('single_seeds.txt','w')
    output_list = []
    count = 0
    s = time.time()
    for line in f:
        s = time.time()
        info = line.strip('\n').split('\t')
        origin_pattern = info[0]
        origin_seeds = info[1:]
        sl = len(origin_seeds)
        print(sl)
        if sl ==1:
            fw_single.write(origin_pattern+'\n')
            continue
        # a = find_sub_pattern3(origin_seeds)
        patterns = find_subpattern6(origin_seeds,origin_pattern)
        tmp_list = []
        for pattern in patterns:
            subpattern = pattern.pattern
            density = pattern.density
            seeds = pattern.seed_region
            tmp_list.append((subpattern,density,seeds))
        tmp_list = sorted(tmp_list, key = lambda x: x[1])
        subpattern_list = []
        for subpattern,density,seeds in tmp_list:
            subpattern_list.append({'subpattern':subpattern,'density':density,'seeds':seeds})
        output_list.append({'pattern':origin_pattern,'subpatterns':subpattern_list})
        count+=1
        if count >10000:
            print(time.time()-s)
            s = time.time()
            count = 0
        #print('seeds len',len(origin_seeds),'time',time.time()-s)

    json_obj = json.dumps(output_list)
    fw.write(json_obj)
    fw.close()
    fw_single.close()


def output_subpattern3():
    '''
    this function works with find_subpattern4,5
    '''
    inputfile = './seed_region/seed_regions_sp5.256.txt'
    f = open(inputfile)
    for line in f:
        info = line.strip('\n').split('\t')
        origin_pattern = info[0]
        origin_seeds = info[1:]
        print(len(origin_seeds))
        # a = find_sub_pattern3(origin_seeds)
        multiprocessing.Process(target=process_find_subpattern6,args=(origin_seeds,origin_pattern),name=origin_pattern).start()
        time.sleep(0.1)
        while(psutil.cpu_percent()>=90 or psutil.virtual_memory().percent>=60):
            time.sleep(5)

def execute_subpattern6_multiprocess(seed_regions:list=[],filename_seedRegions:str='',filename_pattern_jsonout=''):
    '''
    if seed-regions not given, read seed_regions from filename_seedRegions
    
    this function works with find_subpattern4,5,6


    '''
    if not filename_pattern_jsonout:
        filename_pattern_jsonout = 'subpattern*.%s.json'%get_time_now()
    if not seed_regions:
        seed_regions = read_big_file(filename_seedRegions)
        seed_regions = [seed_region.split('\t') for seed_region in seed_regions]
    else:
        seed_regions = [[get_pattern_simple(seed_region)]+seed_region for seed_region in seed_regions]
    
    NUM_PROCESS = 10
    num_seedRegion_per_process = int(len(seed_regions)/NUM_PROCESS) + 1
    pool = multiprocessing.Pool(NUM_PROCESS)
    results = []
    # 异步方法，不会阻塞，程序会向下执行
    for i in range(0,NUM_PROCESS):
        start = i*num_seedRegion_per_process
        end = (i+1)*num_seedRegion_per_process
        group_seed_regions = seed_regions[start:end]
        group_id = i
        r = pool.apply_async(process_find_subpattern6,(group_seed_regions, group_id, filename_pattern_jsonout))
        results.append(r)
    pool.close()
    pool.join()
    sorted_results = []
    for r in results:
        index,targets_r,targets_noseed_r = r.get() # r.get()返回值是一个列表，取第一个
        sorted_results.append((index,targets_r,targets_noseed_r))
    return sorted_results, seed_regions


if __name__ == '__main__':
    s = time.time()
    targets = []
    p = '200119002100000000000000000000**'
    t = pattern2ipv6s_count(p,0,1024)
    print(len(t))
    for i in range(0,4097):
        targets_generated = pattern2ipv6s_count(p,256*i,256)
        if len(targets_generated)!=256:
            print(i,len(targets_generated))
        if not targets_generated:break
        targets+=targets_generated
    targets.sort()
    write_list2file(targets,'test.targets.txt')
    print(len(targets),time.time()-s)
    # range1 = ['1','2','3','4']
    # range2 = ['2','6','9','10']
    # segments = [(28,range1),(31,range2)]
    # pattern = '20010db800000000000000000000*00*'
    # a=repalce_wildcard_conservative(pattern,segments)
    # print(a)
    #output_subpattern4()
    #output_subpattern()
    # p = '2001190021000000000000000001****'
    # ipv6s = pattern2ipv6s(p)
    # output_list2file('2001190021000000000000000001----_seed.txt',ipv6s)
    # test_replace_wildcard()
    #test_find_sub_pattern()
    # a = ['2a0107c8aacb0258505400fffec5f4af','2a0107c8aacb02710000000000000001','2a0107c8aacb027e10de51e8eb667583','2a0107c8aacb027f0000000000000001','2a0107c8aacb02b20000000000000001','2a0107c8aacb02ba505400fffee8eb27','2a0107c8aacb02c4505400fffe8312eb']
    # b = find_subpattern6(a)
    # for c in b:
    #     print(c.pattern,c.seed_region,c.density)
    # print_subpattern_dict(a)
    # print(b)
    # seeds = ['11111111111111111111111111111234','11111111111111111111111111111235','11111111111111111111111111111236','11111111111111111111111111112236','11111111111111111111111111113236','11111111111111111111111111113457','11111111111111111111111111113557','11111111111111111111111111113657']
    # b = find_sub_pattern3(seeds)
    # print(b)
    # a='20011210010000010000000000000017	20011210010000010000000000000218	20011210010500340000040300a80001	20011210010500340000060600a80031	20011210010600010000000000000000	20011210340001520000000000000000	20011210340001520000000000000014	20011210340001520000000000000202	20011210340001570000000000000000	200112107000085a0000000000000000	200112107000085a0000000000000002	20011210000000000000000000010000	20011210000000000000000000010001	2001121000000000000000000001000c	2001121000000000000000000001000d'
    # a=a.split('\t')
    # print_subpattern_dict(a)


    # test class Pattern
    # seeds = ['20011210010000010000000000000017','20011210010000010000000000000218']
    # pattern = Pattern(seeds)
    # print(pattern.pattern,pattern.density,pattern.seed_region)
    # pattern.add('20011210010000010000000000000219')
    # print(pattern.pattern,pattern.density,pattern.seed_region)