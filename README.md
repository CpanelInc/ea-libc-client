University of Washington c-client library
=========================================

This repository holds the c-client library needed by some of
cPanel & WHM's PHP packages.

This is principally used because CentOS pushed libc-client
into the EPEL repository, which we've been instructed not to
use.  The consequence of both of these decisions is that we
can't release the PHP imap extension without creatig our own
c-client library.

Finally, the c-client library lives within UW's imap utility
software package.  This package not only contains the
libc-client library, but also several other libraries and
utilities that we don't want or need in cPanel.

Thus, this repo ONLY builds and extracts the libc-client
functionality, which is a complete departure from EPEL.

Instructions
============

To build this package you need to tell the Makefile which SCL
packages to build.  To do this, you need to add files to the
`macros/` directory.  Each file in the `macros/` directory represents
the package name you want to build and contains information
that will be used for the resulting package's SPEC file.

SCL Package Naming Guidelines
-----------------------------

It's important to understand that the filenames must adhere to
standard SCL naming guidelines.

For example, we currently support PHP 5.6 as an SCL.  The SCL
namespace is `ea-php56`.  This means all packages that live within
the PHP 5.6 SCL namespace are called `ea-php56-<something>`.

If you want to add a new PHP 5.6 extension called 'foobar', then
it should be called `ea-php56-php-foobar`.  If you want to add
the `libfoo` library to the PHP 5.6 SCL namespace, then it would
be called `ea-php56-libfoo`.

SCL Package Definition
----------------------

Since this is a library, each entry in the `macros/` directory looks
similar to the following:
~~~~
$ cat macros/scl-php56-libc-client 
%global scl ea-php56
~~~~

This tells the RPM build system to use the `ea-php56` namespace
when compiling
the package.
