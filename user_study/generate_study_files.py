# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../')
import json
from explanation.rwr_explanation import explanation_items_rwr
from evaluation.eval_rwr import top_k_recs_rwr
import networkx as nx
from networkx.readwrite.gml import literal_destringizer
from elixir_utility.utils import get_file_name
import xlsxwriter
import copy
import operator


def add_rec_exps(user, output_data, ure, model='R', location='TW', dimension='D20'):
    for rec in ure[user]:
        if rec not in output_data[user]:
            output_data[user][rec] = {'explanations': {}, 'M': 0, 'R': 0}
        output_data[user][rec][model] = 1
        output_data[user][rec][dimension] = 1
        for exp, _ in ure[user][rec]:
            if exp not in output_data[user][rec]['explanations']:
                output_data[user][rec]['explanations'][exp] = {'M': 0, 'R': 0, 'TW': 0, 'BW': 0, 'TF': 0, 'BF': 0,
                                                               'P': 1}
            output_data[user][rec]['explanations'][exp][model] = 1
            output_data[user][rec]['explanations'][exp][location] = 1
            output_data[user][rec]['explanations'][exp][dimension] = 1
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


def read_recs(file_name, recs):
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            item_id = int(tabs[1])
            raing = int(float(tabs[3]))
            aspect = ''
            if len(tabs) > 5:
                for elem in tabs[5:]:
                    if elem != 'nan':
                        aspect += elem + ' '
            if user_id not in recs:
                recs[user_id] = {}
            recs[user_id][item_id] = {'rating': raing, 'aspect': aspect}


def read_pairs(file_name, pairs):
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            item1_id = int(tabs[1])
            item2_id = int(tabs[2])
            rating = int(tabs[3])
            aspect = tabs[5]
            comment = tabs[6]
            if user_id not in pairs:
                pairs[user_id] = {}
            if aspect == 'nan':
                aspect = ''
            if comment == 'nan':
                comment = ''
            pairs[user_id][frozenset((item1_id, item2_id))] = {'rating': rating, 'aspect': aspect, 'comment': comment}


def add_recs(users_recs, set_tag, seen_recs, rec_per_user, output_recs):
    for user in users_recs:
        if user not in output_recs:
            output_recs[user] = {}
        counter = 0
        for rec, _ in users_recs[user]:
            if rec in seen_recs[user]:
                counter += 1
                if counter == rec_per_user:
                    break
                else:
                    continue
            if rec not in output_recs[user]:
                output_recs[user][rec] = {'SR': 0, 'PTR': 0, 'PBR': 0, 'ETR': 0, 'EBR': 0}
            output_recs[user][rec][set_tag] = 1
            counter += 1
            if counter == rec_per_user:
                break



