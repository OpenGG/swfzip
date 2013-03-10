#!/usr/bin/python
#
# This script is inspired by jspiro's swf2lzma repo: https://github.com/jspiro/swf2lzma
#
#
# SWF Formats:
## ZWS(LZMA)
## | 4 bytes       | 4 bytes    | 4 bytes       | 5 bytes    | n bytes    | 6 bytes         |
## | 'ZWS'+version | scriptLen  | compressedLen | LZMA props | LZMA data  | LZMA end marker |
##
## scriptLen is the uncompressed length of the SWF data. Includes 4 bytes SWF header and
## 4 bytes for scriptLen itself
##
## compressedLen does not include header (4+4+4 bytes) or lzma props (5 bytes)
## compressedLen does include LZMA end marker (6 bytes)
#
import os
import pylzma
import sys
import struct
import zlib



def confirm(prompt, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        raise Exception('Not valid prompt')

    if resp:
        prompt = '%s %s/%s: ' % (prompt, 'Y', 'n')
    else:
        prompt = '%s %s/%s: ' % (prompt, 'N', 'y')

    while True:
        ans = raw_input(prompt)
        print ''
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def debug(msg, level='info'):
    print '%s : %s' %(level, msg)

def check(test, msg):
    test or exit('Error: \n'+msg)

def unzip(inData):
    if inData[0] == 'C':
        # zlib SWF
        debug('zlib compressed swf detected.')
        decompressData = zlib.decompress(inData[8:])
    elif inData[0] == 'Z':
        # lzma SWF
        debug('lzma compressed swf detected.')
        decompressData = pylzma.decompress(inData[12:])
    elif inData[0] == 'F':
        # uncompressed SWF
        debug('Uncompressed swf detected.')
        decompressData = inData[8:]
    else:
        exit('not a SWF file')

    sigSize = struct.unpack("<I", inData[4:8])[0]
    debug('Filesize in signature: %s' % sigSize)

    decompressSize = len(decompressData) +8
    debug('Filesize decompressed: %s' % decompressSize)

    check((sigSize == decompressSize), 'Length not correct, decompression failed')
    header = list(struct.unpack("<8B", inData[0:8]))
    header[0] = ord('F')

    debug('Generating uncompressed data')
    return struct.pack("<8B", *header)+decompressData

def zip(inData, compression):
    if(compression == 'lzma'):
        check((inData[0] != 'Z'), "already LZMA compressed")

        rawSwf = unzip(inData);

        debug('Compressing with lzma')
        compressData = pylzma.compress(rawSwf[8:], eos=1)
        # 5 accounts for lzma props

        compressSize = len(compressData) - 5

        header = list(struct.unpack("<12B", inData[0:12]))
        header[0]  = ord('Z')
        header[3]  = header[3]>=13 and header[3] or 13
        header[8]  = (compressSize)       & 0xFF
        header[9]  = (compressSize >> 8)  & 0xFF
        header[10] = (compressSize >> 16) & 0xFF
        header[11] = (compressSize >> 24) & 0xFF

        debug('Packing lzma header')
        headerBytes = struct.pack("<12B", *header);
    else:
        check((inData[0] != 'C'), "already zlib compressed")

        rawSwf = unzip(inData);

        debug('Compressing with zlib')
        compressData = zlib.compress(rawSwf[8:])

        compressSize = len(compressData)

        header = list(struct.unpack("<8B", inData[0:8]))
        header[0] = ord('C')
        header[3]  = header[3]>=6 and header[3] or 6

        debug('Packing zlib header')
        headerBytes = struct.pack("<8B", *header)

    debug('Generating compressed data')
    return headerBytes+compressData

def process(infile, outfile, operation='unzip', compression='zlib'):
    debug('Reading '+infile)
    fi = open(infile, "rb")
    infileSize = os.path.getsize(infile)
    inData = fi.read()
    fi.close()

    check((inData[1] == 'W') and (inData[2] == 'S'), "not a SWF file")


    if(operation=='unzip'):
        outData = unzip(inData)
        increment = round(100.0 * len(outData) / infileSize) - 100
        print 'File decompressed, size increased: %d%%' % increment
    else:
        compression = compression == 'lzma' and 'lzma' or 'zlib'
        outData = zip(inData, compression)
        decrement = increment = 100 - round(100.0 * len(outData) / infileSize)
        print 'File compressed with %s, size decreased: %d%% %s' % (compression, decrement,
            decrement<0 and '\n\nNotice: Recompressing may cause filesize increased' or'')

    fo = open(outfile, 'wb')
    fo.write(outData)
    fo.close()

if __name__ == "__main__":

    command = 'swfunzip' in sys.argv[0] and 'unzip' or 'zip';

    if(command == 'unzip'):
        check(len(sys.argv) == 3, 'usage: swfunzip input.swf output.swf')
    else:
        check(
            len(sys.argv) == 3
            or
            len(sys.argv) == 4 and sys.argv[3] in ['lzma', 'zlib', ''],
            'usage: swfzip input.swf output.swf [lzma/zlib] \
            \n\n notice:zlib is used if compression type not given.')

    infile = sys.argv[1]
    debug('Input file: '+infile)
    check(os.path.exists(infile), 'Input file not exists')

    outfile = sys.argv[2]
    debug('Output file: '+outfile)
    if os.path.exists(outfile) and not confirm('Output file exists, overwrite?'):
        sys.exit(0)

    if(command == 'zip'):
        compression = len(sys.argv) == 3 and 'zlib' or sys.argv[3]
        process(infile, outfile, command, compression)
    else:
        process(infile, outfile, command)

    sys.exit(0)

