import sys
import os
import logging
import zlib
from xml.dom.minidom import parseString

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='')


class Kom:
    def __init__(self, path):
        self.path = path

    def open(self):
        with open(self.path, 'rb') as f:
            self.version = f.read(27).decode()
            f.seek(52)
            self.entry_count = int.from_bytes(f.read(4), 'little')
            f.seek(64)
            self.file_timer = int.from_bytes(f.read(4), 'little')
            self.xml_size = int.from_bytes(f.read(4), 'little')
            self.xml = f.read(self.xml_size).decode()
        self.offset = 72 + self.xml_size
        logger.info('Opening %s...'    % self.path)
        logger.info('version     = '   + self.version)
        logger.info('entry_count = %d' % self.entry_count)
        logger.info('file_timer  = %d' % self.file_timer)
        logger.info('xml_size    = %d' % self.xml_size)

    def extract(self, out):
        with open(self.path, 'rb') as f1:
            f1.seek(self.offset)
            for i in parseString(self.xml).getElementsByTagName('Files')[0].childNodes:
                name = i.getAttribute('Name')
                size = int(i.getAttribute('CompressedSize'))
                fullpath = os.path.join(out, name)
                if os.path.exists(fullpath):
                    logger.info('Skipping %s...' % name)
                    continue
                logger.info('Copying %s...' % name)
                with open(fullpath, 'wb') as f2:
                    f2.write(zlib.decompress(f1.read(size)))


def extract(files, out):
    for i in files:
        kom = Kom(i)
        kom.open()
        kom.extract(out)


def parse_args(args):
    out = ''
    files = []
    n = 0
    while n < len(args):
        i = args[n]
        if i == '-d':
            logger.setLevel(logging.DEBUG)
        elif i == '-o':
            n += 1
            if not len(args) > n:
                raise ValueError('-o switch needs an argument')
            i = args[n]
            if not os.path.exists(i):
                raise FileNotFoundError('can\'t find folder ' + i)
            if not os.path.isdir(i):
                raise NotADirectoryError(i + ' is not a folder')
            out = os.path.abspath(i)
        else:
            if not os.path.exists(i):
                raise FileNotFoundError('can\'t find file ' + i)
            if not os.path.isfile(i):
                raise IsADirectoryError(i + 'is not a file')
            files.append(i)
        n += 1
    if not files:
        raise ValueError('Usage: ' + os.path.basename(__file__) + ' files -o folder')
    return files, out


def main(*args):
    extract(*args)


if __name__ == '__main__':
    try:
        main(*parse_args(sys.argv[1:]))
    except ValueError as e:
        logger.critical(e)
    except OSError as e:
        logger.critical(e)
    except Exception:
        logger.exception('An error ocurred')
