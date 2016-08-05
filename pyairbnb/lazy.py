#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on:  28.07.2016 13:13:50 EDT

@author : Edward Holmes
@email:  edward@edward-viral-laptop

Version: 0.01
'''
#------compatibility imports---------------#
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from six import iteritems, add_metaclass
#------------------------------------------#

from abc import abstractmethod, ABCMeta

try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict

@add_metaclass(ABCMeta)
class LazyDict(UserDict, object):
    '''
    '''
    class_ = None

    def __getitem__(self, key):
        class_ = self.class_
        v = self.data[key]

        if not isinstance(v, class_):
            v = class_(key)
            self.data[key] = v
        return v

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()


def main():
    pass

if __name__ == '__main__':
    main()
