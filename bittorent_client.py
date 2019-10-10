import sys
import bencode
import hashlib
import random
from urllib.request import urlopen
from urllib.parse import urlencode
import codecs
import socket
import struct
from bitstring import BitArray


def complete_bitfield(have_index):
    """ updating the bitfield """
    active_peers[0]['bitfield'][have_index] = 1


def receive_rem_data():
    active_peers[0]['data'] += active_peers[0]['socket'].recv(2 * 10 ** 6)
    parse_data(active_peers[0]['data'])


def parse_data(data):
    """ Parses data and handles different message_types accordingly """
    message_types = {0: 'choke',
                     1: 'unchoke',
                     2: 'interested',
                     3: 'not interested',
                     4: 'have',
                     5: 'bitfield',
                     6: 'request',
                     7: 'piece',
                     8: 'cancel'
                     }
    while len(data) > 0:
        if len(data) < 4:
            break
        length = struct.unpack('!I', data[:4])[0]
        if length == 0:
            message_type = 'keep alive'
            data = data[4:]
        else:  # data type anything but 'keep alive'
            try:
                print("Trying to parse data")
                message_type = message_types[data[4]]
                print(message_type)
            except KeyError:
                receive_rem_data()
            length = length - 1
            if message_type == 'choke':
                active_peers[0]['choke'] = True
                print("choked")
            elif message_type == 'unchoke':
                active_peers[0]['choke'] = False
                print("Unchoked")
            elif message_type == 'interested':
                active_peers[0]['interested'] = True
            elif message_type == 'not interested':
                active_peers[0]['interested'] = False
            elif message_type == 'have':
                complete_bitfield(struct.unpack('!I', data[5:5 + length])[0])
            elif message_type == 'bitfield':
                expected_bitfield_length = number_of_pieces
                # print("expected bitfield_length: ", expected_bitfield_length)
                bitfield = BitArray(bytes=data[5:5 + length])
                bitfield = bitfield[:int(expected_bitfield_length)]
                # print(bitfield)
                active_peers[0]['bitfield'] = bitfield
                pass
            elif message_type == 'request':
                pass
            elif message_type == 'piece':
                pass
            elif message_type == 'cancel':
                pass
            else:
                break
            data = data[5 + length:]


def send_interested(active_peers_first):
    """  sending interested message to peers """
    # making interested message
    if active_peers_first is None:
        return
    interested = struct.pack("!I", 1) + struct.pack("!B", 2)
    sock = active_peers_first['socket']
    sock.send(interested)
    data = sock.recv(10 ** 6)
    active_peers[0]['data'] = data


def send_handshake():
    """ sending handshake message to peers
        connection_state_for_peer: a dictionary for every peer to store connection state with every peer
    """
    connectionState_for_peer = {'choke': True,
                                'interested': False}
    peer_socket.send(our_handshake)
    response_handshake = peer_socket.recv(68)
    var = str(response_handshake)

    id = 'peer id'
    if decoded_tracker_response['peers'][0][id] in var:  # need to handle type error
        connectionState_for_peer['socket'] = peer_socket
        active_peers.append(connectionState_for_peer)
    else:
        peer_socket.close()
        active_peers.append(None)


def connect_with_peers(ip_and_port):
    """ TCP connection with the peers using ip address and port number """
    ip, port = ip_and_port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        return sock
    except socket.error as e:
        print("Caught socket error:", e, "on socket", sock.fileno(), "from peer IP", ip)


def make_handshake(i_h, p_i):
    """Creating handshake message """
    handshake = b''.join([chr(19).encode(), b'BitTorrent protocol', (chr(0) * 8).encode(), i_h, p_i.encode()])
    print(handshake)
    return handshake


def make_peers(peers_dictionary):
    """ converting the response of tracker into list of peers ip addresses and port numbers """
    ip_and_port = []
    for peer in peers_dictionary:
        ip_and_port.append((peer['ip'], peer['port']))

    return ip_and_port


