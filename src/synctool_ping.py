#! /usr/bin/env python
#
#	synctool-ping	WJ111
#
#   synctool by Walter de Jong <walter@heiho.net> (c) 2003-2013
#
#   synctool COMES WITH NO WARRANTY. synctool IS FREE SOFTWARE.
#   synctool is distributed under terms described in the GNU General Public
#   License.
#

import os
import sys
import string
import subprocess
import getopt
import shlex
import errno

import synctool.aggr
import synctool.config
import synctool.lib
from synctool.lib import verbose, stderr, unix_out
import synctool.nodeset
import synctool.param
import synctool.unbuffered

NODESET = synctool.nodeset.NodeSet()

OPT_AGGREGATE = False

MASTER_OPTS = []


def ping_nodes(address_list):
	'''ping nodes in parallel'''

	synctool.lib.multiprocess(ping_node, address_list)


def ping_node(addr):
	'''ping a single node'''

	node = NODESET.get_nodename_from_address(addr)
	if node == synctool.param.NODENAME:
		print '%s: up' % node
		return

	verbose('pinging %s' % node)
	unix_out('%s %s' % (synctool.param.PING_CMD, addr))

	packets_received = 0

	# execute ping command and show output with the nodename
	cmd = '%s %s' % (synctool.param.PING_CMD, addr)
	cmd_arr = shlex.split(cmd)

	try:
		f = subprocess.Popen(cmd_arr, shell=False, bufsize=4096,
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
	except OSError, reason:
		stderr('failed to run command %s: %s' % (cmd_arr[0], reason))
		return False

	with f:
		while True:
			line = f.readline()
			if not line:
				break

			line = string.strip(line)

			# argh, we have to parse output here
			#
			# on BSD, ping says something like:
			# "2 packets transmitted, 0 packets received, 100.0% packet loss"
			#
			# on Linux, ping says something like:
			# "2 packets transmitted, 0 received, 100.0% packet loss, time 1001ms"

			arr = string.split(line)
			if len(arr) > 3 and arr[1] == 'packets' and arr[2] == 'transmitted,':
				try:
					packets_received = int(arr[3])
				except ValueError:
					pass

				break

			# some ping implementations say "hostname is alive"
			# or "hostname is unreachable"
			elif len(arr) == 3 and arr[1] == 'is':
				if arr[2] == 'alive':
					packets_received = 100

				elif arr[2] == 'unreachable':
					packets_received = -1

	if packets_received > 0:
		print '%s: up' % node
	else:
		print '%s: not responding' % node


def check_cmd_config():
	'''check whether the commands as given in synctool.conf actually exist'''

	(ok, synctool.param.PING_CMD) = synctool.config.check_cmd_config(
									'ping_cmd', synctool.param.PING_CMD)
	if not ok:
		sys.exit(-1)


def usage():
	print 'usage: %s [options]' % os.path.basename(sys.argv[0])
	print 'options:'
	print '  -h, --help                     Display this information'
	print '  -c, --conf=dir/file            Use this config file'
	print ('                                 (default: %s)' %
		synctool.param.DEFAULT_CONF)

	print '''  -n, --node=nodelist            Execute only on these nodes
  -g, --group=grouplist          Execute only on these groups of nodes
  -x, --exclude=nodelist         Exclude these nodes from the selected group
  -X, --exclude-group=grouplist  Exclude these groups from the selection
  -a, --aggregate                Condense output

  -p, --numproc=NUM              Set number of concurrent procs
  -z, --zzz=NUM                  Sleep NUM seconds between each run
  -v, --verbose                  Be verbose
      --unix                     Output actions as unix shell commands
      --version                  Print current version number

A nodelist or grouplist is a comma-separated list

synctool-ping by Walter de Jong <walter@heiho.net> (c) 2013'''


def get_options():
	global MASTER_OPTS, OPT_AGGREGATE

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hc:vn:g:x:X:aNqp:z:',
			['help', 'conf=', 'verbose', 'node=', 'group=',
			'exclude=', 'exclude-group=', 'aggregate', 'unix', 'quiet',
			'numproc=', 'zzz='])
	except getopt.error, (reason):
		print '%s: %s' % (os.path.basename(sys.argv[0]), reason)
