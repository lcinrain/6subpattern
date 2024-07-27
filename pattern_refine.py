
'''
pattern refining is the second step of pattern mining. It aims to narrow down the pattern whose free dimensions are noted as wildcard *. The wildcard contains 16 addresses which may be not all active.

the basic idea of pattern refining is to generate pre-scan targets according to the seeds distribution in seed region( i.e. variables in free dimension) and then re-present the pattern by range, list or single besides wildcard
according to the distribution of variables in free dimensions.
'''

from myio import read_big_file

LOW_NYBBLES = ['0','1','2','3','4']
MIDDLE_NYBBLES = ['5','6','7','8','9']
HIGH_NYBBLES = ['a','b','c','d','e','f']
FULL_NYBBLES = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']

def read_refine_conservative_pattern(filname_conservative_pattern:str):
    lines = read_big_file(filname_conservative_pattern,throw_exception=True)
    contents = []
    for line in lines:
        info = line.split('\t')
        pattern = info[0]
        density = info[1]
        num_rep = int(info[2])
        rep = info[3:3+num_rep]
        seeds = info[3+num_rep:]
        list_rep = []
        for r in rep:
            index,range_ = r.split(',')
            list_rep.append((int(index),range_))
        content = (pattern,float(density),list_rep,seeds)
        contents.append(content)
        # count+=1
        # if count>100:
        #     break
    return contents

def patterns_refine_conservative(pattern_list:list=[],filename_pattern_in:str='',filename_output=''):
    '''
    pattern_list = [[pattern,density,seeds],]
    Paramter pattern_list or filename_pattern_in, ether is required
    '''
    if not pattern_list:
        pattern_list = read_refine_conservative_pattern(filename_pattern_in)
    result = []
    for info in pattern_list:
        pattern_str = info[0]
        density = info[1]
        seeds = info[2]
        representation = variable_representation(seeds)
        content = (pattern_str,density,representation,seeds)
        result.append(content)
    output_refined_pattern(result,filename_output)
    return result

def output_refined_pattern(results:list,filename_output:str):
    fw = open(filename_output,'w')
    for pattern,density,representations,seeds in results:
        list_tmp = []
        for representation in representations:
            list_tmp.append(','.join([str(x) for x in representation]))
        data = [pattern,str(density),str(len(representations)),'\t'.join(list_tmp)]+seeds
        line = '\t'.join(data)+'\n'
        fw.write(line)
    fw.close()

def variable_representation(seeds:list):
    freed_values_dict = get_freed_variable_dict(seeds)
    result = []
    for freed, variables in freed_values_dict.items():
        variables = list(variables)
        variables.sort()
        representation = ''
        if set(LOW_NYBBLES).intersection(variables):
            if set(MIDDLE_NYBBLES).intersection(variables):
                representation =  '0'+str(variables[-1])
                # if set(HIGH_NYBBLES).intersection(variables):
                #     return '0'+str(variables[-1])
                # else:
                #     return '0'+str(variables[-1])
            elif set(HIGH_NYBBLES).intersection(variables):
                representation = '04af' 
            else:
                # LOW_NYBBLES
                representation = '04'
        elif set(HIGH_NYBBLES).intersection(variables):
            if set(MIDDLE_NYBBLES).intersection(variables):
                # wildcard
                representation = str(variables[0])+str(variables[-1])
            else:
                # HIGH_NYBBLES
                representation = 'af'
        else:# only MIDDLE_NYBBLES
            representation = '59'
        result.append((freed,representation))
    return result



def get_freed_variable_dict(hitlist_exploded:list,pattern_str:str=''):
    free_dimension = dict()
    for i in range(0,32):
        col_i_values = [hitlist_exploded[j][i] for j in range(0,len(hitlist_exploded))]
        col_i_values = list(set(col_i_values))
        if len(col_i_values) > 1:
            free_dimension[i] = col_i_values
    return free_dimension
