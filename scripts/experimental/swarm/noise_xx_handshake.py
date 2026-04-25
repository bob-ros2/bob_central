#!/usr/bin/env python3
"""
noise_xx_handshake.py - Eva's libp2p Noise XX Handshake Implementation.
Fixed: custom HKDF, correct nonce byte order, proper associated data (h).
"""

import json
import os
import hashlib
import hmac
import struct
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)
from cryptography.hazmat.primitives import serialization

PROTOCOL_NAME = b'Noise_XX_25519_ChaChaPoly_SHA256'
CIPHER_KEY_LEN = 32


class NoiseHandshakeError(Exception):
    pass


class SymmetricState:
    def __init__(self):
        self.ck = None
        self.k = None
        self.n = 0
        self.h = None  # handshake hash (used as associated data)

    def initialize_symmetric(self, protocol_name: bytes):
        h = hashlib.sha256(protocol_name).digest()
        self.ck = h
        self.h = h[:]  # copy for handshake hash
        self.k = b'\x00' * CIPHER_KEY_LEN
        self.n = 0

    def mix_key(self, dh_output: bytes):
        temp = hmac.new(self.ck, dh_output, hashlib.sha256).digest()
        out1 = hmac.new(temp, b'\x01', hashlib.sha256).digest()
        out2 = hmac.new(temp, out1 + b'\x02', hashlib.sha256).digest()
        self.ck = out1
        self.k = out2
        self.n = 0

    def mix_hash(self, data: bytes):
        self.h = hashlib.sha256(self.h + data).digest()

    def encrypt_and_hash(self, plaintext: bytes) -> bytes:
        nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', self.n)
        self.n += 1
        aead = ChaCha20Poly1305(self.k)
        ciphertext = aead.encrypt(nonce, plaintext, self.h)
        self.mix_hash(ciphertext)
        return ciphertext

    def decrypt_and_hash(self, ciphertext: bytes) -> bytes:
        nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', self.n)
        self.n += 1
        aead = ChaCha20Poly1305(self.k)
        plaintext = aead.decrypt(nonce, ciphertext, self.h)
        self.mix_hash(ciphertext)
        return plaintext

    def split(self) -> Tuple:
        temp = hmac.new(self.ck, b'', hashlib.sha256).digest()
        out1 = hmac.new(temp, b'\x01', hashlib.sha256).digest()
        out2 = hmac.new(temp, out1 + b'\x02', hashlib.sha256).digest()
        # In Noise XX: out1 is sender key (initiator), out2 is receiver key
        return TransportCipher(out1), TransportCipher(out2)


class TransportCipher:
    def __init__(self, key: bytes):
        self.k = key
        self.n = 0

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', self.n)
        self.n += 1
        aead = ChaCha20Poly1305(self.k)
        return aead.encrypt(nonce, plaintext, None)

    def decrypt(self, ciphertext: bytes) -> bytes:
        nonce = b'\x00\x00\x00\x00' + struct.pack('<Q', self.n)
        self.n += 1
        aead = ChaCha20Poly1305(self.k)
        return aead.decrypt(nonce, ciphertext, None)


