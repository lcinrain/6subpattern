from myio import read_exploded_hitlist,write_densityList2file,write_list2file,read_densityList,read_big_file
from mytime import get_time_now,get_currentime
from space_partition import space_partition,mvc,output_seed_regions,leftmost
import time
import multiprocessing
from pattern import get_pattern_simple,process_find_subpattern6,pattern2ipv6s_simple,pattern2ipv6s_conservative,pattern2ipv6s_count
from pattern_refine import patterns_refine_conservative,read_refine_conservative_pattern
from target_generation2 import generate_targets,generate_targets_conservative
from tool_filter import filter_all,get_dealiased_targets,get_route_targets
import os
import math
from tool_redis import get_response_targets
from tool_io import budget2str
import pyasn
from myipv6 import hexstr2ipv6

K = 10**3
M = 10**6

def output_1d2d_patterns(jsonlist:list,seed_regions:list):
    filename_1d = './seed_region/d/d0/6subpattern/pattern_density_seed_list.1d.mvc.th256.6scan-all.txt'
    filename_2d = './seed_region/d/d0/6subpattern/pattern_density_seed_list.2d.mvc.th256.6scan-all.txt'
    patterns_1d = []
    patterns_2d = []
    fw_1d = open(filename_1d,'w')
    fw_2d = open(filename_2d,'w')
    for seed_region in seed_regions:
        pattern = seed_region[0]
        if pattern.count('*')==1:
            seeds = seed_region[1:]
            seed_num = len(seeds)
            density = seed_num/16
            line = [pattern,str(density)] + seeds
            patterns_1d.append(line)
        elif pattern.count('*') == 2:
            seeds = seed_region[1:]
            seed_num = len(seeds)
            density = seed_num/256
            line = [pattern,str(density)] + seeds
            patterns_2d.append(line)
        else:
            continue
    for subpattern_list in jsonlist:
        for item in subpattern_list:
            pattern = item['pattern']
            subpatterns = item['subpatterns']
            for sub in subpatterns:
                subpattern = sub['subpattern']
                density = sub['density']
                seeds = sub['seeds']
                seed_num = len(seeds)
                freed = subpattern.count('*')
                if freed == 1:
                    line = [subpattern,str(density)] + seeds
                    patterns_1d.append(line)
                elif freed == 2:
                    line = [subpattern,str(density)] + seeds
                    patterns_2d.append(line)
                else:
                    continue
    fw_1d.writelines(['\t'.join(x)+'\n' for x in patterns_1d])
    fw_2d.writelines(['\t'.join(x)+'\n' for x in patterns_2d])
    fw_1d.close()
    fw_2d.close()
    return patterns_1d,patterns_2d


def get_pattern_density_list16(seed_regions:list):
    density_list = []
    for seed_region in seed_regions:
        pattern = seed_region[0]
        freed = pattern.count('*')
        if freed >3:continue
        seeds = seed_region[1:]
        num_seed = len(seeds)
        density = num_seed/16**freed
        density_list.append((pattern,density,seeds))
    density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
    return density_list

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

def process_generate_targets(freed:int,dir_out,pattern_list,filter_hitlist):
    generate_targets(freed,dir_out,pattern_density_seed_list=pattern_list)
    # fileter
    filter_all(dir_base=dir_out,freed=freed,filename_hitlist=filter_hitlist)


def process_generate_refine_targets(freed,dir_out,pattern_list,filter_hitlist,filename_refinePattern_out):
    pattern_refine = patterns_refine_conservative(pattern_list,'',filename_refinePattern_out)
    generate_targets_conservative(freed,dir_out,pattern_refine,'')
    filter_all(dir_base=dir_out,freed=freed,filename_hitlist=filter_hitlist)


def process_generate_refine_targets_simple(dir_out:str,pattern_density_list:list,filter_hitlist:str,filename_refinePattern_out:str,budget=10**7,rounds=20,extra_budget_percent=0.02,start_input='0'):
    targets = set()
    old_targets = set()
    patterns_generated = set()
    step_budget = int(budget/rounds)
    count_round = 1
    targets_th = step_budget*count_round

    if start_input == '0':
        print('pattern.refine.txt not find, patterns_refine_conservativ')
        pattern_conservative_list = patterns_refine_conservative(pattern_density_list,'',filename_refinePattern_out)
    else:
        pattern_conservative_list = read_refine_conservative_pattern(filename_refinePattern_out)
    for pattern,density,representation,seeds in pattern_conservative_list:
        if pattern in patterns_generated:continue
        patterns_generated.add(pattern)
        targets_generated = pattern2ipv6s_conservative(pattern,representation)
        for target in targets_generated:
            targets.add(target)
        
        if len(targets)>=targets_th:
            targets_output = targets-old_targets
            file_name = 'targets%s.txt'%count_round
            write_list2file(targets_output,dir_out+file_name)
            old_targets = targets.copy()
            count_round+=1
            if count_round>=rounds+2:break
        if count_round >= rounds+1:
            targets_th = budget+extra_budget_percent*budget
        else:
            targets_th = step_budget*count_round
    if count_round<rounds+1:
        targets_output = targets-old_targets
        file_name = 'targets%s.txt'%count_round
        write_list2file(targets_output,dir_out+file_name)
    filtered_addr = filter_all(dir_base=dir_out,filename_hitlist_filter=filter_hitlist,range_start=1,range_end=count_round+1,skip_duplicate=True,num_split_granularity=rounds)
    dir_hitrate  = dir_out+'route/dealiased/noseed/'
    hitrate_10M(dir_hitrate,1,count_round+1,'targets*.route.dealiased.noseed.txt',rounds=rounds,output_targets_unprobed=True,budget=budget,targets_input=filtered_addr)


