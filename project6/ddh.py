#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDH-based Private Intersection-Sum Protocol 简化实现
基于DDH假设的私密交集求和协议
"""

import random
import math

class DDHProtocol:
    """简化的DDH协议实现"""
    
    def __init__(self):
        # 使用更大的素数用于演示
        self.p = 101  # 更大的素数
        self.g = 2  # 生成元
        self.private_key = random.randint(2, self.p - 2)
        self.public_key = pow(self.g, self.private_key, self.p)
        
        print(f"协议初始化: p={self.p}, g={self.g}")
        print(f"公钥: {self.public_key}, 私钥: {self.private_key}")
    
    def encrypt(self, message):
        """ElGamal加密"""
        # 确保消息在有效范围内
        message = message % self.p
        k = random.randint(2, self.p - 2)
        c1 = pow(self.g, k, self.p)
        c2 = (message * pow(self.public_key, k, self.p)) % self.p
        return c1, c2
    
    def decrypt(self, ciphertext):
        """ElGamal解密"""
        c1, c2 = ciphertext
        s = pow(c1, self.private_key, self.p)
        s_inv = pow(s, -1, self.p)
        return (c2 * s_inv) % self.p


def run_protocol(data1, data2):
    """运行私密交集求和协议"""
    print("\n" + "="*50)
    print("开始运行DDH私密交集求和协议")
    print("="*50)
    
    # 初始化协议
    protocol = DDHProtocol()
    
    print(f"P1数据: {data1}")
    print(f"P2数据: {data2}")
    
    # 计算交集
    intersection = set(data1.keys()) & set(data2.keys())
    print(f"交集: {intersection}")
    
    if not intersection:
        print("没有交集")
        return
    
    # 计算交集值的总和
    total_sum = 0
    for item in intersection:
        total_sum += data1[item] + data2[item]
    
    print(f"交集值总和: {total_sum}")
    
    # 演示加密解密过程
    print(f"\n加密解密演示:")
    for item in intersection:
        value1 = data1[item]
        value2 = data2[item]
        
        # 加密
        encrypted1 = protocol.encrypt(value1)
        encrypted2 = protocol.encrypt(value2)
        
        # 解密
        decrypted1 = protocol.decrypt(encrypted1)
        decrypted2 = protocol.decrypt(encrypted2)
        
        print(f"项目 {item}:")
        print(f"  P1值: {value1} -> 加密: {encrypted1} -> 解密: {decrypted1}")
        print(f"  P2值: {value2} -> 加密: {encrypted2} -> 解密: {decrypted2}")
        print(f"  验证: {'正确' if decrypted1 == value1 % protocol.p and decrypted2 == value2 % protocol.p else '错误'}")
    
    print(f"\n协议执行完成，交集值总和: {total_sum}")
    return total_sum


def demo():
    """演示函数"""
    print("DDH私密交集求和协议演示")
    
    # 示例数据 - 使用较小的数值
    data1 = {"A": 10, "B": 20, "C": 30}
    data2 = {"A": 5, "B": 15, "D": 40}
    
    run_protocol(data1, data2)


if __name__ == "__main__":
    demo()
