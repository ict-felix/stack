import amsoil.core.pluginmanager as pm
from com_rm_delegate import CRMGENIv3Delegate

def setup():
    # setup config keys
    config = pm.getService("config")
    config.set("flask.bind", "0.0.0.0")
    config.set("flask.app_port", 18445)

    xmlrpc = pm.getService("xmlrpc")
    handler = pm.getService("geniv3handler")
    delegate = CRMGENIv3Delegate()
    handler.setDelegate(delegate)
    xmlrpc.registerXMLRPC("com_rm_geni_v3", handler, "/xmlrpc/geni/3/")