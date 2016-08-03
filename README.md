# pyairbnb 
A Python interface to the Airbnb unofficial API

##Installation

Download, cd to folder, and type:
```shell
python setup.py install
```

## Example usage

### Login

You can optionally login to airbnb using the authorizer module. For public endpoints you do
not have to login.

```python
from pyairbnb.authorizer import Auth

auth = Auth('airbnb username', 'airbnb password')
```

### Retrieving listings information for a location

```python
import pyairbnb

s = pyairbnb.Searcher()
listings = s.get_listings('Portland, ME')
print(listings.results) # listings all saved in s.results
```

View a map of the listings with markers

```python
listings.view()
```

User information for a listing can be found in the users dict by listing id.
Data for the user is lazily downloaded on access.

```python
u = s.users[listing id number]
print(u.results)
```

Airbnb API Parameters can be passed to get_listings as keyword argument. For more information on
possible parameters check out this website, [Airbnb API docs](http://airbnbapi.org/)

### Retrieving single listing information

```python
listing = s.get_listing(listing id number)
print(listing.results)
```

Cycle through listing photos

```python
listing.view()
listing.view()
```

### Retrieving a users information

```python
user = s.get_user(user id number)
print(user.results)
```

Cycle through user photos

```python
user.view()
user.view()
```

