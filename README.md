GitHub restricts the size of uploaded data. We only share code here, and once the data upload is complete, we will publicly release the link. You can contact us for these data right now. email: lcinrain@sina.com

- Dependencies:
    - redis
    - python36(+)
        - pip install redis



- codes:
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
            ```
                step 1:

                run HTTPServer.py in your server: python HTTPServer.py
                change zmap command in HTTPServer.py
                
                step 2:

                add your server IP in cfg.py
                
                step 3:

                in your code:

                from myscan2 import scan
                import redis
                import requests
                r = redis.Redis(host='localhost', port=6379, decode_responses=True,db=1)
                sessions = []
                for _ in URLs:
                    session = requests.Session()
                    sessions.append(session)
                responsive_addrs, unresp_addrs = scan(targets_you_wantto_scan,r,sessions,URLs)
            ```
    - 6Graph: we add target generation step
    - 6Forest: we add the target generation step as 6Graph after costing<=three free dimension patterns.
    - 6Tree, AddrMiner, DET: integrated scanning framework.



- data
    - 9 seed sets sampled in Gasser's hitlist


    | Seed set | Sampling Strategy | Seed Number |Range |
    |----------|-------------------|-------------|-------------------------------------------------------------------------------------------------------|
    | $C_1$    | Down Sampling     | 10K         | 2001:200:16a:1113::168-2c0f:ff48:30:130::c554:8241                                                  |
    | $C_2$    | Down Sampling     | 100K        | 2001:200:0:1::6-2c0f:ff48:30:130::c554:8265                                                         |
    | $C_3$    | Down Sampling     | 1M          | 2001:200:0:1::7-2c0f:ffc8::c401:3e99                                                                 |
    | $C_4$    | Biased Sampling   | 10K         | 2001:41d0:203:38e8::-2001:41d0:302:2200::936                                                          |
    | $C_5$    | Biased Sampling   | 100K        | 2a00:d680:20:50::a293-2a01:488:42:1000:50ed:825f:ffb6:5071                                           |
    | $C_6$    | Biased Sampling   | 1M          | 2003:a:107f:add3:464e:6dff:fe1e:f8a0-2600:1fa0:818b:8371:36e7:caba::                                  |
    | $C_7$    | Prefix-based Sampling | 10K     | 2a02:26f0:500::215:84a8-2600:9000:1116::422                                                           |
    | $C_8$    | Prefix-based Sampling | 100K    | 2001:200:e00:a0::1999:1-2c0f:fef8:a:3:face:b00c:0:a7                                               |
    | $C_9$    | Prefix-based Sampling | 1M      | 2001:200:e000::5-2c0f:fe98:c:2b::3                                                    |
    - 6GAN: 
        - conda virtual enviroment. The author didn't provde the detailed versions of each dependency. It costs much time to deal with the incompatible dependencies for a novice in nerual networks. You can use our enviroment to run 6GAN directly without additional configurations.
        - models and output generated targets on 9 datasets.
    - 6Graph, 6Forest, 6Tree, 6Hit, 6Tree, DET, 6Scan, 6GAN, Entropy/IP: generated targets and responsive addresses on 9 datasets.
