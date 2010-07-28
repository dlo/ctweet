Requirements
============

* [Python 2.6+](http://www.python.org/download/releases/2.6.5/)
* [A Twitter account](http://www.twitter.com/)
* An internet connection (duh)

Usage
=====

Well, there's not much to it. Just run

    ./ctweet.py <screen_name>

You'll get prompted for your password (don't worry, it will not get sent to my
personal stolen passwords server, I promise), and off you go.

Caching is done locally via Berkeley DB (in a file calling `/tmp/twitter.db`),
so it's doubtful you'll hit the Twitter API rate limit.

Contributing
============

Send me a pull request on Github, and I'll add your patch if it adds features
or fixes something that's broken.

Wish List
=========

  * Tweet while watching the stream.
  * Save password after first use.

Release Notes
=============

0.4 (07/28/2010)

  * Add Growl notifications, stop notifications on command line.

0.3 (04/20/2010)

  * Add more contextual info for follows.

0.2 (04/20/2010)

  * Clean up how deletions are displayed.

0.1 (04/20/2010)

  * Implementation for `tweet`, `follow`, `favorite`, `unfavorite`, and `retweet`.

License
=======

Copyright &copy; 2010 Dan Loewenherz.

See LICENSE for details.