if __name__ == "__main__":
    dataset = 'movielens-user-study'
    path = 'YOUR PATH'
    num_users = 25
    train_ratio = 1
    rec_per_user = 30
    exp_per_rec = 3
    num_votes = 0
    dimension = 10

    # read the description file
    items_desc_file = path + "movies_features.txt"
    with open(items_desc_file) as json_file:
        items_desc_list = json.load(json_file)
    items_files = path + 'items.txt'
    users_file = path + "users.txt"
    user_id_name_map = id_name_map(users_file)
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

    # ---------------------------------- phase2 ---------------------------------
    # read recs and explanations for RWR
    users_scores_file = path + get_file_name('pr_users_scores', num_users, train_ratio)
    items_scores_file = path + get_file_name('pr_items_scores', num_users, train_ratio)
    graph_file = path + get_file_name('graph', num_users, train_ratio, 'gml')
    graph = nx.read_gml(graph_file, destringizer=literal_destringizer)
    rwr_ur = top_k_recs_rwr(users_scores_file, graph, rec_per_user)
    users = rwr_ur.keys()
    rwr_ure_good = explanation_items_rwr(items_scores_file, graph, rwr_ur, exp_per_rec)
    rwr_ure_bad = explanation_items_rwr(items_scores_file, graph, rwr_ur, exp_per_rec, location='bottom')

    # merging data {user: {rec: {explanations: {exp: {M: R: S: P: TW: BW: TF: BF:}} M: R:}}}
    output_data = {}
    for user in users:
        output_data[user] = {}
        # merge recs
        output_data = add_rec_exps(user, output_data, rwr_ure_good, model='R', location='TW')
        output_data = add_rec_exps(user, output_data, rwr_ure_bad, model='R', location='BW')

    # writing to files
    n_files = 6
    for i in range(1, n_files+1):
        workbook = xlsxwriter.Workbook(path + 'recs_exps_' + str(i) + '.xlsx')
        workbook_me = xlsxwriter.Workbook(path + 'recs_exps_me_' + str(i) + '.xlsx')
        black_format = workbook.add_format({'bold': False, 'font_color': 'black'})  #, 'text_wrap': True})
        red_format = workbook.add_format({'font_color': 'red', 'bold': True})
        for user in output_data:
            user_name = user_id_name_map[user]
            # print 'start wrting data for user', user_name
            worksheet = workbook.add_worksheet(user_name)
            worksheet_me = workbook_me.add_worksheet(user_name)
            row = 0
            # writing data for me
            worksheet_me.write_string(row, 0, 'Code')
            worksheet_me.write_string(row, 1, 'rec_id')
            worksheet_me.write_string(row, 2, 'exp_id')

            worksheet.write_string(row, 0, 'Recommendation')
            worksheet.write_string(row, 1, 'Recommendation link')
            worksheet.write_string(row, 2, 'Explanation')
            worksheet.write_string(row, 3, 'Explanation link')
            worksheet.write_string(row, 4, 'features/similarities')
            worksheet.write_string(row, 5, 'Question1')
            worksheet.write_string(row, 6, 'Rating')
            worksheet.write_string(row, 7, 'Question2')
            worksheet.write_string(row, 8, 'Answer (for example director, actor, genre or content)')
            worksheet.write_string(row, 9, 'Comments')


            row += 1
            all_recs = output_data[user].keys()
            chunck_size = len(all_recs) / n_files
            start = (i-1) * chunck_size
            end = start + chunck_size
            if i == n_files:
                end = len(all_recs)
            for rec in all_recs[start:end]:
                rec_code = generate_code({'M': output_data[user][rec]['M'], 'R': output_data[user][rec]['R']})
                # worksheet.write_string(row, 0, rec_code)
                # write data for me
                worksheet_me.write_string(row, 0, rec_code)
                worksheet_me.write_string(row, 1, str(rec))
                worksheet_me.write_string(row, 2, '')

                rec_link = items_id_link[rec]
                rec_name = items_links_name[rec_link]
                # worksheet.write_url(row, 0, rec_link, string=rec_name, cell_format=black_format)
                worksheet.write_string(row, 0, rec_name)
                worksheet.write_url(row, 1, rec_link)
                worksheet.write_string(row, 2, '---')
                worksheet.write_string(row, 3, '---')
                sims = find_sims(items_desc, rec=rec)
                worksheet.write_string(row, 4, str(sims.encode("utf-8")))
                worksheet.write_string(row, 5, 'Rate the rec (1-5):', cell_format=red_format)
                worksheet.write_string(row, 6, '')
                worksheet.write_string(row, 7, "What do(don't) you like?")
                worksheet.write_string(row, 8, '')
                worksheet.write_string(row, 9, '')
                # worksheet.write_string(row, 8, str(rec))
                # worksheet.write_string(row, 9, '')
                row += 1
                for exp in output_data[user][rec]['explanations']:
                    if exp in output_data[user]:
                        print 'error', user_name, exp
                    exp_code = generate_code(output_data[user][rec]['explanations'][exp])

                    # write data for me
                    worksheet_me.write_string(row, 0, exp_code)
                    worksheet_me.write_string(row, 1, str(rec))
                    worksheet_me.write_string(row, 2, str(exp))

                    exp_link = items_id_link[exp]
                    exp_name = items_links_name[exp_link]
                    # worksheet.write_url(row, 0, rec_link, string=rec_name, cell_format=black_format)
                    worksheet.write_string(row, 0, rec_name)
                    worksheet.write_url(row, 1, rec_link)
                    worksheet.write_string(row, 2, exp_name)
                    worksheet.write_url(row, 3, exp_link)
                    sims = find_sims(items_desc, rec=rec, exp=exp)
                    worksheet.write_string(row, 4, sims)
                    worksheet.write_string(row, 5, 'Like the sim between rec and exp? (0/1)')
                    worksheet.write_string(row, 6, '')
                    worksheet.write_string(row, 7, "What do(don't) you like?")
                    worksheet.write_string(row, 8, '')
                    worksheet.write_string(row, 9, '')

                    row += 1
        workbook.close()
        workbook_me.close()

    # ------------------------------- phase 3 --------------------------------
    setup_postfix = '_rec_' + str(rec_per_user) + '_v_' + str(num_votes)
    graph_file = path + get_file_name('graph', num_users, train_ratio, 'gml')
    graph = nx.read_gml(graph_file, destringizer=literal_destringizer)
    updated_graph_file = path + get_file_name('graph' + setup_postfix, num_users, train_ratio, 'gml')
    updated_graph = nx.read_gml(updated_graph_file, destringizer=literal_destringizer)
    data_path = path
    # read the already recommended items
    seen_recs = {}
    recs_file = path + 'test_users_25_partition_0.txt'
    read_recs(recs_file, seen_recs)
    rec_per_user = 30


    # RWR: single, pair (T, B), pair + single (T, B)
    scores_files = [
        data_path + get_file_name('pr_users_scores'+setup_postfix, num_users, train_ratio, 'txt'),
        path + get_file_name('updated_pr_users_scores', num_users, train_ratio, 'txt'),
        path + get_file_name('updated_pr_users_scores_bottom', num_users, train_ratio, 'txt'),
        path + get_file_name('updated_pr_users_scores'+setup_postfix, num_users, train_ratio,
                      'txt'),
        path + get_file_name('updated_pr_users_scores'+setup_postfix+'_bottom', num_users,
                      train_ratio, 'txt'),
    ]
    file_tags = ['SR', 'PTR', 'PBR', 'ETR', 'EBR']
    output_recs = {}
    for i in range(len(scores_files)):
        file_tag = file_tags[i]
        file_name = scores_files[i]
        users_recs = top_k_recs_rwr(file_name, updated_graph, rec_per_user)
        add_recs(users_recs, file_tag, seen_recs, rec_per_user, output_recs)

    # writing recs to file
    n_files = 1
    for i in range(1, n_files+1):
        workbook = xlsxwriter.Workbook(data_path + 'phase3/recs_' + str(i) + '.xlsx')
        workbook_me = xlsxwriter.Workbook(data_path + 'phase3/recs_me_' + str(i) + '.xlsx')
        black_format = workbook.add_format({'bold': False, 'font_color': 'black'})  #, 'text_wrap': True})
        red_format = workbook.add_format({'font_color': 'red', 'bold': True})
        for user in output_recs:
            print user, len(output_recs[user])
            user_name = user_id_name_map[user]
            # print 'start wrting data for user', user_name
            worksheet = workbook.add_worksheet(user_name)
            worksheet_me = workbook_me.add_worksheet(user_name)
            row = 0
            # writing data for me
            worksheet_me.write_string(row, 0, 'Code')
            worksheet_me.write_string(row, 1, 'rec_id')

            worksheet.write_string(row, 0, 'Recommendation')
            worksheet.write_string(row, 1, 'Recommendation link')
            worksheet.write_string(row, 2, 'features')
            worksheet.write_string(row, 3, 'Question1')
            worksheet.write_string(row, 4, 'Rating')
            worksheet.write_string(row, 5, 'Comments')

            row += 1
            all_recs = output_recs[user].keys()
            chunck_size = len(all_recs) / n_files
            start = (i-1) * chunck_size
            end = start + chunck_size
            if i == n_files:
                end = len(all_recs)
            for rec in all_recs[start:end]:
                rec_code = generate_code(output_recs[user][rec])
                # write data for me
                worksheet_me.write_string(row, 0, rec_code)
                worksheet_me.write_string(row, 1, str(rec))

                rec_link = items_id_link[rec]
                rec_name = items_links_name[rec_link]
                # worksheet.write_url(row, 0, rec_link, string=rec_name, cell_format=black_format)
                worksheet.write_string(row, 0, rec_name)
                worksheet.write_url(row, 1, rec_link)
                sims = find_sims(items_desc, rec=rec)
                worksheet.write_string(row, 2, str(sims.encode("utf-8")))
                worksheet.write_string(row, 3, 'Rate the rec (1-5):')
                worksheet.write_string(row, 4, '')
                worksheet.write_string(row, 5, '')
                row += 1
        workbook.close()
        workbook_me.close()