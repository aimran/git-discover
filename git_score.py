import numpy
import pandas as pd
import os
import sys
import glob
import time
import argparse
import operator
import numpy as np
from datetime import datetime, timedelta
from dateutil.parser import parse
import pandas.io.sql as psql
import pandas as pd
import pymysql
import networkx as nx

from git_db import GitDB

import access_keys

class GitScore(object):
    """Docstring for GitScore """

    def __init__(self, db):
        self.db = db
        self.result_frame = self._collect_frames()

    def get_lang_match(self, search=['Python','C++']):
        all_lang_frame = self.db.lang_match_frame
        search_frame = pd.DataFrame(index=['0xthis0xcant0xwork'],
                columns= self.db.all_languages)
        search_frame.fillna(0, inplace=True)
        N = len(search)
        if N < 0:
            print "fail... must have atleast one language to search"
        for l in search:
            search_frame[l] = 1.0/np.sqrt(N)
        result_frame = all_lang_frame.dot(search_frame.T.values).copy()
        result_frame = result_frame[result_frame[0]>0]
        result_frame.sort(0, ascending=False, inplace=True)

        return result_frame


    def _collect_frames(self):
        df_pub_rep_count = self.db.get_pub_repo_count()
        df_pub_rep_count['log_repo_count'] = np.log10(df_pub_rep_count.public_repo_count)
        df_pub_rep_count['normal_repo_count'] = (df_pub_rep_count.log_repo_count - df_pub_rep_count.log_repo_count.mean())/(
                                                            df_pub_rep_count.log_repo_count.std())

        df_pgrank = self.db.get_page_rank()
        df_pgrank['log_page_rank'] = np.log10(df_pgrank.pagerank)
        df_pgrank['normal_page_rank'] = (df_pgrank.log_page_rank - df_pgrank.log_page_rank.mean())/(df_pgrank.log_page_rank.std())

        df_fork_count = self.db.get_fork_count()
        df_fork_count['log_fork_count'] = np.log10(df_fork_count.fork_per_repo)
        df_fork_count['normal_fork_count'] = (df_fork_count.log_fork_count - df_fork_count.log_fork_count.mean())/(
                                                df_fork_count.log_fork_count.std())

        df_star_count = self.db.get_star_count()
        df_star_count['log_star_count'] = np.log10(df_star_count.star_per_repo)
        df_star_count['normal_star_count'] = (df_star_count.log_star_count - df_star_count.log_star_count.mean())/(
                                                df_star_count.log_star_count.std())

        df_repo_per_month = self.db.get_repo_per_month()
        df_repo_per_month['log_rpm'] = np.log10(df_repo_per_month.repo_per_month)
        df_repo_per_month['normal_rpm'] = (df_repo_per_month.log_rpm - df_repo_per_month.log_rpm.mean())/(
                                                df_repo_per_month.log_rpm.std())

        df_result = None
        df_result = pd.merge(df_pub_rep_count[['public_repo_count','normal_repo_count']], df_pgrank[['pagerank','normal_page_rank']],
                     how='inner',left_index=True, right_index=True)

        df_result = df_result.merge(df_star_count[['star_count','normal_star_count']],
                                    left_index=True, right_index=True, copy=False)
        df_result = df_result.merge(df_fork_count[['fork_count','normal_fork_count']],
                                    left_index=True, right_index=True, copy=False)

        df_result = df_result.merge(df_repo_per_month[['repo_per_month','normal_rpm']],
                                    left_index=True, right_index=True, copy=False)

        return df_result

    def get_score(self, result_frame):
        pgrank_wt = 0.00005
        star_wt = 2.0
        fork_wt = 0.8
        repo_per_month_wt = 0.5

        result = (pgrank_wt * result_frame.normal_page_rank) \
                + (star_wt * result_frame.normal_star_count) \
                + (fork_wt * result_frame.normal_fork_count)  \
                + (repo_per_month_wt * result_frame.normal_rpm)

        return result

    def get_final_score(self, search=['Python', 'C++', 'C']):
        final_score_frame = self.result_frame.copy()
        final_score_frame['final_score'] = final_score_frame.apply(self.get_score, axis=1)

        #lets only keep ppl based on search criteria match
        final_score_frame = final_score_frame.merge(self.get_lang_match(search), how='right',
                left_index=True, right_index=True, copy=False)
        final_score_frame.dropna(inplace=True)

        return final_score_frame


if __name__ == '__main__':
    db = GitDB()
    score = GitScore(db)
