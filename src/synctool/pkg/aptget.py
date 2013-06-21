#
#	synctool.pkg.aptget.py		WJ111
#
#   synctool Copyright 2013 Walter de Jong <walter@heiho.net>
#
#   synctool COMES WITH NO WARRANTY. synctool IS FREE SOFTWARE.
#   synctool is distributed under terms described in the GNU General Public
#   License.
#

import os

import synctool.lib
from synctool.pkgclass import SyncPkg


class SyncPkgAptget(SyncPkg):
	'''package installer class for apt-get + dpkg'''

	def __init__(self):
		SyncPkg.__init__(self)


	def list(self, pkgs = None):
		SyncPkg.list(self, pkgs)

		cmd = 'dpkg -l'

		if pkgs:
			cmd = cmd + ' ' + ' '.join(pkgs)

		synctool.lib.DRY_RUN = False
		synctool.lib.shell_command(cmd)
		synctool.lib.DRY_RUN = self.dryrun


	def install(self, pkgs):
		SyncPkg.install(self, pkgs)

		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

		cmd = 'apt-get -y install ' + ' '.join(pkgs)

		synctool.lib.shell_command(cmd)


	def remove(self, pkgs):
		SyncPkg.remove(self, pkgs)

		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

		cmd = 'apt-get -y remove ' + ' '.join(pkgs)

		synctool.lib.shell_command(cmd)


	def update(self):
		SyncPkg.update(self)

		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
		synctool.lib.shell_command('apt-get update')


	def upgrade(self):
		SyncPkg.upgrade(self)

		os.environ['DEBIAN_FRONTEND'] = 'noninteractive'

		if self.dryrun:
			cmd = 'apt-get -s upgrade'		# --simulate
		else:
			cmd = 'apt-get -y upgrade'

		synctool.lib.DRY_RUN = False
		synctool.lib.shell_command(cmd)
		synctool.lib.DRY_RUN = self.dryrun


	def clean(self):
		SyncPkg.clean(self)

		synctool.lib.shell_command('apt-get clean')

# EOB
