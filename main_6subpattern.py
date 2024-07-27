from myio import write_densityList2file,write_list2file,read_densityList,read_big_file
from mytime import get_time_now,get_currentime
from space_partition import space_partition,mvc,output_seed_regions,leftmost
import time
import multiprocessing
from pattern import process_find_subpattern6,pattern2ipv6s_simple,pattern2ipv6s_conservative,pattern2ipv6s_count
from pattern_refine import patterns_refine_conservative,read_refine_conservative_pattern
import os
from myipv6 import ipv62hexstr

K = 10**3
M = 10**6


def format_subpatternJsonList(jsonlist:list,seed_regions:list,num_freed):
    '''
    return pattern_density_list,no duplicate pattern. Sort by Density DESC
    '''
    density_list = []
    for seed_region in seed_regions:
        pattern = seed_region[0]
        freed = pattern.count('*')
        if freed >num_freed:continue
        seeds = seed_region[2]
        #num_seed = len(seeds)
        density = seed_region[1]
        density_list.append((pattern,density,seeds))
    for subpattern_list in jsonlist:
        for item in subpattern_list:
            origin_density = item['density']
            origin_seeds = item['seeds']
            pattern = item['pattern']
            subpatterns = item['subpatterns']
            for sub in subpatterns:
                subpattern = sub['subpattern']
                density = sub['density']
                density = float(density)
                seeds = sub['seeds']
                num_seed = len(seeds)
                freed = subpattern.count('*')
                if freed > num_freed: continue
                density_list.append((subpattern,density,seeds))
    density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
    density_list_noduplicate = []
    patterns = set()
    for pattern,density,seeds in density_list:
        if pattern in patterns:continue
        density_list_noduplicate.append((pattern,density,seeds))
        patterns.add(pattern)
    return density_list_noduplicate


def process_generate_refine_targets_simple2(output_dir:str,pattern_density_list:list,filename_refinePattern_out:str,budget=10**7,input_seeds={},start_input='0'):
    '''
    store targets in  one file
    '''
    targets_all = set()
    patterns_generated = set()
    budget_total = budget
    if start_input != '3':
        print('pattern.refine.txt not find, refining patterns(conservative)')
        pattern_conservative_list = patterns_refine_conservative(pattern_density_list,'',filename_refinePattern_out)
    else:
        pattern_conservative_list = read_refine_conservative_pattern(filename_refinePattern_out)
    for pattern,density,representation,seeds in pattern_conservative_list:
        if pattern in patterns_generated:continue
        patterns_generated.add(pattern)
        targets_generated = pattern2ipv6s_conservative(pattern,representation)
        targets_generated = set(targets_generated) - set(input_seeds)
        targets_all.update(targets_generated)
        budget_total-=len(targets_generated)
        if budget_total<=0:break
    
    output_filename = output_dir + f'target{budget}'
    write_list2file(targets_all,output_filename)
    print(get_currentime(),'generate targets with conservative patterns done')

def process_generate_targets_simple2v2(output_dir:str,pattern_density_list:list,budget=10**6,input_seeds={}):
    '''
    直接输出目标，去掉round参数
    '''
    input_seeds = set(input_seeds)
    total_budget = budget

    patterns_generated = set()
    pattern_density_list_3dplus = []
    all_targets = set()
    # generate with 3d patthern
    while total_budget>0:
        for  pattern,density,seeds in pattern_density_list:
            if density == 1.0:continue
            pfreed = pattern.count('*')
            if pfreed>3:
                pattern_density_list_3dplus.append((pattern,density,seeds))
                continue
            if pattern in patterns_generated:continue
            patterns_generated.add(pattern)
            targets_generated = pattern2ipv6s_simple(pattern)
            targets_generated = set(targets_generated) - input_seeds
            len_origin = len(all_targets)
            all_targets.update(targets_generated)
            budget_cost = len(all_targets) - len_origin
            total_budget-=budget_cost
            if total_budget<=0:break
        print('3d pattern done, budget left',total_budget)

    num_round = 0
    num2generate = 256 if total_budget>1*K else 16
    pattern_density_list_3dplus.sort(key=lambda x:x[1],reverse=True)
    while(total_budget>0 and pattern_density_list_3dplus):
        for pattern,density,seeds in pattern_density_list_3dplus:
            targets_generated = pattern2ipv6s_count(pattern,num_round*num2generate,num2generate)
            targets_generated = set(targets_generated) - input_seeds
            len_origin = len(all_targets)
            all_targets.update(targets_generated)
            num_generated = len(all_targets) - len_origin
            total_budget-=num_generated
            if total_budget<=0:break
    output_filename = output_dir + f'target{budget}'
    write_list2file(all_targets,output_filename)
    print(get_currentime(),'generate targets done')
    return all_targets


