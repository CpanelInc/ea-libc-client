%define ea_openssl_ver 1.1.1d-1

%define soname    c-client
%define somajor   2007
%define shlibname lib%{soname}.so.%{somajor}

%define prefix_dir /opt/cpanel/ea-libc-client
%define prefix_lib %{prefix_dir}/lib64
%define prefix_bin %{prefix_dir}/bin
%define prefix_inc %{prefix_dir}/include

Name:    ea-libc-client
# The .1 is for Ubuntu, which cannot handle either the f in 2007f, or just 2007, so the .1 is added, means nothing
Version: 2007.1
# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4574 for more details
%define release_prefix 1
Release: %{release_prefix}%{?dist}.cpanel
Summary: UW C-client mail library
Group:   System Environment/Libraries
URL:     http://www.washington.edu/imap/
Vendor: cPanel, Inc.
License: ASL 2.0
Source0: imap-2007f.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%global pkg_name %{name}
%global ssldir  /etc/pki/tls

Patch5: imap-2007e-overflow.patch
Patch9: imap-2007e-shared.patch
Patch10: imap-2007e-authmd5.patch
Patch11: imap-2007f-cclient-only.patch

Patch20: 1006_openssl11_autoverify.patch
Patch21: 2014_openssl1.1.1_sni.patch

Patch30: 0001-add-extra-to-tmp-buffer.patch
Patch31: 0002-These-are-only-used-with-very-old-openssl.patch
Patch32: 0003-I-had-to-repair-this-code-because-I-could-not-turn-l.patch

BuildRequires: krb5-devel%{?_isa}, pam-devel%{?_isa}

%if 0%{?rhel} >= 8
# In C8 we use system openssl. See DESIGN.md in ea-openssl11 git repo for details
BuildRequires: openssl, openssl-devel
%else
BuildRequires: ea-openssl11 >= %{ea_openssl_ver}, ea-openssl11-devel%{?_isa}
%endif

%description
Provides a common API for accessing mailboxes.

This is intended for internal builds only and will not be delivered to customers.

%prep
%setup -q -n imap-2007f

%patch5 -p1 -b .overflow
%patch9 -p1 -b .shared
%patch10 -p1 -b .authmd5
%patch11 -p1 -b .cclient

%patch20 -p1
%patch21 -p1

%if 0%{?rhel} >= 8
%patch30 -p1
%patch31 -p1
%patch32 -p1
%endif

%build
# Kerberos setup
test -f %{_root_sysconfdir}/profile.d/krb5-devel.sh && source %{_root_sysconfdir}/profile.d/krb5-devel.sh
test -f %{_root_sysconfdir}/profile.d/krb5.sh && source %{_root_sysconfdir}/profile.d/krb5.sh
GSSDIR=$(krb5-config --prefix)

%if 0%{?rhel} < 8
# SSL setup, probably legacy-only, but shouldn't hurt -- Rex
export PKG_CONFIG_PATH="/opt/cpanel/ea-openssl11/lib/pkgconfig/"
export EXTRACFLAGS="$EXTRACFLAGS $(pkg-config --cflags openssl 2>/dev/null)"
%endif

# $RPM_OPT_FLAGS
export EXTRACFLAGS="$EXTRACFLAGS -fPIC $RPM_OPT_FLAGS"
# jorton added these, I'll assume he knows what he's doing. :) -- Rex
export EXTRACFLAGS="$EXTRACFLAGS -fno-strict-aliasing"
export EXTRACFLAGS="$EXTRACFLAGS -Wno-pointer-sign"

