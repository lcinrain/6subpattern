
import time
import redis
from myio import read_big_file
#r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)



def insert2redis(r,addrs:list,type='',verbose=False):
    '''
    Parameters:
        - r: redis connection, e.g.,r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
        - addrs: IPv6 addrs to insert or update
        - type: 'responsive' or 'unresponsive'. if responsive, the keys of addrs in redis are '1', e.g., {'2001:db8::':'1'}; if unresponsive key='0', e.g., {'2001:db8::1':'0'}
    '''
    if not addrs:return 0
    if type == 'unresponsive':
        key = 0
    elif type == 'responsive':
        key = 1
    else:
        raise ValueError('Parameter type is required')
    addrs = list(set(addrs))
    addrs_len = len(addrs)
    if verbose:
        print(f'{type} num: {addrs_len}')
    num = addrs_len/400000
    for j in range(0,int(num)+1):
        stime = time.time()
        start = j*400000
        end = (j+1)*400000
        addr_slice = addrs[start:end]
        values = [key]*len(addr_slice)
        targets_dict = dict(zip(addr_slice,values))
        rv = r.mset(targets_dict) # rv = Bool
        #print(rv)
    etime = time.time()
    if verbose:
        print(f'insert {addrs_len} {type} addrs to redis.  time cost: ',etime-stime, 's')


def del_targets(r,targets:list=[]):
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

def get_response_targets(r,targets,output=False,verbose=False,file_name=''):
    '''
    query responsive and unprobed targets in redis.

    Patamters:
        - r: redis connection
        - targets: list of compressed ipv6 or a file name with one compressed ipv6 a line.
        - output: bool. if true, output 2 files. the one is responsive targets at the dir of input input file(param. targets) default. another is unprobed targets.
        - out_filename: if output is true. output the responsive targets and probed targets to the file
        - verbose: bool. if print info to stdout
    
    Returns:
        - responsive targets: list
        - unprobed targets: list
    '''
    targets = list(set(targets)) # remove duplicates
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

def scan_keys(r):
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
    r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    for sample in ['down','prefix','biased']:
        for seed_num in ['10k','100k','100k']:
            file_response = f'6scan.{sample}.{seed_num}seed.response.txt'
            file_name = './data/'+file_response
            try:
                f = open(file_name)
            except FileNotFoundError:
                continue
            responsive_targets = [x.strip('\n') for x in f.readlines()]
            print(file_name,len(responsive_targets))
            if not responsive_targets:continue
            insert2redis(r,responsive_targets,'responsive')
            f.close()
    # insert2redis(r,[],'unresponsive')