#-*-coding:utf-8-*-

import traceback
import socket
import time
import zlib
import struct
import subprocess
import pickle
import re
def get_currentime():
    ctime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return f'[{ctime}]    '

def get_public_ipv6():
    '''
    
    '''
    cmd = "ip -6 addr show | grep -E 'inet6.*global' | awk '{print $2}'"
    result = subprocess.check_output(cmd, shell=True).decode().strip()
    ipv6_addresses = re.findall(r'[0-9a-fA-F:]+/[0-9]+', result)
    if ipv6_addresses:
        return ipv6_addresses[0].split('/')[0]
    else:
        return None

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


def SocketFunction(HOST='',POST=51886):
    ADDR=(HOST,POST)
    tcpServerSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  #建立服务端的套接字
    socket.setdefaulttimeout(5*60)
    tcpServerSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tcpServerSocket.bind(ADDR) #将地址与套接字绑定
    tcpServerSocket.listen(50)  #监听
    print(get_currentime()," port on listening :", POST)
    return tcpServerSocket


def Rcvdata(HandlSocket:socket.socket,BUFFER_SIZE = 4096,file_name='zmap.targets.txt'):
    data_len = HandlSocket.recv(4)
    # header, ie, data length
    data_len = struct.unpack('!I',data_len[:4])[0]
    rcvdata = b''
    while data_len>0:
        data = HandlSocket.recv(BUFFER_SIZE)
        rcvdata+=data
        data_len-=len(data)
    content = zlib.decompress(rcvdata)
    ipv6_list = pickle.loads(content) # deserialization
    write_list2file(ipv6_list,file_name=file_name)
    #print (get_currentime(),"receive")
    return file_name

def SendFile(clientSocket,sendFileName='zmap.target.response.txt'):
    with open(sendFileName, 'rb') as f:
        file_data = f.read()
        print(len(file_data))
        file_data = zlib.compress(file_data)
        data_len = len(file_data)
        print(data_len)
        send_data = struct.pack(f'!I{data_len}s',data_len,file_data)
        clientSocket.sendall(send_data)

def Execute(filename,srcv6,output_filename='zmap.target.response.txt'):
    cmd = f"sudo zmap --ipv6-source-ip={srcv6} --ipv6-target-file={filename} -M icmp6_echoscan --cooldown-time=10 -q -o {output_filename}"
    print(cmd)
    subprocess.call(cmd,shell=True,stdout=subprocess.PIPE)   #返回值int类型的0
    print (get_currentime(),"zmap over")
    return output_filename

#建立连接
def Connect(tcpServerSocket:socket.socket,srcv6):
    '''
    Parameters:
        - srcv6: public ipv6 in this device
    '''
    while True:
        try:
            tcpClientSocket,clientaddr=tcpServerSocket.accept()
            print(get_currentime(),"accept successful")
        except Exception as e:
            print("0 Error : %s" % e)
            traceback.print_exc()
            tcpClientSocket.close()
            continue
        try:
            print (get_currentime(),'From host:', tcpClientSocket.getpeername())
            rcv_filename=Rcvdata(tcpClientSocket)
        except Exception as e:
            print("1 Error : %s" % e)
            traceback.print_exc()
            tcpClientSocket.close()
            continue
        if rcv_filename:
            print (get_currentime(),"receive successfully, start zmap")
            try:
                sendFileName =Execute(rcv_filename,srcv6)
                SendFile(tcpClientSocket,sendFileName)
                print(get_currentime(),"send successfully")
            except Exception as e:
                print("2 Error : %s" % e)
                traceback.print_exc()
                tcpClientSocket.close()
                continue
            try:
                tcpClientSocket.close()
            except Exception as e:
                print("3 Error : %s" % e)
                traceback.print_exc()
        else:
            tcpClientSocket.close()

if __name__=="__main__":
    print (get_currentime(),"start!")
    srcv6 = get_public_ipv6()
    print('[+] public IPv6 in this device: ', srcv6)
    tcpServerSocket=SocketFunction(HOST='',POST=51886)
    print(get_currentime(),"tcpServerSocket created successfully, waiting to be connected...")
    Connect(tcpServerSocket,srcv6)




