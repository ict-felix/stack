from delegate.geni.v3.utils.tn import TNUtils

from flask import current_app
from flask import request
from flask import Response
from functools import wraps


CLI_UNAVAILABLE_MSG = "Method only available via REST API"
GUI_UNAVAILABLE_MSG = "Method only available via GUI"


def parse_output_json(output):
    resp = Response(str(output), status=200, mimetype="application/json")
    return resp


def error_on_unallowed_method(output):
    resp = Response(str(output), status=405, mimetype="text/plain")
    return resp


def get_user_agent():
    from flask import request
    user_agent = "curl"
    try:
        user_agent = request.environ["HTTP_USER_AGENT"]
    except:
        pass
    return user_agent


def warn_must_use_gui():
    user_agent = get_user_agent()
    if "curl" in user_agent:
        return error_on_unallowed_method("Method not supported. \
            Details: %s" % GUI_UNAVAILABLE_MSG)


def warn_must_use_cli():
    user_agent = get_user_agent()
    if "curl" not in user_agent:
        return error_on_unallowed_method("Method not supported. \
            Details: %s" % CLI_UNAVAILABLE_MSG)


def check_request_by_origin(func):
    """
    Enforce check of origin (remote) address and allow
    consequently depending on the accepted values.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.policies_enabled or \
            "*" in current_app.policies_allowed_origins or \
            current_app.policies_enabled and \
            any([orig in request.environ["REMOTE_ADDR"] for
                orig in current_app.policies_allowed_origins]):
            return func(*args, **kwargs)
        else:
            return error_on_unallowed_method("Method not supported.")
    return wrapper


def check_cli_user_agent(func):
    """
    Enforce check of CLI-based agent to access specific methods.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        check_ua = warn_must_use_cli()
        if check_ua is not None:
            return check_ua
        else:
            return func(*args, **kwargs)
    return wrapper


def check_gui_user_agent(func):
    """
    Enforce check of GUI-based agent to access specific methods.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        check_ua = warn_must_use_gui()
        if check_ua is not None:
            return check_ua
        else:
            return func(*args, **kwargs)
    return wrapper


def get_peers():
    # domain_routing = g.mongo.db[current_app.db].domain.routing.find()
    domain_routing = [p for p in current_app.mongo.get_configured_peers()]
    # Retrieve domain URN per peer
    for route in domain_routing:
        try:
            peer_urns = []
            assoc_peers = current_app.mongo.get_info_peers(
                {"_ref_peer": route["_id"]})
            for r in range(0, assoc_peers.count()):
                peer_urns.append(assoc_peers.next().get("domain_urn"))
            route["urn"] = peer_urns
            del route["_id"]
        except:
            pass
    return domain_routing


def get_used_tn_vlans():
    return TNUtils.find_used_tn_vlans()
