import networkx as nx
import pandas as pd
from git_db import GitDB
from git_score import GitScore

def generate_report(db, login, rep_count=0, star_count=0, fork_count=0, rpm=0):
    report = {}

    report['Number of Public Repos'] = int(rep_count)
    report['Stars Per Repo'] = float(star_count/(1.0*rep_count))
    report['Forks Per Repo'] = float(fork_count/(1.0*rep_count))
    report['Repos Per Month'] = float(rpm)

    name, email, location, start_date, avatar = db.get_user_info(login)
    report['Name'] = name or ''
    report['Email'] = email or ''
    report['Start Date'] = start_date.strftime("%B %d, %Y")

    pop_repo, lang = db.get_user_popular_repo(login) or ('','')
    #print lang
    report['Most Popular Repo Language'] = str(lang)

    pref_langs = [l[0] for l in db.get_user_pref_lang(login)[:3]]
    report['Language of Choice'] = pref_langs[0]

    return report


def main():
    db = GitDB(min_repo=6, max_repo=90, min_rpm=1/6.)
    score = GitScore(db)
    result_frame = score.result_frame.copy()
    smaller_frame = result_frame[['public_repo_count','star_count','fork_count','repo_per_month']]
    graph = nx.read_gpickle('github_cnx.gpcl')
    all_node = pd.DataFrame(graph.nodes(), columns=['login'])
    all_node.set_index('login', inplace=True)

    missing_df = all_node.merge(smaller_frame, how='left', left_index=True,
            right_index=True)
    missing_df = missing_df[missing_df.isnull().any(axis=1)]
    graph.remove_nodes_from(missing_df.index)


    for i, login in enumerate(smaller_frame.index[:]):
        if i%100==0: print i
        prc = smaller_frame.loc[login].public_repo_count
        sc = smaller_frame.loc[login].star_count
        fc = smaller_frame.loc[login].fork_count
        rpm = smaller_frame.loc[login].repo_per_month
        report = generate_report(db, login, prc, sc, fc, rpm)
        graph.node[login].update(report)
    nx.write_gpickle(graph, 'report_graph.gpcl')
    nx.write_gexf(graph, 'report_graph.gexf')

if __name__ == '__main__':
    main()
