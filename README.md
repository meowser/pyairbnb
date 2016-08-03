# pyairbnb 
A Python interface to the Airbnb unofficial API

##Installation

Download, cd to folder, and type:
```shell
python setup.py install
```

## Retriving Data

Before retriving data you can optionally login to Airbnb using your username and password, However for simple querying of listing and user information this is unnecessary.

Login example:

```python
from pyairbnb.authorizer import Auth

auth = Auth('airbnb username', 'airbnb password')
```

There are multiple options for querying data. The quickest way to get started is to create a Searcher instance, and to use the 
built-in get methods. All methods return a Query object, but data is also saved in the instance results, users, and listings attributes. 

To get listings data for a location:
```python
import pyairbnb

s = pyairbnb.Searcher()
listings = s.get_listings('Portland, ME')
print(listings.results) # listings all saved in s.results
```

To get a single listing information by id

```python
listing = s.get_listing(listing id number)
print(listing.results)
```

To get a single users information by id

```python
user = s.get_user(user id number)
print(user.results)
```

The results attribute will return a pandas DataFrame (or dict if pandas is not installed), which will contain a variety of listing information. The users and listings attributes are dictionaries containing users or listings from a search. Data for users and listings are lazily downloaded on access.

```python
u = s.users[listing id number]
print(u.results)
```

You can download a map with markers of the listing search using the view method.

```python
listings.view()
```

You can also cycle through individual listing and user images using the view method on the Query objects.
```python
u.view()
u.view()

l.view()
```

You can also use the Query methods themselves to get data bypassing the higher level Searcher object.


## Parameters
Airbnb API Parameters can be passed to get_listings as keyword argument. For more information on
possible parameters check out this website, [Airbnb API docs](http://airbnbapi.org/)


## Future

Other private API endpoints will be added. 
