import tools
import os
from os.path import join, splitext
import yaml
import numpy as np
import re
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from munkres import Munkres, print_matrix
import pickle
from datetime import datetime, timedelta
from shutil import copyfile, rmtree
import argparse
import sys
import csv
from statistics import median
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import stats
import itertools
##############
##  voting  ##
##############
import os
import yaml
from os.path import join
import numpy as np
import re
from sklearn.cluster import DBSCAN, AgglomerativeClustering
import pickle
import tools
import argparse
import sys
import csv
from shutil import copyfile, rmtree

project_dir = os.getcwd()
final_res_dir = join(project_dir,'final_result')
files = os.listdir(final_res_dir)
for f in files:
    if os.path.isdir(join(final_res_dir,f)):
        #print(f)
        t_list = [t for t in os.listdir(join(final_res_dir,f)) if t.endswith('csv')]
        #print(len(t_list))
        for t in t_list:
            idx = t.split('_')[-1][:-4]
            #print(int(idx))
            if (int(idx)+1) == len(t_list):
                copyfile(join(final_res_dir,f,t), join(final_res_dir,t))



def find_max_key(dic, threshold=5):
    if len(dic)==0:
        return None
    ma = 0
    people = ''
    sum = 0
    for k, v in dic.items():
        sum+=v
        if v >= ma:
            ma = v
            people = k
    if sum > threshold:
        return people
    else:
        return None

project_dir = os.getcwd()
with open(join(project_dir, 'config.yaml'), 'r') as f:
    cfg = yaml.load(f)
middle_data_path = join(project_dir, cfg['base_conf']['middle_data_path'])
middle_pic_path = tools.get_meeting_and_path(middle_data_path, r'.+\d+\.pk$')
meeting_npy_paths = tools.get_meeting_and_path(middle_data_path, r'.+\.npy$')
result_data_path = join(project_dir, 'final_result')
paths = os.listdir(result_data_path)
#paths = list(filter(lambda x: re.match(re.escape('2018-09-06-20-35-42') + r'.+\.csv', x), paths))
paths = list(filter(lambda x: re.match(r'.+\.csv', x), paths))

video_info = np.empty([0, 200])
pic_paths = []

for k in middle_pic_path:
    with open(middle_pic_path[k], 'rb') as f:
        iou_pic_path = pickle.load(f)
        pic_paths.extend(iou_pic_path)
        
    iou_vec = np.load(meeting_npy_paths[k])
    try:
        video_info = np.vstack((video_info, iou_vec))
    except:
        print(k)
        
stat = {k: {} for k in pic_paths}
tmp_paths = pic_paths

pic_paths = [k for k in pic_paths]

vectors = dict(zip(pic_paths, video_info))

peoples = set([])


for path in paths:
    temp_path = os.path.split(path)[-1]
    temp_path = re.split(r'-|_', temp_path)
    print(temp_path)
    if temp_path[-1][:-5] == 'voting':
        continue
    add_num = int(temp_path[-1][:-4])

    with open(join(project_dir, 'final_result', path)) as f:
        result = csv.reader(f, delimiter=',')
        for row in result:
            if row[0] in stat:
                peoples.add(row[1])
                if row[1] in stat[row[0]]:
                    stat[row[0]][row[1]] += 1
                else:
                    stat[row[0]][row[1]] = 1

                    
peoples = list(peoples)
peoples.sort()

soft_label = {k: np.zeros([len(peoples)]).astype(np.float64) for k in tmp_paths}
for k, v in stat.items():
    for p, n in v.items():
        soft_label[k][peoples.index(p)] = n

for k, v in soft_label.items():
    if v.sum()==0:
        soft_label[k] = np.zeros([len(peoples)]).astype(np.float64)
    else:
        soft_label[k] = v/v.sum()
        
save_soft_label = {}
for k, v in soft_label.items():
    save_soft_label[tools.get_parent_folder_name(k, 1)] = v
    
result = {k: find_max_key(v, 0) for k, v in stat.items()}


centers = {}

for k, v in result.items():
    if v is None:
        continue
    if v not in centers:
        centers[v] = np.empty([0, 200])
    centers[v] = np.vstack((centers[v], vectors[k]))
    
for k in centers:
    centers[k] = np.mean(centers[k], axis=0)
    
with open(join(project_dir, 'final_result', 'voting_center.pk'), 'wb') as f:
        pickle.dump(centers, f, protocol=pickle.HIGHEST_PROTOCOL)
        


with open(join(project_dir, 'final_result', 'voting.csv'), 'w') as f:
    for k, v in result.items():
        if v is None:
            continue
        f.write('%s,%s\n' % (k, v))
if os.path.exists(join(project_dir, 'final_result', 'voting')):
    rmtree(join(project_dir, 'final_result', 'voting'))
os.mkdir(join(project_dir, 'final_result', 'voting'))

index = 0
for k, v in result.items():
    if v is None:
        continue
    if not os.path.exists(join(project_dir, 'final_result','voting', v)):
            os.mkdir(join(project_dir, 'final_result', 'voting', v))

    s_pic_name = tools.get_parent_folder_name(k, 1)
    #s_spk_name = tools.get_parent_folder_name(k, 2)
    s_meet_name = tools.get_parent_folder_name(k, 3)
    copyfile(join(middle_data_path, s_meet_name, 'segs', s_pic_name),
             join(project_dir, 'final_result', 'voting', v, s_pic_name))
    index += 1

with open(join(project_dir, 'final_result', 'voting','soft_label.pk'), 'wb') as f:
    pickle.dump(save_soft_label, f, protocol=pickle.HIGHEST_PROTOCOL)
