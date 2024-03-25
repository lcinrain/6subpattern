
from mytime import get_currentime
from cfg import URLs
from tool_redis import insert2redis,get_response_targets
from myio import read_big_file,write_list2file
import redis
from myutilities import split_list_by_num
import pickle
import zlib

import requests
import concurrent.futures
def scan(scan_targets,redis_connection,sessions:list,urls:list,verbose=False):
    '''
    query active targets in redis, then scan unprobed targets with Zmap. conbine the results and return.

    Parameters:
        - scan_targets: input targets to scan. Iterable.
        - redis_connection: eg, r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)

    Returns:
        - all responsive addr: set
        - unresponsive addr:set 
    '''
    #responsive_addrs_redis, unprobed_addrs = get_response_targets(redis_connection,scan_targets)
    unprobed_addrs = scan_targets
    responsive_addrs_redis = set()

    responsive_addrs_zmap = set()
    unresponsive_addrs_zmap = set()
    if verbose:
        print(get_currentime(),'query redis done. redis res: ',len(responsive_addrs_redis), ' unprobed:', len(unprobed_addrs))
    if unprobed_addrs:
        # use multiple servers when num of targets > 10000
        if len(unprobed_addrs)>=10000:
            unprobed_addrs_slices = split_list_by_num(unprobed_addrs,len(urls))
            results = []
            executor = concurrent.futures.ProcessPoolExecutor(max_workers=len(urls))
            for i in range(0,len(urls)):
                session = sessions[i]
                url = urls[i]
                unprobed_addr_local = unprobed_addrs_slices[i]
                future = executor.submit(zmap_scan,unprobed_addr_local,session,url)
                results.append(future)
            for future in concurrent.futures.as_completed(results):
                active_addr_zmap_local = future.result()
                print('active addr:',len(active_addr_zmap_local))
                responsive_addrs_zmap.update(active_addr_zmap_local)
        else:
            responsive_addrs_zmap = zmap_scan(unprobed_addrs,session[0],urls[0])

        if verbose:
            print(len(responsive_addrs_zmap))
        # cache data to redis
        unresponsive_addrs_zmap = set(unprobed_addrs) - set(responsive_addrs_zmap)
        # insert responsive data
        if responsive_addrs_zmap:
            insert2redis(redis_connection,responsive_addrs_zmap,type='responsive',verbose=verbose)
        # insert unresponsivedata
        if unresponsive_addrs_zmap:
            insert2redis(redis_connection,unresponsive_addrs_zmap,type='unresponsive',verbose=verbose)
    # all responsive addrs in the input addrs
    responsive_addrs_all = set(responsive_addrs_redis).union(set(responsive_addrs_zmap))
    unres = set(scan_targets) - responsive_addrs_all
    return responsive_addrs_all,unres


def zmap_scan(unprobed_addrs,session,server_url,session_id='0'):
    sendata = pickle.dumps(unprobed_addrs) # serialization, i.e., list to bytes
    sendata = zlib.compress(sendata) # compress to save network traffic and transfer time
    response = session.post(server_url, data=sendata,headers={'Session-ID': session_id})
    content = response.content
    content = zlib.decompress(content)
    addr_list = content.decode(encoding='utf-8').split('\n')
    addr_list.remove('')
    return addr_list # active addr

if __name__ == '__main__':
    r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    sessions = []
    for _ in URLs:
        session = requests.Session()
        sessions.append(session)
    read_file = './hitlist/hitlist_biasedsampling.compressed.10000.txt'
    result_file = './hitlist/hitlist_biasedsampling.compressed.10000.response.txt'
    targets = read_big_file(read_file)
    res,_ = scan(targets,r,sessions,URLs)
    print(res)
    # res = zmap_scan(targets,sessions)
    # write_list2file(res,result_file)