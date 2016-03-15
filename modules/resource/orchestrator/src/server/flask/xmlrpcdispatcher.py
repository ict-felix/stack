from core.config import FullConfParser
from flask import request

import ast


class XMLRPCDispatcher(object):
    """
    Please see documentation in FlaskXMLRPC.
    """

    def __init__(self, log):
        self._log = log
        self.__load_config()

    def __load_config(self):
        self.config = FullConfParser()
        self.policies_category = self.config.get("policies.conf")
        self.general_section = self.policies_category.get("general")
        self.policies_enabled = ast.literal_eval(
            self.general_section.get("enabled"))

    def requestCertificate(self):
        """
        Retrieve the certificate which the client has sent.
        """
        # Get Cert from the request's environment
        if "CLIENT_RAW_CERT" in request.environ:
            return request.environ["CLIENT_RAW_CERT"]
        if "SSL_CLIENT_CERT" in request.environ:
            return request.environ["SSL_CLIENT_CERT"]
        return None

    def _dispatch(self, method, params):
        self._log.info("Called: <%s>" % (method))
        try:
            meth = getattr(self, "%s" % (method))
        except AttributeError, e:
            self._log.warning("Client called unknown method: <%s>" % (method))
            raise e

        # Apply policies
        if self.policies_enabled:
            print "XMLRPCDispatcher > method=", method, ", params=", params
            print "XMLRPCDispatcher > Policies enabled..."
            from policies.manager import PolicyManager
            print "XMLRPCDispatcher > Evaluating policies..."
            PolicyManager.evaluate_rules()

        try:
            return meth(*params)
        except Exception, e:
            # TODO check if the exception has already been logged
            self._log.exception("Call to known method <%s> failed!" % (method))
            raise e
