
from mytime import get_currentime
from TCPClient import GetTCPConnection,Sendata,Rcvdata
from tool_redis import insert2redis,get_response_targets
def scan(scan_targets,redis_connection=None):
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
    print(get_currentime(),'query done')
    if unprobed_addrs:
        while True:
            print(get_currentime(),'connect VPS')
            clientSocket = GetTCPConnection("your addr",51886)
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
        print(len(responsive_addrs_zmap))
        # cache data to redis
        unresponsive_addrs_zmap = set(unprobed_addrs) - set(responsive_addrs_zmap)
        # insert responsive data
        if responsive_addrs_zmap:
            insert2redis(redis_connection,responsive_addrs_zmap,type='responsive')
        # insert unresponsivedata
        if unresponsive_addrs_zmap:
            insert2redis(redis_connection,unresponsive_addrs_zmap,type='unresponsive')
    # all responsive addrs in the input addrs
    responsive_addrs_all = set(responsive_addrs_redis).union(set(responsive_addrs_zmap))
    unres = set(scan_targets) - responsive_addrs_all
    return responsive_addrs_all,unres