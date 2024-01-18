import os
from myio import read_big_file,write_list2file,read_densityList,write_densityList2file
import random
from myipv6 import hexstr2ipv6
from tool_filter import get_route_targets
import json
import math
def sort_targets_in_file(dir:str):
    '''
    read targets from file and sort them and output them to the original file
    '''
    for file_name in os.listdir(dir):
        f = open(dir+file_name)
        targets = f.readlines()
        targets.sort()
        f.close()
        fw = open(dir+file_name,'w')
        fw.writelines(targets)
        fw.close()
        print(file_name)

def remove_singlenode_in_seedregion_file():
    file_name = './seed_region.th16.leftmost.txt'
    f = open(file_name)
    lines = f.readlines()
    f.close()
    fw = open(file_name,'w')
    count = 0
    for line in lines:
        if not '*' in line:
            count+=1
        fw.write(line)
    fw.close()
    print('single num',count)
def count_lines_dir(file_name:str=''):
    # target_dir = './seed_region/2d/targets_noseed/no_duplicate/'
    #target_dir = './seed_region/c/c0/6subpattern-th256/refinement/route/dealiased/noseed/'
    target_dir = './algorithms/6GAN-master/data/candidate_set/'
    total_line_count = 0
    for file in os.listdir(target_dir):
        if not file.endswith('.txt'):continue
        file_name = target_dir+file
        f = open(file_name,'rb')
        content = f.read()
        if not content: continue
        line_count = content.count(b'\n') - 1
        print(file_name,line_count)
        total_line_count+=line_count
    print(total_line_count)

def count_lines_file(file_name:str=''):
    #ile_name = './hitlist/Global_ICMPv6_20220424.response.txt'
    #file_name = 'prefix_matchpyasn/prefix_match.txt'
    #file_name = './seed_region/c/c1/entropyip/targets.txt'
    #file_name = 'E:\\exp\\ipv6_target_generation\\seed_region\\c\\c0\\6tree-simple\\unprobed\\targets.unprobed.txt'
    file_name = './seed_region/c/c0/6tree-simple-10m/seed_regions.th16.txt'
    f = open(file_name,'rb')
    content = f.read()
    line_count = content.count(b'\n') - 1
    print(file_name,line_count)

def count_common_between_files():
    filename1 = './hitlist/Global_ICMPv6_20220424.response.txt'
    filename2 = './hitlist/responsive-addresses20221029.txt'
    content1 = read_big_file(filename1)
    content2 = read_big_file(filename2)
    common = set(content1).intersection(set(content2))
    num_common = len(common)
    loginfo = '%s target num %s, %s target num %s'%(filename1,len(content1),filename2,len(content2))
    print(loginfo)
    loginfo = 'common num %s'%num_common
    print(loginfo)
    loginfo = '%s uqinue num %s'%(filename1,len(content1)-num_common)
    print(loginfo)
    loginfo = '%s uqinue num %s'%(filename2,len(content2)-num_common)
    print(loginfo)

def truncate_file(filename_in:str,filename_out:str,line_count:int):
    content = read_big_file(filename_in)
    print(len(content),'->',line_count)
    write_list2file(content[:line_count],filename_out)

def file_content_is_same():
    '''
    the contents in two files are same or not
    '''
    f1 = open('./comparison.space_partition/seed_regions.leftmost.th16.txt')
    f2 = open('./comparison.space_partition/seed_regions.maxcovering.th16.txt')
    freed_num_dict_lm = dict()
    freed_num_dict_mc = dict()
    for i in range(1,32):
        freed_num_dict_lm[i] = []
        freed_num_dict_mc[i] = []
    
    for line in f1.readlines():
        line = line.rstrip('\n').split('\t')
        pattern = line[0]
        density = line[1]
        seeds = line[2:]
        freed_num_dict_lm[pattern.count('*')].append(pattern)
    
    for line in f2.readlines():
        line = line.rstrip('\n').split('\t')
        pattern = line[0]
        density = line[1]
        seeds = line[2:]
        freed_num_dict_mc[pattern.count('*')].append(pattern)

    for k,v in freed_num_dict_lm.items():
        v_mc = freed_num_dict_mc[k]
        if set(v)!=set(v_mc):
            print(k,len(v),len(v_mc))




def hexstr2ipv6_file(file_name:str,num=0):
    '''
    read hexstr ipv6 in file and translate into compressed ipv6
    '''
    lines = read_big_file(file_name)
    if num:
        lines = lines[:num]
    lines = [hexstr2ipv6(x) for x in lines]
    return lines

def execute_hexstr2ipv6_file():
    for i in [10000,100000,1000000]:
        filename_in = './hitlist/hitlist_biasedsampling.exploded.%s.txt'%i
        filename_out = './hitlist/hitlist_biasedsampling.compressed.%s.txt'%i
        targets = hexstr2ipv6_file(filename_in)
        write_list2file(targets,filename_out)
