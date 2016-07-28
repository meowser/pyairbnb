#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
googlemaps static api

Created on:  27.07.2016 12:56:29 EDT

@author : Edward O. Holmes
@email:  edward.o.holmes@gmail.com

Version: 0.01
'''
#--------compatibility imports--------#
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from six import iteritems, BytesIO
#-------------------------------------#

import re
import requests

from ast import literal_eval
from json import JSONDecodeError
from PIL import Image
from requests import HTTPError

try:
    import polyline
except ImportError:
    pass


def get_static(conn=None, max_attempts=3, size='800x600', **kwargs):
    conn = conn or requests
    base_url = 'https://maps.googleapis.com/maps/api/staticmap?'

    try:
        markers = '&markers={}'.format(kwargs.pop('markers'))
    except KeyError:
        markers = ''

    # convert coordinates into polyline if not already
    try:
        path = kwargs.get('path', '')
        substring = re.search('{}(.*){}'.format('enc:', '\|'), path).group()
        data = json.loads(substring.split('enc:')[1])
        encoded = polyline.encode(data)
        path.replace(substring, 'enc:{}|'.format(encoded))
        params['path'] = path
    except NameError:
        raise AttributeError('Unable to create polyline encoding because '
                             'polyline module is not installed')
    except (AttributeError, IndexError, JSONDecodeError):
        pass

    # one url to bring them all and in the darkness bind them
    params = '&'.join(['{}={}'.format(k,v) for k,v in iteritems(kwargs)])
    url = '{b}{p}&size={s}{m}'.format(b=base_url, s=size, p=params, m=markers)
    url = url[:2048].rsplit('|', 1)[0] #to keep url within 2048 char max limit

    for x in range(max_attempts):
        try:
            res = conn.get(url)
            res.raise_for_status()
            break
        except HTTPError:
            pass

        # raise if all attempts fail
        res.raise_for_status()

    img = Image.open(BytesIO(res.content))
    return img

def main():
    pass

if __name__ == '__main__':
    main()

