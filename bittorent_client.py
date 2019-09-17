import sys
import bencode

torrent_File = sys.argv[1]

with open(sys.argv[1], "r") as torrentFile:
    bencode.bdecode(torrentFile)
