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

dimension=200
hyper_para=15
para = float(hyper_para)/100

copy_seg = True

project_dir = os.getcwd()
print(project_dir)
with open(join(project_dir, 'config.yaml'), 'r') as f:
    cfg = yaml.load(f)
    

origin_data_path = join(project_dir, cfg['base_conf']['origin_data_path'])
middle_data_path = join(project_dir, cfg['base_conf']['middle_data_path'])
all_meetings = []

wifi_files = tools.get_format_file(origin_data_path, 1, r'.+\.txt$')
for file in wifi_files:
    names = re.split(r'\/|\.|\\', file)
    name = names[-2]
    all_meetings.append(name)


def find_mac_use_name(name):
    mac = []
    for key, value in cfg['mac_name'].items():
        if value == name:
            mac.append(key)
    return mac

def get_rssi_list(target_mac, wifi_file):
    rssi_list = []
    with open(wifi_file, 'r') as w:
        w_lines = w.readlines()
        for w_line in w_lines:
            w_line = w_line.strip('\n')
            w = w_line.split('\t')
            if target_mac in w:
                rssi_list.append(int(w[2]))
    return rssi_list
    
def find_rssi_median(target_mac, wifi_file):
    rssi_list = get_rssi_list(target_mac, wifi_file)
    rssi_list.sort()
    idx = int(len(rssi_list) * 3 / 4)
    if not rssi_list:
        return 1
    else:
        return int(median(rssi_list))
        #return rssi_list[idx]
    
# find each participants' rssi in a wifi file    
def get_all_stat_in_file(path):
    stat = {}
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip('\n')
            l = line.split('\t')
            if len(l) == 2 or l[2] == '':
                continue
            try:
                strength = int(l[2])
            except:
                nums = l[2].split(',')
                strength = max(nums, key=lambda x: int(x))
                strength = int(strength)

            if l[1] not in stat:
                stat[l[1]] = []
            stat[l[1]].append(int(l[2]))
    return stat
    
def get_all_median_in_file(path):
    stat = get_all_stat_in_file(path)
    med = {}
    for k, v in stat.items():
        #stat[k].sort()
        #idx = int(len(stat[k]) * 3 / 4)
        #med[k] = stat[k][idx]
        med[k] = int(median(stat[k]))

    return med

def copy_segments(header, para, cycle_num, result_dir):
    if copy_seg:
        if os.path.exists(join(result_dir, '%s_%d_%d' % (header, int(para*100), cycle_num))):
            rmtree(join(result_dir, '%s_%d_%d' % (header, int(para*100), cycle_num)))
        os.mkdir(join(result_dir, '%s_%d_%d' % (header, int(para*100), cycle_num)))
        for k, v in final_res.items():
            index = 0
            print('####### '+k)
            if not k=='':
                os.mkdir(join(result_dir, '%s_%d_%d'%(header, int(para*100), cycle_num), k))
            
                for dur in v:
                    for paths in v[dur]:
                        # for path in paths:
                        s_seg_name = tools.get_parent_folder_name(paths, 1)
                        s_meet_name = tools.get_parent_folder_name(paths, 3)
                        copyfile(join(middle_data_path, s_meet_name, 'segs', s_seg_name),
                                 join(result_dir, '%s_%d_%d'%(header, int(para*100), cycle_num), k, '%s_%d.wav'%(k, index)))
                        index += 1
    else:
        if '%d_%d'%(int(para*100), add_num) == '':
            if os.path.exists(join(project_dir, 'final_result', '%s_%d_%d' % (header, int(para*100), cycle_num))):
                rmtree(join(project_dir, 'final_result', '%s_%d_%d' % (header, int(para*100), cycle_num)))
            os.mkdir(join(project_dir, 'final_result', '%s_%d_%d' % (header, int(para*100), cycle_num)))
            for k, v in final_res.items():
                index = 0
                os.mkdir(join(project_dir, 'final_result', '%s_%d_%d' % (header, int(para*100), cycle_num), k))
                for dur in v:
                    for paths in v[dur]:
                        # for path in paths:
                        s_seg_name = tools.get_parent_folder_name(paths, 1)
                        s_meet_name = tools.get_parent_folder_name(paths, 3)
                        copyfile(join(middle_data_path, s_meet_name, 'segs', s_seg_name), 
                                 join(project_dir, 'final_result', '%s_%d_%d' % (header, int(para*100), cycle_num), 
                                          k, '%s_%d.wav' % (k, index)))
                        index += 1


