#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on:  25.07.2016 00:04:40 EDT

@author : Edward Holmes
@email:  edward@edward-viral-laptop

Version: 0.01

==== API urls ========
https://api.airbnb.com/v2/search_results?
https://api.airbnb.com/v2/reviews?
https://api.airbnb.com/v2/users/(user ID here)?
https://api.airbnb.com/v2/listings/(listing ID here)?
'''

#------compatibility imports--------------------------------#
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from six import iteritems, BytesIO, StringIO, add_metaclass
#-----------------------------------------------------------#

import copy
import json
import requests

try:
    import pandas as pd
except ImportError:
    pass

from . import authorizer, googlemaps
from . authorizer import CLIENT_ID, headers
from abc import abstractmethod, ABCMeta
from PIL import Image
from requests import HTTPError

API_URL = 'https://api.airbnb.com/v2/'


@add_metaclass(ABCMeta)
class AuthSetup(object):
    '''
    Airbnb authorization setup base class
    '''
    def __init__(self, auth=None):
            self.api_url = API_URL
        self.auth = auth or authorizer.current_auth
        self.session = None
        self.uid = None
        self.token = None

        try:
            self._setup_auth()
        except AttributeError:
            self.session = requests.Session()
            self.session.headers = headers
            self.uid = 'client_id={}'.format(CLIENT_ID)

    def _setup_auth(self):
        auth = self.auth
        self.uid = auth.uid
        self.token = auth.token
        self.session = auth.session
        return


class Searcher(AuthSetup):
        '''
        Search airbnb using various class get methods. The methods return Query
        objects with semi-organized data. Query objects are also stored in 
        various class variables (listings, users, reviews, etc...)

        Available search methods:
            - get_listings()
            - get_listing()
            - get_user()
            - get_reviews()

        Parameters
        ----------
        auth : Auth instance, default None
            A pyairbnb Auth object to use for connecting to airbnb with a valid
            username and password.
        '''
    def __init__(self, auth=None):
        super(Searcher, self).__init__(auth)
        self.listings = None
        self.searches = {}
        self.users = {}
        self.reviews = None
        self.last_url = ''

    def get_listings(self, location='', **kwargs):
        '''
        Gather all airbnb listings from a location.

        Parameters
        ----------
        location : str, default ""
            A location (e.g. "Portland, ME") to search for airbnb listings
        kwargs : various
            Additional parameters to pass to airbnb api url. See api
            documentation for available paramters.

        Returns
        -------
        Search instance with all attached listings
        '''
        search = Search(query=data, auth=self.auth)
        self.listings = search
        self.searches.update({location:search})
        return search

    def get_user(self, user_id, **kwargs):
        session = self.session
        endpoint = 'users/{}?'.format(user_id)
        url = self._setup_url(endpoint, **kwargs)
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        user = User(data)
        self.users.update({user.user_id:user})
        return user

    def get_reviews(self):
        pass

    def get_listing(self, listing_id):
        pass

    def scan(self):
        pass


@add_metaclass(ABCMeta)
class Query(AuthSetup):
    '''
    Base class for query objects.
    '''
    def __init__(self, query=None, auth=None):
        super(Query, self).__init__(auth)
        self.query = query
        self.results = None
        self.image_fields = []
        self.images = {}
        self._viewer = None

    def __str__(self):
        self.results

    @abstractmethod
    def _parse_query(self):
        pass

    def _setup_url(self, endpoint, **kwargs):
        access = self.uid
        api_url = self.api_url
        params = ['{!s}={!s}'.format(k, v) for k,v in iteritems(kwargs)]
        params = '&{}'.format('&'.join(params))
        url = ('{api_url}{endpoint}{access}{params}'
               ''.format(api_url=api_url,
                         endpoint=endpoint,
                         access=access,
                         params=params))
        return url

    def _view(self):
        '''
        Generator for view method
        '''
        images = self.images

        for key in images:
            res = requests.get(self.images[key])
            img = Image.open(StringIO(res.content))
            yield img.show()

    def view(self):
        '''
        Cycle through and download an image for a user or listing
        '''
        if not self._viewer:
            self._viewer = self._view()

        try:
            self._viewer.next()
        except StopIteration:
            self._viewer = None
            self.view()
        return


class Search(Query):
    def __init__(self, location='', query=None, auth=None, **kwargs):
        super(Search, self).__init__(query, auth)
        self.image_fields = ['picture_count',
                             'picture_url',
                             'picture_urls',
                             'thumbnail_url',
                             'xl_picture_url',
                             'xl_picture_urls']
        self._parse_query()

        if location and not query:
            self.get_listings(location, **kwargs)

    def __str__(self):
        return self.results.to_string()

    def _parse_query(self):
        query = copy.deepcopy(self.query)

        if not query:
            return

        metadata = query['metadata']
        res = query['search_results']
        listings = {l['listing']['id']:l['listing'] for l in res}

        ## seperate some fields ##
        users = {k:v.pop('user') for k, v in iteritems(listings)}
        hosts = {k:v.pop('primary_host') for k, v in iteritems(listings)}
        quotes = {k:v.pop('pricing_quote', None)
                  for k, v in iteritems(listings) if 'pricing_quote' in v}
        tags = {k:v.pop('listing_tags', None)
                for k, v in iteritems(listings) if 'listing_tags' in v}

        # image data
        images = {k:{i:v.pop(i) for i in self.image_fields}
                  for k, v in iteritems(listings)}

        try:
            data = pd.DataFrame.from_dict(listings, orient='index')
        except NameError:
            data = listings

        self._listings = listings
        self.users = users
        self.hosts = hosts
        self.quotes = quotes
        self.images = images
        self.results = data
        self.metadata = metadata
        return

    #~ @property
    #~ def users():
        #~ return self._users

    #~ @users.setter
    #~ def users():
        #~ pass

    #~ def _lazy_user(self, propery_id):
        #~ user = self._users[property_id]

        #~ if not isinstance(user, User):
            #~ s = Searcher()
            #~ endpoint = 'users/{}?'.format(user_id)
            #~ res = session.get(url)
            #~ res.raise_for_status()
            #~ data = res.json()
            #~ user = User(data)
            #~ self.users.update({user.user_id:user})
        #~ return user

    def get_listings(self, location='', **kwargs):
        '''
        Gather all airbnb listings from a location.

        Parameters
        ----------
        location : str, default ""
            A location (e.g. "Portland, ME") to search for airbnb listings
        kwargs : various
            Additional parameters to pass to airbnb api url. See api
            documentation for available paramters.

        Returns
        -------
        Search instance with all attached listings
        '''
        session = self.session
        endpoint = 'search_results?'
        offset = 0
        max_items = 50
        kwargs.update({'_limit':max_items, '_offset':offset})

        if location:
            loc = location.replace(' ', '%20')
            kwargs['location'] = loc

        # get first page
        url = self._setup_url(endpoint, **kwargs)
        res = session.get(url)
        res.raise_for_status()
        data = res.json()
        meta = data['metadata']
        count = meta['listings_count']
        count = count if count <= 1000 else 1000
        pages = int(count/max_items) - 1

        # get remaining pages
        for page in range(pages):
            off = offset + max_items
            url = url.replace('_offset={}'.format(offset), '_offset={}'.format(off))
            print(url)
            res = session.get(url)
            res.raise_for_status()
            new_listings = res.json()['search_results']
            data['search_results'].extend(new_listings)
            offset += max_items

        self.query = data
        self._parse_query()
        return

    def view(self, filtrate={}, size='640x640', **kwargs):
        '''
        Display a google maps image with listings as markers.

        Parameters
        -----------
        size : str, default "800x600"
            Size (in pixels) of returned image. Max size for free lookup is
            limited to 640x640.
        filtrate : dict, default {}
            A dictionary of keys as column names and values to filter by.
            e.g. {"beds":1} will show markers for listings with only 1 bed. 
        **kwargs : various
            Additional arguments to pass to googlemaps static api.

        Notes
        -----
        Markers are limited by number of characters in the api url (2048 chars)

        Examples
        --------
        >>> ss.view(size='400x400', zoom=12)
        >>> ss.view(filtrate={'beds':2, 'room_type':'Private room'})
        '''
        df = self.results

        if df.empty:
            return

        for f, value in iteritems(filtrate):
            try:
                df = df[df[f].isin([value])]
            except TypeError:
                df = df[df[f].isin(value)]

        df = df[['lat', 'lng']]
        center = '{},{}'.format(*df.mean().values)
        markers = '|'.join(['{},{}'.format(lat,lng) for lat, lng in df.values])
        params = {'center':center, 'markers':markers}
        params.update(kwargs)
        img = googlemaps.get_static(requests, size=size, **params)
        img.show()
        return


class User(Query):
    def __init__(self, user_id='',  query=None, auth=None, **kwargs):
        super(User, self).__init__(query, auth)
        self.user_id = user_id
        self.image_fields = ['picture_url',
                             'picture_url_large',
                             'thumbnail_url',
                             'thumbnail_medium_url']
        self._parse_query()

        if user_id:
            self.get_user(user_id, **kwargs)

    def __repr__(self):
        return 'User: user_id={}'.format(self.user_id)

    def _parse_query(self):
        query = copy.deepcopy(self.query)

        if not query:
            return

        metadata = query['metadata']
        res = query['user']
        user_id = res['id']
        images = {i:res.pop(i) for i in self.image_fields if i in res}

        try:
            data = pd.DataFrame.from_dict({user_id:res}, orient='index')
        except NameError:
            data = res
        self.user_id = user_id
        self.images = images
        self.results = data
        self.metadata = metadata
        return

    def get_user(self, user_id, **kwargs):
        session = self.session
        endpoint = 'users/{}?'.format(user_id)
        url = self._setup_url(endpoint, **kwargs)
        res = session.get(url)
        res.raise_for_status()
        self.query = res.json()
        self._parse_query()
        return


class Listing(Query):
    def __init__(self, **kwargs):
        super(Listing, self).__init__(**kwargs)


class Review(Query):
    def __init__(self, **kwargs):
        super(Review, self).__init__(**kwargs)


def main():
    s = Searcher()
    listings = s.get_listings('Portland, ME')
    print(listings.results)

if __name__ == '__main__':
    main()
