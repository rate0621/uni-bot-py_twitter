from requests_oauthlib import OAuth1Session
from pytz import timezone
from datetime import datetime, timedelta
from time import sleep
import sys, os

import pytz
import json
import re
from pprint import pprint

# twitter.pyが置かれているディレクトリ直下をライブラリパスとして追加
here = os.path.join( os.path.dirname(os.path.abspath(__file__)))
sys.path.append(here)

import auth_file.authkey as authkey
import common_lib.uni_common_tools.ChunithmNet as ChunithmNet
import common_lib.markov.PrepareChain as PrepareChain
import common_lib.markov.GenerateText as GenerateText

class Twitter():
    def __init__(self):
        # 今はファイルから読み込んでいるけどデプロイするときはherokuの環境変数に入れる
        self.twitter = OAuth1Session(authkey.CONSUMER_KEY, authkey.CONSUMER_SECRET, authkey.ACCESS_TOKEN, authkey.ACCESS_TOKEN_SECRET)
    
    def get_userid_from_screen_name(self, screen_name):
        """
        screen_nameからuseridを取得する
        @param  screen_name(string)
        @return user_id(string)
        """
        params = {
            "screen_name": screen_name
        }
        res = self.twitter.get("https://api.twitter.com/1.1/users/show.json", params = params)

        timeline = json.loads(res.text)
        user_id = timeline["id_str"]
        return user_id

    def get_home_timeline(self):
        """
        自分のタイムラインを取得
        @param なし
        @return なし
        """
        params = {}
        res = self.twitter.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)

        timeline = json.loads(res.text)

        for tweet in timeline:
            print (tweet["text"])


    def post_tweet(self, text):
        """
        引数で渡された文字列を呟く
        @param text(string)
        @return res(int?)
        """
        params = {"status": text}
        res = self.twitter.post("https://api.twitter.com/1.1/statuses/update.json", params=params)
        print (res)


    def get_tweet_including_words(self, search_word):
        '''
        引数で渡した単語を含むツイートを取得する
        @param search_word(string)
        @return tweet_list(json)
        '''

        url = "https://api.twitter.com/1.1/search/tweets.json?"
        params = {
            #"q": unicode(search_words, "utf-8"),
            "q": search_word.encode("utf-8"),
            "lang": "ja",
            "result_type": "recent",
            "count": "100"
        }

        res = self.twitter.get(url, params = params)
        tweet_list = json.loads(res.text)

        return tweet_list


    def get_tweet_specific_user(self, screen_name):
        """
        特定ユーザのツイートを取得する
        @param  screen_name(string)
        @return tweet_list(json)
        """

        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {
            #"q": unicode(search_words, "utf-8"),
            "screen_name": screen_name.encode("utf-8"),
            "include_rts": "false",
            "exclude_replies": "false",
            "count": "200"
        }

        res = self.twitter.get(url, params = params)
        tweet_list = json.loads(res.text)

        return tweet_list

    def __output_to_file(self, tweet_list):
        """
        !!ファイルに出力するのはこのクラスに実装すべきではないので外出しする!!
        get_tweet_specific_userやget_tweet_including_wordsなどから返ってきたtweet_listをテキストファイルに出力
        @param tweet_list(json)
        @return file_name(string)
        """

        file_name = here + "/common_lib/tweet.txt"

        with open(file_name, "w") as f:
            # https://api.twitter.com/1.1/search/tweets.jsonから取得したときのループ
            if 'statuses' in tweet_list:
                for tweet in tweet_list["statuses"]:
                    tweet_text = tweet["text"]
                    tweet_text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", tweet_text)  # http(s)的な文字列の削除
                    tweet_text = re.sub(r'@\w+', "", tweet_text) # 「@hogehoge 今日暇？」 を、「今日暇？」に書き換え

                    f.write(tweet_text)
                    f.flush()

            # https://api.twitter.com/1.1/statuses/user_timeline.jsonから取得したときのループ
            else:
                for tweet in tweet_list:
                    tweet_text = tweet["text"]
                    tweet_text = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", tweet_text)  # http(s)的な文字列の削除
                    tweet_text = re.sub(r'@\w+', "", tweet_text) # 「@hogehoge 今日暇？」 を、「今日暇？」に書き換え

                    f.write(tweet_text)
                    f.flush()
        
        return file_name

    def tweet_markov_from_specific_user(self, screen_name):
        """
        !!マルコフ連鎖で文章を作るのも外だしする!!
        渡されたscreen_name（ユーザ名）の過去のツイートを取得してマルコフ連鎖を用いて文章を生成して呟く
        @param  screen_name(string)
        @return なし
        """
        tweet_list = self.get_tweet_specific_user(screen_name)
        file_name = self.__output_to_file(tweet_list)
        chain = PrepareChain.PrepareChain(file_name)
        triplet_freqs = chain.make_triplet_freqs()
        chain.save(triplet_freqs, True)
        generator = GenerateText.GenerateText(2)
        gen_text = generator.generate()
        #tw.post_tweet(gen_text + "【このツイートは自動生成されたものです】")
        print (gen_text + "【このツイートは自動生成されたものです】")

    def tweet_markov_from_specific_word(self, search_word):
        """
        !!マルコフ連鎖で文章を作るのも外だしする!!
        渡されたsearch_word（検索文字列）を含むツイートを取得してマルコフ連鎖を用いて文章を生成して呟く
        @param  search_word(string)
        @return なし
        """
        tweet_list = self.get_tweet_including_words(search_word)
        file_name = self.__output_to_file(tweet_list)
        chain = PrepareChain.PrepareChain(file_name)
        triplet_freqs = chain.make_triplet_freqs()
        chain.save(triplet_freqs, True)
        generator = GenerateText.GenerateText(4)
        gen_text = generator.generate()
        #tw.post_tweet(gen_text + "【このツイートは自動生成されたものです】")
        print (gen_text + "【このツイートは自動生成されたものです】")

    def streaming(self, follow=None, track=None):
        """
        いったん以下のコードで自分の呟きをリアルタイムで取得できる
        受け取ったテキストによって色々処理をわけたりできそうで夢が広がるけどいったん保留
        注意点として、垂れ流す対象のユーザを指定できるが、screen_nameではなく、user_idのため、
        get_userid_from_screen_nameからuser_idを引っ張ってきてから使うこと
        """

        # 引数チェック
        if all((follow is None, track is None)):
            raise ValueError({'message': "No filter parameters specified."})

        data = {}
        if follow is not None:
            data['follow'] = ','.join(follow)
        if track is not None:
            data['track'] = ','.join(track)


        url = "https://stream.twitter.com/1.1/statuses/filter.json"
        res = self.twitter.post(url, stream=True, data=data)
        print ("準備OK")
        for line in res.iter_lines():
            if line:
                decode_line = json.loads(line.decode("utf-8"))
                yield decode_line

    def user_stream(self):
        url = "https://userstream.twitter.com/1.1/user.json"

        res = self.twitter.get(url, stream=True)

        for line in res.iter_lines():
            if line:
                print (line)


if __name__ == '__main__':
    tw = Twitter()
    #tw.tweet_markov_from_specific_user("chatrate")
    tw.tweet_markov_from_specific_word("プリコネ")
    
    #tw.get_userid_from_screen_name("chatrate")
    #tw.user_stream()
    
    ### ウニのプレイログを呟く
    #tw.tweet_playlog()
    
    ### ストリーミング
    #tw.stream()
