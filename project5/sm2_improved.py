#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import random
import time

class SM2Improved:
    def __init__(self):
        self.p = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
        self.a = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
        self.b = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
        self.n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
        self.Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
        self.Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
        self.G = (self.Gx, self.Gy)
        
        self.point_cache = {}
        self.scalar_cache = {}

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
        cache_key = (k, P)
        if cache_key in self.scalar_cache:
            return self.scalar_cache[cache_key]

        result = None
        addend = P
        while k:
            if k & 1:
                result = self.add_points(result, addend)
            addend = self.add_points(addend, addend)
            k >>= 1

        self.scalar_cache[cache_key] = result
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

    def batch_encrypt(self, messages, public_key):
        results = []
        for msg in messages:
            result = self.encrypt(msg, public_key)
            results.append(result)
        return results

    def batch_decrypt(self, ciphertexts, private_key):
        results = []
        for C1, C2, C3 in ciphertexts:
            result = self.decrypt(C1, C2, C3, private_key)
            results.append(result)
        return results

    def clear_cache(self):
        self.point_cache.clear()
        self.scalar_cache.clear()


def main():
    print("=== SM2改进版本测试 ===")
    sm2 = SM2Improved()

    print("\n1. 生成密钥对...")
    private_key, public_key = sm2.generate_keypair()
    print(f"私钥: {hex(private_key)}")
    print(f"公钥: ({hex(public_key[0])}, {hex(public_key[1])})")

    print("\n2. 测试加密解密...")
    message = "Hello, SM2! 你好，SM2！".encode('utf-8')
    print(f"原始消息: {message.decode('utf-8')}")

    start_time = time.time()
    C1, C2, C3 = sm2.encrypt(message, public_key)
    encrypt_time = time.time() - start_time
    print(f"加密耗时: {encrypt_time:.6f}秒")

    start_time = time.time()
    decrypted = sm2.decrypt(C1, C2, C3, private_key)
    decrypt_time = time.time() - start_time
    print(f"解密耗时: {decrypt_time:.6f}秒")

    if decrypted:
        print(f"解密结果: {decrypted.decode('utf-8')}")
        print("✓ 加密解密测试成功")
    else:
        print("✗ 加密解密测试失败")

    print("\n3. 测试批量操作...")
    messages = [f"消息{i}".encode('utf-8') for i in range(3)]
    print(f"批量加密 {len(messages)} 条消息...")
    
    start_time = time.time()
    ciphertexts = sm2.batch_encrypt(messages, public_key)
    batch_encrypt_time = time.time() - start_time
    print(f"批量加密耗时: {batch_encrypt_time:.6f}秒")

    start_time = time.time()
    decrypted_messages = sm2.batch_decrypt(ciphertexts, private_key)
    batch_decrypt_time = time.time() - start_time
    print(f"批量解密耗时: {batch_decrypt_time:.6f}秒")

    print("批量解密结果:")
    for i, msg in enumerate(decrypted_messages):
        if msg:
            print(f"  消息{i}: {msg.decode('utf-8')}")

    print(f"\n缓存统计:")
    print(f"  标量乘法缓存: {len(sm2.scalar_cache)} 项")
    print(f"  点加法缓存: {len(sm2.point_cache)} 项")


if __name__ == "__main__":
    main()
