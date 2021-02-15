# -*- coding: utf-8 -*-
import sys
reload(sys)
import pandas as pd
sys.path.append('../')

from generate_study_files import id_name_map


if __name__ == "__main__":
    dataset = 'movielens-user-study'
    path = "YOUR PATH"
    res_path = path + 'phase2/'
    num_users = 25
    train_ratio = 1
    rec_per_user = 30
    exp_per_rec = 5
    phase = 2
    num_files = 5

    items_files = path + 'items.txt'
    users_file = path + "users.txt"
    user_id_name_map = id_name_map(users_file)
    users_name_id_map = {v: k for k, v in user_id_name_map.items()}
    items_id_link = id_name_map(items_files)
    items_link_id = {val: key for key, val in items_id_link.items()}

    if phase == 2:
        # ------------------- generating feedback pair files phase 2 + extended training files  --------------------
        # ----- output files
        rwr_tf_file = res_path + 'RWR_feedback_top.txt'
        rwr_bf_file = res_path + 'RWR_feedback_bottom.txt'
        rwr_recs_phase_2 = res_path + 'RWR_rated_recs_phase_2.txt'
        
        # ---- read the files
        rating_files = ['recs_exps_'+str(i)+'.xlsx' for i in range(num_files)]
        meta_data_files = ['recs_exps_me_'+str(i)+'.xlsx' for i in range(num_files)]

        with open(rwr_tf_file, 'w') as ft_rwr, \
            open(rwr_bf_file, 'w') as fb_rwr, \
            open(rwr_recs_phase_2, 'w') as f_rwr:
            f_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
            ft_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
            fb_rwr.write('user\titem\ttimestamp\trating\taspects\tanswer\tcomment')
            for f1, f2 in zip(rating_files, meta_data_files):
                print 'feedback file', f1
                f1_file = pd.ExcelFile(res_path + f1)
                dfs_1 = {sheet_name: f1_file.parse(sheet_name)
                       for sheet_name in f1_file.sheet_names}
                f2_file = pd.ExcelFile(res_path + f2)
                dfs_2 = {sheet_name: f2_file.parse(sheet_name)
                       for sheet_name in f2_file.sheet_names}
                for sheet_name in dfs_1:
                    user_id = users_name_id_map[str(sheet_name)]
                    # read the code
                    codes = dfs_2[sheet_name]['Code']
                    ratings = dfs_1[sheet_name]['Rating']
                    rec_ids = dfs_2[sheet_name]['rec_id']
                    exp_ids = dfs_2[sheet_name]['exp_id']
                    comments = dfs_1[sheet_name]['Comments']
                    answers = dfs_1[sheet_name]['Answer (for example director, actor, genre or content)']
                    aspects = dfs_1[sheet_name]['features/similarities']
                    row = 0
                    for code in codes:
                        rec_id = int(rec_ids[row])
                        try:
                            rating = int(ratings[row])
                        except:
                            print sheet_name, row, 'int opr invalid', ratings[row], f1
                            rating = -1
                        comment = str(comments[row]).strip()
                        answer = str(answers[row]).strip()
                        if answer == 'nan':
                            print sheet_name, row, 'no valid answer', f1
                        aspect = aspects[row]
                        if 'P' not in code:
                            if rating not in [1, 2, 3, 4, 5]:
                                print sheet_name, row, 'no valid rating', ratings[row], f1
                                row += 1
                                continue

                            if 'R' in code:
                                f_rwr.write('\n')
                                f_rwr.write('%d\t%d\t%s\t%d\t%s\t%s\t%s' %
                                            (user_id, rec_id, '', rating, aspect, answer, comment))
                        else:
                            if rating not in [0, 1]:
                                print sheet_name, row, 'no valid feedback', ratings[row], f1

                            exp_id = int(exp_ids[row])
                            if rating == 0:
                                rating = -1

                            if 'TW' in code:
                                ft_rwr.write('\n')
                                ft_rwr.write('%d\t%d\t%d\t%d\t%s\t%s\t%s' % (user_id, rec_id, exp_id, rating, aspect,
                                                                             answer, comment))
                            if 'BW' in code:
                                fb_rwr.write('\n')
                                fb_rwr.write('%d\t%d\t%d\t%d\t%s\t%s\t%s' % (user_id, rec_id, exp_id, rating, aspect,
                                                                             answer, comment))
                        row += 1
    elif phase == 3:
        # ------------------- generating all_rated_recs_phase_3.txt  --------------------
        # ---- read the files
        rwr_recs_phase_3 = path + 'phase3/recs_phase3.xlsx'
        meta_data_phase3 = path + 'phase3/recs_phase3_me.xlsx'
        phase3_recs = path + 'all_rated_recs_phase3.txt'

        with open(phase3_recs, 'w') as f_rwr:
            f_rwr.write('user\titem\ttimestamp\trating\taspects\tcomment')
            f1_file = pd.ExcelFile(rwr_recs_phase_3)
            dfs_1 = {sheet_name: f1_file.parse(sheet_name)
                         for sheet_name in f1_file.sheet_names}
            f2_file = pd.ExcelFile(meta_data_phase3)
            dfs_2 = {sheet_name: f2_file.parse(sheet_name)
                         for sheet_name in f2_file.sheet_names}
            for sheet_name in dfs_1:
                user_id = users_name_id_map[str(sheet_name)]
                # read the code
                codes = dfs_2[sheet_name]['Code']
                ratings = dfs_1[sheet_name]['Rating']
                rec_ids = dfs_2[sheet_name]['rec_id']
                comments = dfs_1[sheet_name]['Comments']
                print sheet_name
                aspects = dfs_1[sheet_name]['features']
                row = 0
                for code in codes:
                    rec_id = int(rec_ids[row])
                    try:
                        rating = int(ratings[row])
                    except:
                        print sheet_name, row, 'int opr invalid', ratings[row]
                        rating = -1
                    comment = str(comments[row]).strip()
                    aspect = aspects[row]
                    if rating not in [1, 2, 3, 4, 5]:
                        print sheet_name, row, 'no valid rating', ratings[row]
                        row += 1
                        continue
                    f_rwr.write('\n')
                    f_rwr.write('%d\t%d\t%s\t%d\t%s\t%s' % (user_id, rec_id, '', rating, aspect, comment))
                    row += 1