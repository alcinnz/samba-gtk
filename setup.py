#!/usr/bin/python

from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.sdist import sdist
from distutils.command.install import install
import os, subprocess

if not os.path.exists('/usr/share/applications'):
    print ("WARNING! You do not appear to be running a freedesktop.org"
            " compliant desktop.")
    print "This install may not work and an alternative may need to be provided."

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
##        "man/gwcrontab.1.xml": "man/gwcrontab.1",
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
    return os.path.exists("/usr/bin/update-mime-database")

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
    scripts=['bin/gtkldb'],
    maintainer='Jelmer Vernooij',
    maintainer_email='jelmer@samba.org',
    data_files=[ ('/usr/share/applications', ['meta/gtkldb.desktop']),
                 ('/usr/share/samba-gtk', ['res/samba-logo-small.png']),
                 ('/usr/share/icons/hicolor/512/apps', ['icons/512/samba.png']),
                 ('/usr/share/icons/hicolor/256/apps', ['icons/256/samba.png']),
                 ('/usr/share/icons/hicolor/128/apps', ['icons/128/samba.png']),
                 ('/usr/share/icons/hicolor/64/apps', ['icons/64/samba.png']),
                 ('/usr/share/icons/hicolor/48/apps', ['icons/48/samba.png']),
                 ('/usr/share/icons/hicolor/32/apps', ['icons/32/samba.png']),
                 ('/usr/share/icons/hicolor/24/apps', ['icons/24/samba.png']),
                 ('/usr/share/icons/hicolor/16/apps', ['icons/16/samba.png']),
                 ('/usr/share/man/man1', ['man/gtkldb.1']),
                 ('/usr/share/mime/packages', ['mime/sambagtk.xml'])],
        cmdclass={'build': BuildData,
                  'build_manpages': BuildManpages,
                  'sdist': SourceDist,
                  'install': InstallData,
                  'install_mime': InstallMime,
                  'associate_mime': AssociateMime},
    )
