#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import random

class SM2Basic:
    def __init__(self):
        self.p = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
        self.a = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
        self.b = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
        self.n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
        self.Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
        self.Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
        self.G = (self.Gx, self.Gy)

    def add_points(self, P1, P2):
        if P1 is None:
            return P2
        if P2 is None:
            return P1

        x1, y1 = P1
        x2, y2 = P2

        if x1 == x2 and y1 != y2:
            return None

        if P1 == P2:
            lam = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, self.p) % self.p
        else:
            lam = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p

        x3 = (lam * lam - x1 - x2) % self.p
        y3 = (lam * (x1 - x3) - y1) % self.p
        return (x3, y3)

    def scalar_multiply(self, k, P):
        result = None
        addend = P
        while k:
            if k & 1:
                result = self.add_points(result, addend)
            addend = self.add_points(addend, addend)
            k >>= 1
        return result

    def generate_keypair(self):
        private_key = random.randint(1, self.n - 1)
        public_key = self.scalar_multiply(private_key, self.G)
        return private_key, public_key

    def kdf(self, Z, klen):
        ct = 1
        k = b''
        while len(k) < klen:
            k = k + hashlib.sha256(Z + ct.to_bytes(4, 'big')).digest()
            ct += 1
        return k[:klen]

    def encrypt(self, message, public_key):
        klen = len(message)
        while True:
            k = random.randint(1, self.n - 1)
            C1 = self.scalar_multiply(k, self.G)
            kP = self.scalar_multiply(k, public_key)
            t = self.kdf(kP[0].to_bytes(32, 'big') + kP[1].to_bytes(32, 'big'), klen)
            if any(t):
                break

        C2 = bytes(a ^ b for a, b in zip(message, t))
        C3_input = kP[0].to_bytes(32, 'big') + message + kP[1].to_bytes(32, 'big')
        C3 = hashlib.sha256(C3_input).digest()
        return C1, C2, C3

    def decrypt(self, C1, C2, C3, private_key):
        dC1 = self.scalar_multiply(private_key, C1)
        t = self.kdf(dC1[0].to_bytes(32, 'big') + dC1[1].to_bytes(32, 'big'), len(C2))
        if not any(t):
            return None

        message = bytes(a ^ b for a, b in zip(C2, t))
        C3_input = dC1[0].to_bytes(32, 'big') + message + dC1[1].to_bytes(32, 'big')
        C3_check = hashlib.sha256(C3_input).digest()

        if C3 != C3_check:
            return None
        return message

    def sign(self, message, private_key, public_key):
        e = int.from_bytes(hashlib.sha256(message).digest(), 'big')
        while True:
            k = random.randint(1, self.n - 1)
            kG = self.scalar_multiply(k, self.G)
            x1 = kG[0]
            r = (e + x1) % self.n
            if r == 0 or r + k == self.n:
                continue
            s = pow(1 + private_key, -1, self.n) * (k - r * private_key) % self.n
            if s != 0:
                break
        return r, s

    def verify(self, message, signature, public_key):
        r, s = signature
        if not (1 <= r < self.n and 1 <= s < self.n):
            return False

        e = int.from_bytes(hashlib.sha256(message).digest(), 'big')
        t = (r + s) % self.n
        if t == 0:
            return False

        sG = self.scalar_multiply(s, self.G)
        tP = self.scalar_multiply(t, public_key)
        point = self.add_points(sG, tP)
        if point is None:
            return False

        return r == (e + point[0]) % self.n


def main():
    print("=== SM2测试 ===")
    sm2 = SM2Basic()

    print("\n1. 生成密钥对...")
    private_key, public_key = sm2.generate_keypair()
    print(f"私钥: {hex(private_key)}")
    print(f"公钥: ({hex(public_key[0])}, {hex(public_key[1])})")

    print("\n2. 测试加密解密...")
    message = "Hello, SM2! 你好，SM2！".encode('utf-8')
    print(f"原始消息: {message.decode('utf-8')}")

    C1, C2, C3 = sm2.encrypt(message, public_key)
    print(f"密文: C1=({hex(C1[0])}, {hex(C1[1])}), C2={C2.hex()}, C3={C3.hex()}")

    decrypted = sm2.decrypt(C1, C2, C3, private_key)
    if decrypted:
        print(f"解密结果: {decrypted.decode('utf-8')}")
        print("✓ 加密解密测试成功")
    else:
        print("✗ 加密解密测试失败")

    print("\n3. 测试签名验证...")
    signature = sm2.sign(message, private_key, public_key)
    print(f"签名: r={hex(signature[0])}, s={hex(signature[1])}")

    if sm2.verify(message, signature, public_key):
        print("✓ 签名验证测试成功")
    else:
        print("✗ 签名验证测试失败")

    wrong_message = "Wrong message".encode('utf-8')
    if not sm2.verify(wrong_message, signature, public_key):
        print("✓ 错误消息验证测试成功")
    else:
        print("✗ 错误消息验证测试失败")


if __name__ == "__main__":
    main()