def create_tracker_url(base_url, parameters):
    """ creating URL for trackers """
    return base_url + '?' + urlencode(parameters)


def tracker_response(url):
    """ checking the trackers response """

    print(url)
    res = urlopen(url)
    if res.getcode() == 200:
        return res, True
    return None, False


torrent_File = sys.argv[1]
with open(torrent_File, "rb") as tf:
    # decoding the .torrent file
    decoded_tracker_file = bencode.bdecode(tf.read())
    keys_in_info = sorted(list(decoded_tracker_file['info'].keys()))
    info_dict = {}
    for k in keys_in_info:
        info_dict[k] = decoded_tracker_file['info'][k]

    file_name = decoded_tracker_file['info']['name']
    # How many files
    multiple_files = decoded_tracker_file.get('files', None)
    number_of_files = len(multiple_files) if multiple_files else 1

    # calculating the total size of file
    size = 0
    try:
        k = 'files'
        m = 'length'
        for file in decoded_tracker_file['info'][k]:
            size += file[m]
    except KeyError:
        m = 'length'
        size = decoded_tracker_file['info'][m]

    # information about the pieces
    pieces = decoded_tracker_file['info']['pieces']
    piece_length = decoded_tracker_file['info']['piece length']
    assert len(pieces) % 20 == 0
    number_of_pieces = len(pieces) / 20

    # information about the blocks
    block_length = max(2 ** 14, piece_length)
    whole_blocks_per_piece = piece_length / block_length
    last_block_size = piece_length % block_length

    # creating info_hash with sha1()
    version = 1000
    info_hash = codecs.decode(hashlib.sha1(bencode.bencode(info_dict)).hexdigest(), 'hex')
    downloaded = uploaded = 0
    port = 6881
    # peer_id
    peer_id = "-CA%s-" % version + str(random.randint(10 ** 11, 10 ** 12 - 1))
    params = {
        'info_hash': info_hash,
        'peer_id': peer_id,
        'port': port,
        'uploaded': uploaded,
        'downloaded': downloaded,
        'left': size
    }

    # creating tracker URL
    tracker_url = ''
    connected_to_tracker = False
    if 'announce-list' in decoded_tracker_file.keys():
        for announce in decoded_tracker_file['announce-list']:
            if connected_to_tracker:
                break
            if announce[0].startswith('http'):
                tracker_url = create_tracker_url(announce[0], params)
            try:
                response, connected_to_tracker = tracker_response(tracker_url)
            except TimeoutError:
                print("couldn't connect to trackers:Timeout")
    else:
        announce = decoded_tracker_file['announce']
        if announce.startswith('http'):
            tracker_url = create_tracker_url(decoded_tracker_file['announce'], params)
        try:
            response, gitconnected_to_tracker = tracker_response(tracker_url)
        except TimeoutError:
            print("couldn't connect to trackers:Timeout")

    # connecting to tracker and get its response
    if connected_to_tracker:
        decoded_tracker_response = bencode.bdecode(response.read())
        if 'failure reason' in decoded_tracker_response:
            print(decoded_tracker_response['failure reason'])
        # else:
        #     peers_dict = decoded_tracker_response['peers']
    else:
        print("...couldn't connected to tracker")

    client_bitfield = BitArray(int(number_of_pieces))
    active_peers = []

    print(decoded_tracker_response)
    peers_dict = make_peers(decoded_tracker_response['peers'])
    peer_socket = connect_with_peers(peers_dict[0])
    our_handshake = make_handshake(info_hash, peer_id)
    send_handshake()
    # print(len(active_peers), active_peers[0], decoded_tracker_response['peers'][0]['peer id'])

    active_peers[0]['bitfield'] = BitArray(int(number_of_pieces))
    send_interested(active_peers[0])  # handle Nonetype error
    parse_data(active_peers[0]['data'])
    op_file = open(file_name, "wb")
