# Copyright (C) 2014 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
# -*- coding: utf-8 -*-

import dbusmock
import subprocess
import unittest
import sys
import os
import dbus.mainloop.glib

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class TestUDisks(dbusmock.DBusTestCase):
    '''Test mocking udisks'''

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(True)

    def setUp(self):
        (self.p_mock, self.mgr) = self.spawn_server_template(
            'udisks',
            {},
            stdout=subprocess.PIPE)
        self.dbusmock = dbus.Interface(self.mgr,
                                       dbusmock.MOCK_IFACE)

    def tearDown(self):
        self.p_mock.terminate()
        self.p_mock.wait()

    def add_objects(self):
        # This is directly copied from scan.py output:
        # object /org/freedesktop/UDisks2/drives/Samsung_SSD_840_Series_S19MNSAD500335K
        interfaces = dbus.Array(signature='(sss)')
        # interface org.freedesktop.UDisks2.Drive.Ata
        name = 'org.freedesktop.UDisks2.Drive.Ata'
        ata_props = ''' {
            'SmartSupported': dbus.Boolean(True),
            'SmartEnabled': dbus.Boolean(True),
            'SmartUpdated': dbus.UInt64(1395404729L),
            'SmartFailing': dbus.Boolean(False),
            'SmartPowerOnSeconds': dbus.UInt64(5313600L),
            'SmartTemperature': dbus.Double(309.15000000000003),
            'SmartNumAttributesFailing': dbus.Int32(0),
            'SmartNumAttributesFailedInThePast': dbus.Int32(0),
            'SmartNumBadSectors': dbus.Int64(0L),
            'SmartSelftestStatus': dbus.String(u'success'),
            'SmartSelftestPercentRemaining': dbus.Int32(0),
            'PmSupported': dbus.Boolean(True),
            'PmEnabled': dbus.Boolean(True),
            'ApmSupported': dbus.Boolean(False),
            'ApmEnabled': dbus.Boolean(False),
            'AamSupported': dbus.Boolean(False),
            'AamEnabled': dbus.Boolean(False),
            'AamVendorRecommendedValue': dbus.Int32(0),
            'WriteCacheSupported': dbus.Boolean(True),
            'WriteCacheEnabled': dbus.Boolean(True),
            'SecurityEraseUnitMinutes': dbus.Int32(2),
            'SecurityEnhancedEraseUnitMinutes': dbus.Int32(2),
            'SecurityFrozen': dbus.Boolean(True),
        }'''
        ata_methods = ''' [
            ('SmartUpdate', 'a{sv}', '', ''),
            ('SmartGetAttributes', 'a{sv}', 'a(ysqiiixia{sv})', ''),
            ('SmartSelftestStart', 'sa{sv}', '', ''),
            ('SmartSelftestAbort', 'a{sv}', '', ''),
            ('SmartSetEnabled', 'ba{sv}', '', ''),
            ('PmGetState', 'a{sv}', 'y', ''),
            ('PmStandby', 'a{sv}', '', ''),
            ('PmWakeup', 'a{sv}', '', ''),
            ('SecurityEraseUnit', 'a{sv}', '', ''),
        ] '''
        ata_interface = dbus.Struct((name, ata_props, ata_methods))
        interfaces.append(ata_interface)
        # interface org.freedesktop.UDisks2.Drive
        name = 'org.freedesktop.UDisks2.Drive'
        drive_props = ''' {
            'Vendor': dbus.String(u''),
            'Model': dbus.String(u'Samsung SSD 840 Series'),
            'Revision': dbus.String(u'DXT08B0Q'),
            'Serial': dbus.String(u'S19MNSAD500335K'),
            'WWN': dbus.String(u'0x50025385a0031e7c'),
            'Id': dbus.String(u'Samsung-SSD-840-Series-S19MNSAD500335K'),
            'Configuration': dbus.Dictionary({}, signature=dbus.Signature('sv')),
            'Media': dbus.String(u''),
            'MediaCompatibility': dbus.Array([], signature=dbus.Signature('s')),
            'MediaRemovable': dbus.Boolean(False),
            'MediaAvailable': dbus.Boolean(True),
            'MediaChangeDetected': dbus.Boolean(True),
            'Size': dbus.UInt64(250059350016L),
            'TimeDetected': dbus.UInt64(1395046081653886L),
            'TimeMediaDetected': dbus.UInt64(1395046081653886L),
            'Optical': dbus.Boolean(False),
            'OpticalBlank': dbus.Boolean(False),
            'OpticalNumTracks': dbus.UInt32(0L),
            'OpticalNumAudioTracks': dbus.UInt32(0L),
            'OpticalNumDataTracks': dbus.UInt32(0L),
            'OpticalNumSessions': dbus.UInt32(0L),
            'RotationRate': dbus.Int32(0),
            'ConnectionBus': dbus.String(u''),
            'Seat': dbus.String(u'seat0'),
            'Removable': dbus.Boolean(False),
            'Ejectable': dbus.Boolean(False),
            'SortKey': dbus.String(u'00coldplug/00fixed/sd____a'),
            'CanPowerOff': dbus.Boolean(False),
            'SiblingId': dbus.String(u''),
        }'''
        drive_methods = ''' [
            ('Eject', 'a{sv}', '', ''),
            ('SetConfiguration', 'a{sv}a{sv}', '', ''),
            ('PowerOff', 'a{sv}', '', ''),
        ] '''
        drive_interface = dbus.Struct((name, drive_props, drive_methods))
        interfaces.append(drive_interface)
        self.dbusmock.AddUdevObject('/org/freedesktop/UDisks2/drives/Samsung_SSD_840_Series_S19MNSAD500335K', interfaces)

    def test_sleep(self):
        # add some test objects
        self.add_objects()

        # spawn d-feet with the right DBus
        print "DBUS_SYSTEM_BUS_ADDRESS=" + os.environ['DBUS_SYSTEM_BUS_ADDRESS']
        subprocess.call("d-feet")

if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout, verbosity=2))
