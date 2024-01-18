import pyasn
from myio import read_big_file,write_list2file
from myipv6 import hexstr2ipv6
import os,math
from mytime import get_time_now
asndb_alias = pyasn.pyasn('E:/exp/ipv6_target_generation/hitlist/20221231-aliased-prefixes.pyasn')
asndb_route = pyasn.pyasn('E:/exp/ipv6_target_generation/routeview/all-prefixes.txt')

def get_dealiased_targets(targets:list):
    route_targets = []
    [route_targets.append(x) for x in targets if not asndb_alias.lookup(x)[1]]
    return route_targets


def get_route_targets(targets:list):
    route_targets = []
    [route_targets.append(x) for x in targets if asndb_route.lookup(x)[1]]
    return route_targets


def filter_duplicate_among_files(dir_base:str,freed:int,filename_pattern:str='targets*.txt',range_start=-1,range_end=-1):
    '''
    remove duplicates among targets files in dir_based
    '''
    if freed == -1:
        r_step = 1
    else:
        r_step = -1
        range_start = 16**freed+1
        range_end = 1
    dir_out = dir_base+'noduplicate/'
    cmd = 'mkdir "%s"'%dir_out
    os.system(cmd)
    fw_log = open(dir_out+'log.txt','w')
    targets = []
    for i in range(range_start,range_end,r_step):
        filename_read = filename_pattern.replace('*',str(i))
        filename_out = filename_read.replace('.txt','.noduplicate.txt')
        targets_read = read_big_file(dir_base+filename_read)
        if not targets_read:continue
        targets_noduplicate = set(targets_read) - set(targets)
        targets+=list(targets_noduplicate)
        write_list2file(targets_noduplicate,dir_out+filename_out)
        num_targets_read = len(targets_read)
        num_targets_noduplicate = len(targets_noduplicate)
        num_reduce = num_targets_read - num_targets_noduplicate
        loginfo = "[%s] %s origion target num %s, %s noduplicate num %s, reduce num %s "%(get_time_now(),filename_read,num_targets_read,filename_out,num_targets_noduplicate,num_reduce)
        print(loginfo)
        fw_log.write(loginfo+'\n')
    loginfo = '[%s] no duplicate target totol num %s'%(get_time_now(),len(targets))
    print(loginfo)
    fw_log.write(loginfo+'\n')
    fw_log.close()


