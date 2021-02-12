from networkx.readwrite.gml import literal_destringizer
import networkx as nx
from multiprocessing import Pool
import time
import sys
sys.path.append('../')
from elixir_utility.utils import get_file_name
import argparse
import ConfigParser


def compute_pagerank(graph, nodes, alpha, epsilon):
    inputs = []
    pref = {node: 0.0 for node in graph.nodes()}
    for node in nodes:
        pd = dict(pref)
        pd[node] = 1.0
        inputs.append((graph, 1 - alpha, pd, 500, epsilon, None, 'weight', None))
    pool = Pool(processes=10)
    print 'started multiprocessing for forward push'
    res = pool.map(local_page_rank, inputs)
    return res


def write_pr_scores(file_name, nodes, pr_scores):
    with open(file_name, 'w') as f_out:
        f_out.write('node_id\t(node_id, score)')
        for i in range(len(nodes)):
            f_out.write('\n')
            node1 = nodes[i]
            f_out.write(node1)
            for node2 in pr_scores[i]:
                value = pr_scores[i][node2]
                if value != 0.0:
                    f_out.write('\t%s,%.16e ' % (node2, value))


def local_page_rank(params):
    return nx.pagerank(params[0], params[1], params[2], params[3], params[4], params[5], params[6], params[7])


def node_pagerank(graph, node, alpha, epsilon):
    pd = {node: 0.0 for node in graph.nodes()}
    pd[node] = 1.0
    return nx.pagerank(graph, 1 - alpha, pd, 500, epsilon, None, 'weight', None)


if __name__ == "__main__":
    # ----- fixed parameters ------
    alpha = 0.15
    epsilon = 1e-9

    # ---------- reading argumanets ----------
    # --- with argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--g', help='experiment group id')
    args = parser.parse_args()
    configFilePath = args.c
    experiment_mode = args.g
    # --- with configparser
    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    num_users = int(configParser.get('shared', 'num_users'))
    dimension = int(configParser.get('shared', 'dimension'))
    rec_per_user = int(configParser.get('shared', 'rec_per_user'))
    num_votes = int(configParser.get('shared', 'v'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))

    res_path = 'YOUR PATH'
    graph_prefix = 'graph_d_' + str(dimension)
    scores_prefix = 'pr_users_scores_d_' + str(dimension)
    if experiment_mode == 'S':
        graph_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
        scores_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
    graph_file = res_path + get_file_name(graph_prefix, num_users, train_ratio, 'gml')
    graph = nx.read_gml(graph_file, destringizer=literal_destringizer)

    users = []
    items = []
    for node in graph.nodes():
        if graph.node[node]['type'] == 'user':
            users.append(node)
        if graph.node[node]['type'] == 'item':
            items.append(node)

    # ------------ user pagerank --------------
    print 'start computing pagerank'
    t1 = time.time()
    res = compute_pagerank(graph, users, alpha, epsilon)
    print 'finished user pagerank', time.time() - t1

    # write scores into file
    users_scores_file = res_path + get_file_name(scores_prefix, num_users, train_ratio, 'txt')
    write_pr_scores(users_scores_file, users, res)

    # ------------ generate explanations ------------
    if experiment_mode != 'S':
        print 'start computing pagerank for', len(items), 'items'
        t1 = time.time()
        res = compute_pagerank(graph, items, alpha, epsilon)
        print 'finished user pagerank', time.time() - t1

        # write scores into file
        items_scores_file = res_path + get_file_name('pr_items_scores_d_'+str(dimension), num_users, train_ratio, 'txt')
        write_pr_scores(items_scores_file, items, res)