def check_converge(old_header, header, cycle_num, result_dir):
    # check two csv file, if no change then converge
    old_csv = {}
    new_csv = {}
    with open(join(result_dir, '%s_%d_%d.csv'%(old_header, int(para*100), cycle_num-1)), 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            old_csv[row[0]] = row[1]
        
    with open(join(result_dir, '%s_%d_%d.csv'%(header, int(para*100), cycle_num)), 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            new_csv[row[0]] = row[1]
            
    
    for k,v in old_csv.items():
        try:
            if new_csv[k] != v:
                print(k)
        except:
            print('new file no '+k)
        
    return old_csv == new_csv

def generate_participants_per_meeting(header, para, cycle_num):
    all_meeting_people_name = {}
    for file in os.listdir(origin_data_path):
        if not file.startswith('.'):
            meeting = splitext(file)[0]
            meeting_middle_data_path = join(middle_data_path, meeting)
            meeting_path = join(origin_data_path, meeting + '.txt')

            if not os.path.exists(meeting_middle_data_path):
                os.mkdir(meeting_middle_data_path)
            
            th = cfg['pre_process']['wifi_threshold']

            try:
                medians = get_all_median_in_file(meeting_path)
    
                y_lable = []
                all_meeting_people_name[meeting] = []
                
                for k in medians.keys():
                    if k in cfg['mac_name'].keys():
                        y_lable.append(cfg['mac_name'][k])
                        all_meeting_people_name[meeting].append(cfg['mac_name'][k])
    
                print('Finish meeting people name of meeting %s'%meeting)
            except KeyError:
                print('Can not find wifi data file!')
            except RuntimeError('Invalid DISPLAY variable'):
                print('Cannot plot wifi... Remember add plt.switch_backend(\`agg\`) after import matplotlib.pyplot as plt ')

    return all_meeting_people_name


def update_personal_distribution(old_header, header, para, cycle_num, result_dir):
    distribution = {}
    if cycle_num == 0:
        # initialize personal rssi threshold using config file
        for k in cfg['mac_name'].keys():
            distribution[k] = [cfg['pre_process']['wifi_threshold']]
    else:
        # gather attendance info (in which meeting did person A attend)
        attendance = {}
        with open(join(result_dir, '%s_%d_%d.csv'%(old_header, int(para*100), cycle_num-1)), 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[1] not in attendance:
                    attendance[row[1]] = []
                attendance[row[1]].append(tools.get_parent_folder_name(row[0], 3))
            
        in_meeting = {}
        for k, v in attendance.items():
            in_meeting[k] = []
            meetings = list(set(v))
            for m in meetings:
                #if v.count(m) > 15:
                in_meeting[k].append(m)
                    
        out_meeting = {}
        for k, v in in_meeting.items():
            out_meeting[k] = [x for x in all_meetings if x not in v]
        
        # find hard threshold for each mac addr
        meds = {}
        for k, v in in_meeting.items():
            if len(v) > 0:
                macs = find_mac_use_name(k)
                for mac in macs:
                    meds[mac] = []
                    # find median of each meeting that person A attend
                    for m in v:
                        wifi_file = join(origin_data_path,'%s.txt'%m)
                        if find_rssi_median(mac, wifi_file) < 0:   
                            meds[mac].append(find_rssi_median(mac, wifi_file)) 
        
        meds_thres = {}
        # if the label is wrongly assigned, use the initial threshold 
        # (i.e. the meetings where these segs are from does not have this person's mac addr)
        for k in cfg['mac_name'].keys():
            meds_thres[k] = cfg['pre_process']['wifi_threshold']
        for k, v in meds.items():
            if len(v) > 0:
                meds_thres[k] = min(meds[k])
            
        # for each person, collect all rssi when he attend meeting and all rssi when he doesn't
        all_rssi_in_meeting = {}  
        all_rssi_out_meeting = {}
        for k in in_meeting.keys():
            target_macs = find_mac_use_name(k)
            for mac in target_macs:
                all_rssi_in_meeting[mac] = []
                for m in in_meeting[k]:
                    wifi_file = join(origin_data_path,'%s.txt'%m)
                    all_rssi_in_meeting[mac].extend(get_rssi_list(mac, wifi_file))
            
                all_rssi_out_meeting[mac] = []
                for m in out_meeting[k]:
                    wifi_file = join(origin_data_path,'%s.txt'%m)
                    all_rssi_out_meeting[mac].extend(get_rssi_list(mac, wifi_file))
       
        # initialize dist to heard threshold
        for k in cfg['mac_name'].keys():
            distribution[k] = [meds_thres[k]]
        
        # fit a gaussian on stats of each mac addr (in meeting)
        for k in all_rssi_in_meeting.keys():
            # if this person has both in_meeting and out_meeting distribution, save these two distributions           
            if (len(all_rssi_in_meeting[k]) > 0 and len(all_rssi_out_meeting[k]) > 0):
                m_in, std_in = stats.norm.fit(all_rssi_in_meeting[k])
                m_out, std_out = stats.norm.fit(all_rssi_out_meeting[k])
                distribution[k] = [m_in, std_in, len(all_rssi_in_meeting[k]), m_out, std_out, len(all_rssi_out_meeting[k])]
            
                
    print('>>> finish update distribution')
    print(distribution)
 
    # update personal median
    with open(join(result_dir, 'dist%s_%d_%d.pk' % (header, int(para*100), cycle_num)), 'wb') as f:
            pickle.dump(distribution, f, protocol=pickle.HIGHEST_PROTOCOL)
        

def compute_prob_from_dist(m_in, std_in, num_in, m_out, std_out, num_out, med):
    if med > m_in:
        return 1
    elif med < m_out:
        return 0
    else:
        prior_in = float(num_in/(num_in + num_out))
        prior_out = float(num_out/(num_in + num_out))
        likelihood_in = float(stats.norm(m_in, std_in).pdf(med))
        likelihood_out = float(stats.norm(m_out, std_out).pdf(med))
        posterior_in = likelihood_in * prior_in
        posterior_out = likelihood_out * prior_out
        # normalize
        return (posterior_in/(posterior_in+posterior_out))
        

def find_participant_prob(header, para, cycle_num, meeting, person, result_dir):
    with open(join(result_dir, 'dist%s_%d_%d.pk' % (header, int(para*100), cycle_num)), 'rb') as f:
        personal_dist = pickle.load(f)
    
    macs = find_mac_use_name(person)
    for m in macs:
        wifi_file = join(origin_data_path,'%s.txt'%meeting)
        med = find_rssi_median(m, wifi_file)
        if med > 0:
            continue
        else:
            # if only has hard threshold
            dist = personal_dist[m]
            if len(dist) == 1:
                if med >= dist[0]:
                    return 1
                else:
                    return 0
            # if has distribution
            else:
                return compute_prob_from_dist(dist[0], dist[1], dist[2], dist[3], dist[4], dist[5], med)


                
for hyper in range(0, 22, 2):
    print('>>> ' + str(hyper))
    old_header = ''
    os.mkdir(join(project_dir, 'final_result', 'hyper0.%d'%hyper))
    result_dir = join(project_dir, 'final_result', 'hyper0.%d'%hyper)
    print('>>> '+ str(result_dir))
    
    # clear all pngs in middle data
    filelist = [os.path.join(subdir, filename) for subdir, dirs, files in os.walk(middle_data_path) for filename in files if filename.endswith('.png')]
    if len(filelist) > 0:
        for png in filelist:
            os.remove(png)
    print('>>> remove png: '+ str(len(filelist)) + ' pics')
    
    for cycle_num in range(1):
        header = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')
        
        # initialize or update personal rssi threshold
        update_personal_distribution(old_header, header, para, cycle_num, result_dir)

        # generate .png files in middle_data_path
        all_meeting_people_name = generate_participants_per_meeting(header, para, cycle_num)
        
        # get people, meeting info, make context info 
        middle_data_path = join(project_dir, cfg['base_conf']['middle_data_path'])

        # meeting_npy_paths, the npy path that contains feature vectors, after running feature_extraction_classification.py
        meeting_npy_paths = tools.get_meeting_and_path(middle_data_path, r'.+\.npy$')
        middle_seg_path = tools.get_meeting_and_path(middle_data_path, r'.+\.pk$')
            

        #all_meeting_people_name = tools.get_meeting_people_name(middle_data_path, '%d'%(cycle_num))
        people = []
        for k, v in all_meeting_people_name.items():
            all_meeting_people_name[k] = [p for p in v if p not in cfg['filter_people']]

        for p in all_meeting_people_name.values():
            people.extend(p)
        people = list(set(people))
        people.sort()
        people_num = len(people)
        print(people)

        
        # get meeting names and index meetings
        meeting_name = list(all_meeting_people_name.keys())
        meeting_name.sort()
        meeting_num = len(all_meeting_people_name)
        meeting_index = dict(zip(meeting_name, list(range(meeting_num))))
            
        # generate context info (who participate which meeting)
        context_info_init = np.zeros([meeting_num, people_num]).astype(np.float64)

        for k, v in all_meeting_people_name.items():
            for name in v:
                # find probability of a participant attending this meeting from distribution
                context_info_init[meeting_index[k], people.index(name)] = find_participant_prob(header, para, cycle_num, k, name, result_dir)
        # remove person who has all zero participant
        del_i = 0
        for i in range(len(context_info_init[0])):
            if all(v == 0 for v in context_info_init[:,i]):
                del people[i-del_i]
                del_i = del_i + 1
        context_info = context_info_init[:,~(context_info_init==0).all(0)]
        people_num = len(people)
        print('>>> after removing all-zero participants')
        print(people_num)
        print(len(context_info[0]))
            
        
        # match xvector with its segment
        seg_info = np.empty([0, dimension])
        seg_paths = []
        file_paths = list(middle_seg_path.keys())
        file_paths.sort()
        for k in file_paths:
            with open(middle_seg_path[k], 'rb') as f:
                seg_path = pickle.load(f)
                seg_paths.extend(seg_path)
                xvec = np.load(meeting_npy_paths[k])
                try:
                    seg_info = np.vstack((seg_info, xvec))
                except:
                    print(k)
        
        
        # concatenate features and participant vector (ctx information)
        seg_features = []
        print('start translate')
        for feature, path in zip(seg_info, seg_paths):
            parent = tools.get_parent_folder_name(path, 3)
            c = parent.split('_')
            try:
                li = list(map(lambda x: x * para, context_info[meeting_index['%s_%s' % (c[0], c[1])]]))
                temp = np.concatenate((feature, li), axis=0)
            except:
                print('err')
            seg_features.append(temp)
        print('finish translate')
        
        # clustering, varying the number of clusters by adding different number of `participants' (to account for
        # the presence of non-people-of-interest
        
        # event vector of clusters
        #seg_people_in_meetings = np.zeros([people_num+add_num, meeting_num])
        # event vector of MAC addresses
        wifi_people_in_meetings = np.zeros([people_num, meeting_num])
            
        for i in range(people_num):
            for name in meeting_name:
                wifi_people_in_meetings[i, meeting_index[name]] = context_info[meeting_index[name],i]
            
        print('start SCAN for fraction {}'.format(hyper/10))
        final_res, save_matrix = tools.scan_func(seg_features, seg_paths, wifi_people_in_meetings, people,
                                                 seg_info, meeting_index, meeting_num, 
                                                 hyper_para=hyper/10, frac_start=0.9)
        print('finish SCAN for fraction {}'.format(hyper/10))
        
                    
        with open(join(result_dir, '%d_%d_center.pk'%(int(para*100), cycle_num)), 'wb') as f:
            pickle.dump(save_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)
                
        with open(join(result_dir, '%s_%d_%d.csv'%(header, int(para*100), cycle_num)), 'w') as f:
            for k, v in final_res.items():
                for dur in v:
                    for paths in v[dur]:
                        # for path in paths:
                        f.write('%s,%s\n'%(paths, k))
            
        copy_segments(header, para, cycle_num, result_dir)
                            
        # check converge
        if cycle_num > 0:
            if check_converge(old_header, header, cycle_num, result_dir):
                print('converge')
                break
        
        old_header = header
    
        
        




