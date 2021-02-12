import ConfigParser
import sys
sys.path.append('../')
from simulation.data_split import get_file_name
import argparse


if __name__ == "__main__":
    # -------- reading arguments ---------
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    parser.add_argument('--g', help='experiment group id')
    parser.add_argument('--l', help='exp location', default='top')
    args = parser.parse_args()
    configFilePath = args.c
    experiment_mode = args.g
    exp_loc = args.l

    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    dataset = configParser.get('shared', 'd')
    dimension = int(configParser.get('shared', 'dimension'))
    folder = configParser.get('shared', 'folder')
    users_per_file = int(configParser.get('merge', 'users_per_file'))
    res_path = 'YOUR PATH' + folder
    rec_per_user = int(configParser.get('shared', 'rec_per_user'))
    num_votes = int(configParser.get('shared', 'v'))
    num_users = int(configParser.get('shared', 'num_users'))
    train_ratio = float(configParser.get('experiments', 'train_ratio'))

    setup_postfix = '_rec_'+str(rec_per_user)+'_v_'+str(num_votes)
    prefix = 'updated_pr_users_scores'
    if experiment_mode == 'SP':
        prefix += setup_postfix
    if exp_loc == 'bottom':
        prefix += '_bottom'
    users_scores_file = res_path + get_file_name(prefix, num_users, train_ratio, 'txt')

    num_files = num_users / users_per_file
    with open(users_scores_file, 'w') as f_out:
        f_out.write('node_id\t(node_id, score)')
        for i in range(num_files):
            start_user = i * users_per_file
            end_user = start_user + users_per_file
            file_name_prefix = 'updated_pr_users_scores_' + str(start_user) + '_' + str(end_user)
            if experiment_mode == 'SP':
                file_name_prefix += setup_postfix
            if exp_loc == 'bottom':
                file_name_prefix += '_bottom'
            file_name = res_path + get_file_name(file_name_prefix, num_users, train_ratio, 'txt')
            f_out.write('\n')
            with open(file_name, 'r') as f_in:
                f_in.readline()
                f_out.write(f_in.read())

