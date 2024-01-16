import time
from mytime import get_time_now
from myipv6 import hexstr2ipv6
import json
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
    p = '200119002100000000000000000*****'
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