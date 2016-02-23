from flask import request


class XMLRPCDispatcher(object):
    """
    Please see documentation in FlaskXMLRPC.
    """
    def __init__(self, log):
        self._log = log

    def requestCertificate(self):
        """
        Retrieve the certificate which the client has sent.
        """
        # Get cert from the request's environment
        # NGINX
        if "CLIENT_RAW_CERT" in request.environ.keys():
            return request.environ["CLIENT_RAW_CERT"]
        # Apache
        if "SSL_CLIENT_CERT" in request.environ.keys():
            return request.environ["SSL_CLIENT_CERT"]
        return None

    def _dispatch(self, method, params):
        self._log.info("Called: <%s>" % (method))
        try:
            meth = getattr(self, "%s" % (method))
        except AttributeError, e:
            self._log.warning("Client called unknown method: <%s>" % (method))
            raise e

        try:
            return meth(*params)
        except Exception, e:
            # TODO check if the exception has already been logged
            self._log.exception("Call to known method <%s> failed!" % (method))
            raise e
