#!/usr/bin/python

from distutils.core import setup, Command
from distutils.command.build import build
from distutils.command.sdist import sdist
import os


class BuildManpages(Command):
    description = "Create manual pages"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def get_command_name(self):
        return 'build_manpages'

    def compile(self, source, target):
        import subprocess
        subprocess.check_call(["/usr/bin/xsltproc", "-o", target,
            "http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl",
            source])

    manpages = {
        "man/gepdump.1.xml": "man/gepdump.1",
        "man/gregedit.1.xml": "man/gregedit.1",
        "man/gtkldb.1.xml": "man/gtkldb.1",
        "man/gwcrontab.1.xml": "man/gwcrontab.1",
        "man/gwsvcctl.1.xml": "man/gwsvcctl.1"}

    def run(self):
        for source, target in self.manpages.iteritems():
            self.compile(source, target)
        return True


def has_xsltproc(cmd):
    return os.path.exists("/usr/bin/xsltproc")


class BuildData(build):
    sub_commands = build.sub_commands[:]
    sub_commands.append(('build_manpages', has_xsltproc))


class SourceDist(sdist):
    sub_commands = sdist.sub_commands[:]
    sub_commands.append(('build_manpages', has_xsltproc))


setup(
    version="0.0.1",
    name='samba-gtk',
    packages=[
        'sambagtk',
    ],
    scripts=['bin/gtkldb', 'bin/gepdump', 'bin/gregedit'],
    maintainer='Jelmer Vernooij',
    maintainer_email='jelmer@samba.org',
    data_files=[ ('share/applications', ['meta/gepdump.desktop',
                                         'meta/gregedit.desktop',
                                         'meta/gtkldb.desktop',
                                         'meta/gwcrontab.desktop',
                                         'meta/gwsam.desktop',
                                         'meta/gwsvcctl.desktop']),
                 ('share/man/man1', ['man/gepdump.1',
                                     'man/gtkldb.1',
                                     'man/gregedit.1'])],
        cmdclass={'build': BuildData,
                  'build_manpages': BuildManpages,
                  'sdist': SourceDist},
    )