def main2(dir_base,seed_file,budget=10**6,th=16,num_freed=32,strategy='23',start_input='0',NUM_PROCESS = 10,indicator_func=leftmost,subpattern_freed=3):
    '''

    Parameters:
        - num_freed: the patterns whose free dimensions > num_freed will not be used to generate targets.
        - th: the threshold in space partition (DHC).
        - start_input:
            - 0: start from reading hitlist
            - 1: start from reading seed regions
            - 2: start from reading density list
        - strategy: str. eg,'1' or '2', or '12', '123',.... If multiple strategies are used, the results will be output to different folders.
            - '1': use dynamic generation
            - '2': use static generation
            - '3': use static generation + refined patterns(conservative patterns)
        - subpattern_freed: the subpatterns whose number of free dimensions > this value will not used to generate targets. 
    '''

    filename_hitlist_read = seed_file
    hitlist_compressed = read_big_file(seed_file)
    hitlist_exploded = [ipv62hexstr(x) for x in hitlist_compressed]
    write_list2file(hitlist_exploded,seed_file+'.exploded.txt')
    input_seeds = hitlist_exploded

    density_list = []
    if start_input == '2':
        print(get_currentime(),'start from reading density_list')
        filename_densityList = os.path.join(dir_base,'density_list.sorted.txt')
        density_list = read_densityList(filename_densityList)
        density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
        density_list_noduplicate = []
        patterns = set()
        for pattern,density,seeds in density_list:
            if pattern in patterns:continue
            density_list_noduplicate.append((pattern,density,seeds))
            patterns.add(pattern)
        print('read',filename_densityList,' done, reduce len ',len(density_list),'->',len(density_list_noduplicate))
        density_list = density_list_noduplicate
    
    if start_input == '1':
        print('start from read seed_regions #############')
        filename_densityList = dir_base + 'seed_regions.th%s.txt'%th
        density_list = read_densityList(filename_densityList)
        density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
        density_list_noduplicate = []
        patterns = set()
        for pattern,density,seeds in density_list:
            if pattern in patterns:continue
            density_list_noduplicate.append((pattern,density,seeds))
            patterns.add(pattern)
        print('read',filename_densityList,' done, reduce len ',len(density_list),'->',len(density_list_noduplicate))
        density_list = density_list_noduplicate

    if start_input=='0' or not density_list:
        print(get_currentime(),'start...')
        s = time.time()

        loginfo = '%s read hitlist %s done, target num %s, time cost %ss'%(get_currentime(),filename_hitlist_read,len(hitlist_exploded),time.time()-s)
        print(loginfo)
        loginfo = '[%s]    space partition start...'%get_time_now()

        s = time.time()
        seed_regions = space_partition(exploded_hitlist=hitlist_exploded,th=th,func=indicator_func)
        
        loginfo = '[%s] space partition done, seed regions num %s, time cost %ss'%(get_time_now(),len(seed_regions),time.time()-s)
        print(loginfo)
        loginfo = '[%s] process output seed regions start'

        filename_seedRegions_out = os.path.join(dir_base,f'seed_regions.th{th}.txt')

        seed_regions = output_seed_regions(seed_regions,filename_seedRegions_out,return_density_list=True)
        #multiprocessing.Process(target=output_seed_regions,args=(seed_regions16,filename_seedRegions_out16)).start()

        filename_pattern_jsonout = os.path.join(dir_base,f'seed_regions*.th{th}.json')
        
        num_seedRegion_per_process = int(len(seed_regions)/NUM_PROCESS) + 1
        pool = multiprocessing.Pool(NUM_PROCESS)
        results = []
    
        for i in range(0,NUM_PROCESS):
            start = i*num_seedRegion_per_process
            end = (i+1)*num_seedRegion_per_process
            group_seed_regions = seed_regions[start:end]
            group_id = i
            r = pool.apply_async(process_find_subpattern6,(group_seed_regions, group_id, filename_pattern_jsonout,subpattern_freed))
            results.append(r)
        pool.close()
        pool.join()
        jsonlist = []
        for r in results:
            outjsons = r.get()
            jsonlist.append(outjsons)

        loginfo = '[%s] get_density list start'%get_time_now()
        print(loginfo)
        density_list = format_subpatternJsonList(jsonlist,seed_regions,num_freed=num_freed)

        loginfo = '[%s] get_density list done'%get_time_now()
        print(loginfo)


        filename_densityList = os.path.join(dir_base,'density_list.sorted.txt')
        write_densityList2file(density_list,filename_densityList)

    if '2' in strategy:
        dir_targets = dir_base+'norefinement/'
        if not os.path.exists(dir_targets):
            os.makedirs(dir_targets)
        multiprocessing.Process(target=process_generate_targets_simple2v2,args=(dir_targets,density_list,budget,input_seeds)).start()

    if '3' in strategy:
        filename_refinePattern = 'pattern.refine.txt'
        dir_refine = dir_base+'refinement/'
        if not os.path.exists(dir_refine):
            os.makedirs(dir_refine)
        multiprocessing.Process(target=process_generate_refine_targets_simple2,args=(dir_refine,density_list,dir_base+filename_refinePattern,budget,input_seeds,start_input)).run()


if __name__ == '__main__':
    
    budget = 1*K
    base_dir  = './data/'
    seed_file = base_dir+'seed.txt'


    process_number = 10
    freed = 6
    threshold = 256
    func = mvc
    sfd = 3
    

    main2(base_dir,seed_file,budget=budget,th=threshold,num_freed=freed,strategy='23',start_input='0',indicator_func=func,NUM_PROCESS=process_number,subpattern_freed=sfd)

