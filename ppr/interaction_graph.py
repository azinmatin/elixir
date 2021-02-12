import networkx as nx
import numpy as np
import sys
sys.path.append('../')
from elixir_utility.utils import get_file_name
import argparse
import ConfigParser


class InteractionGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.type_colors = {}
        self.similar_nodes = {}

    def set_graph(self, g):
        self.graph = g

    def set_type_colors(self, type_colors):
        self.type_colors = type_colors

    def set_edge_weight(self, node1, node2, weight):
        if not self.graph.has_edge(node1, node2):
            raise Exception('edge does not exists %d-%d' % (node1, node2))
        self.graph[node1][node2]['weight'] = weight

    def add_similar_nodes(self, node_1, node_2, value):
        if node_1 not in self.similar_nodes:
            self.similar_nodes[node_1] = {}
        if node_2 not in self.similar_nodes:
            self.similar_nodes[node_2] = {}
        self.similar_nodes[node_1][node_2] = value
        self.similar_nodes[node_2][node_1] = value

    def get_node_node_sim(self, item1, item2):
        if item1 in self.similar_nodes and item2 in self.similar_nodes[item1]:
            return self.similar_nodes[item1][item2]
        return 0.0

    def item_item_similarity(self, file_name, sim_threshold):
        self.similar_nodes = {}
        with open(file_name, 'r') as f_in:
            next(f_in)
            for line in f_in:
                tabs = line.strip().split('\t')
                item1 = tabs[0]
                item2 = tabs[1]
                sim_val = float(tabs[2])
                if sim_val > sim_threshold:
                    item1_node = 'item_' + item1
                    item2_node = 'item_' + item2
                    if self.graph.has_node(item1_node) and self.graph.has_node(item2_node):
                        self.add_similar_nodes(item1_node, item2_node, sim_val)

    def get_similar_nodes(self):
        return self.similar_nodes

    def set_similar_nodes(self, similar_nodes):
        self.similar_nodes = similar_nodes

    def set_similar_pairs(self, similar_pairs, sim_threshold):
        self.similar_nodes = {}
        for pair in similar_pairs:
            sim_val = similar_pairs[pair]
            if sim_val < sim_threshold:
                continue
            item1 = list(pair)[0]
            if len(list(pair)) == 1:
                item2 = item1
            else:
                item2 = list(pair)[1]
            item1_node = 'item_' + str(item1)
            item2_node = 'item_' + str(item2)
            if self.graph.has_node(item1_node) and self.graph.has_node(item2_node):
                self.add_similar_nodes(item1_node, item2_node, sim_val)

    def merge_similarities(self, similar_pairs, lambda_value, sim_threshold):
        # to be deleted
        orig_pairs = {}

        for item1 in self.similar_nodes:
            for item2 in self.similar_nodes[item1]:
                # to be deleted
                # if self.similar_nodes[item1][item2] >= 0.625:
                #     orig_pairs[frozenset([int(item1[5:]), int(item2[5:])])] = True
                self.similar_nodes[item1][item2] *= lambda_value


        new_pairs_count = 0
        for pair in similar_pairs:
            pair_list = list(pair)
            item1 = 'item_' + str(pair_list[0])
            if len(pair_list) < 2:
                item2 = item1
            else:
                item2 = 'item_' + str(pair_list[1])
            if self.get_node_node_sim(item1, item2) == 0.0:
                new_pairs_count += 1
            new_sim = (1 - lambda_value) * similar_pairs[pair] + self.get_node_node_sim(item1, item2)
            if new_sim >= sim_threshold:
                self.add_similar_nodes(item1, item2, new_sim)
        print 'new pairs added', new_pairs_count
        # remove sims less than threshold
        deleted_pairs = {}
        for item1 in self.similar_nodes:
            for item2 in self.similar_nodes[item1]:
                if self.similar_nodes[item1][item2] < sim_threshold:
                    if item1 == item2:
                        print 'errooorrrrr', self.similar_nodes[item1][item2], item1, item2
                    deleted_pairs[frozenset((item1, item2))] = True
                    # to be deleted
                    # item1_id = int(item1[5:])
                    # item2_id = int(item2[5:])
                    # ids_pair = frozenset([item1_id, item2_id])
                    # if ids_pair in similar_pairs and ids_pair not in orig_pairs:
                    #     print item1_id, item2_id, 'from new deleted'
        for pair in deleted_pairs:
            pair_list = list(pair)
            item1 = pair_list[0]
            item2 = pair_list[1]
            del self.similar_nodes[item1][item2]
            del self.similar_nodes[item2][item1]
            if len(self.similar_nodes[item1]) == 0:
                del self.similar_nodes[item1]
            if len(self.similar_nodes[item2]) == 0:
                del self.similar_nodes[item2]

    def recwalk_weights(self, beta):
        """
        :param beta: the control parameter of random walk
         type_threshold: type dependent thresholds below
         which the weights are considered as zero
        :return: weighted graph beta*H + (1-beta)*P
         based on the following paper:
         RecWalk: Nearly Uncoupled Random Walks
         for Top-N Recommendation
         http://nikolako.net/papers/ACM_WSDM2019_RecWalk.pdf
        """

        # updating weights to betha*H
        for node in self.graph.nodes():
            num_neighbors = len(self.graph.successors(node))
            for neighbor in self.graph.successors(node):
                self.graph[node][neighbor]['weight'] = beta / num_neighbors

        if beta == 1.0:
            return

        type_nodelist = {}
        for node in self.graph.nodes():
            node_type = self.graph.node[node]['type']
            if node_type not in type_nodelist:
                type_nodelist[node_type] = []
            type_nodelist[node_type].append(node)
        for node_type, l in type_nodelist.items():
            node_name_id_map = {l[i]: i for i in range(len(l))}
            max_row_sum = 0
            num_nodes = len(l)
            type_weight = np.zeros((num_nodes, num_nodes))
            for i in range(num_nodes):
                # add sim to itself
                type_weight[i][i] = 1
                # add the similar nodes
                if l[i] in self.similar_nodes:
                    for sim_node, sim_val in self.similar_nodes[l[i]].items():
                        type_weight[i][node_name_id_map[sim_node]] = sim_val
                row_sum = type_weight[i].sum()
                if row_sum > max_row_sum:
                    max_row_sum = row_sum

            # normalizing the weight matrix by dividing by max_row_sum
            one_vector = np.ones(num_nodes)
            type_weight /= max_row_sum
            extra_weights = one_vector - np.dot(type_weight, one_vector.T)
            for i in range(num_nodes):
                type_weight[i][i] += extra_weights[i]

            #  type_weight += np.diag(one_vector - np.dot(type_weight, one_vector.T))

            # updating the edge_weights in the graph
            counter_edge = 0
            for i in range(num_nodes):
                added_value = 0
                if not self.graph.has_edge(l[i], l[i]):
                    self.add_edge(l[i], l[i])
                    self.graph[l[i]][l[i]]['weight'] = 0
                    self.graph[l[i]][l[i]]['name'] = 'similar_to'
                self.graph[l[i]][l[i]]['weight'] += (1 - beta) * type_weight[i][i]
                # added_value += (1 - beta) * type_weight[i][i]
                if l[i] in self.similar_nodes:
                    for sim_node, _ in self.similar_nodes[l[i]].items():
                        # do not count self loop again
                        if sim_node == l[i]:
                            continue
                        edge_weight = type_weight[i][node_name_id_map[sim_node]]
                        if edge_weight != 0:
                            node1 = l[i]
                            node2 = sim_node
                            if not self.graph.has_edge(node1, node2):
                                self.graph.add_edge(node1, node2)
                                counter_edge += 1
                                self.graph[node1][node2]['weight'] = 0
                                self.graph[node1][node2]['name'] = 'similar_to'
                            self.graph[node1][node2]['weight'] += (1-beta) * edge_weight
                            # added_value += (1-beta) * edge_weight
                # print l[i], added_value
            print counter_edge, 'edges added in type', node_type

    def create_node(self, node_name, type, node_desc=""):
        if not self.graph.has_node(node_name):
            self.graph.add_node(node_name)
            self.graph.node[node_name]['color'] = self.type_colors[type]
            self.graph.node[node_name]['type'] = type
            self.graph.node[node_name]['desc'] = node_desc

    def has_node(self, node):
        return self.graph.has_node(node)

    def add_edge(self, source, target):
        if not self.graph.has_edge(source, target):
            self.graph.add_edge(source, target)

    def add_edge_attributes(self, source, target, attributes):
        if self.graph.has_edge(source, target):
            for x, y in attributes.items():
                self.graph[source][target][x] = y

    def remove_item(self, item):
        if self.graph.has_node(item):
            for neighbor in self.graph.successors(item):
                if self.graph.node[neighbor]['type'] == 'review':
                    self.graph.remove_node(neighbor)
                    break
            self.graph.remove_node(item)

    def count_edges(self, edge_name):
        counter = 0
        for u, v in self.graph.edges():
            if self.graph[u][v]['name'] == edge_name:
                counter += 1
        return counter

    def remove_edges(self, edge_name):
        counter = 0
        deleted_edges = []
        for u, v in self.graph.edges():
            if self.graph[u][v]['name'] == edge_name:
                deleted_edges.append((u, v))
        for u, v in deleted_edges:
            self.graph.remove_edge(u, v)
            counter += 1
        return counter
        # print counter, 'similarity edges deleted'

    def number_stc(self):
        return nx.number_strongly_connected_components(self.graph)

    def get_nodes(self, node_type):
        nodes = []
        for node in self.graph.nodes():
            if self.graph.node[node]['type'] == node_type:
                nodes.append(node)
        return nodes

    def store_graph_gml(self, file_name):
        from networkx.readwrite.gml import literal_stringizer
        nx.write_gml(self.graph, file_name, stringizer=literal_stringizer)

    def load_graph_gml(self, file_name):
        from networkx.readwrite.gml import literal_destringizer
        self.graph = nx.read_gml(file_name, destringizer=literal_destringizer)