def process_generate_refine_targets_simple2(output_dir:str,pattern_density_list:list,filename_refinePattern_out:str,budget=10**7,asndb_alias=None,asndb_route=None,input_seeds={},start_input='0'):
    '''
    store targets in  one file
    '''
    targets_all = set()
    patterns_generated = set()
    budget_total = budget
    if start_input != '3':
        print('pattern.refine.txt not find, patterns_refine_conservativ')
        pattern_conservative_list = patterns_refine_conservative(pattern_density_list,'',filename_refinePattern_out)
    else:
        pattern_conservative_list = read_refine_conservative_pattern(filename_refinePattern_out)
    for pattern,density,representation,seeds in pattern_conservative_list:
        if pattern in patterns_generated:continue
        patterns_generated.add(pattern)
        targets_generated = pattern2ipv6s_conservative(pattern,representation)
        targets_generated = set(targets_generated) - set(input_seeds)
        targets_generated = get_route_targets(targets_generated)
        targets_generated = get_dealiased_targets(targets_generated)
        targets_all.update(targets_generated)
        budget_total-=len(targets_generated)
        if budget_total<=0:break
    
    output_filename = output_dir + f'target{budget}'
    write_list2file(targets_all,output_filename)


def process_generate_targets_simple(dir_out:str,pattern_density_list:list,filter_hitlist:str,budget=10**7,rounds=20,extra_budget_percent=0.02):

    targets = set()
    old_targets = set()
    targets_noduplicate_all = []
    patterns_generated = set()
    step_budget = int(budget/rounds)
    count_round = 1
    targets_th = step_budget*count_round
    pattern_density_list_3dplus = []
    for pattern,density,seeds in pattern_density_list:
        if density == 1.0:continue
        pfreed = pattern.count('*')
        if pfreed>3:
            pattern_density_list_3dplus.append((pattern,density,[]))
            continue
        if pattern in patterns_generated:continue
        patterns_generated.add(pattern)
        targets_generated = pattern2ipv6s_simple(pattern)
        for target in targets_generated:
            targets.add(target)
        
        if len(targets)>=targets_th:
            targets_output = targets-old_targets
            targets_noduplicate_all+=list(targets_output)
            file_name = 'targets%s.txt'%count_round
            write_list2file(targets_output,dir_out+file_name)
            old_targets = targets.copy()
            count_round+=1
            if count_round>=rounds+2:break
        if count_round >= rounds+1:
            targets_th = budget+extra_budget_percent*budget
        else:
            targets_th = step_budget*count_round
    
    budget_left = budget*(1+extra_budget_percent) - len(targets)
    num_round = 0
    num_to_generate = 4096 if budget>=10**6 else 256
    print('3d done, budget left',budget_left)
    while(budget_left>0 and pattern_density_list_3dplus):
        for pattern,density,seeds in pattern_density_list_3dplus:
            targets_generated = pattern2ipv6s_count(pattern,num_round*num_to_generate,num_to_generate)
            len_origin = len(targets)
            for target in targets_generated:
                targets.add(target)
            budget_cost = len(targets)-len_origin
            budget_left-=budget_cost
            num_round+=1
            if len(targets)>=targets_th:
                targets_output = targets-old_targets
                targets_noduplicate_all+=list(targets_output)
                file_name = 'targets%s.txt'%count_round
                write_list2file(targets_output,dir_out+file_name)
                old_targets = targets.copy()
                count_round+=1
                if count_round>=rounds+2:break
            if count_round >= rounds+1:
                targets_th = budget+extra_budget_percent*budget
            else:
                targets_th = step_budget*count_round
            if budget_left <= 0:break
    
    if count_round<rounds+1:
        targets_output = targets-old_targets
        targets_noduplicate_all+=list(targets_output)
        file_name = 'targets%s.txt'%count_round
        write_list2file(targets_output,dir_out+file_name)
    targets_filtered = filter_all(dir_base=dir_out,filename_hitlist_filter=filter_hitlist,range_start=1,range_end=count_round+1,skip_duplicate=True,targets_input=targets_noduplicate_all)
    dir_hitrate  = dir_out+'route/dealiased/noseed/'
    hitrate_10M(dir_hitrate,1,count_round+1,'targets*.route.dealiased.noseed.txt',output_targets_unprobed=True,budget=budget,targets_input=targets_filtered)

def process_generate_targets_simple2(output_dir:str,pattern_density_list:list,budget=10**7,asndb_alias=None,asndb_route=None,input_seeds={}):
    '''
    直接输出目标，去掉round参数
    '''
    input_seeds = set(input_seeds)
    total_budget = budget

    patterns_generated = set()
    pattern_density_list_3dplus = []
    all_targets = set()
    pattern_density_list.sort(key=lambda x:x[1]) # sort by density
    # generate with 3d patthern
    while total_budget>0:
        while pattern_density_list:
            pattern,density,seeds = pattern_density_list.pop()
            if density == 1.0:continue
            pfreed = pattern.count('*')
            if pfreed>3:
                pattern_density_list_3dplus.append((pattern,density,seeds))
                continue
            if pattern in patterns_generated:continue
            patterns_generated.add(pattern)
            targets_generated = pattern2ipv6s_simple(pattern)
            targets_generated = set(targets_generated) - input_seeds
            targets_generated = get_route_targets(targets_generated,asndb_route)
            targets_generated = get_dealiased_targets(targets_generated,asndb_alias)
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
            targets_generated = get_route_targets(targets_generated,asndb_route)
            targets_generated = get_dealiased_targets(targets_generated,asndb_alias)
            len_origin = len(all_targets)
            all_targets.update(targets_generated)
            num_generated = len(all_targets) - len_origin
            total_budget-=num_generated
            if total_budget<=0:break
    output_filename = output_dir + f'target{budget}'
    write_list2file(all_targets,output_filename)
    return all_targets

