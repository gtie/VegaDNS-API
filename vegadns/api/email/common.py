from builtins import object
from vegadns.api.config import config


class Common(object):
    def get_support_email(self):
        support_name = config.get('email', 'support_name').strip("\"")
        support_email = config.get('email', 'support_email').strip("\"")

        return "\"" + support_name + "\" <" + support_email + ">"
