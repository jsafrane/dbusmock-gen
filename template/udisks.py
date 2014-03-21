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

"""
UDisks2 mock template.
"""
__author__ = 'Jan Safranek'
__email__ = 'jsafrane@redhat.com'
__copyright__ = '(c) 2014 Red Hat Inc.'
__license__ = 'LGPL 2+'

import dbus

from dbusmock import MOCK_IFACE
import dbusmock
import sys

BUS_NAME = 'org.xxx'
MAIN_OBJ = '/org/freedesktop/UDisks2'
MANAGER_OBJ = '/org/freedesktop/UDisks2/Manager'
MANAGER_IFACE = 'org.freedesktop.UDisks2.Manager'
SYSTEM_BUS = True

OBJECT_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"

BLOCK_IFACE = 'org.freedesktop.UDisks2.Block'
PARTITION_IFACE = 'org.freedesktop.UDisks2.PartitionTable'
IS_OBJECT_MANAGER = True


def load(mock, parameters):
    self = mock
#     # add manager
#     mock.AddObject(MANAGER_OBJ, MANAGER_IFACE,
#             {
#                     'Version': dbus.String('2.1.2'),
#             },
#             [
#                     ('LoopSetup', 'ha{sv}', 'o', ''),
#                     ('MDRaidCreate', 'aossta{sv}', 'o', ''),
#             ])
#
#     # add a disk
#     mock.AddObject('/org/freedesktop/UDisks2/block_devices/sda', BLOCK_IFACE,
#             {
#                     'Device': dbus.ByteArray('/dev/sda\000'),
#                     'Id': 'by-id-scsi-0QEMU_QEMU_HARDDISK_drive-scsi0-0-0-0',
#             },
#             [])
#     obj = dbusmock.get_object('/org/freedesktop/UDisks2/block_devices/sda')
#     obj.AddProperties(PARTITION_IFACE, {
#             'Test': 'hello world',
#             })

    # object /org/freedesktop/UDisks2/Manager
    # interface org.freedesktop.UDisks2.Manager
    manager_props = {
        'Version': dbus.String(u'2.1.2', variant_level=0),
    }
    manager_methods = [
        ('LoopSetup', 'ha{sv}', 'o', ''),
        ('MDRaidCreate', 'aossta{sv}', 'o', ''),
    ]
    self.AddObject('/org/freedesktop/UDisks2/Manager',
        'org.freedesktop.UDisks2.Manager',
        manager_props,
        manager_methods)


@dbus.service.method(MOCK_IFACE,
                     in_signature='s', out_signature='s')
def AddPartitionDevice(self, device_name):
    """ Just a testing method """
    # add a disk
    path = "/org/freedesktop/UDisks2/block_devices/" + device_name
    block_properties = {
            'Device': dbus.ByteArray("/dev/" + device_name + "\000"),
            'Id': "by-id-scsi-0QEMU_QEMU_HARDDISK_drive-scsi0-0-0-0",
    }
    self.AddObject(path, BLOCK_IFACE, block_properties, [])
    obj = dbusmock.get_object(path)

    partition_properties = {
            'Test': 'hello world ' + device_name,
    }
    obj.AddProperties(PARTITION_IFACE, partition_properties)

    manager = dbusmock.get_object(MAIN_OBJ)
    manager.EmitSignal(OBJECT_MANAGER_IFACE, 'InterfacesAdded',
                       'oa{sa{sv}}', [
                           dbus.ObjectPath(path),
                           {
                                   BLOCK_IFACE: block_properties}
#                                   PARTITION_IFACE: partition_properties,
#                           },
                       ])
    print >> sys.stderr, "sending event on", path
    return path

@dbus.service.method(MOCK_IFACE,
                     in_signature='sa(sss)', out_signature='')
def AddUdevObject(self, path, interfaces):
    first = True
    for iface in interfaces:
        (name, propcode, methcode) = iface
        props = eval(propcode)
        methods = eval(methcode)

        if first:
            first = False
            self.AddObject(path, name, props, methods)
            obj = dbusmock.get_object(path)
        else:
            obj.AddProperties(name, props)
            obj.AddMethods(name, methods)

    # TODO: emit interface-added signal
