# -*- coding: utf-8 -*-
import sys
import json
import networkx as nx
sys.path.append('../')
import xlsxwriter
import copy
import operator

from explanation.rwr_explanation import explanation_items_rwr
from evaluation.eval_rwr import top_k_recs_rwr
from networkx.readwrite.gml import literal_destringizer
from elixir_utility.utils import get_file_name
from evaluation.eval import get_users_data


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


def find_sims_movies(items_desc, rec=None, exp=None):
    features = items_desc[rec]
    tags = features['tags']
    genres = features['genres']
    directors = features['directors']
    cast = features['cast']
    tag_header = 'content: '
    genres_header = 'genre: '
    directors_header = 'director: '
    cast_header = 'actor: '
    common_features = 5

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

    tags_string = ', '.join(tags[:common_features])
    genres_string = ', '.join(genres[:common_features])
    directors_string = ', '.join(directors[:common_features])
    cast_string = ', '.join(cast[:common_features])

    res = []
    if directors_string != '':
        res.append(directors_header + directors_string)
    if cast_string != '':
        res.append(cast_header + cast_string)
    if genres_string != '':
        res.append(genres_header + genres_string)
    if tags_string != '':
        res.append(tag_header + tags_string)

    return ' ------ '.join(res)


def find_sims_books(items_desc, rec=None, exp=None):
    features = items_desc[rec]
    genres = features['tags']
    authors = features['authors']
    genres_header = 'genre(s): '
    authors_header = 'author(s): '
    common_features = 5

    if exp is not None:
        exp_features = items_desc[exp]
        genres = list(set(genres) & set(exp_features['tags']))
        authors = list(set(authors) & set(exp_features['authors']))
        genres_header = 'same genre(s): '
        authors_header = 'same author(s): '

    genres_string = ', '.join(genres[:common_features])
    authors_string = ', '.join(authors[:common_features])

    res = []
    if genres_string != '':
        res.append(genres_header + genres_string)
    if authors_string != '':
        res.append(authors_header + authors_string)

    return ' ------ '.join(res)


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
    path = "YOUR_PATH" + dataset + '-data/'
    score_path = "YOUR_PATH"
    phase = 2
    num_users = 25
    train_ratio = 1
    rec_per_user = 30
    exp_per_rec = 5
    num_votes = 0
    dimension = 20
    extra_c = -1
    if dataset == 'goodreads-user-study':
        extra_c = 0  # extra column for book description

    if dataset == 'movielens-user-study':
        # read the description file for movies
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

    elif dataset == 'goodreads-user-study':
        # read the features file for books
        books_desc_text = {}
        items_desc_file = path + "books_features_updated.txt"
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
            name = item_dict['title']
            items_links_name[link] = name
        for item_dict in items_desc_list:
            item_id = items_link_id[item_dict['link']]
            items_desc[item_id] = copy.deepcopy(item_dict)
            tags_dict = items_desc[item_id]['tags']
            tags_count_sorted = sorted(tags_dict.items(), key=operator.itemgetter(1), reverse=True)
            tags = [e[0] for e in tags_count_sorted]
            items_desc[item_id]['tags'] = list(tags)

        # read the book description
        book_desc_file = path + "books_descriptions.txt"
        books_desc_text = {}
        with open(book_desc_file, 'r') as f_in:
            next(f_in)
            for line in f_in:
                tabs = line.strip().split('\t')
                if len(tabs) >= 2:
                    books_desc_text[tabs[0]] = tabs[1].replace('&apos;', '')
                else:
                    books_desc_text[tabs[0]] = 'No description found.'

    # ---------------------------------- phase2 ---------------------------------
    if phase == 2:
        # read recs and explanations for RWR
        users_scores_file = path + get_file_name('pr_users_scores_d_'+str(dimension), num_users, train_ratio)
        items_scores_file = path + get_file_name('pr_items_scores_d_'+str(dimension), num_users, train_ratio)
        graph_file = path + get_file_name('graph_d_'+str(dimension), num_users, train_ratio, 'gml')
        graph = nx.read_gml(graph_file, destringizer=literal_destringizer)
        train_data = get_users_data(path + get_file_name('train_d_' + str(dimension), num_users, train_ratio))
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
        path += 'phase2/'
        n_files = 5
        for i in range(1, n_files+1):
            workbook = xlsxwriter.Workbook(path+ 'recs_exps_' + str(i) + '.xlsx')
            workbook_me = xlsxwriter.Workbook(path + 'recs_exps_me_' + str(i) + '.xlsx')
            black_format = workbook.add_format({'bold': False, 'font_color': 'black'})
            red_format = workbook.add_format({'font_color': 'red', 'bold': True})
            red_format.set_align('vcenter')
            blue_format = workbook.add_format({'font_color': 'blue'})
            blue_format.set_align('vcenter')
            text_wrap_format = workbook.add_format({'text_wrap': True})
            text_wrap_format.set_align('vcenter')
            cell_vcenter_format = workbook.add_format()
            cell_vcenter_format.set_align('vcenter')
            for user in output_data:
                user_name = user_id_name_map[user]
                # print 'start wrting data for user', user_name
                worksheet = workbook.add_worksheet(user_name)
                worksheet.set_column(0, 0, 25)
                worksheet.set_column(2, 2, 25)
                worksheet.set_column(4, 4, 30)
                worksheet.set_column(5, 5, 30)
                worksheet.set_column(6, 6, 35)
                worksheet.set_column(8, 8, 22)
                worksheet.set_column(9, 9, 40)
                worksheet.set_column(10, 10, 10)
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
                worksheet.write_string(row, 5, 'Book description')  # must be commented for movies
                worksheet.write_string(row, 6, 'Question1')
                worksheet.write_string(row, 7, 'Rating')
                worksheet.write_string(row, 8, 'Question2')
                worksheet.write_string(row, 9, 'Answer (for example genre, content, author)')
                worksheet.write_string(row, 10, 'Comments')

                row += 1
                all_recs = output_data[user].keys()
                chunck_size = len(all_recs) / n_files
                start = (i-1) * chunck_size
                end = start + chunck_size
                if i == n_files:
                    end = len(all_recs)
                for rec in all_recs[start:end]:
                    rec_code = generate_code({'M': output_data[user][rec]['M'], 'R': output_data[user][rec]['R']})
                    # write data for me
                    worksheet_me.write_string(row, 0, rec_code)
                    worksheet_me.write_string(row, 1, str(rec))
                    worksheet_me.write_string(row, 2, '')

                    rec_link = items_id_link[rec]
                    rec_name = items_links_name[rec_link]
                    worksheet.write_string(row, 0, rec_name, cell_vcenter_format)
                    worksheet.write_url(row, 1, rec_link, blue_format)
                    worksheet.write_string(row, 2, '---', cell_vcenter_format)
                    worksheet.write_string(row, 3, '---', cell_vcenter_format)
                    if dataset == 'movielens-user-study':
                        sims = find_sims_movies(items_desc, rec=rec)
                    else:  # assuming the else case to be goodreads
                        sims = find_sims_books(items_desc, rec=rec)
                    worksheet.write_string(row, 4, str(sims.encode("utf-8")),  cell_format=text_wrap_format)
                    if dataset == 'goodreads-user-study':
                        worksheet.write_string(row, 5, books_desc_text[items_id_link[rec]],
                                               cell_format=text_wrap_format)
                    worksheet.write_string(row, 6 + extra_c, 'Rate the rec (1-5):', cell_format=red_format)
                    worksheet.write_string(row, 7 + extra_c, '', cell_vcenter_format)
                    worksheet.write_string(row, 8 + extra_c, "What do(don't) you like?", cell_vcenter_format)
                    worksheet.write_string(row, 9 + extra_c, '', cell_vcenter_format)
                    worksheet.write_string(row, 10 + extra_c, '', cell_vcenter_format)
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
                        worksheet.write_string(row, 0, rec_name, cell_vcenter_format)
                        worksheet.write_url(row, 1, rec_link, blue_format)
                        worksheet.write_string(row, 2, exp_name, cell_vcenter_format)
                        worksheet.write_url(row, 3, exp_link, blue_format)
                        if dataset == 'movielens-user-study':
                            sims = find_sims_movies(items_desc, rec=rec, exp=exp)
                        else:  # assuming the else case to be goodreads
                            sims = find_sims_books(items_desc, rec=rec, exp=exp)
                        worksheet.write_string(row, 4, sims,  cell_format=text_wrap_format)
                        if dataset == 'goodreads-user-study':
                            worksheet.write_string(row, 5, '----------', cell_vcenter_format)
                        worksheet.write_string(row, 6 + extra_c,
                                               'Like the sim between rec and exp? (0/1)', cell_vcenter_format)
                        worksheet.write_string(row, 7 + extra_c, '', cell_vcenter_format)
                        worksheet.write_string(row, 8 + extra_c, "What do(don't) you like?", cell_vcenter_format)
                        worksheet.write_string(row, 9 + extra_c, '', cell_vcenter_format)
                        worksheet.write_string(row, 10 + extra_c, '', cell_vcenter_format)

                        row += 1
            workbook.close()
            workbook_me.close()

    elif phase == 3:
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
            data_path + get_file_name('pr_users_scores' + setup_postfix, num_users, train_ratio, 'txt'),
            path + get_file_name('updated_pr_users_scores', num_users, train_ratio, 'txt'),
            path + get_file_name('updated_pr_users_scores_bottom', num_users, train_ratio, 'txt'),
            path + get_file_name('updated_pr_users_scores' + setup_postfix, num_users, train_ratio,
                                 'txt'),
            path + get_file_name('updated_pr_users_scores' + setup_postfix + '_bottom', num_users,
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
        for i in range(1, n_files + 1):
            workbook = xlsxwriter.Workbook(data_path + 'phase3/recs_' + str(i) + '.xlsx')
            workbook_me = xlsxwriter.Workbook(data_path + 'phase3/recs_me_' + str(i) + '.xlsx')
            black_format = workbook.add_format({'bold': False, 'font_color': 'black'})
            red_format = workbook.add_format({'font_color': 'red', 'bold': True})
            blue_format = workbook.add_format({'font_color': 'blue'})
            blue_format.set_align('vcenter')
            text_wrap_format = workbook.add_format({'text_wrap': True})
            text_wrap_format.set_align('vcenter')
            cell_vcenter_format = workbook.add_format()
            cell_vcenter_format.set_align('vcenter')
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
                if dataset == 'goodreads-user-study':
                    worksheet.write_string(row, 3, 'Book description')
                worksheet.write_string(row, 4 + extra_c, 'Question1')
                worksheet.write_string(row, 5 + extra_c, 'Rating')
                worksheet.write_string(row, 6 + extra_c, 'Comments')

                row += 1
                all_recs = output_recs[user].keys()
                chunck_size = len(all_recs) / n_files
                start = (i - 1) * chunck_size
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
                    worksheet.write_string(row, 0, rec_name)
                    worksheet.write_url(row, 1, rec_link)
                    if dataset == 'movielens-user-study':
                        sims = find_sims_movies(items_desc, rec=rec)
                    else:  # assuming the else case to be goodreads
                        sims = find_sims_books(items_desc, rec=rec)
                    worksheet.write_string(row, 2, str(sims.encode("utf-8")))
                    if dataset == 'goodreads-user-study':
                        worksheet.write_string(row, 3, books_desc_text[items_id_link[rec]],
                                               cell_format=text_wrap_format)
                    worksheet.write_string(row, 4 + extra_c, 'Rate the rec (1-5):', cell_format=cell_vcenter_format)
                    worksheet.write_string(row, 5 + extra_c, '', cell_format=cell_vcenter_format)
                    worksheet.write_string(row, 6 + extra_c, '', cell_format=cell_vcenter_format)
                    row += 1
            workbook.close()
            workbook_me.close()
