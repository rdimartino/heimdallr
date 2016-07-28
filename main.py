#!/usr/bin/env python
from bs4 import BeautifulSoup
from time import sleep
import requests
import dateutil.parser
import twitter
import settings

api = twitter.Api(consumer_key=settings.consumer_key,
                  consumer_secret=settings.consumer_secret,
                  access_token_key=settings.access_token_key,
                  access_token_secret=settings.access_token_secret)
url = 'http://projects.fivethirtyeight.com/2016-election-forecast/index.html'
history = '/var/www/heimdallr/update.txt'


# Soup processing functions
def span_has_data_tag(tag):  # Soup filter to find timestamps
    return tag.name == 'span' and tag.has_attr('data-timestamp')


def get_timestamp(soup):  # Returns maximum timestamp from 538
    return max([dateutil.parser.parse(tag['data-timestamp']) for tag in soup.find_all(span_has_data_tag)])


def get_data(soup):  # Returns list of tuples with candidate probabilities
    tags = (soup
            .find('div', {'data-card-id':'US-winprob-sentence'})
            .find('div', class_='powerbarnoheads')
            .find_all('p', class_='candidate-val winprob'))
    return [(tag.next_sibling.string, tag['data-party'], tag.contents[0]) for tag in tags]


# Tweet functions
def tweet(data, timestamp):  # Post the tweet
    status = ('2016 Presidential Election Probabilities!\n'
              + ''.join(['{0} - {1}%\n'.format(format_name(d[0]), d[2]) for d in data])
              + 'Updated: {:%b %d, %H:%M:%S} UTC\n'.format(timestamp)
              + url)
    try:
        api.PostUpdate(status, verify_status_length=False)
    except:
        pass
    return None


def format_name(name):  # Takes fullname and returns last name
    return name.split()[-1]


# Timestamp logging functions
def recover_timestamp():  # Recovers timestamp from history txt file
    with open(history, 'r') as h:
        timestamp = h.read()
    if not timestamp:
        timestamp = '2016-07-07T13:46:08.000Z'
    return timestamp


def record_timestamp(timestamp):  # Records timestamp in history txt file
    with open(history, 'w') as h:
        h.write(timestamp + '\n')


if __name__ == '__main__':
    newest_update = dateutil.parser.parse(recover_timestamp())
    print(api.VerifyCredentials())
    while True:
        result = requests.get(url)
        if result.status_code == 200:
            page = result.content
            soup = BeautifulSoup(page, 'html.parser')
            last_update = get_timestamp(soup)
            if last_update > newest_update:
                tweet(get_data(soup), last_update)
                newest_update = last_update
                record_timestamp(str(newest_update))
        else:
            pass
        sleep(600)


# Tests
def run_tests():
    print('\n1) Testing Twitter API permissions:')
    print(api.VerifyCredentials())
    print('\n2) Testing last recorded timestamp:')
    print(recover_timestamp())
    print('\n3) Testing 538 connection:')
    result = requests.get(url)
    print('Status code: {}'.format(result.status_code))
    soup = BeautifulSoup(result.content, 'html.parser')
    print('Timestamp: '),
    print(get_timestamp(soup))
    print('Data: '),
    print(get_data(soup))
    print('\n4) Testing tweet:')
    print(api.PostUpdate('This is a test of the tweet broadcast system.'))
