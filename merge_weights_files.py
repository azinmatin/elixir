import numpy as np
import ConfigParser
import sys
sys.path.append('../')
from simulation.data_split import get_file_name
import argparse


if __name__ == "__main__":
    # -------- reading arguments ---------
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--l', help='exp location', default='top')
    args = parser.parse_args()
    configFilePath = args.c
    exp_loc = args.l

    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    dimension = int(configParser.get('shared', 'dimension'))
    folder = configParser.get('shared', 'folder')
    users_per_file = int(configParser.get('merge', 'users_per_file'))
    num_users = int(configParser.get('merge', 'users_per_file'))
    num_users = int(configParser.get('shared', 'num_users'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))


    res_path = 'YOUR PATH' + folder
    weight_file = res_path + get_file_name('user_weight_vector_learned', num_users, train_ratio)
    if exp_loc == 'bottom':
        weight_file = res_path + get_file_name('user_weight_vector_learned_bottom', num_users, train_ratio)
    files = []
    num_files = num_users / users_per_file
    for i in range(num_files):
        start_user = i * users_per_file
        end_user = start_user + users_per_file
        file_name_prefix = 'user_weight_vector_learned_' + str(start_user) + '_' + str(end_user)
        if exp_loc == 'bottom':
            file_name_prefix += '_bottom'
        file_name = get_file_name(file_name_prefix, num_users, train_ratio)
        files.append(file_name)

    users_weights = np.zeros((num_users, dimension + 1))
    index = 0
    for file_name in files:
        weights = np.genfromtxt(res_path + file_name, delimiter=',')
        users_weights[index:index+users_per_file, :] = weights[0:users_per_file, :]
        index += users_per_file
    np.savetxt(weight_file, users_weights, delimiter=',') 
