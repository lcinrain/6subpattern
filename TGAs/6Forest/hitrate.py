import redis
from myipv6 import hexstr2ipv6
import time
import pyasn
import multiprocessing
import os
from myio import read_big_file,write_list2file
import random
import math
r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)

def get_response_targets(targets,output=False,out_filename='',verbose=True):
    '''
    give the hitrate of targets in redis

    Patamters:
        - targets: list of compressed ipv6 or a file name with one compressed ipv6 a line.
        - output: bool. if true, output 2 files. the one is responsive targets at the dir of input input file(param. targets) default. another is unprobed targets.
        - out_filename: if output is true. output the responsive targets and probed targets to the file
        - verbose: bool. if print info to stdout
    
    Returns:
        - responsive targets: list
        - unprobed targets: list
    '''
    file_name = '.txt'
    if isinstance(targets,str):
        file_name = targets
        fr = open(file_name)
        targets = [x.strip('\n') for x in fr.readlines()]
    targets = list(set(targets)) # remove duplicates
    if not ':' in targets[0]:
        targets = [hexstr2ipv6(x) for x in targets]
    responsive_targets = []
    unresponsive_targets = []
    unprobed_targets = []
    num = len(targets)/400000
    for j in range(0,int(num)+1):
        start = j*400000
        end = (j+1)*400000
        new_targets = targets[start:end]
        responses = r.mget(new_targets)
        for i,j in zip(responses,new_targets):
            if i == '0':
                unresponsive_targets.append(j)
            elif i== '1':
                responsive_targets.append(j)
            else:
                unprobed_targets.append(j)
    if verbose:
        file_not_probe_num = len(unprobed_targets)
        file_unresponse_num = len(unresponsive_targets)
        file_hit_num = len(responsive_targets)
        hitrate = file_hit_num/(file_hit_num+file_unresponse_num)
        print(file_name,'targets num',len(targets),'not probe number',file_not_probe_num,'hit number(minus not probe)',file_hit_num,'unresponse num(minus not probe)',file_unresponse_num,'hitrate(minues not probe',hitrate)
    
    if output:
        responsive_filename = file_name.replace('.txt','.response.txt')
        fw = open(responsive_filename,'w',newline='\n')
        fw.writelines([x+'\n' for x in responsive_targets])
        fw.close()
        unprobed_filename = file_name.replace('.txt','.unprobed.txt')
        fw = open(unprobed_filename,'w',newline='\n')
        fw.writelines([x+'\n' for x in unprobed_targets])
        fw.close()
    return responsive_targets, unprobed_targets

