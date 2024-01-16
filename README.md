GitHub restricts the size of uploaded data. We only share code here, and once the data upload is complete, we will publicly release the link.

Dependencies:
- redis
- python36(+)
    - pip install redis



codes:
- scanning framework:
    - TCP_Server: python3/python TCP_Sever.py. read code to change Zmap command and the port
    - myscan1v2.py: use in your function.
    ```
        from myscan1v2 import scan
        r=redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
        responsive_addr,unresponsive_addr = scan(your_target_list:Iterable,r)
    ```
    - myscan2.py: surport distributed scanning.

    
- 6Graph: we add target generation step


- data
    - 6GAN: 
        - conda virtual enviroment. The author didn't provde the detailed versions of each dependency. It costs much time to deal with the incompatible dependencies for a novice in nerual networks. You can use our enviroment to run 6GAN directly without additional configurations.
    - 6Graph: generated targets and responsive addresses on 9 datasets.