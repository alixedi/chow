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

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.utils import to_utf8
from slackbot.bot import Bot, respond_to, PluginsManager
from slackbot.dispatcher import MessageDispatcher


PWD = path.dirname(path.abspath(__file__))
USERS = TinyDB(path.join(PWD, 'users.json'))
CHOWS = TinyDB(path.join(PWD, 'chows.json'))
SLACK = None
ADMIN = 'alixedi'


HELP = '''I can pair you up with a random coworker for lunch.
If you are game, just type *I am in*. If you change your mind, type *I am out*.
Just before lunch, if you are in, I will IM you the name of your partner.
After lunch, you, can anonymously rate your partner by using Emojis.
'''

WELCOME = '''Hello, welcome and thanks for being awesome!
I am going to pair you up with a random coworker at lunch.
If at anytime, you feel the urge to chicken out, just shout: *I am out*.
If you need help, type *help*.'''

CHICKEN = '''Well, well, well.
So, if you want in again, type: *I am in*.
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
Yeah, just type: *I am out*.
If you need help, just type: *help*.'''

ETC_OUT = '''Hey there.
I see you haven't signed up for lunch.
This little puppy will die if you don't.
Maybe not, but still if you want in, just say: *I am in*.
Or if you need help, just type: *help*.'''

ODD = '''Hey! I'm sorry I couldn't pair you up today because odd numbers.'''


class MyMessageDispatcher(MessageDispatcher):

    def _default_reply(self, msg):
        self._client.rtm_send_message(msg['channel'], to_utf8(HELP))


class MyBot(Bot):

    def __init__(self):
        self._client = SlackClient(
            settings.API_TOKEN,
            bot_icon = settings.BOT_ICON if hasattr(settings, 'BOT_ICON') else None,
            bot_emoji = settings.BOT_EMOJI if hasattr(settings, 'BOT_EMOJI') else None
        )
        self._plugins = PluginsManager()
        self._dispatcher = MyMessageDispatcher(self._client, self._plugins)


@respond_to('help', re.IGNORECASE)
def help(message):
    message.reply(HELP)


@respond_to('i am in', re.IGNORECASE)
def im_in(message):
    user = Query()
    if USERS.get(user.id == message.body['user']) is None:
        USERS.insert({'id': message.body['user']})
    return message.reply(WELCOME)


@respond_to('i am out', re.IGNORECASE)
def im_out(message):
    user = Query()
    if not USERS.get(user.id == message.body['user']) is None:
        USERS.remove(user.id == message.body['user'])
    return message.reply(CHICKEN)


@respond_to('lunchtime', re.IGNORECASE)
def lunch(message):
    # We shall only respond if this is sent by admin
    admin = get_user_id(ADMIN)
    if not message.body['user'] == admin:
        return message.reply('Meh...')
    # Record reactions
    chow = Query()
    CHOWS.update(save_reaction(), chow.reaction == None)
    # Pair participants and send invites
    users = map(lambda x: x['id'], USERS.all())
    pairs = random_pairs(users)
    for user1, user2 in pairs:
        if user2 is None:
            send_im(user1, ODD)
        else:
            send_invite(user1, user2)
            send_invite(user2, user1)
    # Reset USERS
    USERS.purge()


@respond_to('debug', re.IGNORECASE)
def debug(message):
    # We shall only respond if this is sent by admin
    admin = get_user_id(ADMIN)
    if message.body['user'] == admin:
        return message.reply('%s %s' % (USERS.all(), CHOWS.all()))
    return message.reply('You are not my master!')


@respond_to('feedback (.*)', re.IGNORECASE)
def feedback(message, username):
    # Get user id, return error if not found
    user = get_user_id(username)
    if user == None:
        return message.reply('Sorry. I do not know him/her.')
    # Get all reactions for this user
    chow = Query()
    reactions = map(lambda x: x['reaction'],
        CHOWS.search((chow.user == user)
                   & (chow.reaction != None)
                   & (chow.reaction != '')
        )
    )
    if len(reactions) > 2:
        hist = list(Counter(reactions).iteritems())[:3]
    else:
        return message.reply('You need to lunch 3 times to have a feedback.')
    feedback = map(lambda (x, y): ':%s:: %d' % (x, y), hist)
    message.reply(' '.join(feedback))


def get_user_id(username):
    users = SLACK.users.list().body['members']
    user = filter(lambda x: x['name'] == username, users)
    if len(user) > 0:
        return user[0]['id']


def save_reaction():
    def transform(user):
        user['reaction'] = get_reaction(user['pair'])
    return transform


def send_im(user, im):
    ch = SLACK.im.open(user).body['channel']['id']
    SLACK.chat.post_message(ch, im, as_user=True, unfurl_media=True)


def send_invite(user, pair):
    tpl = Template(LUNCH)
    send_im(user, tpl.substitute(pair=pair))
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
    lunch_msgs = filter(lambda x: 'You will be having lunch with' in x['text'], msgs)
    if len(lunch_msgs) > 0:
        lunch_msgs.sort(key=lambda x: x['ts'])
        msg = lunch_msgs.pop()
        if 'reactions' in msg:
            return msg['reactions'][0]['name']
    return 'x'


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
    bot = MyBot()
    global SLACK
    SLACK = bot._client.webapi
    bot.run()


if __name__ == "__main__":
    main()
