import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.pyplot as plt
import os

class SimpleWatermark:
    """简单的水印嵌入和提取系统"""
    
    def __init__(self, watermark_size=32):
        self.watermark_size = watermark_size
    
    def embed_watermark(self, image_path, watermark, output_path=None):
        """嵌入水印到图像中"""
        # 加载图像
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # 确保水印长度正确
        if len(watermark) != self.watermark_size:
            raise ValueError(f"水印长度必须为{self.watermark_size}")
        
        # 将水印转换为二进制序列
        watermark_binary = np.array([int(bit) for bit in watermark])
        
        # 在图像的最低有效位中嵌入水印
        # 使用图像的蓝色通道
        blue_channel = img_array[:, :, 2].copy()
        
        # 将水印嵌入到蓝色通道的最低有效位
        for i, bit in enumerate(watermark_binary):
            if i < blue_channel.size:
                # 清除最低位并设置水印位
                blue_channel.flat[i] = (blue_channel.flat[i] & 0xFE) | bit
        
        # 更新图像数组
        img_array[:, :, 2] = blue_channel
        
        # 创建新图像
        watermarked_img = Image.fromarray(img_array)
        
        # 保存结果
        if output_path is None:
            output_path = 'watermarked_' + os.path.basename(image_path)
        
        watermarked_img.save(output_path)
        print(f"水印已嵌入，保存为: {output_path}")
        
        return watermarked_img
    
    def extract_watermark(self, image_path):
        """从图像中提取水印"""
        # 加载图像
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # 从蓝色通道提取水印
        blue_channel = img_array[:, :, 2]
        
        # 提取最低有效位
        extracted_watermark = []
        for i in range(self.watermark_size):
            if i < blue_channel.size:
                bit = blue_channel.flat[i] & 0x01
                extracted_watermark.append(bit)
            else:
                extracted_watermark.append(0)
        
        return np.array(extracted_watermark)
    
    def generate_random_watermark(self):
        """生成随机水印"""
        return np.random.randint(0, 2, self.watermark_size)
    
    def calculate_accuracy(self, original_watermark, extracted_watermark):
        """计算水印提取准确率"""
        if len(original_watermark) != len(extracted_watermark):
            return 0.0
        
        correct_bits = np.sum(original_watermark == extracted_watermark)
        return correct_bits / len(original_watermark)

def create_test_image():
    """创建测试图像"""
    # 创建一个简单的测试图像
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    test_img = Image.fromarray(img_array)
    test_img.save('test_image.png')
    print("测试图像已创建: test_image.png")
    return 'test_image.png'

def apply_attacks(image_path, attack_type):
    """应用各种攻击"""
    img = Image.open(image_path)
    
    if attack_type == 'flip':
        # 水平翻转
        attacked_img = img.transpose(Image.FLIP_LEFT_RIGHT)
        output_path = 'attacked_flip.png'
    elif attack_type == 'rotate':
        # 旋转
        attacked_img = img.rotate(15)
        output_path = 'attacked_rotate.png'
    elif attack_type == 'crop':
        # 截取
        width, height = img.size
        left = width // 4
        top = height // 4
        right = 3 * width // 4
        bottom = 3 * height // 4
        attacked_img = img.crop((left, top, right, bottom))
        output_path = 'attacked_crop.png'
    elif attack_type == 'contrast':
        # 调整对比度
        enhancer = ImageEnhance.Contrast(img)
        attacked_img = enhancer.enhance(2.0)
        output_path = 'attacked_contrast.png'
    elif attack_type == 'noise':
        # 添加噪声
        img_array = np.array(img)
        noise = np.random.randint(0, 50, img_array.shape, dtype=np.uint8)
        attacked_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        attacked_img = Image.fromarray(attacked_array)
        output_path = 'attacked_noise.png'
    elif attack_type == 'blur':
        # 模糊处理
        attacked_img = img.filter(ImageFilter.BLUR)
        output_path = 'attacked_blur.png'
    else:
        raise ValueError(f"未知的攻击类型: {attack_type}")
    
    attacked_img.save(output_path)
    print(f"{attack_type}攻击已应用，保存为: {output_path}")
    return output_path

def run_watermark_test():
    """运行水印测试"""
    print("=" * 50)
    print("简单水印嵌入与提取系统")
    print("=" * 50)
    
    # 创建水印系统
    watermark_system = SimpleWatermark(watermark_size=32)
    
    # 创建测试图像
    test_image_path = create_test_image()
    
    # 生成随机水印
    original_watermark = watermark_system.generate_random_watermark()
    print(f"原始水印: {original_watermark}")
    
    # 嵌入水印
    print("\n1. 嵌入水印...")
    watermarked_image = watermark_system.embed_watermark(test_image_path, original_watermark)
    
    # 提取水印
    print("\n2. 提取水印...")
    extracted_watermark = watermark_system.extract_watermark('watermarked_test_image.png')
    print(f"提取的水印: {extracted_watermark}")
    
    # 计算准确率
    accuracy = watermark_system.calculate_accuracy(original_watermark, extracted_watermark)
    print(f"水印提取准确率: {accuracy:.2%}")
    
    # 鲁棒性测试
    print("\n3. 鲁棒性测试...")
    attack_types = ['flip', 'rotate', 'crop', 'contrast', 'noise', 'blur']
    results = {}
    
    for attack_type in attack_types:
        try:
            print(f"\n测试 {attack_type} 攻击...")
            # 应用攻击
            attacked_image_path = apply_attacks('watermarked_test_image.png', attack_type)
            
            # 从攻击后的图像提取水印
            extracted_after_attack = watermark_system.extract_watermark(attacked_image_path)
            
            # 计算准确率
            attack_accuracy = watermark_system.calculate_accuracy(original_watermark, extracted_after_attack)
            results[attack_type] = attack_accuracy
            
            print(f"{attack_type}攻击后水印提取准确率: {attack_accuracy:.2%}")
            
        except Exception as e:
            print(f"{attack_type}攻击测试失败: {e}")
            results[attack_type] = 0.0
    
    # 绘制结果
    plot_results(results)
    
    return results

def plot_results(results):
    """绘制测试结果"""
    attack_names = list(results.keys())
    accuracies = list(results.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(attack_names, accuracies, color='skyblue', alpha=0.7)
    
    # 添加数值标签
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{acc:.2%}', ha='center', va='bottom')
    
    plt.title('水印鲁棒性测试结果')
    plt.xlabel('攻击类型')
    plt.ylabel('水印提取准确率')
    plt.ylim(0, 1)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('robustness_results.png', dpi=150, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    try:
        results = run_watermark_test()
        print("\n" + "=" * 50)
        print("实验完成!")
        print("生成的文件:")
        print("- test_image.png: 测试图像")
        print("- watermarked_test_image.png: 嵌入水印后的图像")
        print("- attacked_*.png: 各种攻击后的图像")
        print("- robustness_results.png: 鲁棒性测试结果图")
        print("\n鲁棒性测试结果汇总:")
        for attack_type, accuracy in results.items():
            print(f"{attack_type}: {accuracy:.2%}")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc() 