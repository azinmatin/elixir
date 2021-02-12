import sys
import argparse
import os
import networkx as nx
from networkx.readwrite.gml import literal_destringizer
sys.path.append('../')
from elixir_utility.utils import get_file_name
import matplotlib
matplotlib.use('Agg')
from eval import test_ndcg
from eval import test_ndcg_sample
from eval import test_map_k
from eval import test_precision_k
from eval import test_precision_k_sample
from eval import get_users_data
from eval import read_random_recs
import ConfigParser
from eval import test_map_sample_k
from eval import significance_test_wilcoxon


def top_k_recs_rwr(scores_file, graph, k):
    users_recs = users_ranking_list(graph, scores_file)
    for user in users_recs:
        users_recs[user] = users_recs[user][:k]
    return users_recs


def users_ranking_list(graph, scores_file):
    users_items = {}
    with open(scores_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            graph_user_id = tabs[0]
            user_id = int(graph_user_id.split('_')[1])
            recs = list([])
            if user_id not in users_items:
                users_items[user_id] = []
            for elem in tabs[1:]:
                parts = elem.split(',')
                graph_item_id = parts[0]
                item_id = int(graph_item_id.split('_')[1])
                rec_score = float(parts[1])
                if graph.node[graph_item_id]['type'] == 'item' and not graph.has_edge(graph_user_id, graph_item_id):
                    recs.append((item_id, rec_score))
            recs.sort(key=lambda x: x[1], reverse=True)
            users_items[user_id] = recs
    return users_items


def read_ppr_scores(scores_file):
    users_items_scores = {}
    with open(scores_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            graph_user_id = tabs[0]
            user_id = int(graph_user_id.split('_')[1])
            if user_id not in users_items_scores:
                users_items_scores[user_id] = {}
            for elem in tabs[1:]:
                parts = elem.split(',')
                graph_item_id = parts[0]
                item_id = int(graph_item_id.split('_')[1])
                rec_score = float(parts[1])
                users_items_scores[user_id][item_id] = rec_score
    return users_items_scores


if __name__ == "__main__":
    # ------------- reading arguments -----------
    # ---- with argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--t', help='test strategy', default='sample')
    parser.add_argument('--l', help='exp loc', default='top')
    args = parser.parse_args()
    configFilePath = args.c
    test_strategy = args.t
    exp_loc = args.l
    # ---- with configparser
    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    exp_per_rec = int(configParser.get('shared', 'e'))
    item_per_pair = int(configParser.get('shared', 'i'))
    num_votes = int(configParser.get('shared', 'v'))
    dimension = int(configParser.get('shared', 'dimension'))
    rec_per_user = int(configParser.get('shared', 'rec_per_user'))
    folder = configParser.get('shared', 'folder')
    num_users = configParser.get('shared', 'num_users')
    feedback_ratio = float(configParser.get('experiments', 'feedback_ratio'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))
    test_ratio = float(configParser.get('experiments', 'test_ratio'))

    res_path = 'YOUR PATH'
    setup_postfix = '_rec_' + str(rec_per_user) + '_v_' + str(num_votes)
    test_file = res_path + get_file_name('test', num_users, test_ratio)
    if test_strategy == "sample":
        sample_test_file = res_path + get_file_name('test_sample', num_users, test_ratio)
        users_samples = read_random_recs(sample_test_file)
    #rwr_feedback_file = res_path + folder + get_file_name('RWR_simulated_feedback', num_users, feedback_ratio)
    graph_file = res_path + get_file_name('graph', num_users, train_ratio, 'gml')
    graph = nx.read_gml(graph_file, destringizer=literal_destringizer)
    updated_graph_file = res_path + get_file_name('graph_d_'+str(dimension) + setup_postfix, num_users, train_ratio,
                                                  'gml')
    if os.path.exists(updated_graph_file):
        updated_graph = nx.read_gml(updated_graph_file, destringizer=literal_destringizer)

    users_test_data = get_users_data(test_file)
    #users_feedback_recs = get_users_feedback_recs(rwr_feedback_file)


    # test code to be deleted
    counter = 0
    for user in users_test_data:
        seen = False
        for item in users_test_data[user]:
            item_graph_id = 'item_' + str(item)
            if users_test_data[user][item]['rating'] == 1 and graph.has_node(item_graph_id):
                counter += 1
                seen = True
                break
        if not seen:
            print user
    print counter, 'users with at least one positive item'

    k1 = 3
    k2 = 5
    k3 = 10
    ks = [k1, k2, k3]

    # --------------- only item-level feedback -------------------
    prefix = 'pr_users_scores_d_' + str(dimension) + setup_postfix
    scores_file = res_path + get_file_name(prefix, num_users, train_ratio, 'txt')
    if os.path.exists(scores_file):
        print '-----------only item-level feedback-----------'
        users_recs_3 = users_ranking_list(updated_graph, scores_file)
        if test_strategy == 'all':
            P_ks_org = [test_precision_k(users_test_data, users_recs_3, k) for k in ks]
            ndcg_ks_org = [test_ndcg(users_test_data, users_recs_3, k) for k in ks]
            MAP_ks_org = [test_map_k(users_test_data, users_recs_3, k) for k in ks]
        else:
            users_scores = read_ppr_scores(scores_file)
            P_ks_org = [test_precision_k_sample(users_samples, users_scores, k) for k in ks]
            ndcg_ks_org = [test_ndcg_sample(users_samples, users_scores, k) for k in ks]
            MAP_ks_org = [test_map_sample_k(users_samples, users_scores, k) for k in ks]

        for i in range(len(ks)):
            print P_ks_org[i][0]
        for i in range(len(ks)):
            print MAP_ks_org[i][0]
        for i in range(len(ks)):
            print ndcg_ks_org[i][0]

    # ------------- only pair feedback ----------------
    print '-----------only pair feedback-----------'
    scores_file = res_path + folder + get_file_name('updated_pr_users_scores', num_users, train_ratio, 'txt')
    if exp_loc == 'bottom':
        scores_file = res_path + folder + get_file_name('updated_pr_users_scores_bottom', num_users, train_ratio, 'txt')
    users_recs_2 = users_ranking_list(updated_graph, scores_file)
    print users_recs_2.keys()
    if test_strategy == 'all':
        P_ks_pairs = [test_precision_k(users_test_data, users_recs_2, k) for k in ks]
        ndcg_ks_pairs = [test_ndcg(users_test_data, users_recs_2, k) for k in ks]
        MAP_ks_pairs = [test_map_k(users_test_data, users_recs_2, k) for k in ks]
    else:
        users_scores = read_ppr_scores(scores_file)
        P_ks_pairs = [test_precision_k_sample(users_samples, users_scores, k) for k in ks]
        ndcg_ks_pairs = [test_ndcg_sample(users_samples, users_scores, k) for k in ks]
        MAP_ks_pairs = [test_map_sample_k(users_samples, users_scores, k) for k in ks]

    for i in range(len(ks)):
        print P_ks_pairs[i][0], significance_test_wilcoxon(P_ks_org[i][1], P_ks_pairs[i][1])
    for i in range(len(ks)):
        print MAP_ks_pairs[i][0], significance_test_wilcoxon(MAP_ks_org[i][1], MAP_ks_pairs[i][1])
    for i in range(len(ks)):
        print ndcg_ks_pairs[i][0], significance_test_wilcoxon(ndcg_ks_org[i][1], ndcg_ks_pairs[i][1])

    # --------------- both item and pair-level feedback --------------
    prefix = 'updated_pr_users_scores' + setup_postfix
    scores_file = res_path + folder + get_file_name(prefix, num_users, train_ratio, 'txt')
    if exp_loc == 'bottom':
        scores_file = res_path + folder + get_file_name(prefix+'_bottom', num_users, train_ratio, 'txt')
    # print 'third setup file', scores_file
    if os.path.exists(scores_file):
        print '-----------both item-level and pair-level feedback-----------'
        users_recs_4 = users_ranking_list(updated_graph, scores_file)
        if test_strategy == 'all':
            P_ks_both = [test_precision_k(users_test_data, users_recs_4, k) for k in ks]
            ndcg_ks_both = [test_ndcg(users_test_data, users_recs_4, k) for k in ks]
            MAP_ks_both = [test_map_k(users_test_data, users_recs_4, k) for k in ks]
        else:
            users_scores = read_ppr_scores(scores_file)
            P_ks_both = [test_precision_k_sample(users_samples, users_scores, k) for k in ks]
            ndcg_ks_both = [test_ndcg_sample(users_samples, users_scores, k) for k in ks]
            MAP_ks_both = [test_map_sample_k(users_samples, users_scores, k) for k in ks]

        for i in range(len(ks)):
            print P_ks_both[i][0], significance_test_wilcoxon(P_ks_org[i][1], P_ks_both[i][1])
        for i in range(len(ks)):
            print MAP_ks_both[i][0], significance_test_wilcoxon(MAP_ks_org[i][1], MAP_ks_both[i][1])
        for i in range(len(ks)):
            print ndcg_ks_both[i][0], significance_test_wilcoxon(ndcg_ks_org[i][1], ndcg_ks_both[i][1])
