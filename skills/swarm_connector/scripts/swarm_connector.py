#!/usr/bin/env python3
"""Swarm Connector Skill - External P2P network interface for Eva."""
import socket
import sys
import time

sys.path.insert(0, '/ros2_ws/src/bob_central/scripts/experimental/swarm')

NOISE_OK = False
try:
    from noise_xx_handshake import perform_xx_handshake
    NOISE_OK = True
except ImportError:
    pass

BOOTSTRAP_NODES = [('51.81.93.51', 4001), ('147.75.83.211', 4001)]


def varint_encode(v):
    buf = []
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            b |= 0x80
        buf.append(b)
        if not v:
            break
    return bytes(buf)


def probe_node(host, port, timeout=8.0):
    """Probe a bootstrap node and return protocol info."""
    result = {'host': host, 'port': port, 'reachable': False, 'protocols': []}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        result['reachable'] = True

        # Multistream
        msg = b'/multistream/1.0.0\n'
        s.send(varint_encode(len(msg)) + msg)
        time.sleep(0.2)
        d = s.recv(1)
        while True:
            val, c = 0, 0
            for i, b in enumerate(d):
                val |= (b & 0x7F) << (7 * i)
                if not (b & 0x80):
                    c = i + 1
                    break
            if c > 0:
                break
            d += s.recv(1)
        s.recv(val)
        result['protocols'].append('multistream')

        # Noise
        msg = b'/noise\n'
        s.send(varint_encode(len(msg)) + msg)
        time.sleep(0.2)
        d = s.recv(1)
        while True:
            val, c = 0, 0
            for i, b in enumerate(d):
                val |= (b & 0x7F) << (7 * i)
                if not (b & 0x80):
                    c = i + 1
                    break
            if c > 0:
                break
            d += s.recv(1)
        resp = s.recv(val)
        if b'noise' in resp:
            result['protocols'].append('noise')
            if NOISE_OK:
                try:
                    hs = perform_xx_handshake(s, timeout=5.0)
                    result['noise_handshake'] = hs is not None
                except Exception:
                    result['noise_handshake'] = False

        # Kad
        msg = b'/ipfs/kad/1.0.0\n'
        s.send(varint_encode(len(msg)) + msg)
        time.sleep(0.2)
        d = s.recv(1)
        while True:
            val, c = 0, 0
            for i, b in enumerate(d):
                val |= (b & 0x7F) << (7 * i)
                if not (b & 0x80):
                    c = i + 1
                    break
            if c > 0:
                break
            d += s.recv(1)
        resp = s.recv(val)
        if b'kad' in resp:
            result['protocols'].append('kad')

        s.close()
    except Exception as e:
        result['error'] = str(e)
    return result


if __name__ == '__main__':
    print('=== Swarm Connector Skill ===')
    print(f'Noise module: {"OK" if NOISE_OK else "NOT AVAILABLE"}')
    for h, p in BOOTSTRAP_NODES:
        r = probe_node(h, p)
        print(f'{h}:{p} -> reachable={r["reachable"]} protocols={r["protocols"]}')
        if r.get('noise_handshake') is not None:
            status = 'SUCCESS' if r['noise_handshake'] else 'FAILED'
            print(f'  Noise handshake: {status}')