%if 0%{?rhel} < 8
export EXTRALDFLAGS="$EXTRALDFLAGS $(pkg-config --libs openssl 2>/dev/null) -Wl,-rpath,/opt/cpanel/ea-openssl11/lib"
%else
# MOAR fun: '-Wl,--build-id=uuid'
# This is complex, so bear with me.  Whenever a library or executable is
# linked in Linux, a .build_id is generated and added to the ELF.  This
# .build_id is also shadow linked to a file in /usr/lib.   In all cases the
# .build_id is a cryptographic signature (sha1 hash) of the binaries contents
# and perhaps "seed".  But in the case of libc-client, we build for each
# version of PHP, and just put the library inside the PHP directory namespace,
# but the libraries are binarily identical (at the time of the hash).  So we
# were getting conflicts when we installed the library on multiple versions of
# PHP as both rpm's owned the .build_id file.  So I am telling the linker
# instead of using the normal sha1 hash, to instead use a random uuid, so each
# version of this library will have a different build_id.  Now further
# consideration, the normal form of this would be -Wl,--build-id,uuid, but for
# some reason that form works perfectly for any of the arguments that use a
# single dash, but does not work for the double hash type.  So I did it
# without the comma, and it is treating that as instead of a parameter, value
# but as a single entity on the linker command line.  Man I am getting a
# headache.
export EXTRALDFLAGS="$EXTRALDFLAGS $(pkg-config --libs openssl 2>/dev/null) '-Wl,--build-id=uuid'"
%endif

echo -e "y\ny" | \
make %{?_smp_mflags} lnp \
IP=6 \
EXTRACFLAGS="$EXTRACFLAGS" \
EXTRALDFLAGS="$EXTRALDFLAGS" \
EXTRAAUTHENTICATORS=gss \
%if 0%{?rhel} < 8
SPECIALS="GSSDIR=${GSSDIR} LOCKPGM=%{_root_sbindir}/mlock SSLCERTS=%{ssldir}/certs SSLDIR=/opt/cpanel/ea-openssl11 SSLINCLUDE=/opt/cpanel/ea-openssl11/include SSLKEYS=%{ssldir}/private SSLLIB=/opt/cpanel/ea-openssl11/lib" \
%else
SPECIALS="GSSDIR=${GSSDIR} LOCKPGM=%{_root_sbindir}/mlock SSLCERTS=%{ssldir}/certs SSLINCLUDE=/usr/include/openssl SSLKEYS=%{ssldir}/private" \
%endif
SSLTYPE=unix \
CCLIENTLIB=$(pwd)/c-client/%{shlibname} \
SHLIBBASE=%{soname} \
SHLIBNAME=%{shlibname}

%install
set -x

echo "FILE LIST"
find . -type f -print

echo "SYSCONFDIR" %{_sysconfdir}

mkdir -p $RPM_BUILD_ROOT/%{prefix_dir}
mkdir -p $RPM_BUILD_ROOT/%{prefix_lib}
mkdir -p $RPM_BUILD_ROOT/%{prefix_bin}
mkdir -p $RPM_BUILD_ROOT/%{prefix_inc}

install -p -m644 ./c-client/c-client.a $RPM_BUILD_ROOT/%{prefix_lib}
ln -s c-client.a $RPM_BUILD_ROOT%{prefix_lib}/libc-client.a

install -p -m755 ./c-client/%{shlibname} $RPM_BUILD_ROOT%{prefix_lib}/

: Installing development components
ln -s %{shlibname} $RPM_BUILD_ROOT%{prefix_lib}/lib%{soname}.so

