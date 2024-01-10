
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



    

if __name__ == '__main__':
    ''' test code
    pattern = '2001028822011000000000000000***a'
    seeds = ['2001028822011000000000000000068a','20010288220110000000000000000bba','20010288220110000000000000000caa','2001028822011000000000000000138a']
    a = pattern2ipv6s2(pattern,seeds)
    print(a)
    '''
