from rspecs.commons import validate
from handler.geni.v3 import exceptions as geni_ex
from delegate.geni.v3.rm_adaptor import AdaptorFactory

import core
logger = core.log.getLogger("base-plugin")


class BasePlugin(object):
    def __init__(self):
        pass

    def validate_rspec(self, rspec):
        (result, error) = validate(rspec)
        if result is not True:
            m = "RSpec validation failure: %s" % (error,)
            raise geni_ex.GENIv3GeneralError(m)
        logger.info("Validation success!")

    def manage_renew(self, peer, urns, creds, etime, beffort):
        try:
            adaptor, uri = AdaptorFactory.create_from_db(peer)
            logger.debug("Adaptor=%s, uri=%s" % (adaptor, uri))
            return adaptor.renew(urns, creds[0]["geni_value"], etime, beffort)
        except Exception as e:
            if beffort:
                logger.error("manage_renew exception: %s", e)
                return []
            else:
                logger.critical("manage_renew exception: %s", e)
                raise e