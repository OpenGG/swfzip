# swfzip

Toolset to compress/decompress swf with zlib/lzma

## Installation

0. First you need python2.7 with pylzma package installed;
0. Run `build.py` to set up symbolic link;

## Usage

Compressing: `swfzip.py input.swf output.swf [lzma/zlib]`
If no compression format is given, then `zlib` is used, for its better compatibility

Desompressing: `swfunzip.py input.swf output.swf`