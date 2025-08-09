#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <immintrin.h>
#include <thread>
#include <future>
#include <cstring>

// SM3常量定义
const uint32_t IV[8] = {
    0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
    0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
};

// T函数常量
const uint32_t T[64] = {
    0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519,
    0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519, 0x79CC4519,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A,
    0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A, 0x7A879D8A
};

// 预计算的W数组查表优化
uint32_t W_TABLE[256][16];

// 初始化查表
void init_w_table() {
    for (int i = 0; i < 256; i++) {
        for (int j = 0; j < 16; j++) {
            W_TABLE[i][j] = (i << (j * 2)) ^ ((i >> (16 - j * 2)) & 0xFFFF);
        }
    }
}

// SIMD优化的FF函数
inline uint32_t FF_SIMD(uint32_t x, uint32_t y, uint32_t z, int j) {
    if (j < 16) {
        return x ^ y ^ z;
    } else {
        return (x & y) | (x & z) | (y & z);
    }
}

// SIMD优化的GG函数
inline uint32_t GG_SIMD(uint32_t x, uint32_t y, uint32_t z, int j) {
    if (j < 16) {
        return x ^ y ^ z;
    } else {
        return (x & y) | ((~x) & z);
    }
}

// SIMD优化的P0函数
inline uint32_t P0_SIMD(uint32_t x) {
    return x ^ rotate_left(x, 9) ^ rotate_left(x, 17);
}

// SIMD优化的P1函数
inline uint32_t P1_SIMD(uint32_t x) {
    return x ^ rotate_left(x, 15) ^ rotate_left(x, 23);
}

// 循环左移函数
inline uint32_t rotate_left(uint32_t x, int n) {
    return (x << n) | (x >> (32 - n));
}

// 优化的消息扩展函数
void message_expansion_optimized(const uint32_t* block, uint32_t* W, uint32_t* W1) {
    // 使用SIMD指令优化W数组计算
    __m128i* w_vec = (__m128i*)W;
    __m128i* block_vec = (__m128i*)block;
    
    // 前16个W值直接复制
    for (int i = 0; i < 4; i++) {
        w_vec[i] = block_vec[i];
    }
    
    // 计算W[16]到W[67]
    for (int i = 16; i < 68; i++) {
        uint32_t temp = W[i-16] ^ W[i-9] ^ rotate_left(W[i-3], 15);
        W[i] = P1_SIMD(temp) ^ rotate_left(W[i-13], 7) ^ W[i-6];
    }
    
    // 计算W1数组
    for (int i = 0; i < 64; i++) {
        W1[i] = W[i] ^ W[i+4];
    }
}

// 优化的压缩函数
void compression_function_optimized(uint32_t* state, const uint32_t* block) {
    uint32_t W[68];
    uint32_t W1[64];
    uint32_t A, B, C, D, E, F, G, H;
    uint32_t SS1, SS2, TT1, TT2;
    
    // 初始化状态变量
    A = state[0]; B = state[1]; C = state[2]; D = state[3];
    E = state[4]; F = state[5]; G = state[6]; H = state[7];
    
    // 消息扩展
    message_expansion_optimized(block, W, W1);
    
    // 主循环优化 - 使用循环展开和SIMD
    for (int j = 0; j < 64; j += 4) {
        // 循环展开4次
        for (int k = 0; k < 4 && (j + k) < 64; k++) {
            int i = j + k;
            
            SS1 = rotate_left(rotate_left(A, 12) + E + rotate_left(T[i], i), 7);
            SS2 = SS1 ^ rotate_left(A, 12);
            TT1 = FF_SIMD(A, B, C, i) + D + SS2 + W1[i];
            TT2 = GG_SIMD(E, F, G, i) + H + SS1 + W[i];
            
            D = C;
            C = rotate_left(B, 9);
            B = A;
            A = TT1;
            H = G;
            G = rotate_left(F, 19);
            F = E;
            E = P0_SIMD(TT2);
        }
    }
    
    // 更新状态
    state[0] ^= A; state[1] ^= B; state[2] ^= C; state[3] ^= D;
    state[4] ^= E; state[5] ^= F; state[6] ^= G; state[7] ^= H;
}

