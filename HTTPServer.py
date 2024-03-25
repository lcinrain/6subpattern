#-*-coding:utf-8-*-

import traceback
import socket
import time
import zlib
import struct
import subprocess
import pickle
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
SRC_v6 = ''

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

def get_md5(input_b):
    md5_hash = hashlib.md5()

    # 更新 MD5 对象的值
    md5_hash.update(input_b)

    # 获取 MD5 值
    md5_digest = md5_hash.hexdigest()
    return md5_digest

class ServerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        session_id = self.headers.get('Session-ID')
        data = self.rfile.read(content_length)
        print(content_length,session_id,data)
        # 处理接收到的文件，这里示例中简单地把文件内容翻转并发送回客户端
        content = zlib.decompress(data)
        file_name = get_md5(content)
        ipv6_list = pickle.loads(content) # deserialization
        
        write_list2file(ipv6_list,file_name=file_name)
        print (get_currentime(),"receive")
        output_filename = file_name+'.response'
        cmd = f"sudo zmap --ipv6-source-ip={SRC_v6} --ipv6-target-file={file_name} -M icmp6_echoscan --cooldown-time=10 -B 10M -q -o {output_filename}"
        print(cmd)
        subprocess.call(cmd,shell=True,stdout=subprocess.PIPE)   #返回值int类型的0
        print (get_currentime(),"zmap over")

        f= open(output_filename,'rb')
        file_data = f.read()
        print(len(file_data))
        file_data = zlib.compress(file_data)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(file_data)

if __name__=="__main__":
    print (get_currentime(),"start!")
    SRC_v6 = get_public_ipv6()
    print('[+] public IPv6 in this device: ', SRC_v6)

    server_address = ('', 8001)
    httpd = HTTPServer(server_address, ServerHandler)
    print('Server is running...')
    httpd.serve_forever()




