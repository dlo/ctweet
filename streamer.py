#!/usr/bin/env python

import sys
import asyncore
import socket
import json
import bsddb
import urllib2
import getpass

WHITE = "\033[00;37m"
AQUA = "\033[01;36m"

class http_client(asyncore.dispatcher):

    def __init__(self, host, path, username, password):
        authorization = "%s:%s" % (username, password)
        authorization = authorization.encode("base-64")[:-1]

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, 80))
        self.buffer = 'GET %s HTTP/1.0\r\nAuthorization: Basic %s\r\n\r\n' % (path, authorization)
        self.tweet_buffer = ""
        self.db = bsddb.btopen("/tmp/twitter.db", 'c')

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        d = self.recv(8192)
        self.tweet_buffer += d.strip()

        tweet = self.tweet_buffer.split('\n')[-1]

        try:
            tweet = json.loads(tweet)
            print AQUA + "<tweet> " + WHITE + \
                    tweet['user']['screen_name'] + ": " + tweet['text']
        except Exception, e:
            print e, "+", tweet

        self.db.sync()

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

if __name__ == '__main__':
    username = sys.argv[1]
    password = getpass.getpass()
    c = http_client('stream.twitter.com', '/1/statuses/sample.json?delimited=length', username, password)
    asyncore.loop()


