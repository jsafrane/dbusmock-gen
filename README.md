DBus mock generator
===================

Tool to scan all DBus objects provided by a DBus service and
write all of them in format expected by 'dbusmock' library.

https://pypi.python.org/pypi/python-dbusmock/

Usage:
  python scan.py --system --dest org.freedesktop.UDisks2

Generated code usage
====================

The generated code is usable only with template/udisks.py template.
Just copy the interesting objects into a method, the generated code
will add the objects to UDev at given path. See test.py for example.