def file_minus_file(file1:str,file2:str):
    '''
    fil1 - file2 and  write to file1
    '''
    lines1 = read_big_file(file1)
    lines2 = read_big_file(file2)
    write_list2file(list(set(lines1)-set(lines2)),file1)

def file_minus_file_execute():
    target_dir = './algorithms/6tree/src/'
    alias = hexstr2ipv6_file(target_dir+'targets.route.aliased.txt')
    file1 = 'targets.route.unprobed.response.txt'
    lines = read_big_file(target_dir+file1)
    outlines = set(lines) - set(alias)
    print(file1,len(lines),'->',len(outlines))
    write_list2file(outlines,target_dir+file1)
    file2 = 'targets.route.unprobed.txt'
    lines = read_big_file(target_dir+file2)
    outlines = set(lines) - set(alias)
    print(file1,len(lines),'->',len(outlines))
    write_list2file(outlines,target_dir+file2)

def combine_files():
    '''
    write content of file1 into file2
    '''
    #target_dir = './algorithms/6tree/src/'
    file2 = './seed_region/c/c0/6tree-simple/unprobed/targets.unprobed.10m.txt'
    file1 = './unprobed/unprobedc1-c9-6tree-simple.txt'
    lines = read_big_file(file2)
    fw = open(file1,'a',newline='\n')
    fw.writelines([x+'\n' for x in lines])
    fw.close()

def reshape_file(dir_out:str,filename_pattern_out:str,num_file_out=20,file_name='',contents_in=[],budget=10**7):
    if file_name:
        contents = read_big_file(file_name)
    else:
        contents = contents_in
    line_count_per_file = math.ceil(budget/num_file_out)
    num_file_actual = math.ceil(len(contents)/line_count_per_file)
    for i in range(0,num_file_actual):
        start = i*line_count_per_file
        end = (i+1)*line_count_per_file
        content_seg = contents[start:end]
        filename_out = dir_out+filename_pattern_out.replace('*',str(i))
        write_list2file(content_seg,filename_out)


def remove_duplicates_in_file():
    target_dir = 'E:\\exp\\ipv6_target_generation\\algorithms\\6tree\\src\\'
    file_name = 'targets.txt'
    targets = read_big_file(target_dir+file_name,remove_duplicates=True)
    tmp_filename = target_dir+file_name+str(random.randint(0,1000))
    write_list2file(targets,tmp_filename)
    cmd = 'del %s'%target_dir+file_name
    os.system(cmd)
    cmd = 'ren "%s" "%s"'%(tmp_filename,target_dir+file_name)
    os.system(cmd)
    print(file_name,'line count',len(targets))

def remove_duplicates_among_files():
    dir_base = './seed_region/refinement/conservative/2d/'
    dir_out = dir_base+'no_duplicate/'
    cmd = 'mkdir "%s"'%dir_out
    os.system(cmd)
    fw_log = open(dir_out+'log.txt','w')
    
    targets = []
    for i in range(256,1,-1):
        filename_read = 'targets%s.txt'%i
        filename_out = filename_read.replace('.txt','.noduplicate.txt')
        targets_read = read_big_file(dir_base+filename_read)
        targets_noduplicate = set(targets_read) - set(targets)
        targets+=list(targets_noduplicate)
        write_list2file(targets_noduplicate,dir_out+filename_out)
        num_targets_read = len(targets_read)
        num_targets_noduplicate = len(targets_noduplicate)
        num_reduce = num_targets_read - num_targets_noduplicate
        loginfo = "%s origion target num %s, %s noduplicate num %s, reduce num %s "%(filename_read,num_targets_read,filename_out,num_targets_noduplicate,num_reduce)
        print(loginfo)
        fw_log.write(loginfo+'\n')
    loginfo = 'no duplicate target totol num %s'%len(targets)
    print(loginfo)
    fw_log.write(loginfo+'\n')
    fw_log.close()



def d3_combine_files():
    dir_base = './seed_region/3d/'
    dir_combine = './seed_region/3d/combine/'
    for i in range(0,15):
        dir_seed = dir_base+str(i)+'/targets/'
        print(dir_seed)
        for j in range(2,257):
            file_name = 'targets%s.txt'%j
            try:
                f = open(dir_seed+file_name)
            except FileNotFoundError:
                continue
            targets_route = get_route_targets(f.read().splitlines())
            filename_out = file_name.replace('.txt','.route.txt')
            fw = open(dir_combine+filename_out,'a',newline='\n')
            fw.writelines([x+'\n' for x in targets_route])
            fw.close()
            f.close()
            print(filename_out)

