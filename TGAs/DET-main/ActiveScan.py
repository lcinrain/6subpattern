#!/usr/bin/python3.6
# encoding:utf-8
import time,socket
from tool_redis import get_response_targets,insert2redis
from TCPClient import Sendata,Rcvdata,GetTCPConnection
from cfg import SRV_IP,PORT
def get_currentime():
    ctime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return f'[{ctime}]    '
def write_list2file(targets:list,file_name:str,append_LF=True):
    '''
    write list to file. append_LF default True means add '\n' at each line.
    newline is LF not CRLF
    '''
    fw = open(file_name,'w',newline = '\n')
    if append_LF:
        fw.writelines([x+'\n' for x in targets])
    else:
        fw.writelines(list(targets))
    fw.close()


def Scan(addr_set, source_ip, output_file, tid,r):
    """
    运用扫描工具检测addr_set地址集中的活跃地址

    Args：
        addr_set：待扫描的地址集合
        source_ip
        output_file
        tid:扫描的线程id
        r: redis connection, eg, r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
        clientSocket: TCP socket

    Return：
        active_addrs：活跃地址集合
    """
    print('[+]Scanning {} addresses...'.format(len(addr_set)))
    t_start = time.time()

    # get data in redis
    print(get_currentime(),'query in redis, querying num:',len(addr_set))
    responsive_addrs_redis, unprobed_addrs = get_response_targets(r,addr_set)
    # deal with data not in redis, ie, unprobed addrs
    responsive_addrs_zmap = set()
    unresponsive_addrs_zmap = set()
    print(get_currentime(),'query done')
    if unprobed_addrs:
        while True:
            print(get_currentime(),'connect VPS')
            clientSocket = GetTCPConnection(SRV_IP,PORT)
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
            insert2redis(r,responsive_addrs_zmap,type='responsive')
        # insert unresponsivedata
        if unresponsive_addrs_zmap:
            insert2redis(r,unresponsive_addrs_zmap,type='unresponsive')
    # all responsive addrs in the input addrs
    responsive_addrs_all = set(responsive_addrs_redis).union(set(responsive_addrs_zmap))
    # write data to disk
    scan_input = f'{output_file}/zmap/scan_input_{tid}.txt'
    scan_output = f'{output_file}/zmap/scan_output_{tid}.txt'
    scan_unprobed = f'{output_file}/zmap/scan_output_{tid}.unprobed.txt'
    scan_unprobed_response = f'{output_file}/zmap/scan_output_{tid}.unprobed_response.txt'
    scan_unprobed_unresponse = f'{output_file}/zmap/scan_output_{tid}.unrpobed_unresponse.txt'
    write_list2file(addr_set,scan_input)
    write_list2file(responsive_addrs_all,scan_output)
    if unprobed_addrs:
        write_list2file(unprobed_addrs,scan_unprobed)
    if responsive_addrs_zmap:
        write_list2file(responsive_addrs_zmap,scan_unprobed_response)
    if unresponsive_addrs_zmap:
        write_list2file(unresponsive_addrs_zmap,scan_unprobed_unresponse)

    print('[+]Over! Scanning duration:{} s'.format(time.time() - t_start))
    print('[+]{} active addresses detected!'
        .format(len(responsive_addrs_all)))
    return responsive_addrs_all



if __name__ == '__main__':
    addr_set = set()
    addr_set.add('2400:da00:2::29')
    addr_set.add('2404:0:8f82:a::201e')
    addr_set.add('2404:0:8e04:9::201e')
    Scan(addr_set)
    print('Over!')
