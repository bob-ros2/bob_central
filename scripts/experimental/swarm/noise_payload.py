#!/usr/bin/env python3
"""
noise_payload.py - Manual protobuf encoding for NoiseHandshakePayload.
Implements the libp2p NoiseHandshakePayload message without requiring protoc.

Message schema (from libp2p noise spec):
message NoiseExtensions {
    repeated bytes webtransport_certhashes = 1;
    repeated string stream_muxers = 2;
}

message NoiseHandshakePayload {
    optional bytes identity_key = 1;
    optional bytes identity_sig = 2;
    optional NoiseExtensions extensions = 4;
}
"""

import struct


def _varint_encode(value: int) -> bytes:
    buf = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        buf.append(byte)
        if not value:
            break
    return bytes(buf)


def _encode_field(field_num: int, wire_type: int, value: bytes) -> bytes:
    """Encode a protobuf field with tag + length + value."""
    tag = (field_num << 3) | wire_type
    return _varint_encode(tag) + _varint_encode(len(value)) + value


def encode_noise_handshake_payload(identity_key: bytes, identity_sig: bytes,
                                    stream_muxers: list = None) -> bytes:
    """
    Encode a NoiseHandshakePayload protobuf message.
    
    Args:
        identity_key: Serialized libp2p PublicKey (protobuf)
        identity_sig: Signature of the Noise static key
        stream_muxers: List of supported stream muxer protocol IDs
    
    Returns:
        Serialized protobuf message bytes
    """
    payload = b''
    
    # Field 1: identity_key (bytes, wire type 2)
    if identity_key:
        payload += _encode_field(1, 2, identity_key)
    
    # Field 2: identity_sig (bytes, wire type 2)
    if identity_sig:
        payload += _encode_field(2, 2, identity_sig)
    
    # Field 4: extensions (message, wire type 2)
    if stream_muxers:
        ext_data = b''
        for muxer in stream_muxers:
            # Field 2 in NoiseExtensions: stream_muxers (string, wire type 2)
            muxer_bytes = muxer.encode('utf-8')
            ext_data += _encode_field(2, 2, muxer_bytes)
        
        payload += _encode_field(4, 2, ext_data)
    
    return payload


def encode_libp2p_public_key(key_type: int, key_data: bytes) -> bytes:
    """
    Encode a libp2p PublicKey protobuf message.
    
    message PublicKey {
        required KeyType Type = 1;
        required bytes Data = 2;
    }
    
    enum KeyType {
        RSA = 0;
        Ed25519 = 1;
        Secp256k1 = 2;
        ECDSA = 3;
    }
    """
    payload = b''
    # Field 1: Type (enum = varint, wire type 0)
    payload += _varint_encode((1 << 3) | 0) + _varint_encode(key_type)
    # Field 2: Data (bytes, wire type 2)
    payload += _encode_field(2, 2, key_data)
    return payload


def build_handshake_payload(static_key_bytes: bytes, 
                             ed25519_private_key=None) -> tuple:
    """
    Build a complete NoiseHandshakePayload.
    
    In a full implementation, this would:
    1. Serialize the libp2p identity public key
    2. Sign the Noise static key with the identity private key
    3. Package everything into a NoiseHandshakePayload
    
    For now, returns a minimal payload with placeholder values.
    
    Returns:
        (payload_bytes, identity_key_bytes)
    """
    # Placeholder: use a simple Ed25519 key format
    # In production, this would use the actual libp2p identity key
    
    # Create a minimal identity key (Ed25519 type = 1)
    # For testing, we use a dummy key
    dummy_key_data = b'\\x00' * 32  # 32-byte Ed25519 public key
    identity_key = encode_libp2p_public_key(1, dummy_key_data)
    
    # Create a dummy signature (64 bytes for Ed25519)
    dummy_sig = b'\\x00' * 64
    
    # Build payload with stream muxers
    payload = encode_noise_handshake_payload(
        identity_key=identity_key,
        identity_sig=dummy_sig,
        stream_muxers=['/mplex/6.7.0', '/yamux/1.0.0']
    )
    
    return payload, identity_key


if __name__ == '__main__':
    # Test encoding
    payload, id_key = build_handshake_payload(b'\\x00' * 32)
    print(f'Payload size: {len(payload)} bytes')
    print(f'Identity key size: {len(id_key)} bytes')
    print(f'Payload hex: {payload[:40].hex()}...')
