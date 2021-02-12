# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../')
import json
from explanation.mf_explanations import explanation_items_mf
from explanation.rwr_explanation import explanation_items_rwr
from evaluation.eval_mf import top_k_recs_mf
from evaluation.eval_rwr import top_k_recs_rwr
import networkx as nx
from networkx.readwrite.gml import literal_destringizer
from simulation.data_split import get_file_name
import numpy as np
from evaluation.eval import get_users_data
import xlsxwriter
import copy
import operator
import pandas as pd


def add_rec_exps(user, output_data, ure, model='R', location='TW'):
    for rec in ure[user]:
        if rec not in output_data[user]:
            output_data[user][rec] = {'explanations': {}, 'M': 0, 'R': 0}
        output_data[user][rec][model] = 1
        for exp, _ in ure[user][rec]:
            if exp not in output_data[user][rec]['explanations']:
                output_data[user][rec]['explanations'][exp] = {'M': 0, 'R': 0, 'TW': 0, 'BW': 0, 'TF': 0, 'BF': 0,
                                                               'P': 1}
            output_data[user][rec]['explanations'][exp][model] = 1
            output_data[user][rec]['explanations'][exp][location] = 1
    return output_data


def id_name_map(file_name, id_type='int'):
    output = {}
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            name = tabs[0]
            id_ = tabs[1]
            if id_type == 'int':
                id_ = int(id_)
            output[id_] = name
    return output


def generate_code(d):
    res = []
    for k in d:
        if d[k] == 1:
            res.append(k)
    return '-'.join(res)


def find_sims(items_desc, rec=None, exp=None):
    features = items_desc[rec]
    tags = features['tags']
    genres = features['genres']
    directors = features['directors']
    cast = features['cast']
    tag_header = 'content: '
    genres_header = 'genre: '
    directors_header = 'director: '
    cast_header = 'actor: '
    if exp is not None:
        exp_features = items_desc[exp]
        tags = list(set(tags) & set(exp_features['tags']))
        genres = list(set(genres) & set(exp_features['genres']))
        directors = list(set(directors) & set(exp_features['directors']))
        cast = list(set(cast) & set(exp_features['cast']))
        tag_header = 'similar content: '
        genres_header = 'similar genre: '
        directors_header = 'similar director: '
        cast_header = 'similar actor: '
    tags_string = ', '.join(tags[:5])
    genres_string = ', '.join(genres[:5])
    directors_string = ', '.join(directors[:5])
    cast_string = ', '.join(cast[:5])
    # p1 =  tag_header + ' ' + tags_string + '-----' + genres_header + ' ' + genres_string + '-----'
    # p2 = directors_header + ' ' + directors_string + '-----' + cast_header + ' ' + cast_string
    res = []
    if directors_string != '':
        res.append(directors_header + directors_string)
    if cast_string != '':
        res.append(cast_header + cast_string)
    if genres_string != '':
        res.append(genres_header + genres_string)
    if tags_string != '':
        res.append(tag_header + tags_string)

    return '------'.join(res)


