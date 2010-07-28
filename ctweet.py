#!/usr/bin/env python

import sys
import asyncore
import socket
import json
import bsddb
import urllib2
import getpass
import Growl as growl

notifier = growl.GrowlNotifier("Twitter Update", [""])
notifier.register()

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
        self.connect((host, 80))
        self.send_buffer = 'GET %s HTTP/1.0\r\nAuthorization: Basic %s\r\n\r\n' % (path, authorization)
        self.receive_send_buffer = ""
        self.db = bsddb.btopen("/tmp/twitter.db", 'c')

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(8192)
        self.receive_send_buffer += data

        if self.receive_send_buffer == "":
            return

        if self.receive_send_buffer.endswith("\r\n"):
            try:
                data = json.loads(self.receive_send_buffer)
            except:
                data = {}

            if 'delete' in data:
                key = 'user_%s' % data['delete']['status']['user_id']
                source = self.db.get(key)
                if not source:
                    source = user_info(data['delete']['status']['user_id'])
                    self.db[key] = source
                source_data = json.loads(source)

                image_data = urllib2.urlopen(source_data['profile_image_url']).read()
                icon = growl.Image.imageWithData(image_data)
                notifier.notify(noteType = "", title = source_data['screen_name'], description = \
                  "%s deleted a tweet (%d)" % (source_data['screen_name'], \
                  data['delete']['status']['id']), icon = icon)

            elif 'event' in data:
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

                if data['event'] in ['favorite', 'unfavorite', 'retweet']:
                    key = 'tweet_%s' % data['target_object']['id']
                    tweet = self.db.get(key)
                    if not tweet:
                        tweet = tweet_info(data['target_object']['id'])
                        self.db[key] = tweet
                    tweet_data = json.loads(tweet)

                    notifier.notify(noteType = "", title = data['event'], description = \
                        "%s by %s, %s: %s" % (data['event'], source_data['screen_name'], target_data['screen_name'],
                            tweet_data['text']))
                elif data['event'] == 'follow':
                    notifier.notify(noteType = "", title = 'follow', description = \
                        "%s started following %s" % (source_data['screen_name'], target_data['screen_name']))
                else:
                    notifier.notify(noteType = "", title = 'unknown', description = \
                        "source: %s, target: %s" % (source_data['screen_name'], target_data['screen_name']))

            elif 'id' in data:
                image_data = urllib2.urlopen(data['user']['profile_image_url']).read()
                icon = growl.Image.imageWithData(image_data)
                notifier.notify(noteType = "", title = data['user']['screen_name'], description = \
                  data['text'], icon = icon)

            self.receive_send_buffer = ""

        self.db.sync()

    def writable(self):
        return (len(self.send_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.send_buffer)
        self.send_buffer = self.send_buffer[sent:]

if __name__ == '__main__':
    username = sys.argv[1]
    password = getpass.getpass()
    c = http_client('chirpstream.twitter.com', '/2b/user.json', username, password)
    asyncore.loop()

