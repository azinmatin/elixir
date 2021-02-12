from sklearn.feature_extraction import DictVectorizer
import numpy as np
from numpy import asarray
from numpy import savetxt
import json
import nimfa


if __name__ == "__main__":
    dataset = 'movielens-user-study'
    path = 'YOUR PATH'
    items_features_file = path + "movies_features.txt"
    items_ids_files = path + 'items.txt'
    dimensions = 20

    with open(items_features_file, 'r') as json_file:
        items_features = json.load(json_file)
        print 'len(items_features)', len(items_features)
    links_ids_map = {}
    with open(items_ids_files, 'r') as f_in:
        next(f_in)
        for line in f_in:
            tabs = line.strip().split('\t')
            link = tabs[0]
            item_id = int(tabs[1])
            links_ids_map[link] = item_id
    tags_dict = {}
    genres_dict = {}
    cast_dict = {}
    directors_dict = {}
    items_list = []
    X1 = []
    X2 = []
    X = []
    no_tag = 0
    no_genre = 0
    no_cast = 0
    no_dir = 0
    for item_dict in items_features:
        # count stats
        if len(item_dict['tags']) == 0:
            no_tag += 1
        if len(item_dict['genres']) == 0:
            no_genre += 1
        if len(item_dict['cast']) == 0:
            print 'no cast', item_dict['link']
            no_cast += 1
        if len(item_dict['directors']) == 0:
            no_dir += 1

        link = item_dict['link']
        item_id = links_ids_map[link]
        d = {}
        d1 = {}
        tags_values = item_dict['tags'].values()
        if len(tags_values) > 0:
            max_val = max(tags_values)
            for tag in item_dict['tags']:
                if len(tag) == 0:
                    continue
                d1[tag] = 1.0
                d[tag] = 1.0
                tags_dict[tag] = True
        for genre in item_dict['genres']:
            if len(genre) == 0:
                continue
            d1[genre] = 1.0
            d[genre] = 1.0
            genres_dict[genre] = True
        d2 = {}
        for p in item_dict['cast']:
            if len(p) == 0:
                continue
            d2[p] = 1.0
            d[p] = 1.0
            cast_dict[p] = True
        for p in item_dict['directors']:
            if len(p) == 0:
                continue
            d2[p] = 1.0
            d[p] = 1.0
            directors_dict[p] = True
        if len(d1) == 0:
            print item_dict['link'], 'len d1 = 0'
        if len(d2) == 0:
            print item_dict['link'], 'len d2 = 0'
        items_list.append(item_id)
        X1.append(dict(d1))
        X2.append(dict(d2))
        X.append(dict(d))

    print '#tags, genres, cast, directors', len(tags_dict), len(genres_dict), len(cast_dict), len(directors_dict)
    print 'no tags:', no_tag, 'no genres:', no_genre, 'no cast:', no_cast, 'no directors', no_dir

    vec = DictVectorizer()
    Y = vec.fit_transform(X).toarray()
    nmf = nimfa.Nmf(Y, rank=dimensions, max_iter=30, update='euclidean', objective='fro')
    nmf_fit = nmf()
    Y_red = nmf_fit.basis()
    all_data = np.append(np.asarray(items_list).reshape(len(items_list), 1), Y_red, 1)
    print 'all data dimension', all_data.shape
    data = asarray(all_data)
    # save to csv file
    savetxt(path + dataset + '-nmf-features-' + str(dimensions) + '.csv', data, delimiter=',')
