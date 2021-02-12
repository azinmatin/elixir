# ELIXIR: Learning from User Feedback on Explanations to Improve Recommender Models
#### Author: [Azin Ghazimatin](http://people.mpi-inf.mpg.de/~aghazima/) (aghazima@mpi-inf.mpg.de)
## Overview
ELIXIR is a human-in-the-loop framework for incorporating users’ feedback on pairs of recommendations and explanations into a given recommendation model. In our paper, we instantiate ELIXIR for a state-of-the-art HIN-based recommender, [RecWalk](https://www.nikolako.net/papers/ACM_WSDM2019_RecWalk.pdf) as a representative of a family of the recommender systems with random walk at their core.
The following figure shows the workflow of ELIXIR. First, a recommendation model is learned based on users’ history of interactions and item-item similarities (step 1). Each recommendation is explained by a set of items with which the user has already interacted. These items are interpreted as the most contributing ones towards the relevance of the recommended item to the user. The set of generated recommendations and explanations are then shown to the user (step 2), where they can rate the recommendations and give feedback on similar aspects of the recommendations and explanations. As the pair-level feedback is expected to be highly sparse, we use label propagation to densify it (step 3). Using the resulting set of pair-level feedback, a user specific preference vector wu is learned (step 4) which is used to update the items’ representations (step 5) and the item-item similarity matrix subsequently (step 6). The updated item-item similarity matrix is fed to the recommendation model (here RecWalk), the model is updated accordingly and finally a new set of recommendations are generated for the user (step 7).
![elixir_framework](https://github.com/azinmatin/elixir/blob/main/images/elixir-framework.png)

## Usage
The released code contains the following packages:

**ppr**: This package implements the recommendation model (RecWalk) and feedback incorporation.
- **interaction_graph.py**: This file builds the interaction graph based on users’ initial ratings and adds similarity edges following the method described in the [RecWalk paper] (https://www.nikolako.net/papers/ACM_WSDM2019_RecWalk.pdf).
- **rwr.py**: This file computes personalized PageRank scores for each user. These scores are directly used to rank the candidate recommendations. In this file, we also compute the contribution score of items in users’ history to their recommendations using an approximation of the [PRINCE algorithm] (https://dl.acm.org/doi/pdf/10.1145/3336191.3371824).
- **feedback_incorporation.py**: In this file, we update items’ representations using the learned user-specific preference vector, update the interaction graph and re-compute the recommendation scores.

**similarity**: This package is responsible for computing as well as updating item-item similarity matrix.
- **lsh_similarity.py**: This file uses a locality-sensitive hashing technique based on random binary projections to populate the item-item similarity matrix and also to find k-NN of a given data point. The similarity metric used here is cosine similarity.
- **update_similarity.py**: This file implements Equation 6 in the paper where a user specific preference vector is learned. This vector is used to transform the items’ representations leading to modification of the item-item similarity matrix.

**simulation**: Here, we implement label propagation (introduced in [3]) to densify users’ pair-level feedback.
- **feedback_simulation.py**: This file simulates users’ feedback on unlabeled pairs by running label propagation algorithm adopted from [3].

**user_study**: In this package, we generate spreadsheets for the study, preprocess the collected data and prepare the data for steps 3-6 of ELIXR’s pipeline.
- **generate_study_files.py**: generates spreadsheets to be shared with the users.
- **read_study_files.py**: reads the spreadsheets shared back by the users.
- **selenium_scraper.py**: crawls features of the movies from movielens.org website using selenium.
- **extract_interactions.py**: reads the initial ratings of the users.
- **setups.py**: prepares data for steps 3-6 of the ELIXIR pipeline.

**scripts**: The script **userstudy.sh** is used to run steps 4-6 for different configurations described in the paper.

**evaluation**: **eval.py** and eval_rwr.py implement required functions for evaluating ELIXIR.

**explanation**: **rwr_explanation.py** generates top (or bottom) e explanations for top k recommendations.

**feature_engineering**: feature_extraction.py learns latent representations of items using NMF.
