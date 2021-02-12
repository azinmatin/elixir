import sys
sys.path.append('../')
import numpy as np
from nearpy import Engine
from nearpy.hashes import RandomBinaryProjections
from nearpy.filters import NearestFilter, DistanceThresholdFilter
from elixir_utility.utils import cosine_sim_1d


class LSHKNN:
    def __init__(self, data_points, sim_threshold=0.5, num_vectors=3):
        self.data_points = data_points
        self.point_num = self.data_points.shape[0]
        self.dimension = self.data_points.shape[1] - 1
        # Create a random binary hash with . bits
        self.rbp = RandomBinaryProjections('rbp', num_vectors, rand_seed=42)
        self.engine = Engine(self.dimension, lshashes=[self.rbp], vector_filters=[DistanceThresholdFilter(
            1-sim_threshold)])
        for i in range(self.point_num):
            self.engine.store_vector(self.data_points[i, 1:], '%d' % i)

    def find_knn(self, query, k, filtered_items={}):
        N = self.engine.neighbours(query)
        neighbors = []
        counter = 0
        for neighbor_elem in N:
            distance = neighbor_elem[-1]
            neighbor_id = int(self.data_points[int(neighbor_elem[-2]), 0])
            if neighbor_id in filtered_items:
                continue
            neighbors.append((neighbor_id, 1-distance))
            counter += 1
            if counter == k:
                break
        return neighbors

    def generate_similar_pairs(self, sim_threshold, output_file="", report=True):
        res = {}
        if output_file != "":
            with open(output_file, 'w') as f_out:
                f_out.write('item_id\titem_id\tsimilarity')
                visited_nodes = {}
                for i in range(self.point_num):
                    query = self.data_points[i, 1:]
                    item_id = int(self.data_points[i, 0])
                    # Get nearest neighbours
                    N = self.engine.neighbours(query)
                    for neighbor_elem in N:
                        distance = neighbor_elem[-1]
                        neighbor_id = int(self.data_points[int(neighbor_elem[-2]), 0])
                        if neighbor_id not in visited_nodes and 1-distance >= sim_threshold:
                            f_out.write('\n')
                            f_out.write('%d\t%d\t%.3f' % (item_id, neighbor_id, 1 - distance))
                    visited_nodes[item_id] = True
                    if i % 1000 == 0:
                        print 'finishe index', i
        else:
            for i in range(self.point_num):
                query = self.data_points[i, 1:]
                item_id = int(self.data_points[i, 0])
                # Get nearest neighbours
                N = self.engine.neighbours(query)
                for neighbor_elem in N:
                    distance = neighbor_elem[-1]
                    neighbor_id = int(self.data_points[int(neighbor_elem[-2]), 0])
                    pair = frozenset((item_id, neighbor_id))
                    if pair not in res and 1-distance >= sim_threshold:
                        res[pair] = 1-distance
                if report:
                    if i % 1000 == 0:
                        print 'finished index', i
        return res

    def generate_similar_pairs_exhaustive(self, sim_threshold):
        res = {}
        for i in range(self.point_num):
            item1 = int(self.data_points[i, 0])
            for j in range(i, self.point_num):
                item2 = int(self.data_points[j, 0])
                pair = frozenset([item1, item2])
                sim = cosine_sim_1d(self.data_points[i, 1:], self.data_points[j, 1:])
                if sim >= sim_threshold:
                    res[pair] = sim
        return res


if __name__ == "__main__":
    # read feature file
    path = 'YOUR PATH'
    file_name = "movielens-user-study-data-nmf-features-20.csv"  # or spotify-svd-features-50.csv
    output_file = path + 'item-item-similarity-20.txt'
    sim_threshold = 0.5

    # ----------- build item-item similarity --------------
    features = np.genfromtxt(path+file_name,delimiter=',')
    lsh_knn = LSHKNN(features, sim_threshold=sim_threshold)
    lsh_knn.generate_similar_pairs(0, output_file)
