import sys
import bencode
import hashlib
import random
from urllib.request import urlopen
from urllib.parse import urlencode

torrent_File = sys.argv[1]
with open(torrent_File, "rb") as tf:
    decoded_file = bencode.bdecode(tf.read())
    # print(decoded_file['announce-list'])

    keys_in_info = sorted(list(decoded_file['info'].keys()))
    info_dict = {}
    for k in keys_in_info:
        info_dict[k] = decoded_file['info'][k]

    # comment below are to check that info_dict is correctly bencoded or not
    # x = bencode.bencode(info_dict)
    # if bencode.bdecode(x) == info_dict:
    #     print('correct')

    size = 0
    try:
        k = 'files'
        length = 'length'
        for file in decoded_file['info'][k]:
            size += file[length]
    except KeyError:
        length = 'length'
        size = decoded_file['info'][length]

    # print(total_length)
    request_Paramaters = {
        'info_hash': hashlib.sha1(bencode.bencode(info_dict)).hexdigest(),
        'peer_id': "-CA2060-" + str(random.randint(100000000000, 999999999999)),
        'port': 6881,
        'uploaded': 0,
        'downloaded': 0,
        'left': size
    }

    tracker_url = decoded_file['announce'] + '?' + urlencode(request_Paramaters)
    print(tracker_url)
    try:
        response = urlopen(tracker_url)
        if response.getcode() == 200:
            # find out the peers ip, port numbers
            pass
    except TimeoutError:
        print("couldn't connect to trackers")







