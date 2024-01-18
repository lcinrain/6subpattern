

from OutlierDetection import OutlierDetect
from SpacePartition import *
from OutlierDetection import *
from IPy import IP
import time
import os
import multiprocessing
from myio import read_densityList,write_list2file,write_densityList2file
from pattern import pattern2ipv6s_simple,pattern2ipv6s_count
from target_generation import generate_prescan_targets
from myscan import scan
import redis
import math
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
                pattern_density_list_3dplus.append((pattern,density,[seeds]))
                continue
            targets_generated = pattern2ipv6s_simple(pattern)
            targets_generated = set(targets_generated) - input_seeds_exploded
            len_origin = len(targets_all)
            targets_all.update(targets_generated)
            total_budget-=(len(targets_all)-len_origin)
            if total_budget<=0:break
        if total_budget>0:
            # prescan
            new_density_list = []
            for pattern,density,seeds in pattern_density_list_3dplus: 
                prescan_targets = generate_prescan_targets(pattern,seeds)
                new_generated_targets = set(prescan_targets) -input_seeds_exploded
                len_origin = len(targets_all)
                targets_all.update(new_generated_targets)
                total_budget-=(len(targets_all)-len_origin)
                if total_budget<=0:break
                res,_ = scan(prescan_targets,redis_connection)
                active_rate = len(res)/len(prescan_targets)
                new_density_list.append(pattern,active_rate,seeds)
        
        if total_budget>0:
            # generate all targets in a pattern by order
            new_density_list.sort(key=lambda x:x[1],reverse=True)

            print('3d done, budget left',total_budget)
            while(total_budget>0 and new_density_list):
                for pattern,density,seeds in new_density_list:
                    num2generate = 2**math.ceil(math.log2(total_budget))
                    # generate all the targets in this pattern. 
                    targets_generated = pattern2ipv6s_count(pattern,0,num2generate)
                    len_origin = len(targets_all)
                    targets_all.update(targets_generated)
                    total_budget-=(len(targets_all-len_origin))
                    if total_budget<=0:break
        write_list2file(targets_all,dir_targets_out+f'target{budget}')
        
   



if __name__ == "__main__":

    K = 10**3
    M = 10**6
    redis_connection = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    filename_densityList = 'pattern_density_list.sorted.txt'
    for sample in ['down','biased','prefix']:
        stime = time.time()
        for seed_num in [10*K,100*K,1*M]:
            budget = 10*seed_num
            dir_base = f'./data/result/{sample}/result{seed_num}/'
            if not os.path.exists(dir_base):
                os.makedirs(dir_base)
            stime = time.time()
            filename_seedin = f'E:/exp/ipv6_target_generation/hitlist/hitlist_{sample}sampling.compressed.{seed_num}.txt'
            input_seeds_exploded = read_big_file(filename_seedin.replace('compressed','exploded'),throw_exception=True)
            multiprocessing.Process(target=main,args=(filename_seedin,dir_base+filename_densityList,dir_base,budget,'0','density',redis_connection,input_seeds_exploded)).run()
            print('**end**886**',time.time()-stime)

