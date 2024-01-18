from collections.abc import Iterable
from myipv6 import ipv6explod

def write_list2file(targets:Iterable,file_name:str,append_LF=True):
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

def write_densityList2file(density_list:list,filename_output:str):
    fw = open(filename_output,'w')
    for pattern,density,seeds in density_list:
        line = '\t'.join([pattern,str(density)]+seeds)
        fw.write(line+'\n')
    fw.close()

def read_densityList(file_name:str):
    list_read = read_big_file(file_name)
    if not list_read:return []
    density_list = []
    for line in list_read:
        info = line.split('\t')
        pattern = info[0]
        density = float(info[1])
        seeds = info[2:]
        density_list.append((pattern,density,seeds))
    return density_list

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


def read_exploded_hitlist_test():
    file_name = './hitlist/hitlist.exploded.txt'
    f = open(file_name)
    count = 0
    targets = []
    for line in f:
        targets.append(line.strip('\n'))
        count+=1
        if count>10000:
            return targets

def read_exploded_hitlist(file_name:str=''):
    if not file_name:
        file_name = './hitlist/hitlist.exploded.txt'
    a = read_big_file(file_name,remove_duplicates=True)
    print('read %s hitlist done, hitlist len %s'%(file_name,len(a)))
    return a

def get_exploded_hitlist():
    f = open('./hitlist/responsive-addresses20221029.txt')
    fw = open('./hitlist/hitlist.exploded2.txt','w')
    lines =  [ipv6explod(x.strip('\n')) for x in f.readlines()]
    fw.writelines([x+'\n' for x in lines])
    f.close()
    fw.close()
    return lines

def change_CRLF(file_path:str):
    # replacement strings
    WINDOWS_LINE_ENDING = b'\r\n'
    UNIX_LINE_ENDING = b'\n'

    # relative or absolute file path, e.g.:
    #file_path = "E:\\exp\\ipv6_target_generation\\algorithms\\6tree\\src\\sampe42w.txt"

    with open(file_path, 'rb') as open_file:
        content = open_file.read()

    content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

    with open(file_path, 'wb') as open_file:
        open_file.write(content)

def hitlistexplode():
    filename1 = './hitlist/Global_ICMPv6_20220424.response.txt'
    filename2 = './hitlist/responsive-addresses20221029.txt'
    filename_cout = './hitlist/6scan.exploded.txt'
    content = read_big_file(filename1)
    targets = list(map(ipv6explod,content))
    targets.sort()
    write_list2file(targets,filename_cout)

if __name__ == '__main__':
    a='./hitlist/hitlist_downsampling.exploded.10000.txt'
    change_CRLF(a)
    a='./hitlist/hitlist_downsampling.exploded.50000.txt'
    change_CRLF(a)
    a='./hitlist/hitlist_downsampling.exploded.100000.txt'
    change_CRLF(a)