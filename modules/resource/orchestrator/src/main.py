import sys
import os


#if __name__ == "__main__":
#    # Adding path to utilities
#    path = os.path.abspath(sys.argv[0])
#    ro_index = path.find("orchestrator")
#    utility_path = path[:ro_index] + "utilities"
#    if utility_path not in [os.path.abspath(x) for x in sys.path]:
#        sys.path.insert(0, utility_path)


from delegate.geni.v3.delegate_v3 import GENIv3Delegate
from handler.geni.v3.handler_v3 import GENIv3Handler
from scheduler.ro_scheduler import ROSchedulerService
from server.flask.flaskserver import FlaskServer
from server.flask.flaskxmlrpc import FlaskXMLRPC


def main(argv=None):
    if not argv:
        argv = sys.argv
    # Try to handle unexpected exceptions
    try:
        # Create and register the RPC server
        flaskserver = FlaskServer()
        xmlrpc = FlaskXMLRPC(flaskserver)
        # GENIv3
        geni_v3_handler = GENIv3Handler()
        geni_v3_delegate = GENIv3Delegate()
        geni_v3_handler.setDelegate(geni_v3_delegate)
        xmlrpc.registerXMLRPC("geni3_ro", geni_v3_handler, "/xmlrpc/geni/3/")
        # Services/Workers to add
        # Topology update
        geni_v3_scheduler = ROSchedulerService()
        # Run server starting the services
        flaskserver.runServer(services=[geni_v3_scheduler])
    except KeyboardInterrupt:
        return True
    except Exception as e:
        sys.stderr.write("Got an exception: %s" % str(e))
        return False
    finally:
        # Stop the services
        geni_v3_scheduler.stop()
    return True


if __name__ == '__main__':
    # Adding paths to server
    # sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    sys.exit(main())
