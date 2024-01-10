import numpy as np
import queue


def DHC(arrs):
    q = queue.Queue()
    q.put(arrs)
    regions_arrs = []
    while not q.empty():
        arrs = q.get()
        if len(arrs) <= 16:
            regions_arrs.append(arrs)
            continue
        # len(arrs)<=16: not isolated seed's arrs
        splits = leftmost(arrs)

        for s in splits:
            seed = arrs[s]
            q.put(seed)
    return regions_arrs


def leftmost(arrs):
    Tarrs = arrs.T # 转置，32个列向量
    # 按列访问
    for i in range(32):
        # 统计列向量中每个nybble出现的频数
        # splits是一个含有16个数的数组，每个数表示0-15出现的频数
        splits = np.bincount(Tarrs[i], minlength=16)
        # splits[splits>0]是频数不为0的频数组成的数组
        # 如果长度大于1说明Tarrs[i]列向量不只有一个数值
        if len(splits[splits > 0]) > 1:
            split_index = i
            # 频数不为0的频数对应的索引，这些索引对应0-15，即nybble
            split_nibbles = np.where(splits != 0)[0]
            break
    x = Tarrs[split_index]
    # np.where(x == nibble)[0] 是该列向量值为nibble的全部索引号
    # 例如有7个种子，第split_index维（共32维）列向量x=[1,2,1,2,3,4,5]，x中不同的nybble有[1,2,3,4,5]，那么np.where(x==1)[0]的列向量x的索引为[0,2]，正好为种子的索引，即第split_index维，nybble为1的种子有第0个和第2个，就把种子0和2分在一组
    return [
        np.where(x == nibble)[0] for nibble in split_nibbles
    ]# 种子分组，每个组（list）是种子的索引号


# show the regions for test 

def show_regions(arrs):
    address_space = []
    Tarrs = arrs.T
    for i in range(32):
        splits = np.bincount(Tarrs[i], minlength=16)
        # print(i, splits, np.argwhere(splits > 0)[0][0])
        if len(splits[splits > 0]) == 1:

            address_space.append(format(np.argwhere(splits > 0)[0][0], "x"))
        else:
            address_space.append("*")

    print("********address region**********")
    print("".join(address_space))
    for i in range(len(arrs)):
        print("".join([format(x, "x") for x in arrs[i]]), " ", i)
    print()
