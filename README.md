# Chow

Slack bot that pairs random people for lunch.


## The problem

I noticed at Duedil that a lot of people preferred having lunch with their team. This is understandable as people want to stay in their comfort zone but it is also a lost opportunity for Duedil on at least 3 counts:

1) Lunch is a great for communication across teams and cross pollination of ideas.

2) Lunch is awesome for ensuring that people who are shy, socially awkward, from half way across the planet or a combination thereof are not left isolated.

3) Lunch is an excuse to make new friends. More happiness. Less turnover.


## The solution

Many ways to do this. I wrote a slack bot. His name is Chow.

    me: Hello Chow!

    chow: Hey there! I see you haven't signed up for the next lunch. If you want in, just type "Count me in", If you need help about anything else, just type "Help".

    me: Help!

    chow: NP. So I can pair you up with a random coworker for lunch. If you are game, just type "I'm in". If you change your mind, type "I'm out". Just before lunch, if you are in, I will IM you the name of your partner. After lunch, you can rate your partner by responding to me message using an Emoji reaction. Your reaction will contribute (anonymously) to your partner's "gravy" - 3 most frequent emojis that his colleagues used to rate him. Yes you may, just type: "Gravy for @me".

    me: I am in!

    chow: You are awesome! See you at lunch! /giphy happy

    me: Hey chow!

    chow: Hello @me! Looking forward to your lunch? If not, just type "I'm out". If you need help about anything else, just type "Help".

    me: I'm out.

    chow: Chicken. /giphy chicken

    me: I am in again!

    chow: You are awesome! See you at lunch! /giphy happy

    ... Lunchtime ...

    chow: Hey @me, you are having lunch with @him today. If you enjoy it or otherwise, you can give feedback using Slack reactions to this message. Your feedback will be anonymous and fun! Now go: /giphy lunch