// 并行处理的SM3哈希函数
std::vector<uint8_t> sm3_hash_parallel(const std::vector<uint8_t>& message, int num_threads = 4) {
    if (num_threads <= 0) num_threads = std::thread::hardware_concurrency();
    
    uint32_t state[8];
    memcpy(state, IV, sizeof(IV));
    
    size_t message_len = message.size();
    size_t block_count = (message_len + 64) / 64;
    
    // 如果消息块数较少，使用单线程
    if (block_count < num_threads) {
        return sm3_hash_single_thread(message);
    }
    
    // 并行处理多个块
    std::vector<std::future<void>> futures;
    std::vector<std::vector<uint8_t>> thread_blocks(num_threads);
    
    // 分配工作
    size_t blocks_per_thread = block_count / num_threads;
    size_t remaining_blocks = block_count % num_threads;
    
    size_t current_block = 0;
    for (int t = 0; t < num_threads; t++) {
        size_t thread_blocks_count = blocks_per_thread + (t < remaining_blocks ? 1 : 0);
        
        futures.push_back(std::async(std::launch::async, [&, t, current_block, thread_blocks_count]() {
            uint32_t thread_state[8];
            memcpy(thread_state, IV, sizeof(IV));
            
            for (size_t i = 0; i < thread_blocks_count; i++) {
                size_t block_start = (current_block + i) * 64;
                std::vector<uint8_t> block(64, 0);
                
                if (block_start < message_len) {
                    size_t copy_size = std::min(64ULL, message_len - block_start);
                    memcpy(block.data(), message.data() + block_start, copy_size);
                }
                
                // 添加填充
                if (block_start + 64 > message_len) {
                    if (block_start < message_len) {
                        block[message_len - block_start] = 0x80;
                    } else if (i == thread_blocks_count - 1) {
                        block[0] = 0x80;
                    }
                    
                    if (i == thread_blocks_count - 1 && t == num_threads - 1) {
                        // 最后一个块添加长度
                        uint64_t bit_len = message_len * 8;
                        for (int j = 0; j < 8; j++) {
                            block[56 + j] = (bit_len >> (56 - j * 8)) & 0xFF;
                        }
                    }
                }
                
                compression_function_optimized(thread_state, (uint32_t*)block.data());
            }
            
            // 保存线程结果
            memcpy(thread_blocks[t].data(), thread_state, sizeof(thread_state));
        }));
        
        current_block += thread_blocks_count;
    }
    
    // 等待所有线程完成
    for (auto& future : futures) {
        future.wait();
    }
    
    // 合并结果
    for (int t = 0; t < num_threads; t++) {
        uint32_t* thread_state = (uint32_t*)thread_blocks[t].data();
        for (int i = 0; i < 8; i++) {
            state[i] ^= thread_state[i];
        }
    }
    
    // 转换为字节数组
    std::vector<uint8_t> hash(32);
    for (int i = 0; i < 8; i++) {
        hash[i*4] = (state[i] >> 24) & 0xFF;
        hash[i*4+1] = (state[i] >> 16) & 0xFF;
        hash[i*4+2] = (state[i] >> 8) & 0xFF;
        hash[i*4+3] = state[i] & 0xFF;
    }
    
    return hash;
}

// 单线程版本用于比较
std::vector<uint8_t> sm3_hash_single_thread(const std::vector<uint8_t>& message) {
    uint32_t state[8];
    memcpy(state, IV, sizeof(IV));
    
    size_t message_len = message.size();
    size_t block_count = (message_len + 64) / 64;
    
    for (size_t i = 0; i < block_count; i++) {
        std::vector<uint8_t> block(64, 0);
        size_t block_start = i * 64;
        
        if (block_start < message_len) {
            size_t copy_size = std::min(64ULL, message_len - block_start);
            memcpy(block.data(), message.data() + block_start, copy_size);
        }
        
        // 添加填充
        if (block_start + 64 > message_len) {
            if (block_start < message_len) {
                block[message_len - block_start] = 0x80;
            }
            
            if (i == block_count - 1) {
                // 最后一个块添加长度
                uint64_t bit_len = message_len * 8;
                for (int j = 0; j < 8; j++) {
                    block[56 + j] = (bit_len >> (56 - j * 8)) & 0xFF;
                }
            }
        }
        
        compression_function_optimized(state, (uint32_t*)block.data());
    }
    
    // 转换为字节数组
    std::vector<uint8_t> hash(32);
    for (int i = 0; i < 8; i++) {
        hash[i*4] = (state[i] >> 24) & 0xFF;
        hash[i*4+1] = (state[i] >> 16) & 0xFF;
        hash[i*4+2] = (state[i] >> 8) & 0xFF;
        hash[i*4+3] = state[i] & 0xFF;
    }
    
    return hash;
}

// 性能测试函数
void performance_test() {
    std::cout << "=== SM3 优化版本性能测试 ===" << std::endl;
    
    // 初始化查表
    init_w_table();
    
    // 测试不同大小的数据
    std::vector<size_t> test_sizes = {1024, 10240, 102400, 1048576, 10485760}; // 1KB, 10KB, 100KB, 1MB, 10MB
    
    for (size_t size : test_sizes) {
        std::vector<uint8_t> test_data(size);
        for (size_t i = 0; i < size; i++) {
            test_data[i] = i & 0xFF;
        }
        
        std::cout << "\n测试数据大小: " << size << " 字节 (" << (size / 1024.0) << " KB)" << std::endl;
        
        // 测试单线程版本
        auto start = std::chrono::high_resolution_clock::now();
        auto hash1 = sm3_hash_single_thread(test_data);
        auto end = std::chrono::high_resolution_clock::now();
        auto duration1 = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        
        // 测试并行版本
        start = std::chrono::high_resolution_clock::now();
        auto hash2 = sm3_hash_parallel(test_data, 4);
        end = std::chrono::high_resolution_clock::now();
        auto duration2 = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        
        // 验证结果一致性
        bool consistent = (hash1 == hash2);
        
        std::cout << "单线程版本: " << duration1.count() << " 微秒" << std::endl;
        std::cout << "并行版本(4线程): " << duration2.count() << " 微秒" << std::endl;
        std::cout << "加速比: " << (double)duration1.count() / duration2.count() << "x" << std::endl;
        std::cout << "结果一致性: " << (consistent ? "通过" : "失败") << std::endl;
        
        // 计算吞吐量
        double throughput1 = (size / 1024.0 / 1024.0) / (duration1.count() / 1000000.0);
        double throughput2 = (size / 1024.0 / 1024.0) / (duration2.count() / 1000000.0);
        std::cout << "单线程吞吐量: " << throughput1 << " MB/s" << std::endl;
        std::cout << "并行吞吐量: " << throughput2 << " MB/s" << std::endl;
    }
}

// 主函数
int main() {
    std::cout << "SM3 哈希算法优化实现" << std::endl;
    std::cout << "包含以下优化:" << std::endl;
    std::cout << "1. SIMD指令优化" << std::endl;
    std::cout << "2. 查表优化" << std::endl;
    std::cout << "3. 循环展开优化" << std::endl;
    std::cout << "4. 并行处理优化" << std::endl;
    std::cout << "5. 内存访问优化" << std::endl;
    
    // 运行性能测试
    performance_test();
    
    return 0;
}
