from builtins import object
import re
import time
import random

from flask import request
from netaddr import IPSet
import peewee
from werkzeug.exceptions import Unauthorized

from vegadns.api.config import config
from vegadns.api.models.account import Account
from vegadns.api.models.oauth_access_token import OauthAccessToken


class Auth(object):
    def __init__(self, request, endpoint):
        self.account = None
        self.request = request
        self.endpoint = endpoint
        self.authUsed = None
        self.authenticate()

    def authenticate(self):
        if self.endpoint.auth_required is False:
            return True

        # determine auth
        auth_header = self.request.headers.get('Authorization', None)
        if auth_header is None:
            # check if ip auth is allowed
            if "ip" in self.endpoint.auth_types:
                return self.ip_authenticate()

            # check if cookie auth is allowed
            if "cookie" in self.endpoint.auth_types:
                if self.request.cookies.get("vegadns") is not None:
                    return self.cookie_authenticate()

            raise Unauthorized

        p = re.compile('^Bearer[ ]+(.*$)')
        match = p.findall(auth_header)
        if match:
            if "oauth" in self.endpoint.auth_types:
                return self.oauth_authenticate(match[0])
        else:
            if "basic" in self.endpoint.auth_types:
                return self.basic_authenticate()

        raise Unauthorized

    def oauth_authenticate(self, token):
        account = self.get_account_by_oauth_token(token)
        self.account = account
        self.authUsed = "oauth"

    def basic_authenticate(self):
        # basic auth for now
        if self.request.authorization is None:
            raise Unauthorized('Invalid username or password')

        email = self.request.authorization.username
        password = self.request.authorization.password

        account = self.get_account_by_email(email)
        if not account.check_password(password):
            raise Unauthorized('Invalid email or password')

        self.authUsed = "basic"

        # update to bcrypt
        if account.get_password_algo() != "bcrypt":
            account.set_password(password)
            account.save()

        self.account = account

    def get_account_by_email(self, email):
        try:
            return Account.get(
                Account.email == email,
                Account.status == 'active'
            )
        except peewee.DoesNotExist:
            raise Unauthorized('Account not found')

    def get_account_by_oauth_token(self, token):
        now = int(time.time())

        # First, remove old tokens every 4 requests or so
        if random.randint(1, 4) == 1:
            q = OauthAccessToken.delete().where(
                OauthAccessToken.expires_at < now
            )
            deleted = q.execute()
            # print "Old tokens deleted: " + str(deleted)

        try:
            access_token = OauthAccessToken.get(
                OauthAccessToken.access_token == token,
                OauthAccessToken.expires_at > now
            )
        except peewee.DoesNotExist:
            raise Unauthorized('invalid_token')

        try:
            return Account.get(
                Account.account_id == access_token.account_id,
                Account.status == 'active'
            )
        except peewee.DoesNotExist:
            raise Unauthorized('Account not found')

    def ip_authenticate(self):
        if len(request.access_route):
            ip = request.access_route[0]
        else:
            raise Unauthorized('No remote IP set')

        trusted = config.get('ip_auth', 'trusted_ips')
        if not trusted:
            raise Unauthorized('IP not authorized: ' + ip)

        trusted = "".join(trusted.split())  # remove whitespace
        trusted_list = trusted.split(',')
        try:
            ip_range = IPSet(trusted_list)
        except Exception:
            raise Unauthorized('Error parsing IP acl list')

        if ip not in ip_range:
            raise Unauthorized('IP not authorized: ' + ip)

        self.authUsed = "ip"

    def cookie_authenticate(self):
        supplied_cookie = self.request.cookies.get("vegadns")
        if supplied_cookie is None:
            raise Unauthorized('Invalid cookie supplied')

        split = supplied_cookie.split("-")
        if len(split) is not 2:
            raise Unauthorized('Invalid cookie supplied')
        account_id = split[0]

        try:
            account = Account.get(
                Account.account_id == account_id,
                Account.status == 'active'
            )
        except peewee.DoesNotExist:
            raise Unauthorized("Invalid cookie supplied")

        user_agent = self.request.headers.get('User-Agent')
        generated_cookie = account.generate_cookie_value(account, user_agent)

        if supplied_cookie != generated_cookie:
            raise Unauthorized("Invalid cookie supplied")

        self.account = account
        self.authUsed = "cookie"