class NoiseXXHandshake:
    """Implements Noise_XX_25519_ChaChaPoly_SHA256 handshake."""

    def __init__(self, initiator: bool = True):
        self.initiator = initiator
        self.symmetric = SymmetricState()
        self.symmetric.initialize_symmetric(PROTOCOL_NAME)
        self.ephemeral_private = X25519PrivateKey.generate()
        self.ephemeral_public = self.ephemeral_private.public_key()
        self.static_private = None
        self.static_public = None
        self.rs = None
        self.re = None

    def set_static_keypair(self, private_key: X25519PrivateKey):
        self.static_private = private_key
        self.static_public = private_key.public_key()

    def _serialize_public(self, key: X25519PublicKey) -> bytes:
        return key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def _deserialize_public(self, data: bytes) -> X25519PublicKey:
        return X25519PublicKey.from_public_bytes(data)

    def _dh(self, private: X25519PrivateKey, public: X25519PublicKey) -> bytes:
        return private.exchange(public)

    def write_message_1(self) -> bytes:
        e_bytes = self._serialize_public(self.ephemeral_public)
        self.symmetric.mix_hash(e_bytes)
        return e_bytes

    def read_message_1(self, data: bytes) -> bytes:
        if len(data) < 32:
            raise NoiseHandshakeError('Message 1 too short')
        e_bytes = data[:32]
        self.re = self._deserialize_public(e_bytes)
        if not self.initiator:
            self.re_init = self.re
        self.symmetric.mix_hash(e_bytes)
        return e_bytes

    def write_message_2(self, payload: bytes = b'') -> bytes:
        self.ephemeral_private = X25519PrivateKey.generate()
        self.ephemeral_public = self.ephemeral_private.public_key()
        e_bytes = self._serialize_public(self.ephemeral_public)
        self.symmetric.mix_hash(e_bytes)
        ee = self._dh(self.ephemeral_private, self.re)
        self.symmetric.mix_key(ee)
        s_bytes = self._serialize_public(self.static_public)
        encrypted_s = self.symmetric.encrypt_and_hash(s_bytes)
        es = self._dh(self.static_private, self.re)
        self.symmetric.mix_key(es)
        encrypted_payload = self.symmetric.encrypt_and_hash(payload)
        return e_bytes + encrypted_s + encrypted_payload

    def read_message_2(self, data: bytes) -> Tuple[bytes, bytes, bytes]:
        offset = 0
        e_bytes = data[offset:offset + 32]
        offset += 32
        self.re = self._deserialize_public(e_bytes)
        self.symmetric.mix_hash(e_bytes)
        ee = self._dh(self.ephemeral_private, self.re)
        self.symmetric.mix_key(ee)
        ct_len = 48
        encrypted_s = data[offset:offset + ct_len]
        offset += ct_len
        s_bytes = self.symmetric.decrypt_and_hash(encrypted_s)
        self.rs = self._deserialize_public(s_bytes)
        es = self._dh(self.ephemeral_private, self.rs)
        self.symmetric.mix_key(es)
        encrypted_payload = data[offset:]
        plaintext = self.symmetric.decrypt_and_hash(encrypted_payload)
        return e_bytes, s_bytes, plaintext

    def write_message_3(self, payload: bytes = b'') -> bytes:
        s_bytes = self._serialize_public(self.static_public)
        encrypted_s = self.symmetric.encrypt_and_hash(s_bytes)
        se = self._dh(self.static_private, self.re)
        self.symmetric.mix_key(se)
        encrypted_payload = self.symmetric.encrypt_and_hash(payload)
        return encrypted_s + encrypted_payload

    def read_message_3(self, data: bytes) -> Tuple[bytes, bytes]:
        offset = 0
        ct_len = 48
        encrypted_s = data[offset:offset + ct_len]
        offset += ct_len
        s_bytes = self.symmetric.decrypt_and_hash(encrypted_s)
        self.rs = self._deserialize_public(s_bytes)
        se = self._dh(self.ephemeral_private, self.rs)
        self.symmetric.mix_key(se)
        encrypted_payload = data[offset:]
        plaintext = self.symmetric.decrypt_and_hash(encrypted_payload)
        return s_bytes, plaintext

    def finalize(self) -> Tuple[TransportCipher, TransportCipher]:
        c1, c2 = self.symmetric.split()
        if self.initiator:
            return c1, c2  # send, receive
        else:
            return c2, c1  # send, receive


def perform_xx_handshake(sock, timeout: float = 10.0) -> Optional[Tuple]:
    try:
        sock.settimeout(timeout)
        static_private = X25519PrivateKey.generate()
        initiator = NoiseXXHandshake(initiator=True)
        initiator.set_static_keypair(static_private)
        
        # Message 1
        msg1 = initiator.write_message_1()
        sock.sendall(struct.pack('>H', len(msg1)) + msg1)
        
        # Message 2
        header = sock.recv(2)
        if not header or len(header) < 2:
            return None
        msg2_len = struct.unpack('>H', header)[0]
        msg2 = b''
        while len(msg2) < msg2_len:
            chunk = sock.recv(min(4096, msg2_len - len(msg2)))
            if not chunk: break
            msg2 += chunk
        initiator.read_message_2(msg2)
        
        # Message 3
        msg3 = initiator.write_message_3()
        sock.sendall(struct.pack('>H', len(msg3)) + msg3)
        
        return initiator.finalize()
    except Exception:
        return None


if __name__ == '__main__':
    print('=== Eva Noise XX Handshake ===')
    print(f'Protocol: {PROTOCOL_NAME.decode()}')
    print('Module loaded successfully')
