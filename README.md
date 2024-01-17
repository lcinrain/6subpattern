GitHub restricts the size of uploaded data. We only share code here, and once the data upload is complete, we will publicly release the link. You can contact us for these data right now. email: lcinrain@sina.com

Dependencies:
- redis
- python36(+)
    - pip install redis



codes:
- scanning framework:
    - before, the dynamic target generation algorithms (TGAs) can only run in one devide. with this framework, you can run the generation process on your machine and put the scanning process on your servers.
    - TCP_Server: python3/python TCP_Sever.py in your server or locally. Read the source code to change Zmap command and the port,etc.
    - myscan1v2.py: run on your machine.
    ```
        from myscan1v2 import scan
        r=redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
        responsive_addr,unresponsive_addr = scan(your_target_list:Iterable,r)
    ```
    - myscan2.py: surport distributed scanning.    
- 6Graph: we add target generation step
- 6Forest: we add the target generation step as 6Graph after costing<=three free dimension patterns.
- 6Tree, AddrMiner, DET: integrated scanning framework.



- data
    - 6GAN: 
        - conda virtual enviroment. The author didn't provde the detailed versions of each dependency. It costs much time to deal with the incompatible dependencies for a novice in nerual networks. You can use our enviroment to run 6GAN directly without additional configurations.
        - models and output generated targets on 9 datasets.
    - 6Graph, 6Forest, 6Tree, 6Hit, 6Tree, DET, 6Scan, 6GAN, Entropy/IP: generated targets and responsive addresses on 9 datasets.
