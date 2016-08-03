# pyairbnb 
A Python interface to the Airbnb unofficial API

##Installation

Download, cd to folder, and type:
```shell
python setup.py install
```

## Retrieving listings for a location
```python
import pyairbnb

listings = pyairbnb.Search('Portland, ME')
print(listings) # results also saved in s.results
```
View a map of the listings with markers
```python
listings.view()
```
Airbnb API Parameters can be passed to get_listings as keyword argument

## Retrieving listing information
```python
l = pyairbnb.Listing(listing id number)
print(l.results)
```
Cycle through listing photos
```python
l.view()
l.view()
```

## Retrieving user information
```python
user = pyairbnb.User(user_id)
print(user.results)
```
