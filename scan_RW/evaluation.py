import os
from os.path import join
import csv
import numpy as np
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import stats
import itertools
from sklearn.metrics import precision_recall_fscore_support
import sys

root_dir = os.getcwd()
print(root_dir)
#voting_pth = join('/Volumes/Passport/audio_scan/result','final_result_agg_global','add0','2018-10-25-15-43-47_15_0.csv')
#voting_pth = join('/Volumes/Passport/audio_scan/result','fil_dia','plda_v1','iter1','voting.csv')
voting_pth = join(root_dir,sys.argv[1])
#list_pth = join('/Volumes/Passport/audio_scan/result','fil_dia','plda_v1','iter0','list.txt')
list_pth = join(root_dir,'middle_data','list.txt')
gt_dir = '/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/dia_groundtruth'

people = ['ambie', 'ar', 'bo', 'bowen', 'changhao', 'dongge', 'hongkai', 'javier', 'jenny', 'joe', 'johan', 'linhai', 'milad','pedro', 'peijun', 'risqi', 'rosa', 'shuyu', 'wei', 'wendy', 'xiaoxuan'] 
# TP FN FP
evaluation = {}
dia_err = 0
for p in people:
    evaluation[p] = [0,0,0]
    
# confusion mat 
# y_axis is true label, x_axis is predicted label
conf_mat = np.zeros([len(people),len(people)])

dia_segs = []
with open(list_pth,'r') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip('\n')
        l = line.split(' ')
        dia_segs.append(l[1])
    
for seg in dia_segs:
    meeting = seg.split('/')[0]
    print(meeting)
    timestamp = seg.split('/')[2]
    print(timestamp)
    if 'seg' not in timestamp:  
        start = int(timestamp.split('_')[0])
        end = int(timestamp.split('_')[1][:-4])
    
        # find the ground truth file
        gt_pth = join(gt_dir, '%s.csv'%meeting)
        gt_timestamps = []
        gt_speakers = []
        with open(gt_pth, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                gt_timestamps.append(row[1])
                gt_speakers.append(row[2])
        #tmp = 1    
        for t in gt_timestamps:
            #print('tmp = %d'%tmp)
            #tmp += 1
            #print('gt_path:%s'%gt_pth)
            if len(t) > 0:
                tick = int(float(t) * 1000)
        
                if start < tick:
                    # check if diarization is incorrect (contain more than one speaker)
                    if end > tick:
                        dia_err += 1

print('dia error = %d' % dia_err)


y_true = []
y_pred = []


dia_err = 0
voting_rst = {}
with open(voting_pth, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        voting_rst[row[0]] = row[1]
ctr = 0 

# open association result
num_rst = 0
for seg, speaker in voting_rst.items():
    num_rst += 1
    meeting = seg.split('/')[10]
    timestamp = seg.split('/')[12]

    if 'seg' in timestamp:
        y_true.append('other')
        y_pred.append(speaker)
    else:
        start = int(timestamp.split('_')[0])
        end = int(timestamp.split('_')[1][:-4])
    
        # find the ground truth file
        gt_pth = join(gt_dir, '%s.csv'%meeting)
        gt_timestamps = []
        gt_speakers = []
        with open(gt_pth, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                gt_timestamps.append(row[1])
                gt_speakers.append(row[2])
    
        # find the duration in ground truth file
        idx = 0
    
        for t in gt_timestamps:
            tick = int(float(t) * 1000)
        
            if start < tick:
                # check if diarization is incorrect (contain more than one speaker)
                if end > tick:
                    dia_err += 1
                    y_true.append('other')
                    y_pred.append(speaker)
                    break
                # check if the label is correct (compute TP, FN, FP)
                else:
                    try:
                        gt_label = gt_speakers[idx-1]
                        gt_idx = people.index(gt_label)
                        speaker_idx = people.index(speaker)
                
                        y_true.append(gt_label)
                        y_pred.append(speaker)
                
                        if gt_label == speaker:
                            # TP
                            ctr += 1
                            evaluation[speaker][0] += 1
                    except:
                        print('what')
                    
                    else:
                        # FP
                        evaluation[speaker][2] += 1
                        # FN (for the gt speaker)
                        evaluation[gt_label][1] += 1
                    
                    conf_mat[gt_idx][speaker_idx] += 1
                
                    break
            else:
                idx += 1


print('accuracy = %f' % float(ctr/len(voting_rst)))
num_lines = sum(1 for line in open('middle_data/list.txt'))
print('num_lines = %d'%num_lines)
print('coverage = %f' % float(num_rst/num_lines))
res = precision_recall_fscore_support(y_true, y_pred, average='macro')
print(res)
print((2 * res[0] * res[1])/(res[0] + res[1]))

