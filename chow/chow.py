'''
Chow - Slack bot that randomly pairs people for lunch.
'''

import re
import sys
import random
from os import path
from string import Template
from datetime import date
from tinydb import TinyDB, Query
from itertools import izip_longest
from collections import Counter
from slackbot.bot import Bot, respond_to, listen_to


PWD = path.dirname(path.abspath(__file__))
USERS = TinyDB(path.join(PWD, 'users.json'))
CHOWS = TinyDB(path.join(PWD, 'chows.json'))
SLACK = None


HELP = '''I can pair you up with a random coworker for lunch.
If you are game, just type *Im in*. If you change your mind, type *Im out*.
Just before lunch, if you are in, I will IM you the name of your partner.
After lunch, you, can anonymously rate your partner by using Emojis.
'''

WELCOME = '''Hello, welcome and thanks for being awesome!
I am going to pair you up with a random coworker at lunch.
If at anytime, you feel the urge to chicken out, just shout: *Im out*.
If you need help, type *help*.'''

CHICKEN = '''Well, well, well.
So, if you want in again, type: *Im in*.
Just in case you didn't want to miss out on all the fun!
Or, maybe you are the careful type? just shout *help*.'''

LUNCH = '''Hey!
You will be having lunch with... <@$pair>
Do add an anonymous (and scandulous?) Emoji as a reaction to this message.
This Emoji *may* describe your lunch experience.
'''

ETC_IN = '''Hey there.
I see you have already signed up for lunch.
If you want out, just shout *IM A CHICKEN!*.
Sorry that was attempted humour.
Yeah, just type: *Im out*.
If you need help, just type: *help*.'''

ETC_OUT = '''Hey there.
I see you haven't signed up for lunch.
This little puppy will die if you don't.
Maybe not, but still if you want in, just say: *Im in*.
Or if you need help, just type: *help*.'''


@respond_to('help', re.IGNORECASE)
def help(message):
    message.reply(HELP)


@respond_to('im in', re.IGNORECASE)
def im_in(message):
    user = Query()
    if USERS.get(user.id == message.body['user']) is None:
        USERS.insert({'id': message.body['user']})
    return message.reply(WELCOME)


@respond_to('im out', re.IGNORECASE)
def im_out(message):
    user = Query()
    if not USERS.update(user.id == message.body['user']) is None:
        USERS.remove(user.id == message.body['user'])
    return message.reply(CHICKEN)


@respond_to('lunch', re.IGNORECASE)
def lunch(message):
    # We shall only respond if this is sent by slackbot
    #if not message.body['user'] == 'USLACKBOT':
    #    return message.reply('''/giphy hungry''')
    # Record reactions
    chow = Query()
    CHOWS.update(save_reaction(), chow.reaction == None)
    # Pair participants and send invites
    users = map(lambda x: x['id'], USERS.all())
    pairs = random_pairs(users)
    for user1, user2 in pairs:
        tpl = Template(LUNCH)
        send_invite(user1, user2, tpl)
        send_invite(user2, user1, tpl)
    # Reset USERS
    USERS.purge()


@respond_to('debug', re.IGNORECASE)
def debug(message):
    print USERS.all(), CHOWS.all()
    message.reply('Into the logs it went :+1:')


@respond_to('gravy @(.*)', re.IGNORECASE)
def gravy(message, username):
    # Get user id, return error if not found
    users = SLACK.users.list().body['members']
    user = filter(lambda x: x['name'] == username, users)
    if len(user) == 0:
        return message.reply('Sorry. I do not know him/her. /giphy anonymous')
    # Get all reactions for this user
    chow = Query()
    reactions = map(lambda x: x['reaction'], CHOW.search(chow.user == user))
    hist = list(Counter(a).iteritems())[:3]
    gravy = map(lambda (x, y): ':%s:: %d' % (x, y), hist)
    return message.reply(' '.join(gravy))


def save_reaction():
    def transform(user):
        user['reaction'] = get_reaction(user['pair'])
    return transform


def send_invite(user, pair, tpl):
    ch = SLACK.im.open(user).body['channel']['id']
    SLACK.chat.post_message(ch, tpl.substitute(pair=pair),
        as_user=True, unfurl_media=True)
    CHOWS.insert(
        {
            'date': str(date.today()),
            'user': user,
            'pair': pair,
            'reaction': None,
        }
    )


def get_reaction(user):
    ch = SLACK.im.open(user).body['channel']['id']
    msgs = SLACK.im.history(ch).body['messages']
    lunch_msgs = filter(lambda x: 'You will be having lunch with' in x, msgs)
    if len(lunch_msgs) > 0:
        msg = lunch_msgs.sort(key=lambda x: x['ts']).pop()
        if 'reaction' in msg:
            return reaction['name']
    return ''


def random_hackernews():
    '''Gets a random article from top hackernews stories.'''
    api_base = 'https://hacker-news.firebaseio.com/v0/'
    latest_articles = json.loads(requests.get(api_base + 'topstories.json').text)
    url = api_base + 'item/' + str(random.choice(latest_articles)) + '.json'
    random_article = requests.get(url).json()
    return random_article['url']


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # Taken from itertools recipes:
    # https://docs.python.org/2/library/itertools.html#recipes
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def random_pairs(iterable, spare=None):
    '''Returns random pairs from given set.'''
    random.shuffle(iterable)
    return grouper(iterable, 2, fillvalue=spare)


def main():
    bot = Bot()
    global SLACK
    SLACK = bot._client.webapi
    bot.run()


if __name__ == "__main__":
    main()
