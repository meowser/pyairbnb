#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='pyairbnb',
      version='0.5',
      description='A wrapper for the airbnb unofficial API',
      author='Edward O. Holmes',
      author_email='edward.o.holmes@gmail.com',
      license='MIT',
      packages=['pyairbnb'],
      install_requires=['pillow', 'requests', 'six'],
      zip_safe=False)

