import random


HEX_STR = set(['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f'])



def find_all_freed_indexes(pattern:str):
    '''
    查找pattern中*出现的全部索引
    '''
    indexes = []
    for i in range(32):
        if pattern[i] == '*':
            indexes.append(i)
    return indexes

def pattern2ipv6s_6graph(pattern,seeds_exploded,num2generate=0,targets_generated={}):
    
    '''
    one Hamming distance generation used in 6Graph. Note: this function is not perfect. It genetates duplicates in the FOR loop .  Recording the used freed and seed, skipping them in next generation will save much time.
    
    Parameters:
        - pattern: used to generate targets
        - seeds_exploded: seeds in this pattern. 32 nibbles, eg, 20010db8...00000
        - num2generate: the number of targets to generate this round
        - targets_generated: the generated targets using this pattern before
    '''
    targets_generated = set(targets_generated)
    budget = num2generate
    freeds = find_all_freed_indexes(pattern)
    for freed in freeds:
        for seed in seeds_exploded:
            targets = replace_wildcard_one_dimession(seed,freed)
            targets = set(targets) - targets_generated
            targets_generated.update(targets)
            budget-=len(targets)
            if budget<=0:
                return targets_generated
    return []

    

def replace_wildcard_one_dimession(pattern:str,freed_index=-1):
    '''
    replace * to 0-f. the pattern must contain one *
    '''
    targets = []
    if freed_index<0:
        freed_index = pattern.index('*')
    part1 = pattern[:freed_index]
    part2 = pattern[freed_index+1:]
    targets = [''.join([part1,hex_char,part2]) for hex_char in HEX_STR]
    return targets


def generate_prescan_targets(pattern:str,seeds,num2generate=0):
    '''
    design for 6Forest targets generation. The author didn't provide details in the paper. This function generates candidate prescan targets that are one nibble Hamming distance from all the seeds, and then randomly sample num2generate targets for prescan. The num2generate is 16 times of the free dimensions. The returned targets may contain seeds.
    '''
    targets_all = set()
    if not num2generate:
        freed = pattern.count('*')
        num2generate = freed*16
    freeds = find_all_freed_indexes(pattern)
    for freed in freeds:
        for seed in seeds:
            targets = replace_wildcard_one_dimession(seed,freed)
            targets_all.update(targets)
    if num2generate<len(targets_all):
        targets_all = random.sample(targets_all,num2generate)
    return targets_all



def replace_wildcard_one_dimession(pattern:str,freed_index=-1):
    '''
    replace * to 0-f. the pattern must contain one *
    '''
    targets = []
    if freed_index<0:
        freed_index = pattern.index('*')
    part1 = pattern[:freed_index]
    part2 = pattern[freed_index+1:]
    targets = [''.join([part1,hex_char,part2]) for hex_char in HEX_STR]
    return targets

def pattern2ipv6s_simple(pattern:str):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = replace_wildcard_simple(pattern)
    return list(map(hexstr2ipv6,p_l))

def replace_wildcard_simple(pattern:str):
    prefix = ''
    prefixes = ['',]
    prefixes_tmp = []
    for h in pattern:
        if h == '*':
            for hex_char in HEX_STR:
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

def pattern2ipv6s(pattern:str):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    p_l = [pattern,]
    count = pattern.count('*')
    l = []
    for i in range(0,count):
        for p in p_l:
            tmp = replace_wildcard(p)
            l = l + tmp
        p_l = l
        l = []
    
    return list(map(hexstr2ipv6,p_l))



def replace_wildcard(pattern_str:str):
    '''
    repalce the most left * in pattern with 0-f

    input a pattern with at least one *, return a list with * replaced with 0-f

    this fuction is a component in fuction pattern2ipv6s
    '''
    l = []
    for hex_char in ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']:
        tmp_pattern = pattern_str.replace('*',hex_char,1)
        l.append(tmp_pattern)
    return l


def get_sorted_pattern(reverse = True):
    pattern_density_list = []
    try:
        f = open('addr_patterns.sorted.txt')
        for line in f.readlines():
            info = line.strip('\n').split('\t')
            pattern = info[0]
            density = float(info[1])
            seeds = info[2:]
            pattern_density_list.append((pattern,density,seeds))
        f.close()
        return pattern_density_list
    except FileNotFoundError:
        pass
    f = open('addr_patterns.txt')
    for line in f.readlines():
        info = line.strip('\n').split('\t')
        pattern = info[1]
        seeds = info[2:]
        density = len(seeds)/16**pattern.count('*')
        pattern_density_list.append((pattern,density,seeds))
    f.close()
    pattern_density_list = sorted(pattern_density_list,key= lambda x:x[1],reverse=reverse)
    
    fw = open('addr_patterns.sorted.txt','w')
    for pattern,density,seeds in pattern_density_list:
        line = '\t'.join([pattern,str(density)]+seeds)+'\n'
        fw.write(line)
    fw.close()
    print(len(pattern_density_list))
    return pattern_density_list

 


def pattern2ipv6s2(pattern:str,seeds_exploded:list):
    """
    change pattern ie '200119002100000000000000000*****' to ipv6 addr by replace * to 0-f

    Return list contain ipv6
    """
    targets = []
    freed_dict = get_free_dimension_dict(seeds_exploded,pattern)
    for seed in seeds_exploded:
        targets+=replace_wildcard2(seed,freed_dict)
    return list(map(hexstr2ipv6,targets))

def get_free_dimension_dict(hitlist_exploded:list,pattern:str):
    indices = [i for i in range(0,32) if pattern[i]=='*' ]
    free_dimension = dict()
    for i in indices:
        col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
        col_i_values = set(col_i_values)
        free_dimension[i] = HEX_STR - col_i_values
    return free_dimension


def replace_wildcard2(seed:str,free_dimension_dict:dict):
    '''
    this is an alternative of replace_wildcard. 
    '''
    l = []
    for wild_card_index,hex_range in free_dimension_dict.items():
        prefix = seed[:wild_card_index]
        postfix = seed[wild_card_index+1:]
        
        for hex_char in hex_range:
            sub_pattern = ''.join([prefix,hex_char,postfix])
            l.append(sub_pattern)
    return l



    

if __name__ == '__main__':
    ''' test code
    pattern = '2001028822011000000000000000***a'
    seeds = ['2001028822011000000000000000068a','20010288220110000000000000000bba','20010288220110000000000000000caa','2001028822011000000000000000138a']
    a = pattern2ipv6s2(pattern,seeds)
    print(a)
    '''