def filter_all(dir_base:str,freed=-1,filename_hitlist_filter='',filename_pattern:str='targets*.txt',range_start=-1,range_end=-1,skip_duplicate=False,num_split_granularity=20,targets_input:list=[]):
    '''
    filter duplicate unroutable, aliased, hitlist IPv6
    '''
    if freed == -1:
            r_step = 1
    else:
        r_step = -1
        range_start = 16**freed+1
        range_end = 1
    if not skip_duplicate:
        filter_duplicate_among_files(dir_base,freed,filename_pattern,range_start,range_end)
        dir_route = dir_base+'noduplicate/route/'
        dir_noroute = dir_base+'noduplicate/noroute/'
    else:
        dir_route = dir_base+'route/'
        dir_noroute = dir_base+'noroute/'

    
    cmd = 'mkdir "%s"'%dir_route
    os.system(cmd)
    cmd = 'mkdir "%s"'%dir_noroute
    os.system(cmd)

    dir_dealiased = dir_route+'dealiased/'
    cmd = 'mkdir "%s"'%dir_dealiased
    os.system(cmd)
    
    dir_noseed = dir_dealiased+'noseed/'
    cmd = 'mkdir "%s"'%dir_noseed
    os.system(cmd)

    total = 0
    total_route = 0
    total_noroute = 0
    total_dealiased = 0
    total_noseed = 0

    fw_log_route = open(dir_route+'log.txt','w')
    fw_log_dealiased = open(dir_dealiased+'log.txt','w')
    fw_log_noseed = open(dir_noseed+'log.txt','w')

    hitlist = read_big_file(filename_hitlist_filter)
    hitlist = set(hitlist)
    print(filename_hitlist_filter,' IPv6 num',len(hitlist),'-----------')

    targets_all = targets_input
    if not targets_all:
        for i in range(range_start,range_end,r_step):
            #filename_read = 'targets%s_noseed.noduplicate.txt'%i
            if skip_duplicate:
                filename_read = 'targets%s.txt'%i
                targets_read = read_big_file(dir_base+filename_read)
            else:
                filename_read = 'targets%s.noduplicate.txt'%i
                targets_read = read_big_file(dir_base+'noduplicate/'+filename_read)
            if not targets_read: continue
            targets_all+=targets_read
    total = len(targets_all)
    num_target_segment = math.ceil(total/num_split_granularity)
    targets_filtered = []
    for i in range(0,num_split_granularity):
        filename_read = 'targets%s.noduplicate.txt'%i
        start = i*num_target_segment
        end = (i+1)*num_target_segment
        targets_read = targets_all[start:end]
        if not targets_read:continue
        # noroute filter
        targets_route = get_route_targets(targets_read)
        total_route+=len(targets_route)
        targets_noroute = list(set(targets_read)-set(targets_route))
        total_noroute+=len(targets_noroute)
        filename_route = 'targets%s.route.txt'%i
        filename_noroute = 'targets%s.noroute.txt'%i
        write_list2file(targets_route,dir_route+filename_route)
        write_list2file(targets_noroute,dir_noroute+filename_noroute)
        loginfo_route = '%s target num %s, route num %s, noroute num %s'%(filename_read,len(targets_read),len(targets_route),len(targets_noroute))
        print(loginfo_route)
        fw_log_route.write(loginfo_route+'\n')

        # alias filter
        filename_dealiased = filename_route.replace('.txt','.dealiased.txt')
        targets_dealiased = get_dealiased_targets(targets_route)
        total_dealiased+=len(targets_dealiased)
        write_list2file(targets_dealiased,dir_dealiased+filename_dealiased)
        loginfo_dealiased = '%s target num %s, dealiased num %s, aliased num %s'%(filename_route,len(targets_route),len(targets_dealiased),len(targets_route)-len(targets_dealiased))
        print(loginfo_dealiased)
        fw_log_dealiased.write(loginfo_dealiased+'\n')


        # hitlist filter
        # hitlist = read_big_file(filename_hitlist_filter)
        # hitlist = set(hitlist)
        # print(filename_hitlist_filter,' IPv6 num',len(hitlist),'-----------')
        filename_noseed = filename_dealiased.replace('.txt','.noseed.txt')
        targets_noseed = set(targets_dealiased) - hitlist
        targets_filtered+=list(targets_noseed)
        total_noseed+=len(targets_noseed)
        write_list2file(targets_noseed,dir_noseed+filename_noseed)
        loginfo_noseed = '%s target num %s, noseed num %s'%(filename_read,len(targets_read),len(targets_noseed))
        print(loginfo_noseed)
        fw_log_noseed.write(loginfo_noseed+'\n')
        

    loginfo_route = '%s target read total %s, route total %s, noroute total %s'%(dir_base,total,total_route,total_noroute)
    print(loginfo_route)
    fw_log_route.write(loginfo_route+'\n')

    loginfo_dealiased = '%s target read total %s, dealiased total %s, aliased total %s'%(dir_route,total_route,total_dealiased,total_route-total_dealiased)
    print(loginfo_dealiased)
    fw_log_route.write(loginfo_dealiased+'\n')

    loginfo_noseed = '%s target read total %s, noseed total %s, reduce %s'%(dir_noseed,total_dealiased,total_noseed,total_dealiased-total_noseed)
    print(loginfo_noseed)
    fw_log_noseed.write(loginfo_noseed+'\n')
    
    fw_log_dealiased.close()
    fw_log_noseed.close()
    fw_log_route.close()
    return targets_filtered


