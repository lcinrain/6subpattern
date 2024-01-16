
from mytime import get_currentime
from TCPClient import GetTCPConnection,Sendata,Rcvdata
from tool_redis import insert2redis,get_response_targets
from myio import read_big_file,write_list2file
import redis
from myutilities import split_list_by_step

def scan(scan_targets,redis_connection=None,verbose=False):
    '''
    query active targets in redis, then scan unprobed targets with Zmap. conbine the results and return.

    Parameters:
        - scan_targets: input targets to scan. Iterable.
        - redis_connection: eg, r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)

    Returns:
        - all responsive addr: set
        - unresponsive addr:set 
    '''
    responsive_addrs_redis, unprobed_addrs = get_response_targets(redis_connection,scan_targets)
    responsive_addrs_zmap = set()
    unresponsive_addrs_zmap = set()
    if verbose:
        print(get_currentime(),'query redis done. redis res: ',len(responsive_addrs_redis), ' unprobed:', len(unprobed_addrs))
    if unprobed_addrs:
        unprobed_addrs_slices = split_list_by_step(unprobed_addrs,100000)
        for unprobed_addrs_slice in unprobed_addrs_slices:
            zmap_step_result = zmap_scan(unprobed_addrs_slice)
            responsive_addrs_zmap.update(zmap_step_result)
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


def zmap_scan(unprobed_addrs):
    while True:
        print(get_currentime(),'connect VPS')
        clientSocket = GetTCPConnection("localhost",51886)
        # send unprobed data
        print(get_currentime(),'connected. sending data')
        clientSocket = Sendata(clientSocket,unprobed_addrs)
        # receive data
        try:
            print(get_currentime(),'sended. receiving data')
            responsive_addrs_zmap = Rcvdata(clientSocket)
            break
        except Exception as e:
            print(e)
            clientSocket.close()
            print(get_currentime(),'receiving time out, connect again')
        print(get_currentime(),'received')
    clientSocket.close()
    return responsive_addrs_zmap

if __name__ == '__main__':
    r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
    read_file = './algorithms/6Forest-main/data/result/biased/result1000000/target10000000'
    result_file = './algorithms/6Forest-main/data/result/biased/result1000000/result10000000'
    targets = read_big_file(read_file)
    res,_ = scan(targets,r)
    write_list2file(res,result_file)