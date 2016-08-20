import pdb
import subprocess
import statistics
import time
import argparse
import requests
import os
import json

MAX_HISTORY = 25*7 # 1 week
def to_filename(s):
    return s.split('/')[-2] + '.json'

class DB(object):
    def __init__(self, directory):
        self.directory = directory
        self.sources = json.loads(
            open(
                os.path.join(directory, 'subreddits.json')
            ).read()
        )

    def update_subreddit(self, subreddit, data):
        subreddit_json = to_filename(subreddit)
        path = os.path.join(self.directory, subreddit_json)
        if os.path.exists(path):
            current_data = json.loads(open(path).read())
        else:
            current_data = []
        new_data = sorted(
            data + current_data,
            key=lambda post: post['created']
        )
        uniq_dict = {}
        for post in new_data:
            uniq_dict[post['id']] = post
        open(path, 'w+').write(json.dumps(list(uniq_dict.values())))

    def posts(self, subreddit, percentile=0.33):
        filename = to_filename(subreddit)
        try:
            posts = json.loads(open(os.path.join(self.directory, filename)).read())
        except Exception:
            posts = []

        posts.sort(key=lambda post: post['score'])
        n = len(posts)
        return posts[int(n-n*percentile):]

    def sent_articles(self):
        try:
            sent_articles = json.loads(open(os.path.join(self.directory, 'sent.json')).read())
        except Exception:
            sent_articles = []
        return sent_articles

    def mark_sent(self, article):
        filename = os.path.join(self.directory, 'sent.json')
        try:
            sent_articles = json.loads(open(filename).read())
        except Exception:
            sent_articles = []
        sent_articles += [article]
        open(filename, 'w+').write(json.dumps(sent_articles))


class DataFetcher(object):
    REDDIT_URL = "https://www.reddit.com"
    def __init__(self):
        pass

    def subreddit(self, name):
        subreddit_json = name[0:-1] + '.json'
        while True:
            print('requesting {}'.format(subreddit_json))
            response = requests.get(DataFetcher.REDDIT_URL + subreddit_json)
            response_json = json.loads(response.text)
            if response_json.get('error') == 429:
                time.sleep(1)
            else:
                break
        def tidy_up(post):
            return {
                'id': post['data']['id'],
                'title': post['data']['title'],
                'score': post['data']['score'],
                'url': post['data']['url'],
                'created': post['data']['created'],
            }

        return list(map(
            tidy_up,
            response_json['data']['children']
        ))

class NewsLetter(object):
    def __init__(self, directory):
        self.db = DB(directory)
        self.data_fetcher = DataFetcher()

    def list_subreddits(self, args):
        for source in self.db.sources:
            print("{}, {}".format(source['subreddit'], source['percentile']))

    def update_subreddits(self, args):
        for source in self.db.sources:
            subreddit = source['subreddit']
            data = self.data_fetcher.subreddit(subreddit)
            self.db.update_subreddit(subreddit, data)

    def get_new_articles(self, args):
        return {
            source['subreddit']: self.db.posts(source['subreddit'], source['percentile'])
            for source in self.db.sources
        }

    def send_new_articles(self, args):
        # get articles
        new_articles = self.get_new_articles(args)
        # compare with sent articles
        sent_articles = set([
            article['id']
            for article in self.db.sent_articles()
        ])
        def flatten_articles(new_articles):
            for sub, articles in new_articles.items():
                for article in articles:
                    article['subreddit'] = sub
                    yield article
        unsent_articles = list(filter(
            lambda article: article['id'] not in sent_articles,
            flatten_articles(new_articles)
        ))
        # send articles in email format
        for article in unsent_articles:
            title = "[RSS][{}] ({}) - {}".format(article['subreddit'], article['score'], article['title'])
            body = """
            {}
            """.format(article['url']).encode('utf-8')
            # send article
            p = subprocess.Popen([
                "mailx", "-s", title, args.email
            ], stdin=subprocess.PIPE)
            p.communicate(body)
            #print(" ".join(["mailx", "-s", title, args.email]))
            # mark as sent
            self.db.mark_sent(article)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory')
    parser.add_argument('--email')
    parser.add_argument('command')
    args = parser.parse_args()

    nl = NewsLetter(args.directory)
    method = getattr(nl, args.command)
    method(args)
