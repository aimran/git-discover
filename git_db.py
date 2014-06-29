import numpy
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

import access_keys

class GitDB(object):
    """Docstring for GitDB """

    def __init__(self, min_repo=10, max_repo=50, min_star=2, min_fork=2, min_rpm=0.3):
        self.cnx = pymysql.connect(host=access_keys.hostname,
                user=access_keys.user,
                passwd=access_keys.password, db=access_keys.dbname)
        self.cnx.ping(reconnect=True)
        self.cursor = self.cnx.cursor()

        self.min_repo = min_repo
        self.max_repo = max_repo
        self.min_star = min_star
        self.min_fork = min_fork
        self.min_rpm = min_rpm
        self.pub_repo_count_frame = self.get_pub_repo_count()
        self.all_languages = self.get_all_langs() #returns an array!!
        self.lang_match_frame = self.get_user_langs()

    def query_by_lang(self, language):
        query = """select login, count(language) as `{0}`
               from repos
               where language = \"{1}\"
               group by login
               order by `{0}`""".format(language,language)
        return query

    def query_all_lang(self):
        query = """ select DISTINCT(language)
                FROM repos
                WHERE language IS NOT NULL
                GROUP BY language;
            """.format()
        return query

    def query_pub_repo_count(self):
        query = """select login, public_repo_count
                from users
                where public_repo_count > {0} and public_repo_count < {1};
                """.format(self.min_repo, self.max_repo)
        return query

    def query_distinct_users(self):
        query = """select distinct(login)
                from users
                where public_repo_count > {0} and public_repo_count < {1};
                """.format(self.min_repo, self.max_repo)
        return query

    def query_followers(self):
        query = """select distinct(follower_login)
                from follower;
                """
        return query

    def query_follower_links(self):
        query = """select follower_login, login
                from follower;
                """
        return query

    def query_following(self):
        query = """select distinct(following_login)
                from following;
                """
        return query

    def query_following_links(self):
        query = """select login, following_login
                from following;
                """
        return query


    def query_fork_count(self, min_fork=1):
        query =  """select login, count(name) as fork_count
                from repos_forked
                group by login
                having fork_count > {0}
                order by fork_count desc;
             """.format(min_fork)
        return query

    def query_star_count(self, min_star=2):
        query =  """select login, count(name) as star_count
                    from repos_starred
                    group by login
                    having star_count > {0}
                    order by star_count desc;
                """
        return query.format(min_star)

    def query_commit_per_month(self):
        query =  """select login, sum(commit_per_month) as cpm
                    from repos_stats
                    group by login
                    order by cpm;
                """
        return query

    def query_repo_per_month(self):
        query =  """select login, start_date, public_repo_count
                    from users
                    where public_repo_count > {0} and public_repo_count < {1};
                """.format(self.min_repo, self.max_repo)
        return query

    def query_is_hireable(self):
        query =  """select login, hireable
                    from users;
                """
        return query

    def query_has_blog(self):
        query =  """select login,
                        blog,
                        (CASE WHEN (blog is null or trim(blog) = '') THEN 0 ELSE 1 END)
                            as has_blog
                    from users;
                """
        return query

    def query_has_email(self):
        query =  """select login,
                        email,
                        (CASE WHEN (email is null or trim(email) = '') THEN 0 ELSE 1 END)
                            as has_email
                    from users;
                """
        return query

    def query_has_location(self):
        query =  """select login,
                        location,
                        (CASE WHEN (location is null or trim(location) = '') THEN 0 ELSE 1 END)
                            as has_loc
                    from users;
                """
        return query

    def query_has_name(self):
        query =  """select login,
                        name,
                        (CASE WHEN (name is null or trim(name) = '') THEN 0 ELSE 1 END)
                            as has_name
                    from users;
                """
        return query

    def query_language_of_choice(self, login):
        query = """
                select language, count(*) as cnt from (select login, language
                from repos where login='{0}') as x group by language
                order by cnt desc;
                """.format(login)
        return query

    def query_popular_repo(self, login):
        query = """
                select name, language from repos
                where (login, name) = (select
                login,name from repos_starred where login='{0}' order by
                count desc limit 1);
                """.format(login)
        return query

    def query_user_info(self, login):
        query = """
                select name, email, location, start_date, avatar_url
                from users
                where login='{0}';
                """.format(login)
        return query


    def get_user_info(self, login):
        self.cursor.execute(self.query_user_info(login))
        result = self.cursor.fetchone()
        return result

    def get_user_popular_repo(self, login):
        self.cursor.execute(self.query_popular_repo(login))
        result = self.cursor.fetchone()
        return result

    def get_user_pref_lang(self, login):
        self.cursor.execute(self.query_language_of_choice(login))
        result = self.cursor.fetchall()
        return result

    def get_all_langs(self):
        all_languages = psql.read_sql(self.query_all_lang(), self.cnx)['language'].values
        return all_languages

    def get_user_langs(self, filename='all_language.pcl', create=False):
        df = None
        if create:
            all_langs = self.get_all_langs()
            df = None
            for lang in all_langs:
                tmp = psql.read_sql(self.query_by_lang(lang), self.cnx)
                if df is None:
                    df = tmp
                else:
                    df = df.merge(tmp, on='login', how='outer')
                    df.fillna(0, inplace=True)
            if df is not None:
                df.set_index('login',inplace=True)
                df = df.div(df.apply(lambda x: np.sqrt(x.dot(x)), axis=1), axis=0)
            df.to_pickle(filename)
        else:
            if filename is not None:
                df = pd.read_pickle(filename)
            else:
                print "Need a filename to unpickle language list"
        return df

    def get_graph(self):
        print "Please be patient... generating graph"
        users = psql.read_sql(self.query_distinct_users(), self.cnx)['login'].values
        flwr = psql.read_sql(self.query_followers(), self.cnx)['follower_login'].values
        flwr_links = psql.read_sql(self.query_follower_links(), self.cnx).values

        flwg = psql.read_sql(self.query_following(), self.cnx)['following_login'].values
        flwg_links = psql.read_sql(self.query_following_links(), self.cnx).values

        graph = nx.DiGraph()
        graph.add_nodes_from(np.append(users, flwr))
        graph.add_edges_from(flwr_links)
        graph.add_nodes_from(np.append(users, flwg))
        graph.add_edges_from(flwg_links)

        return graph

    def get_pub_repo_count(self):
        pub_repos_frame = psql.read_sql(self.query_pub_repo_count(), self.cnx)
        pub_repos_frame.fillna(0, inplace=True)
        pub_repos_frame.set_index('login', inplace=True)

        return pub_repos_frame


    def get_fork_count(self):
        fork_count_frame = psql.read_sql(self.query_fork_count(), self.cnx)
        fork_count_frame.set_index('login',inplace=True)
        fork_count_frame = fork_count_frame.merge(self.pub_repo_count_frame,
                                    how="left",
                                    left_index=True, right_index=True)
        fork_count_frame.dropna(inplace=True)
        fork_count_frame['fork_per_repo'] = fork_count_frame['fork_count']/fork_count_frame['public_repo_count']
        fork_count_frame.drop('public_repo_count', 1, inplace=True)

        return fork_count_frame

    def get_star_count(self):
        star_count_frame = psql.read_sql(self.query_star_count(), self.cnx)
        star_count_frame.set_index('login',inplace=True)
        star_count_frame = star_count_frame.merge(self.pub_repo_count_frame,
                                    how="left",
                                    left_index=True, right_index=True)
        star_count_frame.dropna(inplace=True)
        star_count_frame['star_per_repo'] = star_count_frame['star_count']/star_count_frame['public_repo_count']
        star_count_frame.drop('public_repo_count', 1, inplace=True)

        return star_count_frame

    def get_page_rank(self, filename='page_rank.pcl', create=False):
        pgrank_frame = None
        if create:
            self.graph = self.get_graph()
            pgrank_frame = pd.DataFrame.from_dict(nx.pagerank(self.graph), orient='index')
            pgrank_frame.rename(columns={0:'pagerank'}, inplace=True)
            pgrank_frame.index.name = 'login'
            pgrank_frame.to_pickle(filename)
        else:
            if filename is not None:
                pgrank_frame =  pd.read_pickle(filename)
            else:
                print "Filename required to load stored pagerank pickles!!"

        return pgrank_frame

    def get_repo_per_month(self):
        rpm_frame = psql.read_sql(self.query_repo_per_month(), self.cnx)
        rpm_frame.fillna(0, inplace=True)
        rpm_frame.set_index('login', inplace=True)
        rpm_frame['age'] = datetime.now() - rpm_frame['start_date']
        rpm_frame['age_month'] = rpm_frame.age.apply(lambda x: x.astype('timedelta64[D]')/np.timedelta64(30, 'D'))
        rpm_frame['repo_per_month'] = rpm_frame['public_repo_count']/rpm_frame['age_month']
        rpm_frame.drop(['public_repo_count','age'], 1, inplace=True)

        return rpm_frame

    def get_for_hire(self):
        for_hire_frame = psql.read_sql(self.query_is_hireable(), self.cnx)
        for_hire_frame.set_index('login', inplace=True)

        return for_hire_frame

    def get_has_blog(self):
        has_blog_frame = psql.read_sql(self.query_has_blog(), self.cnx)
        has_blog_frame.set_index('login', inplace=True)

        return has_blog_frame

    def get_has_loc(self):
        has_loc_frame = psql.read_sql(self.query_has_location(), self.cnx)
        has_loc_frame.set_index('login', inplace=True)
        return has_loc_frame

    def get_has_name(self):
        has_name_frame = psql.read_sql(self.query_has_name(), self.cnx)
        has_name_frame.set_index('login', inplace=True)
        return has_name_frame

    def get_has_email(self):
        has_email_frame = psql.read_sql(self.query_has_email(), self.cnx)
        has_email_frame.set_index('login', inplace=True)
        return has_email_frame

if __name__ == '__main__':
    db = GitDB()

