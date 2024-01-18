# -*- coding: utf-8 -*-


import socket
import struct
import zlib
import pickle

def Sendata(clientSocket,data_list:list):
    sendata = pickle.dumps(data_list) # serialization, i.e., list to bytes
    sendata = zlib.compress(sendata) # compress to save network traffic and transfer time
    data_len = len(sendata)
    send_data = struct.pack(f'!I{data_len}s',data_len,sendata)
    clientSocket.sendall(send_data)
    return clientSocket

def Rcvdata(HandlSocket,BUFFER_SIZE = 4096):
    data_len = HandlSocket.recv(4)
    data_len = struct.unpack('!I',data_len[:4])[0]
    rcvdata = b''
    while data_len>0:
        data = HandlSocket.recv(BUFFER_SIZE)
        rcvdata+=data
        data_len-=len(data)
    content = zlib.decompress(rcvdata)
    addr_list = content.decode(encoding='utf-8').split('\n')
    addr_list.remove('')
    print (u"接收成功")
    return addr_list

def GetTCPConnection(srvIP,post):
    clientSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  #创建客户端套接字
    clientSocket.connect((srvIP,post))
    return clientSocket

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

if __name__ == '__main__':
    srvIP,post='64.176.51.8',51886
    clientSocket = GetTCPConnection(srvIP,post)
    ipv6s = read_big_file('../hitlist_downsampling.compressed.10000.txt')
    clientSocket = Sendata(clientSocket=clientSocket,data_list=ipv6s)
    rcvdata = Rcvdata(clientSocket)
    clientSocket.close()
