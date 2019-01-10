import os
from os.path import join
import csv
import numpy as np
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy import stats
import itertools
import pickle
from sklearn.metrics import precision_recall_fscore_support
import pickle
import sys

root_dir = os.getcwd()
#voting_pth = join(root_dir,'final_result','2018-10-19-16-57-33_10_0.csv')
voting_pth = join(root_dir,sys.argv[1])
POI_pth = join(root_dir,'middle_data','POIs.pk')
with open(POI_pth,'rb') as f:
    POIs = pickle.load(f)
print(POIs)

# TP FN FP
evaluation = {}
for p in POIs:
    evaluation[p] = [0,0,0]
    
conf_mat = np.zeros([len(POIs),len(POIs)])


voting_rst = {}
with open(voting_pth, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        voting_rst[row[0]] = row[1]
        
gt_speakers = []
pred_speakers = []
ctr = 0
nonPOI_ctr = 0
POI_ctr = 0
correct = 0

for seg, speaker in voting_rst.items():
    gt = seg.split('/')[-1][:7]
    #print(gt)
    if gt in POIs:
        gt_speakers.append(gt)
    else:
        gt_speakers.append('other')
    pred_speakers.append(speaker)
    
    ctr += 1
    
    if gt in POIs:
        POI_ctr += 1
        gt_idx = POIs.index(gt)
        speaker_idx = POIs.index(speaker)
        if gt == speaker:
            correct = correct + 1
            evaluation[speaker][0] += 1
                    
        else:
            # FP
            evaluation[speaker][2] += 1
            # FN (for the gt speaker)
            evaluation[gt][1] += 1
                    
        conf_mat[gt_idx][speaker_idx] += 1
    else:
        evaluation[speaker][2] += 1
        nonPOI_ctr += 1
        continue

y_true = gt_speakers
y_pred = pred_speakers

        
gt_speakers = set(gt_speakers)
pred_speakers = set(pred_speakers)
print('# of gt_speaker: '+str(len(gt_speakers)))
print('# of pred_speaker: '+str(len(pred_speakers)))

diff = [x for x in pred_speakers if x not in gt_speakers]
print('non_POI in result:')
print(diff)

print('# associated utt: %d' % ctr)
print('# utt assigned to non_POI: %d' % nonPOI_ctr)
print('# utt assigned to POI: %d' % POI_ctr)


#print(correct)
accuracy = correct/ctr
print('>>> accuracy: %f' % accuracy)
#print(accuracy)
utts = []
with open(join('middle_data','meeting_utt.pk'),'rb') as f:
    p = pickle.load(f)
for v in p.values():
    utts.extend(v)
    
#num_lines = sum(1 for line in open(join('middle_data','list.txt')))
num_lines = len(utts)

coverage = ctr/num_lines
print('>>> coverage: %f' % coverage)


res = precision_recall_fscore_support(y_true, y_pred, average='macro')
print('>>> precision, recall')
print(res)
f1 = (2 * res[0] * res[1])/(res[0] + res[1])
print('>>> f1-score: %f' % f1)


