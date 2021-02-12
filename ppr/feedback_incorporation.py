import numpy as np
import argparse
from networkx.readwrite.gml import literal_destringizer
import networkx as nx
import sys
sys.path.append('../')
from elixir_utility.utils import get_file_name
from interaction_graph import InteractionGraph
from similarity.lsh_similarity import LSHKNN
from rwr import node_pagerank
from rwr import write_pr_scores
from elixir_utility.utils import read_features
import time
import copy
import ConfigParser


def read_feedback_file(file_name):
    users_feedback = {}
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            if user_id not in users_feedback:
                users_feedback[user_id] = []
            item1_id = int(tabs[1])
            item2_id = int(tabs[2])
            label = int(tabs[3])
            users_feedback[user_id].append((item1_id, item2_id, label))
    return users_feedback


if __name__ == "__main__":
    # ----- fixed parameters ------
    alpha = 0.15
    epsilon = 1e-9

    # ----------- reading arguments -------------
    # --------- with argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--s', help='index of first user')
    parser.add_argument('--t', help='index of end user')
    parser.add_argument('--g', help='experiment group id')
    parser.add_argument('--l', help='exp location', default='top')
    args = parser.parse_args()
    start_user = int(args.s)
    end_user = int(args.t)
    configFilePath = args.c
    experiment_mode = args.g
    exp_loc = args.l
    # ------- with configparser
    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    dimension = int(configParser.get('shared', 'dimension'))
    feature_reduction = configParser.get('shared', 'feature_reduction')
    model = configParser.get('shared', 'm')
    rec_per_user = int(configParser.get('shared', 'rec_per_user'))
    exp_per_rec = int(configParser.get('shared', 'e'))
    item_per_pair = int(configParser.get('shared', 'i'))
    num_votes = int(configParser.get('shared', 'v'))
    folder_name = configParser.get('shared', 'folder')
    sim_threshold = float(configParser.get('feedback_inc', 'sim_threshold'))
    num_vectors = int(configParser.get('feedback_inc', 'num_vectors'))
    mode = configParser.get('feedback_inc', 'mode')
    beta = float(configParser.get('shared', 'beta'))
    feedback_ratio = float(configParser.get('experiments', 'feedback_ratio'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))
    num_users = int(configParser.get('shared', 'num_users'))
    res_path = 'YOUR PATH'
    input_output_path = res_path + folder_name

    # build interaction graph
    graph_prefix = 'graph_d_' + str(dimension)
    if experiment_mode == 'SP':
        graph_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
    graph_file = res_path + get_file_name(graph_prefix, num_users, train_ratio, 'gml')
    graph_nx = nx.read_gml(graph_file, destringizer=literal_destringizer)
    graph = InteractionGraph()
    graph.set_graph(graph_nx)

    # read the weight vectors and item festures
    weight_file = input_output_path + get_file_name('user_weight_vector_learned', num_users, train_ratio)
    if exp_loc == 'bottom':
        weight_file = input_output_path + get_file_name('user_weight_vector_learned_bottom', num_users, train_ratio)
    feature_file = res_path + dataset + "-" + feature_reduction + "-features-" + str(dimension) + ".csv"
    all_features = read_features(feature_file, normalized=True)
    user_weights = np.genfromtxt(weight_file, delimiter=',')
    print 'read features and weights'

    # keep only the features of the items in the graph
    items = {}
    item_nodes = graph.get_nodes('item')
    for item in item_nodes:
        item_id = int(item.split('_')[1])
        items[item_id] = True
    selected_indices = []
    item_counter = 0
    for i in range(all_features.shape[0]):
        item_id = int(all_features[i, 0])
        if item_id in items:
            selected_indices.append(i)
            items[item_id] = item_counter
            item_counter += 1
    features = all_features[selected_indices, :]
    print 'total items', all_features.shape[0], 'selected items', features.shape[0]

    # for all users 1) update features 2) find item-item sim 3) compute updated sim 4) recwalk 5) run ppr 6) save scores
    user_scores = []
    users = []
    diff_count = 0
    for i in range(start_user, end_user):
        t = time.time()
        user_id = int(user_weights[i, 0])
        user_graph_id = 'user_' + str(user_id)
        user_features = np.copy(features)
        if mode == 'scale':
            user_features[:, 1:] *= user_weights[i, 1:]
        else:  # mode = translation
            user_features[:, 1:] += user_weights[i, 1:]
            # user_features[:, 1:] /= hadamard_norm
        print 'min weight', np.min(user_weights[i, 1:]), 'max weight', np.max(user_weights[i, 1:])

        lsh_knn = LSHKNN(user_features, sim_threshold=sim_threshold, num_vectors=num_vectors)
        # find similar pairs
        similar_pairs = lsh_knn.generate_similar_pairs(sim_threshold)
        print '# new similar pairs:', len(similar_pairs)
        # remove similarity edges
        num_edge_1 = graph.remove_edges('similar_to')
        # add new similarities
        graph.set_similar_pairs(similar_pairs, sim_threshold)
        # run recwalk
        graph.recwalk_weights(beta=beta)
        num_edge_2 = graph.count_edges('similar_to')
        # run ppr
        scores = node_pagerank(graph.graph, user_graph_id, alpha, epsilon)
        users.append(user_graph_id)
        user_scores.append(copy.deepcopy(scores))
        print 'old sim edge count:', num_edge_1, 'new sim edge count', num_edge_2
        print 'finished user', i, 'in', time.time() - t, 'seconds'

    file_prefix = 'updated_pr_users_scores_' + str(start_user) + '_' + str(end_user)
    if experiment_mode == 'SP':
        file_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
    if exp_loc == 'bottom':
        file_prefix += '_bottom'
    users_scores_file = input_output_path + get_file_name(file_prefix, num_users, train_ratio, 'txt')
    write_pr_scores(users_scores_file, users, user_scores)
    print '------------- finished', len(users), len(user_scores)
