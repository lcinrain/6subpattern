import time
from mytime import get_time_now
from myipv6 import hexstr2ipv6
import json
import math

HEX_FULL = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

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



def pattern2ipv6s_simple(pattern:str):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = replace_wildcard_simple(pattern)
    return list(map(hexstr2ipv6,p_l))

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


def process_find_subpattern6(lines:list,process_index,filename_pattern_jsonout:str,max_freed=3):
    filename_jsonout = filename_pattern_jsonout.replace('*',str(process_index))
    loginfo = '[%s] process_find_subpattern6 start. process id: %s. seed region num: %s. output json name %s.'%(get_time_now(),process_index,len(lines),filename_jsonout)
    print(loginfo)
    outjson_list = []
    s = time.time()
    for seeds_pattern,density_origin,seeds_origin in lines:
        if len(seeds_origin) == 1:
            continue
        if seeds_pattern.count('*')==1:
            continue
        patterns = []
        candidate_regions = []
        for i in range(0,len(seeds_origin)):
            for j in range(i+1,len(seeds_origin)):
                start_region = [seeds_origin[i],seeds_origin[j]]
                candidate_regions.append(start_region)
        start_patterns = []
        for region in candidate_regions:
            pattern_str = get_pattern_simple(region)
            if not pattern_str in start_patterns:
                if pattern_str.count('*')<=max_freed:
                    start_patterns.append(pattern_str)
                    patterns.append(Pattern2(region,pattern_str))
        for seed in seeds_origin:
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
        outjson = {'pattern':seeds_pattern,'density':density_origin,'seeds':seeds_origin,'subpatterns':subpattern_list}
        outjson_list.append(outjson)

    fw = open(filename_jsonout,'w')
    json_obj = json.dumps(outjson_list)
    fw.write(json_obj)
    fw.close()

    loginfo = '[%s] process_find_subpattern6 end. process id: %s. seed region num: %s. output json name %s. time cost: %s.'%(get_time_now(),process_index,len(lines),filename_jsonout,time.time()-s)
    print(loginfo)
    return outjson_list


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


