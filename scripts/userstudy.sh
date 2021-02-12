#!/usr/bin/env bash
trap "kill 0" EXIT

# need to run set up first

config_file=code_path/config.txt
cd "code_path/elixir_utility"
python copy_config.py --c "${config_file}"
echo "config file copied"
loc=top

# ----------- incorporating item-level feedback in the graph ----------------
cd  "code_path/ppr"
mode=S
python interaction_graph.py --c  "${config_file}" --g "${mode}"
python rwr.py --c  "${config_file}" --g "${mode}"
echo "finished rwr"

# ------------ learning w values for any setup with pairs ---------------
cd "code_path/similarity"
python update_similarity.py --s 0 --t 5 --c "${config_file}" --l "${loc}"&
python update_similarity.py --s 5 --t 10 --c "${config_file}" --l "${loc}"&
python update_similarity.py --s 10 --t 15 --c "${config_file}" --l "${loc}"&
python update_similarity.py --s 15 --t 20 --c "${config_file}" --l "${loc}"&
python update_similarity.py --s 20 --t 25 --c "${config_file}" --l "${loc}"&
wait
cd "code_path/elixir_utility"
python merge_weights_files.py --c "${config_file}" --l "${loc}"
echo "finished learning w"

# ------------ incorporation of pair-level feedback ---------------
mode=P
cd "code_path/ppr"
python feedback_incorporation.py --s 0 --t 5 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 5 --t 10 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 10 --t 15 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 15 --t 20 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 20 --t 25 --c "${config_file}" --g "${mode}" --l "${loc}"&
wait
cd "code_path/elixir_utility"
python merge_scores_files.py --c "${config_file}" --g "${mode}" --l "${loc}"
echo "finished incorporation"

# ------------ incorporation pair-level + item-level feedback ---------------
mode=SP
cd "code_path/ppr"
python feedback_incorporation.py --s 0 --t 5 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 5 --t 10 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 10 --t 15 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 15 --t 20 --c "${config_file}" --g "${mode}" --l "${loc}"&
python feedback_incorporation.py --s 20 --t 25 --c "${config_file}" --g "${mode}" --l "${loc}"&
wait
cd "code_path/elixir_utility"
python merge_scores_files.py --c "${config_file}" --g "${mode}" --l "${loc}"
echo "finished incorporation"

t=all
cd "code_path/evaluation"
python eval_rwr.py --c "${config_file}" --t "${t}" --l "${loc}"
echo "finished evaluation"

echo "config file"
echo "${config_file}"