def process_generate_targets_simple2v2(output_dir:str,pattern_density_list:list,budget=10**7,asndb_alias=None,asndb_route=None,input_seeds={}):
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
            targets_generated = get_route_targets(targets_generated)
            targets_generated = get_dealiased_targets(targets_generated)
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
            targets_generated = get_route_targets(targets_generated,asndb_route)
            targets_generated = get_dealiased_targets(targets_generated,asndb_alias)
            len_origin = len(all_targets)
            all_targets.update(targets_generated)
            num_generated = len(all_targets) - len_origin
            total_budget-=num_generated
            if total_budget<=0:break
    output_filename = output_dir + f'target{budget}'
    write_list2file(all_targets,output_filename)
    return all_targets

def process_generate_targets_simple(dir_out:str,pattern_density_list:list,filter_hitlist:str,budget=10**7,rounds=20,extra_budget_percent=0.02):

    targets = set()
    old_targets = set()
    targets_noduplicate_all = []
    patterns_generated = set()
    step_budget = int(budget/rounds)
    count_round = 1
    targets_th = step_budget*count_round
    pattern_density_list_3dplus = []
    for pattern,density,seeds in pattern_density_list:
        if density == 1.0:continue
        pfreed = pattern.count('*')
        if pfreed>3:
            pattern_density_list_3dplus.append((pattern,density,[]))
            continue
        if pattern in patterns_generated:continue
        patterns_generated.add(pattern)
        targets_generated = pattern2ipv6s_simple(pattern)
        for target in targets_generated:
            targets.add(target)
        
        if len(targets)>=targets_th:
            targets_output = targets-old_targets
            targets_noduplicate_all+=list(targets_output)
            file_name = 'targets%s.txt'%count_round
            write_list2file(targets_output,dir_out+file_name)
            old_targets = targets.copy()
            count_round+=1
            if count_round>=rounds+2:break
        if count_round >= rounds+1:
            targets_th = budget+extra_budget_percent*budget
        else:
            targets_th = step_budget*count_round
    
    budget_left = budget*(1+extra_budget_percent) - len(targets)
    num_round = 0
    num_to_generate = 4096 if budget>=10**6 else 256
    print('3d done, budget left',budget_left)
    while(budget_left>0 and pattern_density_list_3dplus):
        for pattern,density,seeds in pattern_density_list_3dplus:
            targets_generated = pattern2ipv6s_count(pattern,num_round*num_to_generate,num_to_generate)
            len_origin = len(targets)
            for target in targets_generated:
                targets.add(target)
            budget_cost = len(targets)-len_origin
            budget_left-=budget_cost
            num_round+=1
            if len(targets)>=targets_th:
                targets_output = targets-old_targets
                targets_noduplicate_all+=list(targets_output)
                file_name = 'targets%s.txt'%count_round
                write_list2file(targets_output,dir_out+file_name)
                old_targets = targets.copy()
                count_round+=1
                if count_round>=rounds+2:break
            if count_round >= rounds+1:
                targets_th = budget+extra_budget_percent*budget
            else:
                targets_th = step_budget*count_round
            if budget_left <= 0:break
    
    if count_round<rounds+1:
        targets_output = targets-old_targets
        targets_noduplicate_all+=list(targets_output)
        file_name = 'targets%s.txt'%count_round
        write_list2file(targets_output,dir_out+file_name)
    targets_filtered = filter_all(dir_base=dir_out,filename_hitlist_filter=filter_hitlist,range_start=1,range_end=count_round+1,skip_duplicate=True,targets_input=targets_noduplicate_all)
    dir_hitrate  = dir_out+'route/dealiased/noseed/'
    hitrate_10M(dir_hitrate,1,count_round+1,'targets*.route.dealiased.noseed.txt',output_targets_unprobed=True,budget=budget,targets_input=targets_filtered)



