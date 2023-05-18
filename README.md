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

Add ea-libc-client as a BuildRequire for your package.  It acts as both the main and devel package.

Do not add it as a Require, statically link your package against c-client.a.

