#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on:  24.07.2016 15:29:45 EDT

@author : Edward Holmes
@email:  edward.o.holmes@gmail.com

Version: 0.01
'''
#------compatibility imports---------------#
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from six import iteritems
#------------------------------------------#

from . auth import current_auth

search_params = {'locale': '',
                 'currency': '',
                 '_format': '',
                 '_limit': '',
                 '_offset': '',
                 'fetch_facets': '',
                 'guests': '',
                 'ib':'',
                 'ib_add_photo_flow': '',
                 'location': '',
                 'min_bathrooms': '',
                 'min_bedrooms': '',
                 'min_beds': '',
                 'min_num_pic_urls': '',
                 'price_max': '',
                 'price_min': '',
                 'sort': '',
                 'user_lat': '',
                 'user_lng': ''}

search_url = ('https://api.airbnb.com/v2/search_results?')


class AirData(object):
    def __init__(self, auth=None):
        self.auth = auth or current_auth
        assert self.auth


class Search(AirData):
    def __init__(self, auth=None):
        super(Search, self).__init__(**kwargs)


class User(AirData):
    def __init__(self, auth=None):
        super(User, self).__init__(**kwargs)


class Listing(AirData):
    def __init__(self, auth=None):
        super(Listing, self).__init__(**kwargs)


class Review(AirData):
    def __init__(self, auth=None):
        super(Listing, self).__init__(**kwargs)



def main():
    pass

if __name__ == '__main__':
    main()
