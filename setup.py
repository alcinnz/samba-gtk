#!/usr/bin/python

from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.sdist import sdist
from distutils.command.install import install
import os, subprocess, filecmp

if not os.path.exists('/usr/share/applications'):
    print ("WARNING! You do not appear to be running a freedesktop.org"
            " compliant desktop.")
    print "This install may not work and an alternative may need to be provided."

# update-mime-database takes a bit to run as it loads all known MIMEtypes
# into memory before writing out the indexing files.

# As such avoid calling it.
mimes_changed = (os.path.exists('/usr/share/mime/packages/sambagtk.xml') and
                os.path.exists('mime/sambagtk.xml') and
                not filecmp.cmp('/usr/share/mime/packages/sambagtk.xml',
                            'mime/sambagtk.xml', shallow=False))

class BuildManpages(Command):
    description = "Create manual pages"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def get_command_name(self):
        return 'build_manpages'

    def compile(self, source, target):
        subprocess.check_call(["/usr/bin/xsltproc", "-o", target,
            "http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl",
            source])

    manpages = {
##        "man/gepdump.1.xml": "man/gepdump.1",
##        "man/gregedit.1.xml": "man/gregedit.1",
        "man/gtkldb.1.xml": "man/gtkldb.1",
        "man/gwcrontab.1.xml": "man/gwcrontab.1",
##        "man/gwsvcctl.1.xml": "man/gwsvcctl.1"
    }

    def run(self):
        for source, target in self.manpages.iteritems():
            self.compile(source, target)
        return True


class InstallMime(Command):
    """In order to register a MIMEtype (for the .desktop file to reference),
        this runs `update-mime-database`."""
    description = "run update-mime-database"
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def get_command_name(self):
        return 'install_mime'
    
    def run(self):
        subprocess.check_call(["/usr/bin/update-mime-database", "/usr/share/mime"])

class AssociateMime(Command):
    """In order to associate a (previously registered) MIMEtype with an
        application, `update-desktop-database` may need to be run. 
        
        This is not specified in the standards, but is documented at
        https://wiki.debian.org/MIME#Application_association"""
    description = "run update-desktop-database"
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def get_command_name(self):
        return 'associate_mime'
    
    def run(self):
        subprocess.check_call(["/usr/bin/update-desktop-database",
                                "/usr/share/applications"])

def has_xsltproc(cmd):
    return os.path.exists("/usr/bin/xsltproc")

def has_update_mime_database(cmd):
    return os.path.exists("/usr/bin/update-mime-database") and mimes_changed

def has_update_desktop_database(cmd):
    return os.path.exists("/usr/bin/update-desktop-database")

class BuildData(build):
    sub_commands = build.sub_commands[:]
    sub_commands.append(('build_manpages', has_xsltproc))


class SourceDist(sdist):
    sub_commands = sdist.sub_commands[:]
    sub_commands.append(('build_manpages', has_xsltproc))

class InstallData(install):
    sub_commands = install.sub_commands[:]
    sub_commands.append(('install_mime', has_update_mime_database))
    sub_commands.append(('associate_mime', has_update_desktop_database))

setup(
    version="0.0.1",
    name='samba-gtk',
    packages=[
        'sambagtk',
    ],
    scripts=['bin/gtkldb', 'bin/gwcrontab', 'bin/gwregedit', 'bin/gwsam',
                'bin/gwshare', 'bin/gwsvcctl', 'bin/gwwkssvc'],
    maintainer='Jelmer Vernooij',
    maintainer_email='jelmer@samba.org',
    data_files=[ ('/usr/share/applications', [
                        'meta/gtkldb.desktop',
                        'meta/gwcrontab.desktop',
                        'meta/gwregedit.desktop',
                        'meta/gwsam.desktop',
                        'meta/gwshare.desktop',
                        'meta/gwsvcctl.desktop',
                        'meta/gwwkssvc.desktop'
                 ]),
                 ('/usr/share/samba-gtk', [
                        'res/samba-logo-small.png',
                        'res/registry-binary.png',
                        'res/registry-number.png',
                        'res/registry-string.png',
                        'res/group.png',
                        'res/user.png']),
                 ('/usr/share/icons/hicolor/512x512/apps', [
                        'icons/512/samba.png']),
                 ('/usr/share/icons/hicolor/256x256/apps', [
                        'icons/256/samba.png',
                        'icons/256/samba-gwcrontab.png',
                        'icons/256/samba-registry.png',
                        'icons/256/samba-gwsam.png',
                        'icons/256/samba-gwshare.png',
                        'icons/256/samba-gwsvcctl.png',
                        'icons/256/samba-gwwkssvc.png']),
                 ('/usr/share/icons/hicolor/128x128/apps', [
                        'icons/128/samba.png',
                        'icons/128/samba-gwcrontab.png',
                        'icons/128/samba-registry.png',
                        'icons/128/samba-gwsam.png',
                        'icons/128/samba-gwshare.png',
                        'icons/128/samba-gwsvcctl.png',
                        'icons/128/samba-gwwkssvc.png']),
                 ('/usr/share/icons/hicolor/64x64/apps', [
                        'icons/64/samba.png',
                        'icons/64/samba-gwcrontab.png',
                        'icons/64/samba-registry.png',
                        'icons/64/samba-gwsam.png',
                        'icons/64/samba-gwshare.png',
                        'icons/64/samba-gwsvcctl.png',
                        'icons/64/samba-gwwkssvc.png']),
                 ('/usr/share/icons/hicolor/48x48/apps', [
                        'icons/48/samba.png',
                        'icons/48/samba-gwcrontab.png',
                        'icons/48/samba-registry.png',
                        'icons/48/samba-gwsam.png',
                        'icons/48/samba-gwshare.png',
                        'icons/48/samba-gwsvcctl.png',
                        'icons/48/samba-gwwkssvc.png']),
                 ('/usr/share/man/man1', ['man/gtkldb.1', 'man/gwcrontab.1']),
                 ('/usr/share/mime/packages', ['mime/sambagtk.xml'])],
        cmdclass={'build': BuildData,
                  'build_manpages': BuildManpages,
                  'sdist': SourceDist,
                  'install': InstallData,
                  'install_mime': InstallMime,
                  'associate_mime': AssociateMime},
    )
