import sys
sys.path.append('../')
import torch
import numpy as np
import matplotlib.pyplot as plt
import torch.nn as nn
import torch.optim as optim
import pickle
import time
import argparse
from elixir_utility import utils
from elixir_utility.utils import get_file_name
import ConfigParser


class LTO(nn.Module):
    # Implementation of equation 6 in paper
    def __init__(self, points, d, mode):
        super(LTO, self).__init__()
        if mode == 'translation':
            self.A = nn.Parameter(torch.rand(d, 1, requires_grad=True) * 2 - 1)
        else:
            self.A = nn.Parameter(torch.rand(d, 1, requires_grad=True) * 2 + 1)
        self.initial_val = np.copy(torch.t(self.A).detach().numpy())
        self.points = points
        self.mode = mode

    def forward(self):
        if self.mode == 'scale':
            tmp = self.A.repeat(1, self.points.shape[1]) * self.points
        else:  # mode = translation
            tmp = self.A.repeat(1, self.points.shape[1]) + self.points
        tmp = torch.nn.functional.normalize(tmp, dim=0)
        res = torch.matmul(torch.t(tmp), tmp)
        return res


if __name__ == "__main__":
    # ----------- required parameters ------------
    dimension = 1128
    num_users = 500
    feedback_ratio = 0.4
    train_ratio = 0.4
    feature_reduction = 'tag'
    learning_rate = 0.1
    weight_decay = 1
    n_epoch = 10
    # alpha = 20
    loss_norm = nn.MSELoss(reduction='sum')
    torch.set_default_dtype(torch.double)

    # -------------- reading arguments -------------
    # ------ with argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--s', help='indext of first user')
    parser.add_argument('--t', help='index of last user')
    parser.add_argument('--l', help='exp location', default='top')
    args = parser.parse_args()
    configFilePath = args.c
    start_user = int(args.s)
    end_user = int(args.t)
    exp_loc = args.l
    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    dimension = int(configParser.get('shared', 'dimension'))
    num_users = int(configParser.get('shared', 'num_users'))
    feature_reduction = configParser.get('shared', 'feature_reduction')
    model = configParser.get('shared', 'm')
    exp_per_rec = int(configParser.get('shared', 'e'))
    item_per_pair = int(configParser.get('shared', 'i'))
    num_votes = int(configParser.get('shared', 'v'))
    folder_name = configParser.get('shared', 'folder')
    learning_rate = float(configParser.get('update_sim_unconstr', 'learning_rate'))
    weight_decay = float(configParser.get('update_sim_unconstr', 'weight_decay'))
    n_epoch = int(configParser.get('update_sim_unconstr', 'n_epoch'))
    mode = configParser.get('feedback_inc', 'mode')
    feedback_ratio = float(configParser.get('experiments', 'feedback_ratio'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))


    path = 'YOUR PATH'
    res_path = path + folder_name
    feature_file = path + dataset + "-" + feature_reduction + "-features-" + str(dimension) + ".csv"
    simulated_feedback_file = res_path + get_file_name(model + '_simulated_feedback_d_'+ str(dimension), num_users,
                                                       feedback_ratio)
    if exp_loc == 'bottom':
        simulated_feedback_file = res_path + get_file_name(model + '_simulated_feedback_bottom', num_users,
                                                           feedback_ratio)
        print 'read bottom'
    points_numpy = utils.read_features(feature_file, normalized=True)
    item_id_map = {int(points_numpy[i, 0]): i for i in range(points_numpy.shape[0])}
    points = torch.from_numpy(points_numpy[:, 1:].T)
    print 'started computing cross products'
    points_cross_points = torch.matmul(torch.t(points), points)
    dimension = points.shape[0]
    num_items = points.shape[1]
    # read the feedback pairs
    users_feedback_pairs = {}
    users = []
    print 'started reading the pairs'
    with open(simulated_feedback_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user = int(tabs[0])
            item1 = int(tabs[1])
            item1 = item_id_map[item1]
            item2 = int(tabs[2])
            item2 = item_id_map[item2]
            label = int(tabs[3])
            if user not in users_feedback_pairs:
                users_feedback_pairs[user] = []
                users.append(user)
            users_feedback_pairs[user].append((item1, item2, label))

    # ---------------- training weights for each user -----------
    users_weights = np.zeros((end_user-start_user, dimension + 1))
    user_index = 0
    for user in users[start_user:end_user]:
        # initializing F matrix
        w = torch.zeros([num_items, num_items], dtype=torch.double)
        count_nonzero = 0
        # extracting user's feedback on pairs
        for item1, item2, label in users_feedback_pairs[user]:
            w[item1, item2] = label
            if label != 0:
                count_nonzero += 1

        # continue if user has no feedback pairs
        if count_nonzero == 0:
            users_weights[user_index, 0] = user
            users_weights[user_index, 1:] = np.zeros((1, dimension))
            print users_weights[user_index, 1:]
            user_index += 1
            print 'finished user', user_index
            continue

        # start optimizing
        task = LTO(points, dimension, mode)
        task_loss_list = []
        optimizer = optim.SGD(task.parameters(), lr=learning_rate, weight_decay=weight_decay)
        best_loss = 10e+10
        ct_same = 0
        for epoch in range(n_epoch):
            res = task()
            tmp = w * (points_cross_points - res)
            loss = torch.sum(tmp) / count_nonzero

            task.zero_grad()  # need to clear the old gradients
            loss.backward()
            optimizer.step()
            if loss < best_loss:
                best_loss = loss
                learned_w = list(task.parameters())[0]
            print 'finished epoch', epoch, 'for user', user_index + 1

        users_weights[user_index, 0] = user
        users_weights[user_index, 1:] = torch.t(learned_w).detach().numpy()
        print users_weights[user_index, 1:]
        print task.initial_val
        user_index += 1
        print 'finished user', user_index

    # save user weights
    file_prefix = 'user_weight_vector_learned_' + str(start_user) + '_' + str(end_user)
    if exp_loc == 'bottom':
        file_prefix += '_bottom'
    weight_file = res_path + get_file_name(file_prefix, num_users, train_ratio)
    np.savetxt(weight_file, users_weights, delimiter=',') 
