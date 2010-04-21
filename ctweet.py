#!/usr/bin/env python

import sys
import asyncore
import socket
import json
import bsddb
import urllib2
import getpass

GREEN = "\033[01;32m"
RED = "\033[01;31m"
WHITE = "\033[00;37m"
AQUA = "\033[01;36m"

def tweet_info(tweet_id = 1234):
    url = "http://api.twitter.com/1/statuses/show.json?id=%d" % tweet_id
    response = urllib2.urlopen(url)
    return response.read()

def user_info(user_id = 1234):
    url = "http://api.twitter.com/1/users/show.json?user_id=%d" % user_id
    response = urllib2.urlopen(url)
    return response.read()

class http_client(asyncore.dispatcher):

    def __init__(self, host, path, username, password):
        authorization = "%s:%s" % (username, password)
        authorization = authorization.encode("base-64")[:-1]

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (host, 80) )
        self.buffer = 'GET %s HTTP/1.0\r\nAuthorization: Basic %s\r\n\r\n' % (path, authorization)
        self.tweet_buffer = ""
        self.db = bsddb.btopen("/tmp/twitter.db", 'c')

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        d = self.recv(8192)
        self.tweet_buffer += d

        try:
            for item in self.tweet_buffer.split("\r\n"):
                lb_count = self.tweet_buffer.count('{')
                rb_count = self.tweet_buffer.count('}')

                if lb_count == rb_count and len(self.tweet_buffer) > 0:
                    left_brace = self.tweet_buffer.index('{')
                    right_brace = self.tweet_buffer.rindex('}')
                    data = json.loads(self.tweet_buffer[left_brace:right_brace+1])

                    if 'delete' in data:
                        key = 'user_%s' % data['delete']['status']['user_id']
                        source = self.db.get(key)
                        if not source:
                            source = user_info(data['delete']['status']['user_id'])
                            self.db[key] = source
                        source_data = json.loads(source)

                        print RED + "<deletion>" + WHITE + \
                                " %s deleted a tweet (%d)" % (source_data['screen_name'], data['delete']['status']['id'])
                    elif 'event' in data:
                        if data['event'] in ['favorite', 'unfavorite', 'retweet']:
                            key = 'tweet_%s' % data['target_object']['id']
                            tweet = self.db.get(key)
                            if not tweet:
                                tweet = tweet_info(data['target_object']['id'])
                                self.db[key] = tweet
                            tweet_data = json.loads(tweet)

                            key = 'user_%s' % data['source']['id']
                            source = self.db.get(key)
                            if not source:
                                source = user_info(data['source']['id'])
                                self.db[key] = source
                            source_data = json.loads(source)

                            key = 'user_%s' % data['target']['id']
                            target = self.db.get(key)
                            if not target:
                                target = user_info(data['target']['id'])
                                self.db[key] = target
                            target_data = json.loads(target)

                            print GREEN + "<%s> " % data['event'] + WHITE + \
                                    "by %s, %s: %s" % (source_data['screen_name'], target_data['screen_name'], tweet_data['text'])
                        else:
                            print GREEN + "<%s> " % data['event'] + WHITE + \
                                    "source: %s, target: %s" % (data['source']['id'], data['target']['id'])
                    elif 'id' in data:
                        print AQUA + "<tweet> " + WHITE + \
                                data['user']['screen_name'] + ": " + data['text']

                    self.tweet_buffer = ""
        except Exception, e:
            pass

        self.db.sync()

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

if __name__ == '__main__':
    username = sys.argv[1]
    password = getpass.getpass()
    c = http_client('chirpstream.twitter.com', '/2b/user.json', username, password)
    asyncore.loop()

