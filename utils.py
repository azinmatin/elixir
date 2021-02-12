from sklearn.metrics.pairwise import cosine_similarity
from heapq import *
import numpy as np


def get_file_name(name, num_users, partition, file_type='txt'):
    return name + "_users_" + str(num_users) + "_partition_" + str(int(partition * 100)) + '.' + file_type


def sigmoid(X):
   return 1/(1+np.exp(-X))


def read_features(feature_file, normalized=False):
    features = np.genfromtxt(feature_file, delimiter=',')
    if normalized:
        # features[:, 1:] = np.linalg.norm(features[:, 1:], axis=1, ord=2)
        features[:, 1:] = (features[:, 1:].T / np.linalg.norm(features[:, 1:], ord=2, axis=1)).T
    return features


def find_top_k(l, k):
    min_heap = []

    for i in range(min(k, len(l))):
        heappush(min_heap, l[i])

    for i in range(k, len(l)):
        if l[i][1] > min_heap[0][1]:
            heappop(min_heap)
            heappush(min_heap, l[i])

    return min_heap[:k]


def find_bottom_k(l, k):
    max_heap = []

    for i in range(min(k, len(l))):
        heappush(max_heap, l[i])

    for i in range(k, len(l)):
        if l[i][1] < max_heap[0][1]:
            heappop(max_heap)
            heappush(max_heap, l[i])

    return max_heap[:k]


def cosine_sim_1d(v1, v2):
    # v1 and v2 are 1d vectors of equal size
    dim = v1.shape[0]
    return cosine_similarity(v1.reshape(1, dim), v2.reshape(1, dim))[0, 0]


def top_k_similar(v, features, k, sim='cosine'):
    # returns top k similar row-ids to v
    # assumption: row ids are in the first column of features
    min_heap = []
    l = []
    counter = 0
    for i in range(features.shape[0]):
        if sim == 'cosine':
            sim_value = cosine_sim_1d(v, features[i, 1:])
        else:
            sim_value = np.dot(v, features[i, 1:].T)
            # sim_value = cosine_sim_1d(v, features[i, 1:])
        # sim_value = np.dot(v, features[i, 1:].T)
        item_id = int(features[i, 0])
        pair = (item_id, sim_value)
        if counter < k:
            heappush(min_heap, pair)
        else:
            if sim_value > min_heap[0][1]:
                heappop(min_heap)
                heappush(min_heap, pair)
        counter += 1

    top_pairs = min_heap[:k]
    return [e for e, _ in top_pairs]