def hitrate_of_refined_targets():
    responsive_targets = []
    targets_dir = './targets/'
    asndb = pyasn.pyasn('E:\\exp\\ipv6_target_generation\\hitlist\\20221231-aliased-prefixes.pyasn')
    for i in range(1,157):
        s = time.time()
        file_name = 'targets%s.refine.txt'%i
        f = open(targets_dir+file_name)
        targets = set([x.strip('\n') for x in f.readlines()])
        difference = targets.difference(set(responsive_targets))
        alias = []
        for ip in difference:
            asn,prefix = asndb.lookup(ip)
            if prefix:
                alias.append(ip)
        difference = difference - set(alias)
        responsive_targets+=list(difference) # order is import in responsive_targets becauset the targets is generated by density des
        if len(responsive_targets) >= 10**7: break # 10M targets
        f.close()
        print(file_name,len(responsive_targets),time.time()-s)
    responsive_targets = responsive_targets[:10**7]
    for i in range(0,10):
        start = i*10**6
        end = (i+1)*10**6
        targets = responsive_targets[start:end]
        targets_responsive, targets_unprobed = get_response_targets(targets,verbose=False)
        hitrate = len(targets_responsive)/(10**6-len(targets_unprobed))
        print(i,'response',len(targets_responsive),'unprobed',len(targets_unprobed),hitrate)
        fw = open('./targets/no_duplicate/targets%s.refine.noduplicate.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets])
        fw.close()
        fw = open('./targets/response/targets%s.refine.response.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_responsive])
        fw.close()
        fw = open('./targets/unprobed/targets%s.refine.unprobed.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_unprobed])
        fw.close()


def hitrate_of_6graph():
    '''
    read all the generated targets(./algorithms/6Graph-main/targets_distance_based/no_duplicate/route/) by 6Graph, and randomly select targets of a certain budget for 10 times to calculate the average hitrates. total 10M budget
    '''
    hitrate_dir = ''
    targets = []
    fw_log = open(hitrate_dir+'log','w')
    fw_log.write('read all the generated targets(./algorithms/6Graph-main/targets_distance_based/no_duplicate/route/) by 6Graph, and randomly select targets of a certain budget for 10 times to calculate the average hitrates. total 10M budget\n\n')
    target_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/route/'
    hitrate_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/route/hitrate/'
    for i in range(0,16):
        file_name = 'targets%s.route.txt'%i
        print(file_name)
        targets+=read_big_file(target_dir+file_name)
    for i in range(1,21): # 10M budget
        #budget = int(i*0.5*10)
        budget = int(i*0.5*10**6)
        fw_log.write('budget %sM\n'%(1*0.5))
        print('budget %sM\n'%(1*0.5))
        total = 0
        responsive_count = 0
        for j in range(0,10):
            fw_log.write('round %s\n'%j)
            print('round %s\n'%j)
            indices = random.sample(range(0,len(targets)),budget)
            selected_targets = [targets[index] for index in indices]
            out_filename = 'targets.b%s.round%s.txt'%(budget,j)
            write_list2file(selected_targets,hitrate_dir+out_filename)
            responsive_targets,unprobed_targets = get_response_targets(selected_targets,verbose=False)
            line = 'responsive_targets %s, unprobed_targets %s\n'%(len(responsive_targets),len(unprobed_targets))
            #print(line)
            fw_log.write(line)
            if len(unprobed_targets)!=0:
                print(out_filename,'unprobed len',len(unprobed_targets))
                unprobed_filename = 'targets.b%s.round%s.unprobed.txt'%(budget,j)
                write_list2file(unprobed_targets,hitrate_dir+unprobed_filename)
            hitrate_roundj = len(responsive_targets)/(budget-len(unprobed_targets))
            fw_log.write('hitrate %s\n'%hitrate_roundj)
            #print('hitrate %s\n'%hitrate_roundj)
            total+=(budget-len(unprobed_targets))
            responsive_count+=len(responsive_targets)
        ave_hitrate = responsive_count/total
        print('ave hitrate %s\n\n'%ave_hitrate)
        fw_log.write('ave hitrate %s\n\n'%ave_hitrate)
        print(budget,ave_hitrate)


def hitrate_of_targets():
    responsive_targets = []
    targets_dir = './seed_region/refinement/targets_noseed/'
    # asndb = pyasn.pyasn('E:\\exp\\ipv6_target_generation\\hitlist\\20221231-aliased-prefixes.pyasn')
    for i in range(1,100):
        s = time.time()
        file_name = 'targets%s.noseed.refine.txt'%i
        f = open(targets_dir+file_name)
        targets = set([x.strip('\n') for x in f.readlines()])
        difference = targets.difference(set(responsive_targets))
        # alias = []
        # for ip in difference:
        #     asn,prefix = asndb.lookup(ip)
        #     if prefix:
        #         alias.append(ip)
        # difference = difference - set(alias)
        responsive_targets+=list(difference) # order is import in responsive_targets becauset the targets is generated by density des
        #if len(responsive_targets) >= 10**7: break # 10M targets
        f.close()
        print(file_name,len(responsive_targets),time.time()-s)
    #responsive_targets = responsive_targets[:10**7]
    num = int(len(responsive_targets)/10**6)+1
    for i in range(0,num):
        start = i*10**6
        end = (i+1)*10**6
        targets = responsive_targets[start:end]
        targets_responsive, targets_unprobed = get_response_targets(targets,verbose=False)
        hitrate = len(targets_responsive)/(10**6-len(targets_unprobed))
        print(i,'response',len(targets_responsive),'unprobed',len(targets_unprobed),hitrate)
        fw = open(targets_dir+'no_duplicate/targets%s.noduplicate.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets])
        fw.close()
        fw = open(targets_dir+'response/targets%s.response.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_responsive])
        fw.close()
        fw = open(targets_dir+'unprobed/targets%s.refine.unprobed.txt'%i,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_unprobed])
        fw.close()


def hitrate_single_file():
    targets_dir = './seed_region/3d/combine/'
    file_name = 'targets256.route.txt'
    targets_tmp = read_big_file(targets_dir+file_name)
    print(len(targets_tmp))
    targets_responsive,targets_unprobed = get_response_targets(targets_tmp,verbose=False)
    
    out_filename = targets_dir+file_name.replace('.txt','.response.txt')
    write_list2file(targets_responsive,out_filename)
    out_filename = targets_dir+file_name.replace('.txt','.unprobed.txt')
    write_list2file(targets_unprobed,out_filename)
    print('ave hitrate',len(targets_responsive)/len(targets_tmp))

def hitrate_noduplicate():
   # targets_dir = './algorithms/6Graph-main/targets_distance_based/'
    targets_dir = './seed_region/1d/targets_noseed/no_duplicate/noroute/'
    fw_log = open(targets_dir+'log.targets.txt','w')
    cmd = 'mkdir "%s"'%targets_dir+'response'
    os.system(cmd)
    cmd = 'mkdir "%s"'%targets_dir+'unprobed'
    os.system(cmd)
    cmd = 'mkdir "%s"'%targets_dir+'no_duplicate'
    os.system(cmd)
    all_targets = []
    total_responsive = 0
    for i in range(2,16):
        s = time.time()
        file_name = 'targets%s.noroute.txt'%i
        try:
            targets_tmp = read_big_file(targets_dir+file_name)
        except FileNotFoundError:
            continue
        if not targets_tmp:continue
        noduplicate_targets = list(set(targets_tmp)-set(all_targets))
        all_targets+=noduplicate_targets
        print(file_name,len(noduplicate_targets),time.time()-s)
        
        targets_responsive,targets_unprobed = get_response_targets(noduplicate_targets,verbose=False)
        hitrate = len(targets_responsive)/(len(noduplicate_targets)-len(targets_unprobed))
        
        total_responsive+=len(targets_responsive)
        print(i,'targets num:',len(noduplicate_targets),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate)
        fw_log.write('\t'.join([str(x) for x in [i,'targets num:',len(noduplicate_targets),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate]])+'\n')
        
        out_filename = targets_dir+'no_duplicate/targets%s.noduplicate.txt'%i
        write_list2file(noduplicate_targets,out_filename)
        out_filename = targets_dir+'response/targets%s.response.txt'%i
        write_list2file(targets_responsive,out_filename)
        out_filename = targets_dir+'unprobed/targets%s.unprobed.txt'%i
        write_list2file(targets_unprobed,out_filename)
        print('ave hitrate',total_responsive/len(all_targets))
    fw_log.write('ave hitrate:%s\n'%(total_responsive/len(all_targets),))
    fw_log.close()


def hitrate_10M(targets_dir:str,range_start:int,range_end:int,filename_read_pattern='targets*.route.dealiased.noseed.txt',output_targets_unprobed=True,budget=10**7,rounds = 20,targets_input:list=[]):
    
    
    budget_step = int(budget/rounds)
    #targets_dir = './seed_region/c/c1/entropyip/'
    if output_targets_unprobed:
        dir_unprobed = targets_dir+'unprobed/'
        cmd = 'mkdir "%s"'%dir_unprobed
        os.system(cmd)
        dir_responsive = targets_dir+'responsive/'
        cmd = 'mkdir "%s"'%dir_responsive
        os.system(cmd)
    #targets_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/route/'
    #targets_dir = './algorithms/6Graph-main/targets_noseed/noduplicate/route/dealiased/noseed/'
    #targets_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/route/'
    #targets_dir = './seed_region/refinement/conservative/1d/no_duplicate/route/dealiased/'
    #targets_dir = './hitrate_test/'
    #targets_dir = './seed_region/refinement/conservative/2d/no_duplicate/route/dealiased/noseed/no1d/'
    #targets_dir = './seed_region/d/d0/6subpattern/2d/norefinement/noduplicate/route/dealiased/noseed/'
    #targets_dir = './seed_region/2d/targets/no_duplicate/route/dealiased/noseed/'
    #targets_dir = './seed_region/c/c0/6tree/noduplicate/route/dealiased/noseed/'
    
    fw_log = open(targets_dir+'log.hitrate.10Mbudget.txt','w')

    total_targets = 0
    total_responsive = 0
    total_unprobed = 0
    list_seednum = []
    list_hitrate = []
    list_log_data = []
    list_response_acc = []
    list_response = []
    header = ['seed num','target num','response num','unprobed num','hitrate','total response num']
    list_log_data.append(header)
    targets = targets_input
    if not targets: # targets = [], input is files, not a list
        for i in range(range_start,range_end):
            file_name = filename_read_pattern.replace('*',str(i))
            targets_read = read_big_file(targets_dir+file_name)
            if not targets_read:continue
            targets+=targets_read
            total_targets+=len(targets)
            print(file_name)
            if len(targets)>=budget:break
        if range_end==0:
            targets_read = read_big_file(targets_dir+filename_read_pattern)
            targets+=targets_read
            total_targets+=len(targets)

    targets = targets[:budget]

    print('read done,target num',len(targets))
    for i in range(0,math.ceil(len(targets)/budget_step)):
        start = i*budget_step
        end = (i+1)*budget_step
        targets_seg = targets[start:end]
        if not targets_seg:continue
        targets_responsive,targets_unprobed = get_response_targets(targets_seg,verbose=False)
        if output_targets_unprobed:
            filename_targets_unprobed = 'targets%s.unprobed.txt'%i
            write_list2file(targets_unprobed,dir_unprobed+filename_targets_unprobed)
            filename_targets_responsive = 'targets%s.responsive.txt'%i
            write_list2file(targets_responsive,dir_responsive+filename_targets_responsive)
        #if len(targets)==len(targets_unprobed):continue
        hitrate = len(targets_responsive)/(len(targets_seg)-len(targets_unprobed)) if (len(targets_seg)-len(targets_unprobed))>0 else 0
        total_responsive+=len(targets_responsive)
        total_unprobed+=len(targets_unprobed)
        data = [i,len(targets),len(targets_responsive),len(targets_unprobed),hitrate,total_responsive]
        list_log_data.append(data)
        list_response.append(len(targets_responsive))
        print(i,'targets num:',len(targets_seg),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate)
        fw_log.write('\t'.join([str(x) for x in [i,'targets num:',len(targets_seg),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate]])+'\n')
        list_seednum.append(i)
        list_hitrate.append(hitrate)
        list_response_acc.append(total_responsive)
        
    loginfo = 'ave hitrate:%s, total resp %s, total targets %s, total unprobed %s\n'%(total_responsive/(len(targets)-total_unprobed),total_responsive,len(targets),total_unprobed)
    print(loginfo)
    fw_log.write(loginfo+'\n')
    fw_log.write('seed num:'+'\n')
    fw_log.writelines([str(x)+'\n' for x in list_seednum])
    fw_log.write('hitrates:'+'\n')
    fw_log.writelines([str(x)+'\n' for x in list_hitrate])
    fw_log.write('acc response:\n')
    fw_log.writelines([str(x)+'\n' for x in list_response_acc])
    fw_log.write('acc response(M):\n')
    fw_log.writelines([str(x/10**6)+'\n' for x in list_response_acc])
    fw_log.write('response:\n')
    fw_log.writelines([str(x)+'\n' for x in list_response])
    fw_log.write('response:(M)\n')
    fw_log.writelines([str(x/10**6)+'\n' for x in list_response])

    for data in list_log_data:
        fw_log.writelines('\t'.join([str(x) for x in data]))
        fw_log.write('\n')
    fw_log.close()


def hitrate_simple(output_targets_unprobed=False):
    if output_targets_unprobed:
        dir_unprobed = targets_dir+'unprobed/'
        cmd = 'mkdir "%s"'%dir_unprobed
        os.system(cmd)
        dir_responsive = targets_dir+'responsive/'
        cmd = 'mkdir "%s"'%dir_responsive
        os.system(cmd)
       # targets_dir = './algorithms/6Graph-main/targets_distance_based/'
    #targets_dir = './algorithms/6Graph-main/targets_noseed/noduplicate/route/dealiased/noseed/'
    #targets_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/route/'
    #targets_dir = './seed_region/refinement/conservative/1d/no_duplicate/route/dealiased/'
    #targets_dir = './hitrate_test/'
    #targets_dir = './seed_region/refinement/conservative/2d/no_duplicate/route/dealiased/noseed/no1d/'
    #targets_dir = './seed_region/d/d0/6subpattern/2d/norefinement/noduplicate/route/dealiased/noseed/'
    #targets_dir = './seed_region/2d/targets/no_duplicate/route/dealiased/noseed/'
    #targets_dir = './seed_region/c/c0/6tree/noduplicate/route/dealiased/noseed/'
    targets_dir = './seed_region/c/c1/6subpattern/refinement/noduplicate/route/dealiased/noseed/'
    fw_log = open(targets_dir+'log.hitrate.txt','w')

    total_targets = 0
    total_responsive = 0
    list_seednum = []
    list_hitrate = []
    list_log_data = []
    list_response_acc = []
    header = ['seed num','target num','response num','unprobed num','hitrate','total response num']
    list_log_data.append(header)
    for i in range(0,7):
        #file_name = 'targets%s.route.dealiased.txt'%i
        file_name = 'targets%s.route.dealiased.noseed.txt'%i
        #file_name = 'targets%s.txt'%i
        #file_name = 'targets%s.noseed.txt'%i
        #file_name = 'targets%s.route.dealiased.txt'%i
        targets = read_big_file(targets_dir+file_name)
        if not targets:continue

        total_targets+=len(targets)
        
        targets_responsive,targets_unprobed = get_response_targets(targets,verbose=False)
        if output_targets_unprobed:
            filename_targets_unprobed = file_name.replace('.txt','.unprobed.txt')
            write_list2file(targets_unprobed,dir_unprobed+filename_targets_unprobed)
            filename_targets_responsive = file_name.replace('.txt','.responsive.txt')
            write_list2file(targets_responsive,dir_responsive+filename_targets_responsive)
        #if len(targets)==len(targets_unprobed):continue
        hitrate = len(targets_responsive)/(len(targets)-len(targets_unprobed))
        
        total_responsive+=len(targets_responsive)
        data = [i,len(targets),len(targets_responsive),len(targets_unprobed),hitrate,total_responsive]
        list_log_data.append(data)
        print(i,'targets num:',len(targets),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate)
        fw_log.write('\t'.join([str(x) for x in [i,'targets num:',len(targets),'response num:',len(targets_responsive),'unprobed num:',len(targets_unprobed),'hitrate',hitrate]])+'\n')
        list_seednum.append(i)
        list_hitrate.append(hitrate)
        list_response_acc.append(total_responsive)
        
    loginfo = 'ave hitrate:%s, total resp %s, total targets %s\n'%(total_responsive/total_targets,total_responsive,total_targets)
    print(loginfo)
    fw_log.write(loginfo+'\n')
    fw_log.write('seed num:'+'\n')
    fw_log.writelines([str(x)+'\n' for x in list_seednum])
    fw_log.write('hitrates:'+'\n')
    fw_log.writelines([str(x)+'\n' for x in list_hitrate])
    fw_log.write('acc response:\n')
    fw_log.writelines([str(x)+'\n' for x in list_response_acc])

    for data in list_log_data:
        fw_log.writelines('\t'.join([str(x) for x in data]))
        fw_log.write('\n')
    fw_log.close()


def process_read_file(targets_dir:str,name_pattern:str,start:int,end:int):
    targets_return = []
    for i in range(start,end):
        file_name = name_pattern.replace('*',str(i))
        print(file_name)
        f = open(targets_dir+file_name)
        targets = set([x.strip('\n') for x in f.readlines()])
        difference = targets.difference(set(targets_return))
        targets_return+=list(difference)
    return start,targets_return
    
def hitrate(targets_dir:str,name_pattern:str,start:int,end:int):
    cmd = 'mkdir "%s"'%targets_dir+'response'
    os.system(cmd)
    cmd = 'mkdir "%s"'%targets_dir+'unprobed'
    os.system(cmd)
    cmd = 'mkdir "%s"'%targets_dir+'no_duplicate'
    os.system(cmd)
    s = time.time()
    responsive_targets = []
    indexes = list(range(start,end,20))
    if not end in indexes:
        indexes.append(end)
    pool_size = len(indexes) - 1
    results = []
    pool = multiprocessing.Pool(pool_size)
    # 异步方法，不会阻塞，程序会向下执行
    for i in range(0,len(indexes)-1):
        r = pool.apply_async(process_read_file,(targets_dir,name_pattern,indexes[i],indexes[i+1])) # pool.map_async只允许传入一个参数
        results.append(r)
    pool.close()
    # 阻塞直至所有进程执行完毕
    pool.join()
    sorted_results = []
    for r in results:
        start,targets = r.get() # r.get()返回值是一个列表，取第一个
        sorted_results.append((start,targets))
    sorted_results = sorted(sorted_results,key=lambda x:x[0])
    for index,targets in sorted_results:
        difference = set(targets) - set(responsive_targets)
        responsive_targets+=list(difference)
    print('read targets done, time cost',time.time()-s)
    num = int(len(responsive_targets)/10**6)+1
    for i in range(0,num):
        start = i*10**6
        end = (i+1)*10**6
        targets = responsive_targets[start:end]
        targets_responsive, targets_unprobed = get_response_targets(targets,verbose=False)
        hitrate = len(targets_responsive)/(10**6-len(targets_unprobed))
        print(i,'response',len(targets_responsive),'unprobed',len(targets_unprobed),hitrate)
        filename_out = 'no_duplicate/'+name_pattern.replace('.txt','.noduplicate.txt').replace('*',str(i))
        fw = open(targets_dir+filename_out,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets])
        fw.close()
        filename_out = 'response/'+name_pattern.replace('.txt','.response.txt').replace('*',str(i))
        fw = open(targets_dir+filename_out,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_responsive])
        fw.close()
        filename_out = 'unprobed/'+name_pattern.replace('.txt','.unprobed.txt').replace('*',str(i))
        fw = open(targets_dir+filename_out,'w',newline='\n')
        fw.writelines([x+'\n' for x in targets_unprobed])
        fw.close()

if __name__ == '__main__':
    # file_name = './seed_region/refinement/targets.prescan.txt'
    # file_name = './targets.prescan.txt'

    # get_response_targets(file_name,output=True)
    # hitrate_of_targets()
    # dir = './seed_region/refinement/conservative/targets/'
    # name_pattern = 'targets*.txt'
    # hitrate(dir,name_pattern,0,242)
    # dir = './seed_region/refinement/conservative/targets_noseed/'
    # name_pattern = 'targets*_noseed.txt'
    # hitrate(dir,name_pattern,0,123)
    # dir = './algorithms/6Graph-main/targets_noseed/'
    # name_pattern = 'targets*_noseed.txt'
    # hitrate(dir,name_pattern,0,114)
    #hitrate_simple()
    dir_targets = './seed_region/c/c1/6subpattern/norefinement/noduplicate/route/dealiased/noseed/'
    #dir_targets = './seed_region/c/c1/6tree/noduplicate/route/dealiased/noseed/'
    r_start = 0
    r_end = 31
    hitrate_10M(dir_targets,range_start=r_start,range_end=r_end,output_targets_unprobed=True)