if __name__ == "__main__":
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
    train_partition = float(configParser.get('experiments', 'train_ratio'))
    sim_threshold = float(configParser.get('feedback_inc', 'sim_threshold'))
    beta = float(configParser.get('shared', 'beta'))

    sim_file = 'item-item-similarity-' + str(dimension) + '.txt'
    train_prefix = 'train'
    graph_prefix = 'graph_d_' + str(dimension)
    if experiment_mode == 'S':
        train_prefix = 'train_d_' + str(dimension)
        train_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
        graph_prefix += '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
    interactions_file = get_file_name(train_prefix, num_users, train_partition)
    print 'interaction file', interactions_file
    graph_file = get_file_name(graph_prefix, num_users, train_partition, 'gml')
    dataset_path = 'YOUR PATH'
    res_path = 'YOUR PATH'

    # load item names
    items_name = {}
    item_names_file = 'id_link_map.txt'
    delimiter = '\t'
    name_location = 1

    with open(dataset_path + item_names_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split(delimiter)
            item_id = int(tabs[0])
            item_name = ""
            if len(tabs) > name_location:
                item_name = tabs[name_location]
            items_name[item_id] = item_name

    # build_interaction graph
    graph = InteractionGraph()
    type_colors = {'user': 'red', 'item': 'green'}
    graph.set_type_colors(type_colors)
    with open(res_path + interactions_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            item_id = int(tabs[1])
            timestamp = tabs[2]
            rating = int(float(tabs[3]))
            if rating >= 3:
                # add nodes + interaction edges
                user_node = 'user_' + str(user_id)
                item_node = 'item_' + str(item_id)
                graph.create_node(user_node, 'user')
                graph.create_node(item_node, 'item', items_name[item_id])
                graph.add_edge(user_node, item_node)
                graph.add_edge(item_node, user_node)
                graph.add_edge_attributes(user_node, item_node, {'timestamp': timestamp, 'rating': rating, 'name': 'rated'})
                graph.add_edge_attributes(item_node, user_node, {'timestamp': timestamp, 'rating': rating,
                                                             'name': 'rated_by'})

    # Adding similarity edges
    graph.item_item_similarity(res_path + sim_file, sim_threshold)

    # Add sim edges based on RecWalk
    graph.recwalk_weights(beta=beta)

    # check for connectivity
    print 'number of scc', graph.number_stc()

    # save graph
    graph.store_graph_gml(res_path + graph_file)

    # print some stats
    print 'num nodes', graph.graph.number_of_nodes()
    print 'num edges', graph.graph.number_of_edges()