def process_generate_targets_dynamic(dir_out:str,pattern_density_list:list,filter_hitlist:str,budget=10**7,rounds=20,extra_budget_percent=0.02):
    budget_left = budget+budget*extra_budget_percent
    pattern_score_origin_list = []
    for pattern,density,seeds in pattern_density_list:
        pattern_score_origin_list.append(((pattern,0),density,seeds))
    pattern_score_list = pattern_score_origin_list.copy()
    targets_all = []
    while(budget_left>0):
        ts = time.time()
        new_pattern_score_list = []
        for i in range(len(pattern_score_list)):
            (pattern,multiple),score,seeds = pattern_score_list[i]
            if i == len(pattern_score_list) - 1:
                score_next = 0.01
            else:
                (pattern_next,multiple_next), score_next, seeds_next = pattern_score_list[i+1]
            score_now = score
            flag = True
            while(score_now>=score_next):
                targets_generated = pattern2ipv6s_count(pattern,256*multiple,256)
                if not targets_generated: 
                    flag = False
                    break
                # targets_noduplicate = set(targets_generated) - set(targets_all)
                # targets_all+=list(targets_noduplicate)
                # budget_left-=len(targets_noduplicate)
                targets_all+=targets_generated
                budget_left-=len(targets_generated)
                if budget_left<=0:break
                targets_response, targets_unprobed = get_response_targets(targets_generated,verbose=False)
                score_now = len(targets_response)/len(targets_generated)
                multiple+=1
                item = ((pattern,multiple),score_now,[])
            if budget_left<=0:break
            if flag:
                new_pattern_score_list.append(item)
        if not new_pattern_score_list:
            break
        new_pattern_score_list = sorted(new_pattern_score_list,key=lambda x:x[1],reverse=True)
        if new_pattern_score_list[0][1]<=0.0000000001:
            print('re order')
            dict_pattern_multiple = dict()
            for pattern_multiple,score,seeds in new_pattern_score_list:
                pattern,multiple = pattern_multiple
                dict_pattern_multiple[pattern] = multiple
            list_pattern_tmp = []
            for pattern_multiple,score,seeds in pattern_score_origin_list:
                list_pattern_tmp.append(((pattern,dict_pattern_multiple[pattern]),score,seeds))
            new_pattern_score_list = list_pattern_tmp
        pattern_score_list = new_pattern_score_list
        print('budget left',budget_left,'time cost',time.time()-ts)

    step_budget = math.ceil(budget/rounds)
    num_file = math.ceil(len(targets_all)/step_budget)
    for i in range(0,num_file):
        start = i*step_budget
        end = (i+1)*step_budget
        targets_seg = targets_all[start:end]
        file_name = 'targets%s.txt'%i
        write_list2file(targets_seg,dir_out+file_name)

    filter_all(dir_base=dir_out,filename_hitlist_filter=filter_hitlist,range_start=1,range_end=num_file,skip_duplicate=True)
    dir_hitrate  = dir_out+'route/dealiased/noseed/'
    hitrate_10M(dir_hitrate,1,num_file,'targets*.route.dealiased.noseed.txt',output_targets_unprobed=True,budget=budget)


def main(dir_base,filename_hitlist_read,filename_hitlist_filter,budget,th,extra_budget_percent=0.02,num_freed=32,process='23',start_input='0',rounds=20,dir_varible=''):
    cmd = 'mkdir "%s"'%dir_base
    os.system(cmd)
    density_list = []
    if start_input == '2':
            print('start from read density_list*****************')
            filename_densityList = dir_base + 'density_list.sorted.txt'
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
        print('start from 0 00000000000000000000000000000')
        s = time.time()

        hitlist_exploded = read_exploded_hitlist(filename_hitlist_read)

        loginfo = '[%s] read hitlist %s done, target num %s, time cost %ss'%(get_time_now(),filename_hitlist_read,len(hitlist_exploded),time.time()-s)
        print(loginfo)
        loginfo = '[%s] space partition start...'%get_time_now()

        s = time.time()
        seed_regions = space_partition(exploded_hitlist=hitlist_exploded,th=th,func=mvc)
        
        loginfo = '[%s] space partition done, seed regions num %s, time cost %ss'%(get_time_now(),len(seed_regions),time.time()-s)
        print(loginfo)
        loginfo = '[%s] process output seed regions start'

        filename_seedRegions_out = dir_base+'seed_regions.th%s.txt'%th

        seed_regions = output_seed_regions(seed_regions,filename_seedRegions_out,return_density_list=True)
        #multiprocessing.Process(target=output_seed_regions,args=(seed_regions16,filename_seedRegions_out16)).start()

        filename_pattern_jsonout = dir_base+'seed_regions*.th%s.json'%th
        #seed_regions = [[get_pattern_simple(seed_region)]+seed_region for seed_region in seed_regions256 if len(seed_region)>1]
        #seed_regions = [[get_pattern_simple(seed_region)]+seed_region for seed_region in seed_regions16 if len(seed_region)>1]
        #print('seed regions num',len(seed_regions))
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
            r = pool.apply_async(process_find_subpattern6,(group_seed_regions, group_id, filename_pattern_jsonout,3))
            results.append(r)
        pool.close()
        pool.join()
        jsonlist = []
        for r in results:
            outjsons = r.get() # r.get()返回值是一个列表，取第一个
            jsonlist.append(outjsons)

        loginfo = '[%s] get_density list start'%get_time_now()
        print(loginfo)
        density_list = format_subpatternJsonList(jsonlist,seed_regions,num_freed=num_freed)

        loginfo = '[%s] get_density list done'%get_time_now()
        print(loginfo)


        filename_densityList = dir_base + 'density_list.sorted.txt'
        write_densityList2file(density_list,filename_densityList)


    if '1' in process:
        dir_dynamic = dir_base+'dynamic/'
        cmd = 'mkdir "%s"'%dir_dynamic
        os.system(cmd)
        multiprocessing.Process(target=process_generate_targets_dynamic,args=(dir_dynamic,density_list,filename_hitlist_filter,budget,20,extra_budget_percent)).start()

    if '2' in process:
        dir_targets = dir_base+'norefinement/'
        cmd = 'mkdir "%s"'%dir_targets
        os.system(cmd)
        multiprocessing.Process(target=process_generate_targets_simple,args=(dir_targets,density_list,filename_hitlist_filter,budget,rounds,extra_budget_percent)).run()

    if '3' in process:
        filename_refinePattern = 'pattern.refine.txt'
        dir_refine = dir_base+'refinement%s/'%dir_varible
        cmd = 'mkdir "%s"'%dir_refine
        os.system(cmd)
        multiprocessing.Process(target=process_generate_refine_targets_simple,args=(dir_refine,density_list,filename_hitlist_filter,dir_base+filename_refinePattern,budget,rounds,extra_budget_percent,start_input)).run()

    # patterns_1d,patterns_2d = output_1d2d_patterns(jsonlist,seed_regions)

    # # generate targets for pattern 1d, 2d
    # dir_out1d = './seed_region/d/d0/6subpattern/norefinement/1d/'
    # dir_out2d = './seed_region/d/d0/6subpattern/norefinement/2d/'
    # filter_hitlist = './hitlist/Global_ICMPv6_20220424.response.txt'
    # # generate_targets(1,dir_out1d,pattern_density_seed_list=patterns_1d)
    # # # fileter
    # # filter_all(dir_base=dir_out1d,freed=1,filename_hitlist=filter_hitlist)
    # # generate_targets(2,dir_out2d,pattern_density_seed_list=patterns_2d)
    # # filter_all(dir_base=dir_out2d,freed=2,filename_hitlist=filter_hitlist)
    # multiprocessing.Process(target=process_generate_targets,args=(1,dir_out1d,patterns_1d,filter_hitlist)).start()
    # multiprocessing.Process(target=process_generate_targets,args=(2,dir_out2d,patterns_2d,filter_hitlist)).start()

    # # pattern refine for 1d 2d
    # dir_out_refine1d = './seed_region/d/d0/6subpattern/refinement/1d/'
    # dir_out_refine2d = './seed_region/d/d0/6subpattern/refinement/2d/'
    # cmd = 'mkdir "%s"'%dir_out_refine1d
    # os.system(cmd)
    # cmd = 'mkdir "%s"'%dir_out_refine2d
    # os.system(cmd)
    # filename_refinePattern1d = 'pattern.refine.1d.txt'
    # filename_refinePattern2d = 'pattern.refine.2d.txt'
    # # pattern_refine1d = patterns_refine_conservative(patterns_1d,'',dir_out_refine1d+filename_refinePattern1d)
    # # pattern_refine2d = patterns_refine_conservative(patterns_2d,'',dir_out_refine2d+filename_refinePattern2d)
    # # # generate targets for refining 1d 2d
    # # generate_targets_conservative(1,dir_out_refine1d,pattern_refine1d,'')
    # # filter_all(dir_base=dir_out_refine1d,freed=1,filename_hitlist=filename_hitlist)
    # # generate_targets_conservative(2,dir_out_refine2d,pattern_refine2d,'')
    # # filter_all(dir_base=dir_out_refine2d,freed=2,filename_hitlist=filename_hitlist)
    # # # filter
    # multiprocessing.Process(target=process_generate_refine_targets,args=(1,dir_out_refine1d,patterns_1d,filter_hitlist,dir_out_refine1d+filename_refinePattern1d)).start()
    # multiprocessing.Process(target=process_generate_refine_targets,args=(2,dir_out_refine2d,patterns_2d,filter_hitlist,dir_out_refine2d+filename_refinePattern2d)).start()


