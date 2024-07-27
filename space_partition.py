from pattern import get_pattern_simple
import queue
import time
from collections import Counter,defaultdict

from mytime import get_time_now


def get_free_dimension(hitlist_exploded:list,return_mode:str):
    '''
return free/variable dimensions and corresponding values(nybbles) in hitlist

Parameters:
    - hitlist_exploded:list. hex str format IPv6 without colon. e.g. an element in list is '20010db8000000000000000000000000'
    - return_mode: return mode == 'leftmost', return immediately when meeting a free dimension; \
    return_mode == 'mvc', return free dimensions and corresponding values(nybbles) in a dict; \
    return_mode == 'maxcovering', return free dimensions and corresponding frequency of the nybbles(a dict) in a dict

Returns: 
    - return according to the parameter return_mode. 
    if leftmost return the first/leftmost free dimension and corresponding values(nybbles);
    if mvc return a dict. the keys are free dimensions, the values are corresponding values;
    if maxcovering, return a dict. the keys are free dimensions, the values are dicts where keys are nybbles and values are their occurrence frequency count
    '''
    free_dimension = dict()
    if return_mode == 'leftmost':
        for i in range(0,32):
            col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
            col_i_values = list(set(col_i_values))
            if len(col_i_values) > 1:
                return i,col_i_values
    elif return_mode == 'mvc':
        for i in range(0,32):
            col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
            col_i_values = list(set(col_i_values))
            if len(col_i_values) > 1:
                free_dimension[i] = col_i_values
        return free_dimension
    elif return_mode == 'maxcovering':
        for i in range(0,32):
            col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
            col_i_values_set = list(set(col_i_values))
            if len(col_i_values_set) > 1:
                free_dimension[i] = dict(Counter(col_i_values))
        return free_dimension
    else:
        print('return_mode not correct')
        exit(-1)

    return free_dimension


def mvc(hitlist_exploded):
    free_dimension_dict = get_free_dimension(hitlist_exploded,return_mode='mvc')
    min_length = 17
    min_keys = []
    for key, value in free_dimension_dict.items():
        if len(value) < min_length:
            min_length = len(value)
            min_keys = [key]
        elif len(value) == min_length:
            min_keys.append(key)
    leftmost_freed = min(min_keys)
    
    prefix_dict = defaultdict(list)

    for ip in hitlist_exploded:
        prefix_dict[ip[leftmost_freed]].append(ip)
    # prefix_dict = dict()
    # for freed_value in free_dimension_dict[leftmost_freed]:
    #     prefix_dict[freed_value] = []
    # for ip in hitlist_exploded:
    #     prefix_dict[ip[leftmost_freed]].append(ip)
    return prefix_dict
    #return prefix_dict,leftmost_freed,free_dimension_dict
    # return prefix_dict,leftmost_freed,free_dimension_dict 配合space_parition_record使用，用于画图

def cal_covering(nybble_frequency:dict,seed_num:int):
    count = 0
    for frequency in nybble_frequency.values():
        if frequency<2: continue
        count+=frequency
    return count/seed_num

def max_covering(hitlist_exploded):
    free_dimension_dict = get_free_dimension(hitlist_exploded,return_mode='maxcovering')
    max_covering_values = -1
    leftmost_freed = -1
    free_dimension_nybbles = []
    for freed, nybble_frequency in free_dimension_dict.items():
        covering = cal_covering(nybble_frequency,len(hitlist_exploded))
        if covering>max_covering_values:
            max_covering_values = covering
            free_dimension_nybbles = list(nybble_frequency.keys())
            leftmost_freed = freed
    prefix_dict = dict()


    for freed_value in free_dimension_nybbles:
        prefix_dict[freed_value] = []
    for ip in hitlist_exploded:
        prefix_dict[ip[leftmost_freed]].append(ip)
    return prefix_dict


def leftmost(hitlist_exploded:list):
    free_dimension, variables = get_free_dimension(hitlist_exploded,return_mode='leftmost')
    
    nybble_seeds_dict = dict()
    # initialize dict according to keys(nybbles)
    for nybble in variables:
        nybble_seeds_dict[nybble] = []
    # 根据该维度的自由维度值聚类种子
    for ip in hitlist_exploded:
        nybble_seeds_dict[ip[free_dimension]].append(ip)
    return nybble_seeds_dict


def space_partition(exploded_hitlist:list,th=16,func=leftmost):
    '''
Parameters:
    - exploded_hitlist: list of exploded ipv6 hex str without ':'. e.g. 20010db8000000000000000000000000. its compressed format is 2001:db8::
    '''

    s = time.time()
    seed_regions = []
    q = queue.Queue()
    q.put(exploded_hitlist)
    while not q.empty():
        node = q.get()
        if len(node) <= th:
            seed_regions.append(node)
        else:
            new_nodes = func(node).values()
            for new_node in new_nodes:
                q.put(new_node)

    #print(func.__name__,'space partition done, th=',th,'seed num',len(exploded_hitlist),'time cost',time.time()-s)
    #print('*'*10)
    return seed_regions


def output_seed_regions(seed_regions:list,output_filename:str,output_human_readable=True,return_density_list=False,sorted_list=True):
    """
output seed_regions to files

Parameters:
    - seed_regions: list. double list. e.g. seed_regions = [[],[],]
    - output_filename:str. dir + file name
    - output_human_readable_file: bool. default True. whether to output human readable file. the content in file is same. the format is convinient for people to read.
    """
    s = time.time()
    single_count = 0
    density_list = []
    fw = open(output_filename,'w')
    if not output_human_readable:
        for seeds in seed_regions:
            pattern = get_pattern_simple(seeds)
            line = '\t'.join([pattern,]+seeds)+'\n'
            fw.write(line)
    else:
        if '.txt' in output_filename:
            readable_file = output_filename.replace('.txt','.humanread.txt')
        else:
            readable_file = output_filename+'humanread'
        fw_hr = open(readable_file,'w')
        for seeds in seed_regions:
            if len(seeds) < 2: 
                single_count+=1
                continue
            pattern = get_pattern_simple(seeds)
            density = len(seeds)/16**pattern.count('*')
            density_list.append((pattern,density,seeds))
        if sorted_list:
            density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
        for pattern,density,seeds in density_list:
            line = '\t'.join([pattern,str(density)]+seeds)+'\n'
            fw.write(line)
            fw_hr.write(pattern+str(density)+'\n')
            fw_hr.write('-'*32+'\n')
            fw_hr.writelines([x+'\n' for x in seeds])
            fw_hr.write('#'*32+'\n\n')
        fw_hr.close()
    fw.close()
    loginfo = '[%s] output seed regions done. output dir is %s. seed regions/pattern num is %s. single num is%s. time cost %ss'%(get_time_now(),output_filename,len(seed_regions),single_count,time.time()-s)
    print(loginfo)
    if return_density_list:
        return density_list
    #print(output_filename,'output seed regions done, regions/pattern num',len(seed_regions),'single number',single_count,'time cost: ',time.time()-s)
    #print('#'*10)

