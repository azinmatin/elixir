import sys
sys.path.append('../')
import numpy as np
from scipy.stats import wilcoxon
from scipy import stats


def significance_test(samples1, samples2):
    a = []
    b = []
    for user in samples1:
       a.append(samples1[user])
       b.append(samples2[user])
    x, p = stats.ttest_ind(a, b)
    return p


def significance_test_wilcoxon(samples1, samples2):
    a = []
    b = []
    for user in samples1:
       a.append(samples1[user])
       b.append(samples2[user])
    x, p = wilcoxon(a, b)
    return p


def dcg_score(y_true, y_score, k=None):
    """Discounted cumulative gain (DCG) at rank K.
    website: https://www.kaggle.com/davidgasquez/ndcg-scorer
    Parameters
    ----------
    y_true : array, shape = [n_samples]
        Ground truth (true relevance labels).
    y_score : array, shape = [n_samples, n_classes]
        Predicted scores.
    k : int
        Rank.

    Returns
    -------
    score : float
    """
    order = np.argsort(y_score)[::-1]
    # print 'order', order
    if k is None:
        y_true = np.take(y_true, order)
    else:
        y_true = np.take(y_true, order[:k])

    gain = 2 ** y_true - 1

    discounts = np.log2(np.arange(len(y_true)) + 2)
    # print 'discounts', discounts
    return np.sum(gain / discounts)


def ndcg_score(ground_truth, predictions, k=None):
    """Normalized discounted cumulative gain (NDCG) at rank K.
    website: https://www.kaggle.com/davidgasquez/ndcg-scorer
    Normalized Discounted Cumulative Gain (NDCG) measures the performance of a
    recommendation system based on the graded relevance of the recommended
    entities. It varies from 0.0 to 1.0, with 1.0 representing the ideal
    ranking of the entities.

    Parameters
    ----------
    ground_truth : array, shape = [n_samples]
        Ground truth (true labels represended as integers).
    predictions : array, shape = [n_samples, n_classes]
        Predicted probabilities.
    k : int
        Rank.

    Returns
    -------
    score : float
    """
    # Iterate over each y_true and compute the DCG score
    actual = dcg_score(ground_truth, predictions, k)
    best = dcg_score(ground_truth, ground_truth, k)
    score = float(actual) / float(best+10e-10)

    return score


def get_users_data(file_name):
    users_data = {}
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            item_id = int(tabs[1])
            timestamp = tabs[2]
            rating = int(float(tabs[3]))
            if rating >= 3:
                rating = 1
            else:
                rating = 0
            if user_id not in users_data:
                users_data[user_id] = {}
            users_data[user_id][item_id] = {'rating': rating, 'timestamp': timestamp}
            if len(tabs) > 5:
                users_data[user_id][item_id]['comments'] = tabs[5]
    return users_data


def get_users_feedback_recs(file_name):
    users_data = {}
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            rec_id = int(tabs[1])
            exp_id = int(tabs[2])
            label = int(tabs[3])
            if label >= 1:
                rating = 1
            else:
                rating = 0
            if user_id not in users_data:
                users_data[user_id] = {}
            users_data[user_id][rec_id] = {'rating': rating, 'exp_id': exp_id}
    return users_data


def get_users_feedback(file_name):
    users_data = {}
    with open(file_name, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            user_id = int(tabs[0])
            item1 = int(tabs[1])
            item2 = int(tabs[2])
            label = int(tabs[3])
            if user_id not in users_data:
                users_data[user_id] = []
            users_data[user_id].append((item1, item2, label))
    return users_data


def test_map_k(users_test_data, users_recs, k):
    users_precision_values = {}
    for user in users_recs:
        precision_values = []
        relevant_count = 0
        test_count = 0
        for item, _ in users_recs[user][:k]:
            test_count += 1
            if item in users_test_data[user]:
                if users_test_data[user][item]['rating'] == 1:
                    relevant_count += 1
                    precision = (relevant_count + 0.0) / test_count
                    precision_values.append(precision)
        users_precision_values[user] = sum(precision_values)/(len(precision_values) + 0.000001)
    return sum(users_precision_values.values())/(len(users_precision_values) + 0.0), users_precision_values


def test_precision_k(users_test_data, users_recs, k, label=1):
    users_precision_values = {}
    missing_judgments = {}
    for user in users_recs:
        if user not in missing_judgments:
            missing_judgments[user] = 0
        relevant_count = 0
        for item, _ in users_recs[user][:k]:
            if item in users_test_data[user]:
                if users_test_data[user][item]['rating'] == label:
                    relevant_count += 1
            else:
                missing_judgments[user] += 1
        users_precision_values[user] = (relevant_count + 0.0) / k
    v = missing_judgments.values()
    print 'avg, min, max missing judgments', sum(v)/(len(v) + 0.0), min(v), max(v)
    return sum(users_precision_values.values())/(len(users_precision_values) + 0.0), users_precision_values


def test_precision_k_user(users_test_data, user_recs, user, k, label=1):
    relevant_count = 0
    for item, _ in user_recs[:k]:
        if item in users_test_data[user]:
            if users_test_data[user][item]['rating'] == label:
                relevant_count += 1
    return (relevant_count + 0.0) / k

def test_ndcg(users_test_data, users_recs, k):
    users_ndcg = {}
    for user in users_recs:
        true_relevant = []
        rec_relevant = []
        for item, score in users_recs[user]:
            if item in users_test_data[user]:
                true_relevant.append(users_test_data[user][item]['rating'])
                rec_relevant.append(score)
        value = ndcg_score(true_relevant, rec_relevant, k=k)
        users_ndcg[user] = value
    return sum(users_ndcg.values()) / len(users_ndcg), users_ndcg
