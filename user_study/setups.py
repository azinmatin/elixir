import sys
sys.path.append('../')
from simulation.feedback_simulation import FeedbackSimulation
from elixir_utility import utils
from elixir_utility.utils import get_file_name
from similarity.lsh_similarity import LSHKNN


def densify_feedback(fs, item_per_pair, pair_file, output_file, model):
    fs.read_feedback_pairs(pair_file)
    with open(output_file, 'w') as f_out:
        f_out.write('%s\t%s\t%s\t%s' % ('user', 'item1', 'item2', 'label'))
        for user in fs.feedback_pairs:
            feedback_pairs = fs.label_propagation(user, item_per_pair, model=model)
            for e in feedback_pairs:
                f_out.write('\n')
                f_out.write('%d\t%d\t%d\t%d' % (user, e[0], e[1], e[2]))


if __name__ == "__main__":
    dataset = 'movielens-user-study'
    path = "YOUR PATH"
    dimension = 20
    num_users = 25
    rec_per_user = 30
    num_votes = 0
    item_per_pair = 10
    feature_reduction = 'nmf'
    model = 'RWR'

    # read features
    if model == 'RWR':
        feature_file = path + dataset + "-data-" + feature_reduction + "-features-" + str(dimension) + ".csv"
        features = utils.read_features(feature_file, normalized=True)

    # ---------------- only items ------------------------
    # generate extended training
    recs_file = path + 'phase2/' + model + '_rated_recs_phase_2.txt'
    main_train_file = path + 'train_users_' + str(num_users) + '_partition_100.txt'
    file_prefix = 'train_rec_' + str(rec_per_user) + '_v_' + str(num_votes)
    new_train_file = path + get_file_name(file_prefix, num_users, 1)
    lines_1 = []
    with open(main_train_file, 'r') as f_in:
        for line in f_in:
            lines_1.append(line.strip())
    lines_2 = []
    with open(recs_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            lines_2.append(line.strip())
    with open(new_train_file, 'w') as f_out:
        for line in lines_1:
            f_out.write(line)
            f_out.write('\n')
        for line in lines_2:
            f_out.write(line)
            f_out.write('\n')

    # ---------------- only pairs -------------------------
    fs = FeedbackSimulation(features)
    lsh_knn = LSHKNN(features)
    fs.set_lsh(lsh_knn)
    # read pairs_file
    rwr_tf_file = path + 'phase2/RWR_feedback_top.txt'
    rwr_bf_file = path + 'phase2/RWR_feedback_bottom.txt'
    f1_name = path + 'results/folder2/' + get_file_name(model + '_simulated_feedback', num_users, 1)
    f2_name = path + 'results/folder2/' + get_file_name(model + '_simulated_feedback_bottom_', num_users, 1)
    if model == 'RWR':
        # generate densified feedback files
        densify_feedback(fs, item_per_pair, rwr_tf_file, f1_name, model)
        densify_feedback(fs, item_per_pair, rwr_bf_file, f2_name, model)
