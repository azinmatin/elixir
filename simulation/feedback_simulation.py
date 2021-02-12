import sys
sys.path.append('../')
import numpy as np
from sklearn.semi_supervised import LabelPropagation
from sklearn.metrics.pairwise import cosine_similarity
import math


class FeedbackSimulation:
    def __init__(self, features):
        self.features = features
        self.item_index_map = {int(features[i, 0]): i for i in range(features.shape[0])}
        self.feedback_pairs = {}

    def set_lsh(self, lsh_knn):
        self.lsh_knn = lsh_knn

    def read_feedback_pairs(self, pairs_file):
        self.feedback_pairs = {}
        with open(pairs_file) as f_in:
            next(f_in)
            for line in f_in:
                tabs = line.strip().split('\t')
                user_id = int(tabs[0])
                item1 = int(tabs[1])
                item2 = int(tabs[2])
                label = int(tabs[3])
                if user_id not in self.feedback_pairs:
                    self.feedback_pairs[user_id] = []
                self.feedback_pairs[user_id].append((item1, item2, label))

    def sim_vector(self, item1, item2, normalized=True):
        '''
        This function computes geometric mean of two given vectors (equation 1)
        '''
        item1_index = self.item_index_map[item1]
        item2_index = self.item_index_map[item2]
        if not normalized:
            data_point = self.features[item1_index, 1:] * self.features[item2_index, 1:]
            data_point = np.sqrt(np.abs(data_point)) * np.sign(data_point)
        else:
            point1 = self.features[item1_index, 1:]
            point2 = self.features[item2_index, 1:]
            data_point = point1 * point2
            data_point = np.sqrt(np.abs(data_point)) * np.sign(data_point)
            data_point /= np.linalg.norm(data_point)
        return data_point

    def label_propagation(self, user, k, model='RWR'):
        feedback_pairs = []
        all_pairs = {}
        index = 0
        for item1, item2, label in self.feedback_pairs[user]:
            if label < 0:
                label = 0
            if label > 0:
                label = 1
            all_pairs[frozenset([item1, item2])] = {'index': index, 'label': label}
            index += 1

        # compute size of spare elements
        t1 = len(self.feedback_pairs[user])
        t2 = t1 * (k * (k - 1)) / 2
        added_k = int(math.sqrt(2 * t2)+1)
        print 'added k', added_k
        print 'num user feedback', t1

        # finding similar pairs
        for item1, item2, org_label in self.feedback_pairs[user]:
            # find similar items
            if model == 'RWR':
                v = self.sim_vector(item1, item2)
                tmp = self.lsh_knn.find_knn(v, k + added_k) # to be changed
            else:
                # TO DO
                pass
            sim_items = [elem[0] for elem in tmp]
            counter_pair = 0
            selected_pairs = []
            for i in range(len(sim_items)-1):
                for j in range(i+1, len(sim_items), 1):
                    x = frozenset([sim_items[i], sim_items[j]])
                    normalized = True
                    if model == 'MF':
                        normalized = False
                    pair_sim_vec = self.sim_vector(sim_items[i], sim_items[j], normalized=normalized)
                    pair_score = np.dot(v, pair_sim_vec.T)
                    selected_pairs.append((x, pair_score))
            sorted_selected_pairs = sorted(selected_pairs, key=lambda x: x[1], reverse=True)
            # building similar pairs our of similar items
            for e in sorted_selected_pairs:
                x = e[0]
                if x not in all_pairs:
                    all_pairs[x] = {'index': index, 'label': -1, 'org_label': org_label}
                    index += 1
                    counter_pair += 1
                    if counter_pair >= (k * (k - 1)) / 2:
                        break

        # running label propagation
        num_features = self.features.shape[1] - 1
        data = np.zeros((len(all_pairs), num_features))
        labels = np.zeros((len(all_pairs),))
        for x in all_pairs:
            # compute dot product
            list_x = list(x)
            if model == 'RWR':
                data_point = self.sim_vector(list_x[0], list_x[1])
            else:
                data_point = self.sim_vector(list_x[0], list_x[1], normalized=False)

            data[all_pairs[x]['index'], :] = data_point
            labels[all_pairs[x]['index']] = all_pairs[x]['label']
        # label_prop_model = LabelPropagation(kernel='knn', n_neighbors=7)
        if model == 'RWR':
            print 'label prop with cosine sim'
            label_prop_model = LabelPropagation(kernel=cosine_similarity, max_iter=300)
        else:
            # TO DO
            pass
        label_prop_model.fit(data, labels)
        learned_labels = label_prop_model.transduction_

        non_consistent_pairs = 0
        unlabeled = 0
        for x in all_pairs:
            x_list = list(x)
            item1 = x_list[0]
            item2 = x_list[1]
            pair_index = all_pairs[x]['index']
            label = all_pairs[x]['label']
            if label == -1:  # unlabeled
                unlabeled += 1
                label = learned_labels[pair_index]
            if label == 0:  # replace zero labels with -1
                label = -1
            feedback_pairs.append((item1, item2, label))
        return feedback_pairs
