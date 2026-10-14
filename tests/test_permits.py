"""Permit signer address derivation against published Mavryk protocol vectors."""

import unittest
from types import SimpleNamespace

import base58

from equiteez.utils.permits import address_from_public_key, permit_signer

# Public key/address pairs from the official protocol's key_encoding_vectors.ml:
# https://github.com/mavryk-network/mavryk-protocol/blob/
# 48f5f52201d9a971cd1739b243106259efc3346a/src/lib_crypto/test/key_encoding_vectors.ml
KEY_VECTORS = (
    (
        "edpkufnz668CdgnVC4X5KRvJoXCMgicr29Tjmr5vxGzvMdipwkTZmM",
        "mv1FB775BsnzapSCHxv6qf7W3PgA54G32vX1",
    ),
    (
        "sppk7aFpmJLm3ZxMd3F4osvGBq77R1NeSpiJVnof3Wiv4mt84EBE9aX",
        "mv2e9yeos5chx1A3iZzhb27Ww2dSmzFE85QB",
    ),
    (
        "p2pk66Y3178eHvgWFA4CDsgGPhbkWtwrYCVUKJnsAi41eGP7MbHKv24",
        "mv3NLHF7ap3556oFFayUB9L1H8iJGDYvcm24",
    ),
    (
        "BLpk1ur5XXicWYMMzCVZZWyLZhybtyX8Zot2uCzDCZW8KcC5BdZiLVXRZvZzi4GuZYL9SarUvKpE",
        "mv4exNvckxdb6QUqdaYycTabXyP4p2mNoios",
    ),
    (
        "BLpk1x47e4TtzgBSUEeoahw3BgoDghPhCFTNwUxVtGrqF58Y9vrj2SdCDamNRpj66e6wQKXzfBRk",
        "mv4Rgp1mAghRSJ46ksDjSRnmUMY7zZ8XdAD1",
    ),
)


class PermitSignerTests(unittest.TestCase):
    def test_public_keys_match_known_mavryk_addresses(self):
        for public_key, address in KEY_VECTORS:
            with self.subTest(scheme=public_key[:4], address=address):
                self.assertEqual(address_from_public_key(public_key), address)

    def test_permit_and_execute_uses_public_key_owner(self):
        for public_key, address in KEY_VECTORS:
            with self.subTest(scheme=public_key[:4], address=address):
                item = SimpleNamespace(userPublicKey=public_key)
                self.assertEqual(permit_signer(item), address)

    def test_execute_permit_uses_verified_signer(self):
        for _, address in KEY_VECTORS:
            with self.subTest(address=address):
                self.assertEqual(
                    permit_signer(SimpleNamespace(signer=address)), address
                )

    def test_bad_checksum_is_rejected_for_each_scheme(self):
        for public_key, _ in KEY_VECTORS:
            with self.subTest(scheme=public_key[:4]):
                corrupted = public_key[:-1] + ("1" if public_key[-1] != "1" else "2")
                with self.assertRaises(ValueError):
                    address_from_public_key(corrupted)

    def test_bls_key_with_wrong_binary_prefix_is_rejected(self):
        # A nearby binary prefix still produces the textual BLpk prefix, so
        # textual dispatch alone must not be accepted as a valid encoding.
        public_key = KEY_VECTORS[3][0]
        decoded = base58.b58decode_check(public_key)
        corrupted = base58.b58encode_check(
            decoded[:3] + bytes([205]) + decoded[4:]
        ).decode()
        self.assertTrue(corrupted.startswith("BLpk"))
        with self.assertRaisesRegex(ValueError, "Malformed public key"):
            address_from_public_key(corrupted)

    def test_wrong_key_length_with_valid_checksum_is_rejected(self):
        for public_key, _ in KEY_VECTORS:
            decoded = base58.b58decode_check(public_key)
            for payload in (decoded[:-1], decoded + b"\0"):
                with self.subTest(scheme=public_key[:4], length=len(payload)):
                    malformed = base58.b58encode_check(payload).decode()
                    with self.assertRaises(ValueError):
                        address_from_public_key(malformed)

    def test_unknown_key_prefix_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "Unsupported public key"):
            permit_signer(SimpleNamespace(userPublicKey="unknown-key"))