if __name__ == "__main__":
    dataset = 'movielens-user-study'
    path = "YOUR PATH"
    res_path = path + 'phase2/'
    num_users = 25
    train_ratio = 1
    rec_per_user = 30
    exp_per_rec = 5
    rwr_tf_file = res_path + 'RWR_feedback_top.txt'
    rwr_bf_file = res_path + 'RWR_feedback_bottom.txt'
    rwr_recs_phase_2 = res_path + 'RWR_rated_recs_phase_2.txt'
    num_files = 6

    # --------------- read the description file + other auxiliary files --------------
    items_desc_file = path + "movies_features.txt"
    with open(items_desc_file) as json_file:
        items_desc_list = json.load(json_file)
    items_files = path + 'items.txt'
    users_file = path + "users.txt"
    user_id_name_map = id_name_map(users_file)
    users_name_id_map = {v: k for k, v in user_id_name_map.items()}
    items_id_link = id_name_map(items_files)
    items_link_id = {val: key for key, val in items_id_link.items()}
    items_links_name = {}
    items_desc = {}
    for item_dict in items_desc_list:
        link = item_dict['link']
        name = item_dict['name']
        items_links_name[link] = name
    for item_dict in items_desc_list:
        item_id = items_link_id[item_dict['link']]
        items_desc[item_id] = copy.deepcopy(item_dict)
        # remove empty strings and replace tags dict with tags array
        tags_dict = items_desc[item_id]['tags']
        tags_count_sorted = sorted(tags_dict.items(), key=operator.itemgetter(1), reverse=True)
        tags = [e[0] for e in tags_count_sorted]
        items_desc[item_id]['tags'] = list(tags)

        if '' in items_desc[item_id]['genres']:
            items_desc[item_id]['genres'].remove('')

        if '' in items_desc[item_id]['cast']:
            items_desc[item_id]['cast'].remove('')

        if '' in items_desc[item_id]['directors']:
            items_desc[item_id]['directors'].remove('')

    # ------------------- generating feedback pair files phase 2 + extended training files  --------------------
    # ---- read the files
    rating_files = ['recs_exps_'+str(i)+'.xlsx' for i in range(num_files)]
    meta_data_files = ['recs_exps_me_'+str(i)+'.xlsx' for i in range(num_files)]

    with open(rwr_tf_file, 'w') as ft_rwr, \
        open(rwr_bf_file, 'w') as fb_rwr, \
        open(rwr_recs_phase_2, 'w') as f_rwr:
        f_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
        ft_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
        fb_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
        for f1, f2 in zip(rating_files, meta_data_files):
            print 'feedback file', f1
            f1_file = pd.ExcelFile(res_path + f1)
            dfs_1 = {sheet_name: f1_file.parse(sheet_name)
                   for sheet_name in f1_file.sheet_names}
            f2_file = pd.ExcelFile(res_path + f2)
            dfs_2 = {sheet_name: f2_file.parse(sheet_name)
                   for sheet_name in f2_file.sheet_names}
            for sheet_name in dfs_1:
                user_id = users_name_id_map[str(sheet_name)]
                # read the code
                codes = dfs_2[sheet_name]['Code']
                ratings = dfs_1[sheet_name]['Rating']
                rec_ids = dfs_2[sheet_name]['rec_id']
                exp_ids = dfs_2[sheet_name]['exp_id']
                comments = dfs_1[sheet_name]['Comments']
                answers = dfs_1[sheet_name]['Answer (for example director, actor, genre or content)']
                aspects = dfs_1[sheet_name]['features/similarities']
                row = 0
                for code in codes:
                    rec_id = int(rec_ids[row])
                    try:
                        rating = int(ratings[row])
                    except:
                        print sheet_name, row, 'int opr invalid', ratings[row], f1
                        rating = -1
                    comment = str(comments[row]).strip()
                    answer = str(answers[row]).strip()
                    if answer == 'nan':
                        print sheet_name, row, 'no valid answer', f1
                    aspect = aspects[row]
                    if 'P' not in code:
                        if rating not in [1, 2, 3, 4, 5]:
                            print sheet_name, row, 'no valid rating', ratings[row], f1
                            row += 1
                            continue

                        if 'R' in code:
                            f_rwr.write('\n')
                            f_rwr.write('%d\t%d\t%s\t%d\t%s\t%s\t%s' % (user_id, rec_id, '', rating, aspect, answer, comment))
                    else:
                        if rating not in [0, 1]:
                            print sheet_name, row, 'no valid feedback', ratings[row], f1

                        exp_id = int(exp_ids[row])
                        if rating == 0:
                            rating = -1

                        if 'TW' in code:
                            ft_rwr.write('\n')
                            ft_rwr.write('%d\t%d\t%d\t%d\t%s\t%s\t%s' % (user_id, rec_id, exp_id, rating, aspect,
                                                                         answer, comment))
                        if 'BW' in code:
                            fb_rwr.write('\n')
                            fb_rwr.write('%d\t%d\t%d\t%d\t%s\t%s\t%s' % (user_id, rec_id, exp_id, rating, aspect,
                                                                         answer, comment))
                    row += 1

    # ------------------- generating all_rated_recs_phase_3.txt  --------------------
    # ---- read the files
    rwr_recs_phase_3 = path + 'phase3/recs_phase3_1.xlsx'
    meta_data_phase3 = path + 'phase3/recs_phase3_me_1.xlsx'
    phase3_recs = path + 'all_rated_recs_phase3_complete.txt'

    with open(phase3_recs, 'w') as f_rwr:
        f_rwr.write('user\titem\ttimestamp\trating\taspects\tcomment')
        f1_file = pd.ExcelFile(rwr_recs_phase_3)
        dfs_1 = {sheet_name: f1_file.parse(sheet_name)
                     for sheet_name in f1_file.sheet_names}
        f2_file = pd.ExcelFile(meta_data_phase3)
        dfs_2 = {sheet_name: f2_file.parse(sheet_name)
                     for sheet_name in f2_file.sheet_names}
        for sheet_name in dfs_1:
            user_id = users_name_id_map[str(sheet_name)]
            # read the code
            codes = dfs_2[sheet_name]['Code']
            ratings = dfs_1[sheet_name]['Rating']
            rec_ids = dfs_2[sheet_name]['rec_id']
            comments = dfs_1[sheet_name]['Comments']
            print sheet_name
            aspects = dfs_1[sheet_name]['features']
            row = 0
            for code in codes:
                rec_id = int(rec_ids[row])
                try:
                    rating = int(ratings[row])
                except:
                    print sheet_name, row, 'int opr invalid', ratings[row]
                    rating = -1
                comment = str(comments[row]).strip()
                aspect = aspects[row]
                if rating not in [1, 2, 3, 4, 5]:
                    print sheet_name, row, 'no valid rating', ratings[row]
                    row += 1
                    continue
                f_rwr.write('\n')
                f_rwr.write('%d\t%d\t%s\t%d\t%s\t%s' % (user_id, rec_id, '', rating, aspect, comment))
                row += 1
