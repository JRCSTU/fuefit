import contextlib
import os
import sys

## Adapted from the response to issue(http://bugs.python.org/issue15805):
#    https://gist.githubusercontent.com/msabramo/6043474/raw/b02894848fd683b556f27c0ac2dbcf316f538168/redirect.py
#

@contextlib.contextmanager
def redirected(**kwargs):
    """
    A context manager to temporarily redirect stdout or stderr

    Examples:

    # Redirect stdout to /dev/null
    >>> with redirected(stdout=None):
    ...     os.system("echo foo; ls dfkdjfdkfd")
    ...
    ls: dfkdjfdkfd: No such file or directory

    # Redirect stderr to /dev/null
    >>> with redirected(stderr=None):
    ...     os.system("echo foo; ls djdffdd")
    ...
    foo
    256

    # Redirect stdout and stderr to /dev/null
    >>> with redirected(stdout=None, stderr=None):
    ...     os.system("echo foo; ls djdffdd")
    ...

    # Redirect stdout and stderr to filenames
    >>> with redirected(stdout='stuff_stdout.txt', stderr='stuff_stderr.txt'):
    ...     ret = os.system("echo foo; ls dfjkdfd")
    ...
    >>> open('stuff_stdout.txt').read()
    'foo\n'
    >>> open('stuff_stderr.txt').read()
    'ls: dfjkdfd: No such file or directory\n'

    # Redirect stdout to a file and stderr to a filename
    >>> with open('going_to_stdout.txt', 'w') as out:
    ...     with redirected(stdout=out, stderr='stuff_stderr.txt'):
    ...         ret = os.system("echo stuff going to stdout; ls 123456")
    ...
    >>> open('going_to_stdout.txt', 'r').read()
    'stuff going to stdout\n'
    >>> open('stuff_stderr.txt', 'r').read()
    'ls: 123456: No such file or directory\n'

    # Redirect stdout to a file-like object
    # This does not work with subprocesses.
    >>> from StringIO import StringIO
    >>> out = StringIO()
    >>> with redirected(stdout=out):
    ...     print('printing some stuff')
    ...
    >>> out.getvalue()
    'printing some stuff\n'

    """

    dest_files = {}
    old_filenos = {}
    old_channels = {}

    try:
        for channel_name, destination in kwargs.items():
            stdchannel = getattr(sys, channel_name)
            try:
                old_filenos[channel_name] = os.dup(stdchannel.fileno())
                dupped = True
            except:
                # # Failback if not a real file (i.e. Eclipse's console).
                #
                old_channels[channel_name] = stdchannel
                dupped = False

            if destination is None:
                dest_file = open(os.devnull, 'w')
            elif hasattr(destination, 'startswith'):  # A string => treat as filename
                dest_file = open(destination, 'w')
            else:
                try:
                    _ = destination.fileno()  # A file-like object
                    dest_file = destination
                except Exception:
                    dest_file = None

            if dest_file and dupped:
                os.dup2(dest_file.fileno(), stdchannel.fileno())
                dest_files[channel_name] = dest_file
            else:
                setattr(sys, channel_name, destination)

        yield
    finally:
        for channel_name, old_channel in old_channels.items():
            setattr(sys, channel_name, old_channel)

        for channel_name, old_fileno in old_filenos.items():
            setattr(sys, '%s' % channel_name, getattr(sys, '__%s__' % channel_name))

            if channel_name in dest_files:
                stdchannel = getattr(sys, channel_name)
                dest_file = dest_files[channel_name]

                if old_fileno is not None:
                    os.dup2(old_fileno, stdchannel.fileno())
                if dest_file is not None:
                    dest_file.close()

