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
import sys
from xml.etree import ElementTree
import dbus
import argparse


class Scanner(object):
    """
    DBus scanner.

    It inspects all objects provided by a service and prints their definition
    understandable by udisks template (see templates/udisks.py)
    """

    def __init__(self, bus, name, mock):
        """
        :param bus: DBus bus, system or session one.
        :type bus: dbus.Bus instance
        :param name: Name of the service (its 'bus name')
        :type name: string
        :param mock: Name of variable, which should be used in the generated
                code as dbus.Interface() instance of 'org.freedesktop.DBus.Mock'
                interface
        :type mock: string
        """
        self.bus = bus
        self.name = name
        self.mock = mock
        self.ignored_interfaces = [
                'org.freedesktop.DBus.Properties',
                'org.freedesktop.DBus.Introspectable',
                'org.freedesktop.DBus.Peer',
                'org.freedesktop.DBus.ObjectManager']

        # dictionary interface name -> name constant (like 'org.freedesktop.DBus.Introspectable -> INTROSPECTIBLE_IFACE')
        self.interface_names = {}

    def get_interface_prefix(self, interface):
        """
        Parse DBus interface name and return its short name, usable for
        prefixing generated variables.
        """
        parts = interface.split(".")
        return parts[-1]

    def get_signature(self, methodnode, direction):
        """
        Parse XML tree of <method> node and return DBus signature of its input
        or output parameters.
        :param methodnode: The node to parse.
        :type methodnode: ElementTree
        :param direction: Whether to construct input ("in) or output ("out")
                signature.
        :type direction: string
        """
        #      <arg type="t" name="offset" direction="in"/>
        #      <arg type="t" name="size" direction="in"/>
        sig = ""
        for arg in methodnode.iter('arg'):
            if arg.attrib['direction'] != direction:
                continue
            sig += arg.attrib['type']
        return sig

    def get_dict_signature(self, sig):
        """
        Parse DBus signature of a dictionary and return signature of its
        elements.
        :param sig: Dictionary signature, e.g. "a{sv}".
        :type sig: string
        :return: Signature of the dictionary elements, e.g.g "sv".
        """
        # basically cut off everything before first { and after last }
        left = sig.find("{")
        right = sig.rfind("}")
        return sig[left + 1:right]

    def scan(self, path):
        """
        Recursively scan all objects at given object path and print their
        definitions to stdout.
        """
        obj = self.bus.get_object(self.name, path)
        instrospect = obj.get_dbus_method("Introspect", "org.freedesktop.DBus.Introspectable")
        xml = instrospect()
        tree = ElementTree.fromstring(xml)

        object_created = False
        props_interface = dbus.Interface(obj, dbus_interface="org.freedesktop.DBus.Properties")
        for ifnode in tree.iter('interface'):
            ifname = ifnode.attrib['name']
            if ifname in self.ignored_interfaces:
                continue

            if not object_created:
                print "# object", path
                print "interfaces = dbus.Array(signature='(sss)')"
                object_created = True

            prefix = self.get_interface_prefix(ifname).lower()
            # scan properties
            # <property type="ay" name="Device" access="read"/>
            print "# interface %s" % (ifname)
            print "name = '%s'" % (ifname)
            propnodes = ifnode.findall('property')
            if propnodes:
                print "%s_props = ''' {" % (prefix)
                for propnode in ifnode.iter('property'):
                    propname = propnode.attrib['name']
                    proptype = propnode.attrib['type']
                    value = props_interface.Get(ifname, propname)
                    if not proptype.startswith('v'):
                        # reduce the variant level by creating a copy
                        value = value.__class__(value, variant_level=0)
                    if isinstance(value, dbus.Dictionary) and value.signature is None:
                        # convert dictionaries to dictionaries with proper signature (in case the dict. is empty)
                        value = dbus.Dictionary(value, signature=self.get_dict_signature(proptype))
                    if isinstance(value, dbus.Array) and value.signature is None:
                        # convert dictionaries to arrays with proper signature (in case the array is empty)
                        value = dbus.Array(value, signature=proptype[1:])
                    print "    '%s': %s," % (propname, repr(value))
                print "}'''"
            else:
                print "%s_props = '{}'" % (prefix)

            # scan methods
            #    <method name="CreatePartition">
            #      <arg type="t" name="offset" direction="in"/>
            #      <arg type="t" name="size" direction="in"/>
            #      ...
            #    </method>
            methodnodes = ifnode.findall('method')
            if methodnodes:
                print "%s_methods = ''' [" % (prefix)
                for methodnode in methodnodes:
                    methodname = methodnode.attrib['name']
                    insig = self.get_signature(methodnode, "in");
                    outsig = self.get_signature(methodnode, "out");
                    print "    ('%s', '%s', '%s', '')," % (methodname, insig, outsig)
                print "] '''"
            else:
                print "%s_methods = '[]'" % (prefix)

            print "%s_interface = dbus.Struct( (name, %s_props, %s_methods) )" % (prefix, prefix, prefix)
            print "interfaces.append(%s_interface)" % (prefix)

        if object_created:
            print "%s.AddUdevObject('%s', interfaces)" % (self.mock, path)
            print ""
            print ""


        # recursively scan children
        for node in tree.iter('node'):
            if node.attrib.has_key("name"):
                if path == '/':
                    self.scan(path + node.attrib['name'])
                else:
                    self.scan(path + '/' + node.attrib['name'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", help="connect to system bus (default)",
            action="store_true", dest="system", default=True)
    parser.add_argument("--session", help="connect to session bus",
            action="store_false", dest="system")
    parser.add_argument("--dest", help="bus name to connect to",
            action="store", dest="dest")
    parser.add_argument("--mock",
            help="name of instance of DBusMockObject where the objects should be added",
            action="store", dest="mock", default="self")

    opts = parser.parse_args()

    if opts.system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()

    s = Scanner(bus, opts.dest, opts.mock)
    s.scan("/")


if __name__ == '__main__':
    main()

