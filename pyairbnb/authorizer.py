import requests
import json

current_auth = None
CLIENT_ID = '3092nxybyb0otqw18e8nh5nty'
URL = 'https://api.airbnb.com'
headers = {"Accept": "application/json",
           "Accept-Encoding": "gzip, deflate",
           "Content-Type": "application/json",
           "User-Agent": "Airbnb/4.7.0 iPhone/8.1.2"}


class AuthError(Exception):
    def __init__(*args, **kwargs):
        super(AuthError, self).__init()


class Auth(object):
    def __init__(self,
                 username,
                 password):
        global current_auth

        # get api token
        session = requests.Session()
        session.headers = headers
        params = json.dumps({'username': username,
                             'password': password,
                             'client_id':CLIENT_ID,
                             'locale':'en-US',
                             'currency':'USD',
                             'grant_type':'password'})
        res = session.post('{}/v1/authorize'.format(URL), data=params)
        res.raise_for_status()
        data = res.json()
        token = data["access_token"]
        session.headers.update({"X-Airbnb-OAuth-Token": token})

        # update and get uid
        res = session.get('{}/v1/account/active'.format(URL))
        res.raise_for_status()
        data = res.json()

        # save stuff
        self.session = session
        self.token = token
        self.uid = data["user"]["user"]["id"]
        current_auth = self


def main():
    auth = Auth('anakastakis@gmail.com', 'icecream1')
    prof = auth.get_profile()
    print(prof)

if __name__ == "__main__":
    main()
