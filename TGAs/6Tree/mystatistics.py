from myio import read_big_file,write_list2file
import pyasn
asndb_alias = pyasn.pyasn('E:/exp/ipv6_target_generation/hitlist/20221231-aliased-prefixes.pyasn')

def split_list(lst, x):
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

def get_dealiased_targets(targets:list or set):
    route_targets = []
    [route_targets.append(x) for x in targets if not asndb_alias.lookup(x)[1]]
    return route_targets

K=10**3
M=10**6
budget_dict = {1:100*K,2:1*M,3:10*M}
sampling = ['down','prefix','biased']
indices = [1,2,3]
all_targets = set()
fw = open('hitrate.log.txt','w')
for sam in sampling:
    print(sam)
    fw.write(sam+'\n')
    for index in indices:
        print(index)
        b = budget_dict[index]
        fw.write(f'\nbudget {b}\n')
        file_name_target = f'./{sam}{index}/result/6Tree.target{b}'
        file_name_response = f'./{sam}{index}/result/6Tree.result{b}'
        targets_response = read_big_file(file_name_response)
        targets_response = set(targets_response)
        targets_read = read_big_file(file_name_target)
        targets_read = targets_read[:b]
        all_targets = set()
        aliased_targets_file = set()
        i = 0
        header = ['round','target','dealiased','response_dealiased','hitrate']
        fw.write('\t'.join(header)+'\n')
        r = split_list(targets_read,20)
        for target in r:
            info_list = []
            info_list.append(str(i))# round
            target = set(target)-all_targets
            info_list.append(str(len(target))) # target
            all_targets.update(target)
            dealised_target = set(get_dealiased_targets(target)) #dealiased target
            target_num_roundi = len(dealised_target)
            info_list.append(str(target_num_roundi))

            aliased_targets_file.update(target-dealised_target)
            target_res_roundi =dealised_target.intersection(targets_response) #response dealiased
            response_num_roundi = len(target_res_roundi)
            info_list.append(str(response_num_roundi))

            hitrate_roundi = response_num_roundi/target_num_roundi
            i+=1
            info_list.append(str(hitrate_roundi))
            fw.write('\t'.join(info_list)+'\n')
        num_file_targets = len(set(targets_read))
        num_file_aliased = len(aliased_targets_file)
        num_file_dealiased = num_file_targets - num_file_aliased
        num_file_response = len(targets_response - aliased_targets_file)
        hitrate_file_ave = num_file_response/num_file_dealiased
        info = [f'target num: {num_file_targets}',f'dealiased num: {num_file_dealiased}',f'aliased num: {num_file_aliased}',f'dealiased response: {num_file_response}',f'hitrate:{hitrate_file_ave}']
        fw.write('\t'.join(info)+'\n')
    fw.write('\n\n\n')
fw.close()