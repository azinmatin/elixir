We release data from our study in two separate folders: 
- movielens 
- goodreads
***********************************
*******Description of files********
***********************************
- initial-ratings.txt: This file contains the initial ratings collected from the participants in the first phase of the study. We used these ratings  to initiate users' profiles. Each line shows one user-item interaction (or rating). The ratings are on a scale of 1 to 5 (with 5 interpreted as liking very much and 1 as not liking at all).

- phase2-rec-ratings.txt: In the second phase of the study, we trained an instance of the RecWalk model based on users' initial ratings, generated 30 recommendations accordingly and asked users to rate all these recommendations. This file contains the corresponding rating values. In the column “aspects”, we store a summary 
of the features of the recommended items which were shown to the users to help them with their judgments. 

- phase2-pair-ratings.txt: In this file, we list users’ feedback on pairs of recommendations and explanations. Each line contains information about a user, a recommendation item (item1), its explanation item (item2), user’s feedback on similar aspects of the recommendation and the explanation (1 and -1 refer to liking and disliking a pair, respectively), similar aspects of the recommendation and the explanation items (column “aspects”), user’s answer to the question “What do (don't) you like about the similar aspects of the recommendation and the explanation?” (column “liked/disliked-aspects”) and optional comments written by the user (column “comment”).

- phase3-rec-ratings.txt: In the third phase of the study, we first incorporated users’ feedback on individual as well as pairs of items collected in the second phase. Then, using the updated model, we generated the top 30 recommendations, this time for 5 different configurations which are described in the paper, and asked users to rate them on a scale of 1-5. This file contains the corresponding user ratings.

- movies-features.txt: In this file, we store features of the movies crawled from the movielens.org website. Each element of the list is a dictionary containing information about the cast, directors, genres, tags (along with movielens users’ voting for the tags), link, name, description and the movie's year of release. 

- books-features.txt: This file contains features of books crawled from the goodreads.com. Here, the data is stored as a list of dictionaries, where each dictionary contains information such as title, authors and genres of a book. 

- items.txt: This file shows the mapping of the item ids to their movielens/goodreads urls.
