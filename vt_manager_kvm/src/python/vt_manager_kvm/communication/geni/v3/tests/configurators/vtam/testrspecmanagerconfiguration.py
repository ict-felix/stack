import sys
sys.path.append("/opt/ofelia/core_kvm/lib/am/")
sys.path.append("/opt/ofelia/core_kvm/lib/")
sys.path.append("/opt/ofelia/vt_manager_kvm/src/python/")

import os
import sys
from os.path import dirname, join


# This is needed because wsgi disallows using stdout
sys.stdout = sys.stderr

os.environ['DJANGO_SETTINGS_MODULE'] = 'vt_manager_kvm.settings.settingsLoader'

from vt_manager_kvm.communication.geni.v3.configurators.handlerconfigurator import HandlerConfigurator
from am.rspecs.src.geni.v3.manager import RSpecManager

import unittest

class TestRSpecManagerConfigurator(unittest.TestCase):
    
    def setUp(self):
        self.configurator = HandlerConfigurator
        self.configured_rspec_manager = self.configurator.get_vt_am_rspec_manager()

    def test_should_get_rspec_manager_instance(self):
        self.assertTrue(isinstance(self.configured_rspec_manager, RSpecManager))

if __name__ == "__main__":
    unittest.main()
    
      