def main2(dir_base,filename_hitlist_read,filename_hitlist_filter='',budget=10**7,th=16,extra_budget_percent=0.02,num_freed=32,strategy='23',start_input='0',rounds=20,dir_varible='',NUM_PROCESS = 10,indicator_func=leftmost):
    '''
    20240109

    Parameters:
        - start_input:
            - 0: start from read hitlist
            - 1: start from read seed regions
            - 2: start from read density list
        - strategy: str. eg,'1' or '2', or '12', '123',.... If multiple trategies are used, the results will be output to different forders.
            - '1': use dynamic generation
            - '2': use static generation
            - '3': use static generation + refined patterns
    '''
    asndb_alias = pyasn.pyasn('./hitlist/20221231-aliased-prefixes.pyasn')
    asndb_route = pyasn.pyasn('./routeview/all-prefixes.txt')
    hitlist_exploded = read_exploded_hitlist(filename_hitlist_read) # read seeds. read only
    input_seeds = read_big_file(filename_hitlist_read.replace('exploded','compressed'),throw_exception=True)

    density_list = []
    if start_input == '2':
        print(get_currentime(),'start from read density_list*****************')
        filename_densityList = dir_base + 'density_list.sorted.txt'
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

        filename_seedRegions_out = dir_base+'seed_regions.th%s.txt'%th

        seed_regions = output_seed_regions(seed_regions,filename_seedRegions_out,return_density_list=True)
        #multiprocessing.Process(target=output_seed_regions,args=(seed_regions16,filename_seedRegions_out16)).start()

        filename_pattern_jsonout = dir_base+'seed_regions*.th%s.json'%th
        
        num_seedRegion_per_process = int(len(seed_regions)/NUM_PROCESS) + 1
        pool = multiprocessing.Pool(NUM_PROCESS)
        results = []
        # 异步方法，不会阻塞，程序会向下执行
        for i in range(0,NUM_PROCESS):
            start = i*num_seedRegion_per_process
            end = (i+1)*num_seedRegion_per_process
            group_seed_regions = seed_regions[start:end]
            group_id = i
            r = pool.apply_async(process_find_subpattern6,(group_seed_regions, group_id, filename_pattern_jsonout,3))
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


        filename_densityList = dir_base + 'density_list.sorted.txt'
        write_densityList2file(density_list,filename_densityList)


    if '1' in strategy:
        dir_dynamic = dir_base+'dynamic/'
        if not os.path.exists(dir_dynamic):
            os.makedirs(dir_dynamic)
        multiprocessing.Process
        multiprocessing.Process(target=process_generate_targets_dynamic,args=(dir_dynamic,density_list,filename_hitlist_filter,budget,20,extra_budget_percent)).start()

    if '2' in strategy:
        dir_targets = dir_base+'norefinement/'
        if not os.path.exists(dir_targets):
            os.makedirs(dir_targets)
        multiprocessing.Process(target=process_generate_targets_simple2v2,args=(dir_targets,density_list,budget,asndb_alias,asndb_route,input_seeds)).run()

    if '3' in strategy:
        filename_refinePattern = 'pattern.refine.txt'
        dir_refine = dir_base+'refinement/'
        if not os.path.exists(dir_refine):
            os.makedirs(dir_refine)
        multiprocessing.Process(target=process_generate_refine_targets_simple2,args=(dir_refine,density_list,dir_base+filename_refinePattern,budget,asndb_alias,asndb_route,input_seeds,start_input)).run()


