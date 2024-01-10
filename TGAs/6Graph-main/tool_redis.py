import redis
import time
from myio import read_big_file
from myipv6 import hexstr2ipv6

r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)

def load_redis():
    #response_dir = './algorithms/6Graph-main/targets_distance_based/unprobed/response/'
    response_dir ='./unprobed/' #'./seed_region/c/c3/6subpattern/norefinement/noduplicate/route/dealiased/noseed/unprobed/response/'#
    #target_dir = './seed_region/c/c3/6subpattern/norefinement/noduplicate/route/dealiased/noseed/unprobed/'#'./seed_region/c/c1/6tree/noduplicate/route/dealiased/noseed/unprobed/'
    # target_dir = './algorithms/6Graph-main/targets_distance_based/unprobed/'
    target_dir ='./unprobed/' 
    error_index = []
    for i in range(0,1):
        # target_file = 'targets%s.unprobed.txt'%i
        # response_file = 'targets%s.unprobed.response.txt'%i
        target_file = 'none'
        response_file = 'response-unprobed-c09-6forest.txt'
        s = time.time()
        targets = read_big_file(target_dir+target_file)
        if targets:
            # when the number of itmes > a certain values(>50w), using mset will
            # raise redis.exceptions.ConnectionError
            # so 40w/mset
            print(target_file,'targets num',len(targets))
            num = len(targets)/400000
            count = 0
            for j in range(0,int(num)+1):
                start = j*400000
                end = (j+1)*400000
                new_targets = targets[start:end]
                values = [0]*len(targets)
                targets_dict = dict(zip(new_targets,values))
                rv = r.mset(targets_dict)
                print(rv)
                if not rv:
                    print(i)
                    print(rv)
                count+=len(targets_dict)
            e = time.time()
            print(target_file,'num',len(targets),'time cost ',e-s)

        
        s = time.time()
        responses = read_big_file(response_dir+response_file)
        if responses:
            print(response_file,'num',len(responses))
            if not responses: continue
            num = len(responses)/400000
            for j in range(0,int(num)+1):
                start = j*400000
                end = (j+1)*400000
                new_responses = responses[start:end]
                values = [1]*len(new_responses)
                responses_dict = dict(zip(new_responses,values))
                r.mset(responses_dict)
            e = time.time()
            print(response_file,'num',len(responses),'time cost ',e-s)
            s = time.time()

def del_targets(targets:list=[]):
    '''
    delete targets if not responsive and unroutable
    '''
    #target_dir = 'E:\\exp\\ipv6_target_generation\\algorithms\\6Graph-main\\targets_distance_based\\no_duplicate\\noroute\\' 
    target_dir = './seed_region/2d/targets_noseed/no_duplicate/no_1dduplicate/noroute/'
    for i in range(2,256):
        file_name = 'targets%s.noroute.txt'%i
        targets = read_big_file(target_dir+file_name)
        if not targets: continue
        targets_responsive,targets_unprobed = get_response_targets(targets)
        print(file_name)
        targets_noroute = list(set(targets) - set(targets_responsive))
        num = len(targets)/400000
        for j in range(0,int(num)+1):
            start = j*400000
            end = (j+1)*400000
            new_targets = targets_noroute[start:end]
            del_num = r.delete(*new_targets)
        print('del no route targets num',del_num)

def get_response_targets(targets,output=False,out_filename='',verbose=False):
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

def scan_keys(): # 截至20230216 活跃地址数量  16356779
    s = time.time()
    fw = open('./hitlist/alive_keys.redis.txt','w',newline='\n')
    responsive_targets = set()
    total = 0
    status_code, keys = r.scan(0,count=300000)
    
    total+=len(keys)
    while(status_code!=0):
        total+=len(keys)
        print(total,len(responsive_targets),status_code,len(responsive_targets)/total)
        response = r.mget(keys)
        for i,j in zip(response,keys):
            if i== '1':
                responsive_targets.add(j)
        status_code, keys = r.scan(status_code,count=300000)
    fw.writelines([x+'\n' for x in responsive_targets])
    fw.close()
    print('scan done, time cost',time.time()-s)
if __name__ == '__main__':
    load_redis()