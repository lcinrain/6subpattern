def split_list_by_num(lst, x):
    '''
    split lst into x list
    '''
    avg = len(lst) // x  # 平均分割后每个子列表的长度
    remainder = len(lst) % x  # 余数，用于处理不能平均分割的情况

    result = []  # 存储分割后的子列表
    start = 0

    for i in range(x):
        if remainder > 0:
            sublist = lst[start:start+avg+1]
            remainder -= 1
        else:
            sublist = lst[start:start+avg]
        result.append(sublist)
        start += len(sublist)

    return result

def split_list_by_step(lst, step):
    '''
    every step creat a new list, returns all create lists
    '''
    result = [lst[i:i+step] for i in range(0, len(lst), step)]
    return result

if __name__ == '__main__':
    a=[1,2,3,4,5]
    b=split_list_by_step(a,6)
    print(b)