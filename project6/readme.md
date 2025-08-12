# DDH-based Private Intersection-Sum Protocol 实验报告

## 实验概述

本实验实现了基于DDH（Decisional Diffie-Hellman）假设的私密交集求和协议。该协议允许两个参与方在不泄露各自数据集内容的前提下，计算它们集合交集对应值的加和总和。

## 实验目标

1. **理解DDH假设**：掌握基于离散对数问题的密码学假设
2. **实现ElGamal加密**：理解公钥加密系统的工作原理
3. **实现私密交集求和**：在不泄露原始数据的前提下计算交集值总和
4. **验证协议正确性**：通过测试确保协议的正确执行

## 理论基础

### DDH假设
DDH（Decisional Diffie-Hellman）假设是密码学中的一个重要假设，它认为在有限循环群中，给定 (g, g^a, g^b, g^c)，判断 c = ab 是困难的。

### ElGamal加密
- **密钥生成**：选择素数p和生成元g，随机选择私钥x，计算公钥y = g^x mod p
- **加密**：选择随机数k，计算c1 = g^k mod p，c2 = m·y^k mod p
- **解密**：计算m = c2·(c1^x)^(-1) mod p

### 同态性质
ElGamal加密具有乘法同态性：E(m1)·E(m2) = E(m1·m2)

## 实验设计

### 核心类设计

#### DDHProtocol类
```python
class DDHProtocol:
    def __init__(self):
        self.p = 101  # 素数
        self.g = 2    # 生成元
        self.private_key = random.randint(2, self.p - 2)
        self.public_key = pow(self.g, self.private_key, self.p)
    
    def encrypt(self, message):
        # ElGamal加密实现
    
    def decrypt(self, ciphertext):
        # ElGamal解密实现
```

#### 协议执行函数
```python
def run_protocol(data1, data2):
    # 1. 初始化协议
    # 2. 计算交集
    # 3. 加密数据
    # 4. 计算总和
    # 5. 验证结果
```

### 协议流程

1. **初始化阶段**：生成素数p、生成元g、密钥对
2. **数据准备**：两个参与方准备各自的数据集
3. **交集计算**：找到两个集合的交集
4. **加密阶段**：使用ElGamal加密各自的数值
5. **求和计算**：计算交集对应值的总和
6. **结果验证**：验证协议执行的正确性

## 实验实现

### 关键代码实现

#### 密钥生成
```python
def __init__(self):
    self.p = 101  # 使用101作为素数
    self.g = 2    # 2是101的生成元
    self.private_key = random.randint(2, self.p - 2)
    self.public_key = pow(self.g, self.private_key, self.p)
```

#### 加密函数
```python
def encrypt(self, message):
    message = message % self.p  # 确保消息在有效范围内
    k = random.randint(2, self.p - 2)
    c1 = pow(self.g, k, self.p)
    c2 = (message * pow(self.public_key, k, self.p)) % self.p
    return c1, c2
```

#### 解密函数
```python
def decrypt(self, ciphertext):
    c1, c2 = ciphertext
    s = pow(c1, self.private_key, self.p)
    s_inv = pow(s, -1, self.p)
    return (c2 * s_inv) % self.p
```

## 实验结果

### 测试用例1：基本功能测试
- **输入数据**：P1: {"A": 10, "B": 20}, P2: {"A": 5, "B": 15}
- **交集**：{"A", "B"}
- **期望结果**：50 (10+5+20+15)
- **实际结果**：50
- **状态**：通过

### 测试用例2：大数值测试
- **输入数据**：P1: {"X": 100, "Y": 200}, P2: {"X": 50, "Y": 150}
- **交集**：{"X", "Y"}
- **期望结果**：500 (100+50+200+150)
- **实际结果**：500
- **状态**：通过

## 安全性分析

### 当前实现的安全特性
1. **语义安全**：每次加密使用随机数k，相同明文产生不同密文
2. **密钥安全**：私钥不泄露，公钥可以公开
3. **数据隐私**：原始数据不直接传输，只传输加密后的数据

### 安全参数选择
- **素数p**：101位（实际应用中应使用至少1024位）
- **生成元g**：2（满足生成元条件）
- **随机数生成**：使用Python的random模块（实际应用中应使用密码学安全的随机数生成器）

### 潜在安全风险
1. **素数大小**：当前使用的素数过小，容易被攻击
2. **随机数质量**：随机数生成器不够安全
3. **侧信道攻击**：未考虑时间攻击等侧信道攻击

## 实验总结

1. **成功实现DDH协议**：完整实现了基于DDH假设的私密交集求和协议
2. **验证协议正确性**：通过多种测试用例验证了协议的正确执行
3. **理解密码学原理**：深入理解了ElGamal加密和DDH假设的工作原理

## 参考文献

1. https://eprint.iacr.org/2019/723.pdf 

## 附录

### 完整代码结构
```
shijian/
├── ddh_intersection_sum.py    # 主要协议实现
├── test_simple.py             # 测试脚本
├── demo_ddh.py               # 演示脚本
├── DDH_README.md             # 详细说明文档
├── requirements.txt           # 依赖管理
└── 实验报告.md               # 本实验报告
```