if __name__ == '__main__':

    freed = 5
    th16 = 16
    th256 = 256
    th = 16
    multiplier = 10
    func = mvc
    indicator = func.__name__
    for sample in ['down','biased','prefix']:
        for seed_num in [10*K,100*K,1000*K]:
            budget = seed_num * multiplier
            filename_exploded_seeds = f'./hitlist/hitlist_{sample}sampling.exploded.{seed_num}.txt'
            dir_base256  = f'./data/{sample}/seed-{seed_num}/budget-{budget}/6subpattern-th{th}-{indicator}-freed{freed}/'
            if not os.path.exists(dir_base256):
                os.makedirs(dir_base256)
            stime = time.time()
            main2(dir_base256,filename_exploded_seeds,budget=budget,th=th,num_freed=freed,strategy='3',start_input='1',indicator_func=func)
            etime = time.time()
            print('*'*20,etime-stime)


    #dir_base = './data/c/6subpattern-th256-10k/'
    '''
    dir_base = './data/down/seed-10000/budget-100000/6subpattern-th256-mvc-freed3/'
    file1 = './hitlist/hitlist_downsampling.exploded.10000.txt'
    file2 = './hitlist/hitlist_downsampling.compressed.10000.txt'
    main(dir_base=dir_base,filename_hitlist_read=file1,filename_hitlist_filter=file2,budget=100*K,th=256,process='2',start_input='2')
'''
    # filename_hitlist_read = './hitlist/hitlist_downsampling.exploded.100000.txt'
    # filename_hitlist_filter =  './hitlist/hitlist_downsampling.compressed.100000.txt'
    
    # if process == 'single':
    #     for sample in ['prefix']:
    #         budget = 20*M
    #         seed_num = 1*M
    #         rounds = 40
    #         filename_hitlist_read = './hitlist/seeds/hitlist_%ssampling.exploded.%s.txt'%(sample,seed_num)
    #         filename_hitlist_filter =  './hitlist/hitlist_%ssampling.compressed.%s.txt'%(sample,seed_num)
    #         dir_base256 = 'C:/exp/ipv6_target_generation/seed_region/%s/seednum_varies/'%(sample)
    #         #dir_base256 = 'C:/exp/ipv6_target_generation/seed_region/%s/1000000/256/'%(sample)
    #         os.system('mkdir "%s"'%dir_base256)
    #         #filtered_addr = filter_all(dir_base=dir_base256+'refinement/',filename_hitlist_filter=filename_hitlist_filter,range_start=0,range_end=21,num_split_granularity=20)
    #         #hitrate_10M(targets_dir=dir_base256+'refinement/route/dealiased/noseed/',range_start=1,range_end=22,budget=budget,rounds=40)
    #         multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,budget,th256,0.2,3,'3','2',rounds)).run()
    
    # if '1' in process:
    #     for i in range(5*10**4,10**6,5*10**4):
    #         sample = 'prefix'
    #         seed_num = i
    #         budget = seed_num*10
    #         filename_hitlist_read = './hitlist/seeds/hitlist_%ssampling.exploded.%s.txt'%(sample,seed_num)
    #         filename_hitlist_filter =  './hitlist/seeds/hitlist_%ssampling.compressed.%s.txt'%(sample,seed_num)
    #         dir_base256 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/256/'%(sample,seed_num)
    #         dir_base16 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/16/'%(sample,seed_num)
    #         os.system('mkdir "%s"'%dir_base16)
    #         os.system('mkdir "%s"'%dir_base256)
    #         multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,budget,th256,0.2,3,'23','0',20)).run()
    #         multiprocessing.Process(target=main,args=(dir_base16,filename_hitlist_read,filename_hitlist_filter,budget,th16,0.2,3,'23','0',20)).run()



    # if process == 'filter':
    #     for i in range(5*10**4,10**6+1,5*10**4):
    #         sample = 'prefix'
    #         seed_num = i
    #         budget = seed_num*10

    #         hitlist_filter =  set(read_big_file('./hitlist/responsive-addresses20221029.txt'))
    #         dir_base256 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/256/'%(sample,seed_num)
    #         dir256_noseed_refinement = dir_base256+'refinement/route/dealiased/'
    #         dir256_noseed_norefinement = dir_base256+'norefinement/route/dealiased/'
    #         filter_hitlist(dir_base=dir256_noseed_norefinement,dir_out=dir256_noseed_norefinement+'noc0/',hitlist_filter=hitlist_filter)
    #         filter_hitlist(dir_base=dir256_noseed_refinement,dir_out=dir256_noseed_refinement+'noc0/',hitlist_filter=hitlist_filter)
            
    #         dir_base16 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/16/'%(sample,seed_num)
    #         dir16_noseed_refinement = dir_base16+'refinement/route/dealiased/'
    #         dir16_noseed_norefinement = dir_base16+'norefinement/route/dealiased/'
    #         filter_hitlist(dir_base=dir16_noseed_norefinement,dir_out=dir16_noseed_norefinement+'noc0/',hitlist_filter=hitlist_filter)
    #         filter_hitlist(dir_base=dir16_noseed_refinement,dir_out=dir16_noseed_refinement+'noc0/',hitlist_filter=hitlist_filter)
            

    # if process == 'hitrate':
    #     hitrate16 = []
    #     hitrate16_re =[]
    #     hitrate256 = []
    #     hitrate256_re = []
    #     for i in range(5*10**4,10**6+1,5*10**4):
    #         sample = 'prefix'
    #         seed_num = i
    #         budget = seed_num*10

    #         hitlist_filter =  set(read_big_file('./hitlist/responsive-addresses20221029.txt'))
    #         dir_base256 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/256/'%(sample,seed_num)
    #         dir256_noseed_refinement = dir_base256+'refinement/route/dealiased/noc0/'
    #         hitrate = hitrate_10M(targets_dir=dir256_noseed_refinement,range_start=0,range_end=22,budget=budget,rounds=20,targets_input=[])
    #         hitrate256_re.append(hitrate)
    #         dir256_noseed_norefinement = dir_base256+'norefinement/route/dealiased/noc0/'
    #         hitrate = hitrate_10M(targets_dir=dir256_noseed_norefinement,range_start=0,range_end=22,budget=budget,rounds=20,targets_input=[])
    #         hitrate256.append(hitrate)
    #         dir_base16 = 'C:/exp/ipv6_target_generation/seed_region/%s/%s/16/'%(sample,seed_num)
    #         dir16_noseed_refinement = dir_base16+'refinement/route/dealiased/noc0/'
    #         dir16_noseed_norefinement = dir_base16+'norefinement/route/dealiased/noc0/'
    #         hitrate = hitrate_10M(targets_dir=dir16_noseed_refinement,range_start=0,range_end=22,budget=budget,rounds=20,targets_input=[])
    #         hitrate16_re.append(hitrate)
    #         hitrate = hitrate_10M(targets_dir=dir16_noseed_norefinement,range_start=0,range_end=22,budget=budget,rounds=20,targets_input=[])
    #         hitrate16.append(hitrate)
    #     fw = open('./evaluation/hitrate.noc0.prefix.txt','w')
    #     fw.write('th16\n')
    #     for v in hitrate16:
    #         fw.write(str(v)+'\n')
    #     fw.write('\nth16-re\n')
    #     for v in hitrate16_re:
    #         fw.write(str(v)+'\n')
    #     fw.write('\nth256\n')
    #     for v in hitrate256:
    #         fw.write(str(v)+'\n')
    #     fw.write('\nth16-re\n')
    #     for v in hitrate256_re:
    #         fw.write(str(v)+'\n')
    #     fw.close()
        # dataset = 'c'
        # if dataset == 'c0':
        #     budget = 10*M
        #     hitrate_filename = 'log.hitrate.50.100k.txt'
        #     dir_base256  = './seed_region/c/c0/6subpattern-th16/'
        #     dir_base256_normal = dir_base256+'norefinement/route/dealiased/noseed/'
        #     hitrate_10M(targets_dir=dir_base256_normal,range_start=0,range_end=120,budget=budget,rounds=1,targets_input=[],hitrate_filename=hitrate_filename)
        #     dir_base256_re = dir_base256+'refinement/route/dealiased/noseed/'
        #     hitrate_10M(targets_dir=dir_base256_re,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)

        #     dir_base16  = './seed_region/c/c0/6subpattern-th256/'
        #     dir_base16_normal = dir_base16+'norefinement/route/dealiased/noseed/'
        #     hitrate_10M(targets_dir=dir_base16_normal,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)
        #     dir_base16_re = dir_base16+'refinement/route/dealiased/noseed/'
        #     hitrate_10M(targets_dir=dir_base16_re,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)
        #     exit(0)
        # for i in range(1,2):
        #     dataset = 'c%s'%i
        #     if dataset in ['c1','c4','c7']:
        #         seed_num = 10*K
        #     elif dataset in ['c2','c5','c8']:
        #         seed_num = 100*K
        #     elif dataset in ['c3','c6','c9']:
        #         seed_num = 1*M
        #     else:
        #         print('*')
        #     budget = seed_num*10
        #     hitrate_filename = 'log.hitrate.50.100k.txt'
        #     dir_base256  = './seed_region/c/%s/6subpattern-th%s-%s/'%(dataset,th256,budget2str(seed_num))
        #     dir_base256_normal = dir_base256+'norefinement/route/dealiased/noseed/'
        #     #hitrate_10M(targets_dir=dir_base256_normal,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)
        #     dir_base256_re = dir_base256+'refinement/route/dealiased/noseed/'
        #     hitrate_10M(targets_dir=dir_base256_re,range_start=0,range_end=120,budget=budget,rounds=20,targets_input=[])
        #     #hitrate_10M(targets_dir=dir_base256_re,range_start=0,range_end=120,budget=budget,rounds=20,targets_input=[],hitrate_filename=hitrate_filename)

        #     dir_base16  = './seed_region/c/%s/6subpattern-th%s-%s/'%(dataset,th16,budget2str(seed_num))
        #     dir_base16_normal = dir_base16+'norefinement/route/dealiased/noseed/'
        #     #hitrate_10M(targets_dir=dir_base16_normal,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)
        #     dir_base16_re = dir_base16+'refinement/route/dealiased/noseed/'
        #     #hitrate_10M(targets_dir=dir_base16_re,range_start=0,range_end=120,budget=budget,rounds=50,targets_input=[],hitrate_filename=hitrate_filename)


    # if process == 'high_budget':
    #     filename_hitlist_read = './hitlist/hitlist.exploded.txt'
    #     filename_hitlist_filter = './hitlist/responsive-addresses20221029.txt'
    #     dir_base256  = './seed_region/c/c0/6subpattern-th%s-500m/'%th256
        #multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,500*M,th256,0.002,freed,'23','2',500)).start()
        # targets = filter_all(dir_base=dir_base256+'refinement/',filename_hitlist_filter=filename_hitlist_filter,range_start=0,range_end=120,num_targets_per_file=1*M)
        # hitrate_10M(targets_dir=dir_base256+'refinement/route/dealiased/noseed/',range_start=0,range_end=120,budget=100*M,rounds=100,targets_input=targets)
    # filename_hitlist_read = './hitlist/hitlist.exploded.txt'
    # filename_hitlist_filter = './hitlist/responsive-addresses20221029.txt'
    # dir_base256  = './seed_region/c/c0/6subpattern-th%s/'%th256
    #multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,budget,th256,extra_budget_percent,freed,'23','2')).start()
    # th16
    #multiprocessing.Process(target=main,args=(dir_base16,filename_hitlist_read,filename_hitlist_filter,budget,th16,extra_budget_percent,freed,'23','0')).start()


    # dir_base256  = './seed_region/c/c6/6subpattern-th%s-10m/'%th256

    # filename_hitlist_read = './hitlist/hitlist_%ssampling.exploded.%s.txt'%(sample,seed_num)
    # filename_hitlist_filter =  './hitlist/hitlist_%ssampling.compressed.%s.txt'%(sample,seed_num)
    # multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,budget,th256,0.2,32)).start()
    ''''''

    # hitrate
    # budget = 10**7
    # dir_base_c1  = './seed_region/c/c1/6subpattern-th256-10m/'
    # dir_base_c2  = './seed_region/c/c5/6subpattern-th256-10m/'
    # dir_base_c3  = './seed_region/c/c6/6subpattern-th256-10m/'
    
    
    # hitlist_c1 =  './hitlist/hitlist_downsampling.compressed.10000.txt'
    # hitlist_c2 =  './hitlist/hitlist_downsampling.compressed.50000.txt'
    # hitlist_c3 =  './hitlist/hitlist_downsampling.compressed.100000.txt'
    
    #dir_c1  = dir_base256+'refinement/route/dealiased/noseed/'
    # dir_c2  = dir_base_c2+'norefinement/route/dealiased/noseed/'
    # dir_c3  = dir_base_c3+'norefinement/route/dealiased/noseed/'

    #multiprocessing.Process(target=hitrate_10M,args=(dir_c1,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir_c2,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir_c3,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()

    # dir_c1  = dir_base_c1+'refinement/route/dealiased/noseed/'
    # dir_c2  = dir_base_c2+'refinement/route/dealiased/noseed/'
    # dir_c3  = dir_base_c3+'refinement/route/dealiased/noseed/'

    # multiprocessing.Process(target=hitrate_10M,args=(dir_c1,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir_c2,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir_c3,0,22,'targets*.route.dealiased.noseed.txt',True,budget,20)).start()



    # th16 = 16
    # th256 = 256
    # budget = 10**6
    # dir_base16  = './seed_region/c/c5/6subpattern-th%s/'%th16
    # dir_base256  = './seed_region/c/c5/6subpattern-th%s/'%th256
    # filename_hitlist_read = './hitlist/hitlist_biasedsampling.exploded.50000.txt'
    # filename_hitlist_filter =  './hitlist/hitlist_biasedsampling.compressed.50000.txt'
    # multiprocessing.Process(target=main,args=(dir_base16,filename_hitlist_read,filename_hitlist_filter,budget,th16,0.02)).start()
    # multiprocessing.Process(target=main,args=(dir_base256,filename_hitlist_read,filename_hitlist_filter,budget,th256,0.02)).start()


    # dir1 = './seed_region/c/c2/6subpattern-th16/refinement/route/dealiased/noseed/'
    # dir2 = './seed_region/c/c2/6subpattern-th16/norefinement/route/dealiased/noseed/'
    # dir3 = './seed_region/c/c2/6subpattern-th256/norefinement/route/dealiased/noseed/'
    # dir4 = './seed_region/c/c2/6subpattern-th256/refinement/route/dealiased/noseed/'
    # #hitrate_10M(dir1,0,21,'targets*.route.dealiased.noseed.txt',output_targets_unprobed=True,budget=budget)
    # multiprocessing.Process(target=hitrate_10M,args=(dir1,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir2,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir3,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir4,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    
    # dir1 = './seed_region/c/c3/6subpattern-th16/refinement/route/dealiased/noseed/'
    # dir2 = './seed_region/c/c3/6subpattern-th16/norefinement/route/dealiased/noseed/'
    # dir3 = './seed_region/c/c3/6subpattern-th256/norefinement/route/dealiased/noseed/'
    # dir4 = './seed_region/c/c3/6subpattern-th256/refinement/route/dealiased/noseed/'
    # multiprocessing.Process(target=hitrate_10M,args=(dir1,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir2,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir3,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    # multiprocessing.Process(target=hitrate_10M,args=(dir4,0,21,'targets*.route.dealiased.noseed.txt',True,10**6)).start()
    