#		usage()
		sys.exit(1)

	except getopt.GetoptError, (reason):
		print '%s: %s' % (os.path.basename(sys.argv[0]), reason)
#		usage()
		sys.exit(1)

	except:
		usage()
		sys.exit(1)

	# first read the config file
	for opt, arg in opts:
		if opt in ('-h', '--help', '-?'):
			usage()
			sys.exit(1)

		if opt in ('-c', '--conf'):
			synctool.param.CONF_FILE = arg
			continue

		if opt == '--version':
			print synctool.param.VERSION
			sys.exit(0)

	synctool.config.read_config()
	check_cmd_config()

	# then process the other options
	MASTER_OPTS = [ sys.argv[0] ]

	for opt, arg in opts:
		if opt:
			MASTER_OPTS.append(opt)
		if arg:
			MASTER_OPTS.append(arg)

		if opt in ('-h', '--help', '-?', '-c', '--conf', '--version'):
			# already done
			continue

		if opt in ('-v', '--verbose'):
			synctool.lib.VERBOSE = True
			continue

		if opt in ('-n', '--node'):
			NODESET.add_node(arg)
			continue

		if opt in ('-g', '--group'):
			NODESET.add_group(arg)
			continue

		if opt in ('-x', '--exclude'):
			NODESET.exclude_node(arg)
			continue

		if opt in ('-X', '--exclude-group'):
			NODESET.exclude_group(arg)
			continue

		if opt in ('-a', '--aggregate'):
			OPT_AGGREGATE = True
			continue

		if opt == '--unix':
			synctool.lib.UNIX_CMD = True
			continue

		if opt in ('-q', '--quiet'):
			# silently ignore this option
			continue

		if opt in ('-p', '--numproc'):
			try:
				synctool.param.NUM_PROC = int(arg)
			except ValueError:
				print ("%s: option '%s' requires a numeric value" %
					(os.path.basename(sys.argv[0]), opt))
				sys.exit(1)

			if synctool.param.NUM_PROC < 1:
				print ('%s: invalid value for numproc' %
					os.path.basename(sys.argv[0]))
				sys.exit(1)

			continue

		if opt in ('-z', '--zzz'):
			try:
				synctool.param.SLEEP_TIME = int(arg)
			except ValueError:
				print ("%s: option '%s' requires a numeric value" %
					(os.path.basename(sys.argv[0]), opt))
				sys.exit(1)

			if synctool.param.SLEEP_TIME < 0:
				print ('%s: invalid value for sleep time' %
					os.path.basename(sys.argv[0]))
				sys.exit(1)

			if not synctool.param.SLEEP_TIME:
				# (temporarily) set to -1 to indicate we want
				# to run serialized
				# synctool.lib.multiprocess() will use this
				synctool.param.SLEEP_TIME = -1

			continue

	if args != None and len(args) > 0:
		print '%s: too many arguments' % os.path.basename(sys.argv[0])
		sys.exit(1)


def main():
	synctool.param.init()

	sys.stdout = synctool.unbuffered.Unbuffered(sys.stdout)
	sys.stderr = synctool.unbuffered.Unbuffered(sys.stderr)

	get_options()

	if OPT_AGGREGATE:
		if not synctool.aggr.run(MASTER_OPTS):
			sys.exit(-1)

		sys.exit(0)

	synctool.config.init_mynodename()

	address_list = NODESET.addresses()
	if not address_list:
		print 'no valid nodes specified'
		sys.exit(1)

	ping_nodes(address_list)


if __name__ == '__main__':
	try:
		main()
	except IOError, ioerr:
		if ioerr.errno == errno.EPIPE:		# Broken pipe
			pass
		else:
			print ioerr

	except KeyboardInterrupt:		# user pressed Ctrl-C
		pass

# EOB