mkdir -p $RPM_BUILD_ROOT%{prefix_inc}/c-client/
install -m644 ./c-client/*.h $RPM_BUILD_ROOT%{prefix_inc}/c-client/
# Added linkage.c to fix (#34658) <mharris>
install -m644 ./c-client/linkage.c $RPM_BUILD_ROOT%{prefix_inc}/c-client/
install -m644 ./src/osdep/tops-20/shortsym.h $RPM_BUILD_ROOT%{prefix_inc}/c-client/

mkdir -p $RPM_BUILD_ROOT%{prefix_dir}/share/docs/draft
mkdir -p $RPM_BUILD_ROOT%{prefix_dir}/share/docs/rfc

install -m644 docs/*.txt $RPM_BUILD_ROOT%{prefix_dir}/share/docs/
install -m644 docs/SSLBUILD $RPM_BUILD_ROOT%{prefix_dir}/share/docs/
install -m644 docs/RELNOTES $RPM_BUILD_ROOT%{prefix_dir}/share/docs/
install -m644 docs/draft/* $RPM_BUILD_ROOT%{prefix_dir}/share/docs/draft/
install -m644 docs/rfc/* $RPM_BUILD_ROOT%{prefix_dir}/share/docs/rfc/

install -m644 LICENSE.txt $RPM_BUILD_ROOT%{prefix_dir}/share/docs/
install -m644 NOTICE $RPM_BUILD_ROOT%{prefix_dir}/share/docs/
install -m644 SUPPORT $RPM_BUILD_ROOT%{prefix_dir}/share/docs/

touch c-client.cf
install -p -m644 -D c-client.cf $RPM_BUILD_ROOT/etc/c-client.cf

echo %{buildroot}/etc/c-client.cf

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%clean
rm -rf $RPM_BUILD_ROOT

# This has been the most excrutiating file list I have ever dealt with
# do not touch it or expect hours of pain
%files
%defattr(-,root,root,-)
%dir %{prefix_dir}/share/docs/
%{prefix_lib}/lib%{soname}.so.*
/opt/cpanel/ea-libc-client/share/docs/LICENSE.txt
/opt/cpanel/ea-libc-client/share/docs/NOTICE
/opt/cpanel/ea-libc-client/share/docs/SUPPORT
/opt/cpanel/ea-libc-client/share/docs/FAQ.txt
/opt/cpanel/ea-libc-client/share/docs/IPv6.txt
/opt/cpanel/ea-libc-client/share/docs/RELNOTES
/opt/cpanel/ea-libc-client/share/docs/SSLBUILD
/opt/cpanel/ea-libc-client/share/docs/bugs.txt
/opt/cpanel/ea-libc-client/share/docs/calendar.txt
/opt/cpanel/ea-libc-client/share/docs/commndmt.txt
/opt/cpanel/ea-libc-client/share/docs/draft/README
/opt/cpanel/ea-libc-client/share/docs/draft/i18n.txt
/opt/cpanel/ea-libc-client/share/docs/draft/sort.txt
/opt/cpanel/ea-libc-client/share/docs/drivers.txt
/opt/cpanel/ea-libc-client/share/docs/formats.txt
/opt/cpanel/ea-libc-client/share/docs/imaprc.txt
/opt/cpanel/ea-libc-client/share/docs/internal.txt
/opt/cpanel/ea-libc-client/share/docs/locking.txt
/opt/cpanel/ea-libc-client/share/docs/md5.txt
/opt/cpanel/ea-libc-client/share/docs/mixfmt.txt
/opt/cpanel/ea-libc-client/share/docs/naming.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/README
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc1732.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc1733.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2061.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2062.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2087.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2088.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2177.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2180.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2193.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2195.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2221.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2342.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2683.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc2971.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3348.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3501.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3502.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3503.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3516.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3656.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc3691.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4314.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4315.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4422.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4466.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4467.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4468.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4469.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4505.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4549.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4551.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4616.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4731.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4752.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4790.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4959.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc4978.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5032.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5051.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5092.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5161.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5162.txt
/opt/cpanel/ea-libc-client/share/docs/rfc/rfc5234.txt
%{prefix_inc}/c-client/
%{prefix_lib}/lib%{soname}.so
%{prefix_lib}/c-client.a
%{prefix_lib}/libc-client.a
%ghost %config(missingok,noreplace) /etc/c-client.cf

%changelog
* Tue May 09 2023 Julian Brown <julian.brown@cpanel.net> - 2007.1-1
- ZC-10931: Initial Build

