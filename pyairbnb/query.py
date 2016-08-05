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
from . lazy import LazyDict
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


@add_metaclass(ABCMeta)
class Query(AuthSetup):
    '''
    Base class for query objects.
    '''
    def __init__(self, query=None, auth=None):
        super(Query, self).__init__(auth)
        self.query = query
        self._data = None
        self.results = None
        self.image_fields = []
        self.images = {}
        self._viewer = None

    def __str__(self):
        return self.results.__str__()

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
            res.raise_for_status()
            img = Image.open(BytesIO(res.content))
            yield img.show()

    def view(self):
        '''
        Cycle through and download an image for a user or listing
        '''
        if not self._viewer:
            self._viewer = self._view()

        try:
            next(self._viewer)
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
        self.users = LazyUsers()
        self.listings = LazyListings()
        self._parse_query()

        if location and not query:
            self.get_listings(location, **kwargs)

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
            self._data = listings
            results = pd.DataFrame.from_dict(listings, orient='index')
        except NameError:
            results = listings

        self._listings_additional = listings
        self.listings.update({k:k for k in listings})
        self._users_additional = users
        self.users.update({k:k for k in users})
        self.hosts = hosts
        self.quotes = quotes
        self.images = images
        self.results = results
        self.metadata = metadata
        return

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

        try:
            if df.empty:
                return
        except AttributeError:
            raise NotImplementedError('View method currently only available '
                                      'with pandas installed')

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
            self._data = res
            data = pd.DataFrame({user_id:res})
        except NameError as e:
            data = res

        self.user_id = user_id
        self.images = images
        self.results = data
        self.metadata = metadata
        return

    def _add_data(self, **kwargs):
        data = self._data
        new_values = set(kwargs) - set(data)
        data.update({k:kwarg[k] for k in new_values})

        try:
            self._data = data
            data = pd.DataFrame({self.user_id:data})
        except NameError:
            pass

        self.results = data
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
    def __init__(self, listing_id='', query=None, auth=None, **kwargs):
        super(Listing, self).__init__(query, auth)
        self.listing_id = listing_id
        self.image_fields = ['picture_url',
                             'picture_urls',
                             'thumbnail_url',
                             'thumbnail_urls',
                             'map_image_url',
                             'medium_url',
                             'xl_picture_url',
                             'xl_picture_urls']
        self._parse_query()

        if listing_id:
            self.get_listing(listing_id, **kwargs)

    def _parse_query(self):
        query = copy.deepcopy(self.query)

        if not query:
            return

        metadata = query['metadata']
        res = query['listing']
        listing_id = res['id']

        # seperate image info
        images = {i:res.pop(i) for i in self.image_fields if i in res}
        unpackable = [i for i in images if i.endswith('s')]
        unpacked = {'{} {}'.format(i, c):l for i in unpackable for c, l in enumerate(images.pop(i))}
        images.update(unpacked)

        # seperate user info
        user = res.pop('user')['user']

        try:
            self._data = res
            res = pd.DataFrame({listing_id:res})
            user = pd.DataFrame.from_dict({user['id']:user})
        except NameError as e:
            pass

        self.listing_id = listing_id
        self.images = images
        self.results = res
        self.metadata = metadata
        return

    def get_listing(self, listing_id, **kwargs):
        session = self.session
        endpoint = 'listings/{}?'.format(listing_id)
        kwargs['_format'] = 'v1_legacy_for_p3'
        url = self._setup_url(endpoint, **kwargs)
        res = session.get(url)
        res.raise_for_status()
        self.query = res.json()
        self._parse_query()
        return


#~ class Review(Query):
    #~ def __init__(self, **kwargs):
        #~ super(Review, self).__init__(**kwargs)


class LazyUsers(LazyDict):
    class_ = User


class LazyListings(LazyDict):
    class_ = Listing


class Searcher(AuthSetup):
    '''
    Search airbnb using various "get" methods. The methods return Query
    objects with semi-organized airbnb data. Query objects are also stored in 
    various class variables (listings, users, reviews, etc...)

    Available search methods:
        - get_listings()
        - get_listing()
        - get_user()
        - get_reviews() * not implemented yet

    Parameters
    ----------
    auth : Auth instance, default None
        A pyairbnb Auth object to use for connecting to airbnb with a valid
        username and password.
    '''
    def __init__(self, auth=None):
        super(Searcher, self).__init__(auth)
        self.listings = LazyListings()
        self.searches = {}
        self.users = LazyUsers()
        self.reviews = None
        self.results = None

    def get_listings(self, location='', **kwargs):
        '''
        Gather all airbnb listings from a location.

        Parameters
        ----------
        location : str, default ""
            A location (e.g. "Portland, ME") to search for airbnb listings
        kwargs : various
            Additional parameters to pass to airbnb api url. See api
            documentation for available parameters.

        Returns
        -------
        Search object with all attached listings
        '''
        search = Search(location, auth=self.auth)
        self.results = search.results
        self.searches.update({location:search})
        s.users.update(search.users)
        s.listings.update(search.listings)
        return search

    def get_user(self, user_id, **kwargs):
        '''
        Get user info for one user by airbnb user_id number.

        Parameters
        ----------
        user_id : int
            An airbnb user_id number.
        kwargs : various
            Additional parameters to pass to airbnb api url. See api
            documentation for available parameters.

        Returns
        -------
        User object with all attached listings
        '''
        user = User(user_id, **kwargs)
        self.users.update({user_id:user})
        return user

    def get_reviews(self):
        raise(NotImplementedError)

    def get_listing(self, listing_id, **kwargs):
        '''
        Get data for one airbnb listing by listing id.

        Parameters
        ----------
        listing_id : int
            An airbnb listing_id number.
        kwargs : various
            Additional parameters to pass to airbnb api url. See api
            documentation for available parameters.

        Returns
        -------
        User object with all attached listings
        '''
        listing = Listing(listing_id)
        self.listings.update({listing_id:listing})
        return listing

    def scan(self):
        # todo auto grab all listings and users then combine data
        raise(NotImplementedError)



def main():
    s = Searcher()
    listings = s.get_listings('Portland, ME')
    print(listings.results)

if __name__ == '__main__':
    main()
