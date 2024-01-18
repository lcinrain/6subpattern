
'''using 6Graph target generation strategy'''
from OutlierDetection import OutlierDetect
from SpacePartition import *
from OutlierDetection import *
from IPy import IP
import time
import os
import multiprocessing
from myio import read_densityList,write_list2file,write_densityList2file
from pattern import pattern2ipv6s_simple,pattern2ipv6s_count
from target_generation import generate_prescan_targets,pattern2ipv6s_6graph
from myscan import scan
import redis
import math
import random
from myipv6 import hexstr2ipv6
from myio import read_big_file

def main(filename_seed_in:str,filename_densityList_out:str,dir_targets_out:str,budget=10**7,start_input='0',generate_mode='density',redis_connection=None,input_seeds_exploded={}):
    s = time.time()
    pattern_density_list = []
    if start_input == '1':
        pattern_density_list = read_densityList(filename_densityList_out)
        print('read density list done')
    if start_input == '0' or not pattern_density_list:
        data = []
        with open(filename_seed_in) as f:
            
            for ip in f.read().splitlines():
                data.append([int(x, 16)
                            for x in IP(ip).strFullsize().replace(":", "")])
        data = np.array(data, dtype=np.uint8)
        patterns = []
        outliers = []
        ss = time.time()
        results = DHC(data)
        print('get_seed  time',time.time()-ss)

        for r in results:
            p, o = OutlierDetect(r)
            patterns += p
            outliers += o

        # your can seed the number of iter, usually < 5
        # for _ in range(3):
        #     results = DHC(np.vstack(outliers))
        #     outliers = []
        #     for r in results:
        #         p, o = OutlierDetect(r)
        #         patterns += p
        #         outliers += o

        # display or directly use for yourself
        pattern_density_list = []
        for index, p in zip(list(range(len(patterns))), patterns):
            Tarrs = p.T

            address_space = []

            for i in range(32):
                splits = np.bincount(Tarrs[i], minlength=16)
                if len(splits[splits > 0]) == 1:
                    address_space.append(format(
                        np.argwhere(splits > 0)[0][0], "x"))
                else:
                    address_space.append("*")
            
            #print("No.", index, "address pattern")
            addr_pattern = "".join(address_space)
            #print(addr_pattern)
            #print("-"*32)
            seeds = []
            for iparr in p:
                addr = "".join([format(x, "x") for x in iparr])
                seeds.append(addr)
                #print(addr)
            #print()
            density_ = len(seeds)/16**addr_pattern.count('*')
            pattern_density_list.append((addr_pattern,density_,seeds))
        print('time cost',time.time()-s)
        write_densityList2file(pattern_density_list,filename_densityList_out)

    # bigin to generate targets
    total_budget = budget
    input_seeds_exploded = set(input_seeds_exploded)
    if generate_mode == 'density':
        
        print('density driven start')
        targets_all = set()
        pattern_density_list_3dplus = []
        # generate targets using 3 free dimension patterns
        
        for pattern,density,seeds in pattern_density_list:
            if density == 1.0:continue
            freed = pattern.count('*')
            if freed > 3:
                pattern_density_list_3dplus.append((pattern,density,seeds))
                continue
            targets_generated = pattern2ipv6s_simple(pattern)
            targets_generated = set(targets_generated) - input_seeds_exploded
            len_origin = len(targets_all)
            targets_all.update(targets_generated)
            total_budget-=(len(targets_all)-len_origin)
            if total_budget<=0:break
        
        pattern_targets_dict = dict()
        extra_budget = 0 # the number of seeds
        #pattern_density_list_3dplus.sort(key=lambda x:x[1],reverse=True)
        for pattern,_,seeds in pattern_density_list_3dplus:
            extra_budget+=len(seeds)
            pattern_targets_dict[pattern] = set(seeds)
        total_budget+=extra_budget
        round = 1
        len_targets_last_round = 0
        removing_patternDList = []
        while True:
            # using all the patterns to generate targets is one round
            for pattern,density,seeds in pattern_density_list_3dplus:  
                if density == 1.0:continue
                num2generate = len(seeds)*2**(round-2) if round>=2 else len(seeds)
                targets = pattern2ipv6s_6graph(pattern,seeds,num2generate=num2generate,targets_generated=pattern_targets_dict[pattern])
                if not targets:
                    removing_patternDList.append([pattern,density,seeds])
                    continue
                pattern_targets_dict[pattern] = targets
                targets_all.update(targets)
            round+=1
            if len(targets_all) == len_targets_last_round:
                print('patterns are exhausted. generated target num: ',len(targets_all))
                break
            if len(targets_all)>= total_budget:
                print('generated targets reach the budget:',budget,' target num:',len(targets_all)-extra_budget) # targets_all contains seeds
                break
            len_targets_last_round = len(targets_all)
        
        targets_all = targets_all - set(input_seeds_exploded)
        # sampling targets to scan
        if len(targets_all)>budget: 
            targets_all = random.sample(targets_all,budget)
        targets_all = map(hexstr2ipv6,targets_all)
        file_name = f'target{budget}'
        write_list2file(targets_all,dir_targets_out+file_name)
        print(dir_targets_out,' genetate done')
        

if __name__ == "__main__":

    K = 10**3
    M = 10**6
    redis_connection = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    filename_densityList = 'pattern_density_list.sorted.txt'
    for sample in ['down','biased','prefix']:
        stime = time.time()
        for seed_num in [10*K,100*K,1*M]:
            budget = 10*seed_num
            dir_base = f'./data/result-density/{sample}/result{seed_num}/'
            if not os.path.exists(dir_base):
                os.makedirs(dir_base)
            stime = time.time()
            filename_seedin = f'E:/exp/ipv6_target_generation/hitlist/hitlist_{sample}sampling.compressed.{seed_num}.txt'
            input_seeds_exploded = read_big_file(filename_seedin.replace('compressed','exploded'),throw_exception=True)
            multiprocessing.Process(target=main,args=(filename_seedin,dir_base+filename_densityList,dir_base,budget,'0','density',redis_connection,input_seeds_exploded)).run()
            print('**end**886**',time.time()-stime)

