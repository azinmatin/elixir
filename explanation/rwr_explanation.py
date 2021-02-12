def explanation_items_rwr(items_scores_file, graph, users_recs, k, location='top'):
    '''
    :param items_scores_file: contribution of each item to others
    :param interaction graph
    :param users_recs: dict mapping users to her recs
    :param k: number of explanations returned for each rec
    :return: dict of {user: {rec: [(exp, score)]}
    '''

    # find the item-item scores that are required
    item_item_scores = {}
    for user in users_recs:
        user_graph_id = 'user_' + str(user)
        for n in graph.neighbors(user_graph_id):
            if graph.node[n]['type'] == 'item':
                n_int = int(n.split('_')[1])
                if n_int not in item_item_scores:
                    item_item_scores[n_int] = {}
                for rec, _ in users_recs[user]:
                    item_item_scores[n_int][rec] = 0.0

    with open(items_scores_file, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            item1 = int(tabs[0].split('_')[1])
            if item1 in item_item_scores:
                for elem in tabs[1:]:
                    parts = elem.split(',')
                    item2 = int(parts[0].split('_')[1])
                    score = float(parts[1])
                    if item2 in item_item_scores[item1]:
                        item_item_scores[item1][item2] = score

    # return
    user_recs_exps = {}
    for user in users_recs:
        user_graph_id = 'user_' + str(user)
        if user not in user_recs_exps:
            user_recs_exps[user] = {}
        for rec, _ in users_recs[user]:
            neighbor_scores = []
            if rec not in user_recs_exps[user]:
                user_recs_exps[user][rec] = []
            for n in graph.neighbors(user_graph_id):
                if graph.node[n]['type'] == 'item':
                    n_int = int(n.split('_')[1])
                    score = item_item_scores[n_int][rec]
                    neighbor_scores.append((n_int, score))
            neighbor_scores.sort(key=lambda x: x[1], reverse=True)
            if location == 'top':
                for elem in neighbor_scores[:k]:
                    user_recs_exps[user][rec].append(elem)
            elif location == 'bottom':
                first_index = max(len(neighbor_scores) - k, 0)
                for elem in neighbor_scores[first_index:]:
                    user_recs_exps[user][rec].append(elem)
            else:
                print 'not defined location, rwr_explanation.py'

    # test code
    # for user in user_recs_exps:
    #     # if len(user_recs_exps[user]) != 200:
    #     #     print 'user not euqal 200', user, len(user_recs_exps[user])
    #     for rec in user_recs_exps[user]:
    #         if len(user_recs_exps[user][rec]) != 5:
    #             print 'user not euqal 5', user, rec, len(user_recs_exps[user][rec])

    return user_recs_exps