def filter_all_oneFile(dir_base:str,filename_hitlist_filter:str,filename_read='',targets_input=[]):
    '''
    filter duplicate unroutable, aliased, hitlist IPv6
    '''

    dir_route = dir_base+'route/'
    dir_noroute = dir_base+'noroute/'
    cmd = 'mkdir "%s"'%dir_route
    os.system(cmd)
    cmd = 'mkdir "%s"'%dir_noroute
    os.system(cmd)

    dir_dealiased = dir_route+'dealiased/'
    cmd = 'mkdir "%s"'%dir_dealiased
    os.system(cmd)
    
    dir_noseed = dir_dealiased+'noseed/'
    cmd = 'mkdir "%s"'%dir_noseed
    os.system(cmd)

    total = 0
    total_route = 0
    total_noroute = 0
    total_dealiased = 0
    total_noseed = 0

    fw_log_route = open(dir_route+'log.txt','w')
    fw_log_dealiased = open(dir_dealiased+'log.txt','w')
    fw_log_noseed = open(dir_noseed+'log.txt','w')

    targets_read = read_big_file(dir_base+filename_read) if not targets_input else targets_input

    total = len(targets_read)

    # noroute filter
    targets_route = get_route_targets(targets_read)
    total_route+=len(targets_route)
    targets_noroute = list(set(targets_read)-set(targets_route))
    total_noroute+=len(targets_noroute)
    filename_route = 'targets.route.txt'
    filename_noroute = 'targets.noroute.txt'
    write_list2file(targets_route,dir_route+filename_route)
    write_list2file(targets_noroute,dir_noroute+filename_noroute)
    loginfo_route = '%s target num %s, route num %s, noroute num %s'%(filename_read,len(targets_read),len(targets_route),len(targets_noroute))
    print(loginfo_route)
    fw_log_route.write(loginfo_route+'\n')

    # alias filter
    filename_dealiased = filename_route.replace('.txt','.dealiased.txt')
    targets_dealiased = get_dealiased_targets(targets_route)
    total_dealiased+=len(targets_dealiased)
    write_list2file(targets_dealiased,dir_dealiased+filename_dealiased)
    loginfo_dealiased = '%s target num %s, dealiased num %s, aliased num %s'%(filename_route,len(targets_route),len(targets_dealiased),len(targets_route)-len(targets_dealiased))
    print(loginfo_dealiased)
    fw_log_dealiased.write(loginfo_dealiased+'\n')


    # hitlist filter
    hitlist = read_big_file(filename_hitlist_filter)
    hitlist = set(hitlist)
    filename_noseed = filename_dealiased.replace('.txt','.noseed.txt')
    targets_noseed = set(targets_dealiased) - hitlist
    total_noseed+=len(targets_noseed)
    write_list2file(targets_noseed,dir_noseed+filename_noseed)
    loginfo_noseed = '%s target num %s, noseed num %s'%(filename_read,len(targets_read),len(targets_noseed))
    print(loginfo_noseed)
    fw_log_noseed.write(loginfo_noseed+'\n')
        

    loginfo_route = '%s target read total %s, route total %s, noroute total %s'%(dir_base,total,total_route,total_noroute)
    print(loginfo_route)
    fw_log_route.write(loginfo_route+'\n')

    loginfo_dealiased = '%s target read total %s, dealiased total %s, aliased total %s'%(dir_route,total_route,total_dealiased,total_route-total_dealiased)
    print(loginfo_dealiased)
    fw_log_route.write(loginfo_dealiased+'\n')

    loginfo_noseed = '%s target read total %s, noseed total %s, reduce %s'%(dir_noseed,total_dealiased,total_noseed,total_dealiased-total_noseed)
    print(loginfo_noseed)
    fw_log_noseed.write(loginfo_noseed+'\n')
    
    fw_log_dealiased.close()
    fw_log_noseed.close()
    fw_log_route.close()
    return list(targets_noseed)

def noroute_filter():
    '''
    filter targets not in route view
    '''
    #target_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/'
    dir_target = './seed_region/refinement/conservative/1d/no_duplicate/'
    dir_route = dir_target+'route/'
    dir_noroute = dir_target+'noroute/'
    cmd = 'mkdir "%s"'%dir_route
    os.system(cmd)
    cmd = 'mkdir "%s"'%dir_noroute
    os.system(cmd)
    total_route = 0
    total_noroute = 0
    total = 0
    for i in range(2,16):
        file_name = 'targets%s.noduplicate.txt'%i
        targets = read_big_file(dir_target+file_name)
        if not targets: continue
        total+=len(targets)
        targets_route = get_route_targets(targets)
        total_route+=len(targets_route)
        targets_noroute = list(set(targets)-set(targets_route))
        total_noroute+=len(targets_noroute)
        filename_route = dir_route+'targets%s.route.txt'%i
        filename_noroute = dir_noroute+'targets%s.noroute.txt'%i
        write_list2file(targets_route,filename_route)
        write_list2file(targets_noroute,filename_noroute)
        print(file_name,'target num',len(targets),'route num',len(targets_route),'noroute num',len(targets_noroute))

    print('total num',total,'route len total',total_route,'noroute len',total_noroute)
    

def noroute_filter_onefile():
    '''
    filter targets not in route view
    '''
    #target_dir = './algorithms/6Graph-main/targets_distance_based/no_duplicate/'
    target_dir = './algorithms/6tree/src/'
    total_targets = 0
    file_name = 'targets.full.txt'
    targets_tmp = read_big_file(target_dir+file_name)
    targets_route = get_route_targets(targets_tmp)
    targets_noroute = list(set(targets_tmp)-set(targets_route))
    filename_route = target_dir+'targets.route.txt'
    filename_noroute = target_dir+'targets.noroute.txt'
    write_list2file(targets_route,filename_route)
    write_list2file(targets_noroute,filename_noroute)
    total_targets+=len(targets_route)

    print('route len',len(targets_route),'noroute len',len(targets_tmp)-len(targets_route))

