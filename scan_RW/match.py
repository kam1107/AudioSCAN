import os
from os.path import join
import numpy as np
from collections import Counter
import pickle

root_dir = os.getcwd()
WAV = join(root_dir, 'WAV')
XVEC = join(root_dir, 'XVEC')

meetings = []
with open(WAV, 'r') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip('\n')
        m = line[:35]
        
        meetings.append(m)
        
key = Counter(meetings).keys()
freq = Counter(meetings).values()
meeting_count = dict(zip(key, freq))
meeting_count

# parse all vectors to each meeting and save as npy
vec = np.loadtxt(XVEC, dtype=float)

for meeting, count in meeting_count.items():
    c_vec = np.split(vec, [count])[0]
    if os.path.exists(join(root_dir, 'middle_data', meeting, 'vec%s.npy' % meeting)):
        os.remove(join(root_dir, 'middle_data', meeting, 'vec%s.npy' % meeting))
    
    np.save(join(root_dir, 'middle_data', meeting, 'vec%s.npy' % meeting), c_vec)
    
    vec = np.split(vec, [count])[1]


 # write the path to each vector (in each meeting) as a pickle file
path = []
with open(WAV, 'r') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip('\n')
        l = line.split(' ')[0]
        meeting = l[:35]
        print(meeting)
        seg_len = len(l) - (len(meeting) + 1)
        seg = l[-seg_len:]
        print(seg)
        path.append(join(root_dir, 'middle_data', '%s/segs/%s.wav' % (meeting, seg)))

for meeting, count in meeting_count.items():
    c_path = np.split(path, [count])[0]
    if os.path.exists(join(root_dir, 'middle_data', meeting, 'segs%s.pk' % meeting)):
        os.remove(join(root_dir, 'middle_data', meeting, 'segs%s.pk' % meeting))
        
    with open(join(root_dir, 'middle_data', meeting, 'segs%s.pk' % meeting), 'wb') as f:
            pickle.dump(c_path, f)
    
    path = np.split(path, [count])[1]