def get_123d_pattern():
    pattern_count = 0
    fw = open('./seed_region/123d_pattern_density_list.sorted.txt','w')
    seed_regions = read_big_file('./seed_region/seed_regions_sp5.256.txt')
    print('read seed region done')
    density_list = []
    for seed_region in seed_regions:
        info = seed_region.split('\t')
        pattern = info[0]
        freed = pattern.count('*')
        if freed>3:continue
        seeds = info[1:]
        num_seeds = len(seeds)
        density = num_seeds/16**freed
        #fw.write('\t'.join([pattern,str(density)]+seeds)+'\n')
        density_list.append((pattern,density,seeds))
        pattern_count+=1
    for i in range(1,28):
        filename_read = './seed_region/subpattern%s.json'%i
        fj = open(filename_read)
        subpattern_list = json.load(fj)
        print(filename_read)
        for item in subpattern_list:
            pattern = item['pattern']
            subpatterns = item['subpatterns']
            for sub in subpatterns:
                subpattern = sub['subpattern']
                density = sub['density']
                seeds = sub['seeds']
                num_seeds = len(seeds)
                freed = subpattern.count('*')
                if  freed>3: continue
                pattern_count+=1
                density_list.append((subpattern,density,seeds))
                #fw.write('\t'.join([subpattern,str(density)]+seeds)+'\n')
        fj.close()
    density_list = sorted(density_list,key=lambda x:x[1],reverse=True)
    for pattern,density,seeds in density_list:
        fw.write('\t'.join([subpattern,str(density)]+seeds)+'\n')
    fw.close()
    print('pattern num',pattern_count)

def find_duplicate():
    pattern_list = read_big_file('./seed_region/c/c1/6subpattern/density_list.sorted.txt')
    patterns = set()
    for line in pattern_list:
        pattern = line.split('\t')[0]
        patterns.add(pattern)
    print(len(pattern_list),len(patterns))

def combine_unprobed():
    targets = set()
    for root,dirs,files in os.walk('unprobed'):
        for name in files:
            file_name = os.path.join(root,name)
            print(file_name)
            targets_read = read_big_file(file_name)
            for target in targets_read:
                targets.add(target)
    write_list2file(targets,'./unprobed/unprobed.txt')
    print(len(targets))

def compare_density_list():
    file1 = './seed_region/c/c5/6graph-250k/pattern_density_list.sorted.txt'
    file2 = './seed_region/c/c5/6subpattern-th256-250k/density_list.sorted.txt'
    density_list1 = read_densityList(file1)
    patterns1 = [x[0] for x in density_list1]
    density_list2 = read_densityList(file2)
    patterns2 = [x[0] for x in density_list2]
    print('pattern1 num',len(patterns1))
    print('pattern2 num',len(patterns2))
    comon = set(patterns1).intersection(set(patterns2))
    out_list = [x for x in density_list2 if not x[0] in comon]
    write_densityList2file(out_list,'./seed_region/c/c5/6subpattern-th256-250k/density_list.common.txt')
    print('common num', len(comon))

def unprobed_extract():
    
    targets_unprobed_all = []
    for i in range(5,6):        
        dir_1 = 'E:/exp/ipv6_target_generation/seed_region/c/c%s/6graph-10m/route/dealiased/noseed/unprobed/'%i
        #dir_1 = 'E:/exp/ipv6_target_generation/seed_region/c/c%s/6graph-10m/route/dealiased/noseed/unprobed/'%i
        dir_2 = 'E:/exp/ipv6_target_generation/seed_region/c/c%s-50k/6subpattern-th256-10m/norefinement/route/dealiased/noseed/unprobed/'%i
        dir_3 = 'E:/exp/ipv6_target_generation/seed_region/c/c%s/6subpattern-th256-250k/norefinement/route/dealiased/noseed/unprobed/'%i
        for dir_x in [dir_1,dir_2,dir_3][2:]:
            for file_name in os.listdir(dir_x):
                file_name_read = dir_x+file_name
                print(file_name_read)
                targets_unprobed_all+=read_big_file(file_name_read)
    targets_unprobed_all = set(targets_unprobed_all)
    write_list2file(targets_unprobed_all,'./unprobed/unprobed-c5-6subpattern-250k.txt')
    print('unprobed targets num',len(targets_unprobed_all))

def budget2str(budget:int):
    num = int(budget/10**6)
    if num > 0:
        return str(num)+'m'
    num = int(budget/10**3)
    return str(num)+'k'


if __name__ == '__main__':
    #compare_density_list()
    #count_lines_file()
    #unprobed_extract()
    #combine_unprobed()
    #find_duplicate()
    #remove_duplicates_among_files()
    #truncate_file('./seed_region/c/c0/6tree-simple/unprobed/targets.unprobed.txt','./seed_region/c/c0/6tree-simple/unprobed/targets.unprobed.10m.txt',10**7)
    #count_common_between_files()
    execute_hexstr2ipv6_file()
    #count_lines_file('./unprobed/unprobed-c79-10m-6subpattern256-6graph.txt')