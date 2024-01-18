
import time
#import redis
#r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)

def read_big_file(file_name:str,read_zise=10**9,remove_duplicates=False,throw_exception=False):
    '''
    read lines of file into contents WITHOU /n at line end
    '''
    contents = []
    spliter = b'\r\n'
    try:
        f = open(file_name,'rb')
    except FileNotFoundError:
        if throw_exception:
            raise FileNotFoundError('%s not found'%file_name)
        print(file_name,' not found, continue...')
        return []
    content = f.read(read_zise)
    if not content: return []
    if b'\r\n' in content:
        spliter = b'\r\n'
    elif b'\n' in content:
        spliter = b'\n'
    else:
        print('file content error in myio->read_big_file')
        return(-1)
    while(content):
        lines = content.split(spliter)
        contents+=[x.decode() for x in lines[:-1]]
        line_end = lines[-1]
        content = f.read(read_zise)
        content = line_end + content
    f.close()
    if remove_duplicates: 
        origin_len = len(contents)
        noduplicate =  list(set(contents))
        now_len = len(noduplicate)
        if origin_len!=now_len:
            print('remove done,%s lines %s -> %s, reduce %s'%(file_name,origin_len,now_len,origin_len-now_len))
        return noduplicate
    return contents


def insert2redis(r,addrs:list,type=''):
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

def scan_keys(r): # 截至20230216 活跃地址数量  16356779
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
    pass
    # r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    # insert2redis(r,[],'unresponsive')