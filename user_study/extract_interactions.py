# -*- coding: utf-8 -*-
import pandas as pd


if __name__ == "__main__":
    dataset = 'movielens-user-study-data'
    path = 'YOUR PATH'
    csv_file = path + 'round1.xlsx'
    interaction_file = path + 'sampled_interactions_25.txt'
    users_names_file = path + 'users.txt'
    items_names_file = path + 'items.txt'

    # ---------- reading from a file -------------
    xl = pd.ExcelFile(csv_file)
    user_name_id_map = {}
    item_link_id_map = {}
    user_counter = 1
    item_counter = 1
    with open(interaction_file, 'w') as f_out:
        f_out.write('user\titem\ttimestamp\trating')
        for sheet_name in xl.sheet_names:
            sheet = pd.read_excel(csv_file, sheet_name, header=None)
            start_row = 1
            user_name = sheet_name
            user_name_id_map[user_name] = user_counter
            user_id = user_name_id_map[user_name]
            user_counter += 1
            while start_row < len(sheet.index):
                print user_name, start_row
                item_link = sheet.loc[start_row, 0].strip()
                if item_link not in item_link_id_map:
                    item_link_id_map[item_link] = item_counter
                    item_counter += 1
                item_id = item_link_id_map[item_link]
                rating = sheet.loc[start_row, 1]
                # print item_name, item_link, rating, item_id
                f_out.write('\n')
                f_out.write(str(user_id) + '\t' + str(item_id) + '\t' + '' + '\t' + str(rating))
                start_row += 1
    with open(users_names_file, 'w') as f_out:
        f_out.write('user_name' + '\t' + 'user_id')
        for user_name in user_name_id_map:
            user_id = user_name_id_map[user_name]
            f_out.write('\n')
            f_out.write(user_name.encode('utf-8') + '\t' + str(user_id))
    with open(items_names_file, 'w') as f_out:
        f_out.write('item_name' + '\t' + 'item_id')
        for item_link in item_link_id_map:
            item_id = item_link_id_map[item_link]
            f_out.write('\n')
            f_out.write(item_link.encode('utf-8') + '\t' + str(item_id))
