#!/usr/bin/env python

import sys
import os
import argparse
import glob
import subprocess
import logging


logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stderr)
log = logging.getLogger(__name__)


# python2 back-compat
def makedirs(path, mode=0o777, exist_ok=False):
    try:
        os.makedirs(path, mode=mode, exist_ok=exist_ok)
    except TypeError:
        try:
            os.makedirs(path, mode=mode)
        except OSError as e:
            if exist_ok and e.errno == 17: # File exists
                pass
            else:
                raise


def size_in_bytes(given_size):
    if not given_size:
        return given_size
    quantifiers = 'kmgt'
    size = given_size.lower().rstrip('b')
    if len(size) > 0 and size[-1] in quantifiers:
        multiplier = 1024 ** (quantifiers.find(size[-1]) + 1)
        size = size[:-1]
    else:
        multiplier = 1
    return multiplier * int(size)


class Error(Exception):
    """Base exception class for this project"""
    pass


class FileSizeExceedsMaximumArchiveSizeError(Error):
    def __init__(self, file_path, file_size, archive_max_size):
        self.file_path = file_path
        self.file_size = file_size
        self.archive_max_size = archive_max_size

    def __str__(self):
        return 'size of file {o.file_path} ({o.file_size}) exceeds maximum allowed archive size of {o.archive_max_size}'.format(o=self)


class FileListWriter(object):
    def __init__(self, output_dir, base_name, archive_size, archive_max_size):
        self.index = 0
        self.tar_header_size = 512
        self.tar_overhead_size = 10240
        self.output_dir = output_dir
        self.base_name = base_name
        self.archive_size = archive_size
        self.archive_max_size = archive_max_size
        self.current_size = 0
        self.current_file = None
        self.largest_file_size = -1
        makedirs(self.output_dir, mode=0o750, exist_ok=True)
        self.next_file()

    def next_file(self):
        self.index += 1
        if self.current_file:
            log.info('largest file in archive {0} is {1}'.format(self.current_file.name, self.largest_file_size))
            self.current_file.close()
        file_path = os.path.join(self.output_dir, '{0}-{1:03d}.files'.format(self.base_name, self.index))
        log.info('switching to next file: {0}'.format(file_path))
        self.current_file = open(file_path, 'w')
        self.current_size = 0

    def add(self, line_or_filepath):
        if line_or_filepath.endswith('\n'):
            file_path = line_or_filepath.rstrip('\n')
            line = line_or_filepath
        else:
            file_path = line_or_filepath
            line = line_or_filepath +'\n'
        file_size = os.path.getsize(file_path)
        log.debug('add {0} {1}'.format(file_path, file_size))
        # add metadata + padding to file size
        file_size_in_archive = file_size + self.tar_header_size + (512 - (file_size % 512))

        if file_size_in_archive >= self.archive_max_size:
            raise FileSizeExceedsMaximumArchiveSizeError(
                    file_path, file_size,
                    self.archive_max_size)
        elif file_size_in_archive >= self.archive_size:
            log.warn('size of file {0} ({1}) exceeds preferred archive size of {2}'.format(file_path, file_size, self.archive_size))

        new_archive_size = self.current_size + file_size_in_archive + self.tar_overhead_size
        if new_archive_size >= self.archive_size:
            log.debug('new archive size {0} would exceed prefered archive size {1}'.format(new_archive_size, self.archive_size))
            self.next_file()
        if file_size > self.largest_file_size:
            self.largest_file_size = file_size
        self.current_size += file_size_in_archive
        self.current_file.write(line)

    def process(self, list_or_stream):
        for line_or_filepath in list_or_stream:
            self.add(line_or_filepath)


def create_archive(list_file, archive_file, index_file):
    command = 'tar --create --verbose --directory /'.split()
    command.extend(('--files-from', list_file))
    command.extend(('--index-file', index_file))
    command.extend(('-f', archive_file))
    log.info('creating tar archive at {0} with files from {1}'.format(archive_file, list_file))
    log.debug(command)
    return subprocess.check_call(command)
    #with open(os.devnull, 'w') as dev_null:
    #    return subprocess.check_call(command, stderr=dev_null)


def verify_archive(archive_file):
    command = 'tar --compare --directory /'.split()
    command.extend(('-f', archive_file))
    log.info('verifying tar archive at {0}'.format(archive_file))
    log.debug(command)
    return subprocess.check_call(command, stderr=dev_null)
    #with open(os.devnull, 'w') as dev_null:
    #    return subprocess.check_call(command, stderr=dev_null)


def main(args):
    writer = FileListWriter(
        args.output_dir,
        args.base_name,
        args.tar_size,
        args.max_tar_size)
    writer.process(args.files_from)

    if not args.no_archive:
        for list_file in sorted(glob.glob('{0}/*.files'.format(args.output_dir))):
            #try:
                base_path = os.path.splitext(list_file)[0]
                archive_file = base_path + '.tar'
                index_file = archive_file + '.index'
                exit_code = create_archive(list_file, archive_file, index_file)
                log.debug('exit_code: {0}'.format(exit_code))
                if not args.no_verify:
                    verify_archive(archive_file)
            #except subprocess.CalledProcessError as e:
            #    raise Error(e)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Distribute a list of files among tar archives of a given size',
        epilog='Example: find /input -type f -print | files2tar -s 200G -m 2TB base-name /output')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
        help='set log level to debug')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help='set log level to info')
    parser.add_argument('--files-from', type=argparse.FileType('r'), default=sys.stdin, metavar='FILE',
        help='read list of source-file names from FILE. Defaults to stdin')
    parser.add_argument('-0', '--null', action='store_true',
        help='file list is terminated by a null character instead of by whitespace')
    default_tar_size = '1G'
    parser.add_argument('-s', '--tar-size', default=default_tar_size, type=size_in_bytes,
        help='prefered target size of tar archives, defaults to: \'{}\''.format(default_tar_size))
    parser.add_argument('-m', '--max-tar-size', type=size_in_bytes,
        help='maximum possible size of tar archives, defaults to TAR_SIZE')
    parser.add_argument('--no-archive', action='store_true', default=False,
        help='only create lists of files instead of also creating the tar archives')
    parser.add_argument('--no-verify', action='store_true', default=False,
        help='do not verify created tar archives')
    parser.add_argument('base_name', metavar='base-name',
        help='the prefix to use when creating file names')
    parser.add_argument('output_dir', metavar='output-dir',
        help='the directory in which to create output files')

    args = parser.parse_args(argv)
    if not args.max_tar_size:
        args.max_tar_size = args.tar_size
    if args.verbose:
        logging.root.setLevel(logging.INFO)
    if args.debug:
        logging.root.setLevel(logging.DEBUG)

    log.debug(args)
    return args


def run():
    try:
        args = parse_args(sys.argv[1:])
        main(args)
    except Error as e:
        log.error(e)
        sys.exit(1)
    except KeyboardInterrupt:
        pass # Press Ctrl+C to stop


if __name__ == '__main__':
    run()