def filter_alias():
    target_dir = './algorithms/6tree/src/'
    file_name = 'targets.route.txt'
    targets_tmp = read_big_file(target_dir+file_name)
    targets_tmp = [hexstr2ipv6(x.replace(':','')) for x in targets_tmp]
    targets_route = get_dealiased_targets(targets_tmp)
    filename_route = target_dir+'targets.route.dealiased.txt'
    write_list2file(targets_route,filename_route)
    print('dealiasing done',len(targets_tmp),'->',len(targets_route))


def filter_hitlist():
    '''
    remove IPv6 hitlist from generated targets
    '''
    hitlist = read_big_file('./hitlist/responsive-addresses20221029.txt')
    hitlist = set(hitlist)
    # dir_base = './seed_region/1d/targets/no_duplicate/route/dealiased/'
    #dir_base = './seed_region/2d/targets/no_duplicate/route/dealiased/'
    # dir_base = './seed_region/refinement/conservative/2d/no_duplicate/route/dealiased/'
    dir_base = './seed_region/c/c1/6graph/noduplicate/route/dealiased/'
    dir_base = './seed_region/c/c1/6subpattern/norefinement/noduplicate/route/dealiased/'
    dir_noseed = dir_base+'noseed2/'
    cmd = 'mkdir "%s"'%dir_noseed
    os.system(cmd)
    total = 0
    total_noseed = 0
    fw_log_noseed = open(dir_noseed+'log.txt','w')
    for i in range(0,31):
        filename_read = 'targets%s.route.dealiased.txt'%i  
        targets_read = read_big_file(dir_base+filename_read)

        if not targets_read: continue
        total+=len(targets_read)
        targets_noseed = set(targets_read) - hitlist
        total_noseed+=len(targets_noseed)
        filename_noseed = 'targets%s.route.dealiased.noseed.txt'%i  
        write_list2file(targets_noseed,dir_noseed+filename_noseed)
        loginfo_noseed = '%s target num %s, noseed num %s'%(filename_read,len(targets_read),len(targets_noseed))
        print(loginfo_noseed)
        fw_log_noseed.write(loginfo_noseed+'\n')


    loginfo_noseed = '%s target read total %s, noseed total %s, reduce %s'%(dir_base,total,total_noseed,total-total_noseed)
    print(loginfo_noseed)
    fw_log_noseed.write(loginfo_noseed+'\n')

def filter_1dtargets():
    '''
    remove duplicate targets in 1d from 2d, remove 1d,2d from 3d etc.
    '''
    dir_1d = './seed_region/refinement/conservative/1d/no_duplicate/route/dealiased/'
    dir_2d = './seed_region/refinement/conservative/2d/no_duplicate/route/dealiased/'
    dir_2d_out = './seed_region/refinement/conservative/2d/no_duplicate/route/dealiased/no1d/'
    cmd = 'mkdir "%s"'%dir_2d_out
    os.system(cmd)
    fw_log = open(dir_2d_out+'log.txt','w')
    targets_1d = []
    for i in range(2,16):
        # file_name = 'targets%s.noseed.txt'%i
        file_name = 'targets%s.route.dealiased.txt'%i
        targets_1d+=read_big_file(dir_1d+file_name)
        print(file_name)
    targets_1d = set(targets_1d)
    print('1d total targets',len(targets_1d))
    num_2dtotal = 0
    num_2dtotal_noduplicate = 0
    for i in range(2,256):
        #file_name = 'targets%s.noseed.txt'%i
        file_name = 'targets%s.route.dealiased.txt'%i
        targets = read_big_file(dir_2d+file_name)
        num_2dtotal+=len(targets)
        targets_noduplicate = set(targets) - targets_1d
        num_2dtotal_noduplicate+=len(targets_noduplicate)
        num_duplicate = len(targets) - len(targets_noduplicate)
        if num_duplicate:
            loginfo = '%s target num %s, 1d duplicate num %s, no duplicate num %s'%(file_name,len(targets),num_duplicate,len(targets_noduplicate))
            fw_log.write(loginfo+'\n')
            print(file_name,len(targets),'->',len(targets_noduplicate),'reduce ',num_duplicate)
        write_list2file(targets_noduplicate,dir_2d_out+file_name)
    loginfo = '2d target total %s, no duplicate total %s, duplicate total %s'%(num_2dtotal,num_2dtotal_noduplicate,num_2dtotal-num_2dtotal_noduplicate)
    print(loginfo)
    fw_log.write(loginfo+'\n')
    fw_log.close()
if __name__ == '__main__':
    #filter_files()
    filter_hitlist()
    #filter_1dtargets()
    #filter_all(dir_base='./algorithms/6Graph-main/targets_noseed/',range_start=0,range_end=46,skip_duplicate=True)
