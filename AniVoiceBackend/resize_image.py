import os
from PIL import Image, ImageOps

def process_image(input_path, output_folder, size):
    """
    读取图片，将宽度扩充到和高度一致，然后调整到指定尺寸，最后保存到输出文件夹。

    :param input_path: 输入图片的路径
    :param output_folder: 输出文件夹路径
    :param size: 指定输出图片的尺寸（宽度=高度）
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 打开图片
    try:
        img = Image.open(input_path).convert("RGBA")
    except Exception as e:
        print(f"无法打开图片 {input_path}: {e}")
        return

    # 获取原始图片尺寸
    width, height = img.size

    if height < width:
        print(f"图片高度 ({height}) 必须大于宽度 ({width})，跳过处理：{input_path}")
        return
    
    if height == width:
        img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
    else:
        # 计算需要扩充的宽度两侧的填充量
        padding = (height - width) // 2
        left_padding = padding
        right_padding = height - width - padding

        # 扩充宽度到和高度一致
        img_padded = ImageOps.expand(img, border=(left_padding, 0, right_padding, 0), fill=(255, 255, 255, 0))

        # 调整到指定尺寸
        img_resized = img_padded.resize((size, size), Image.Resampling.LANCZOS)

    # 构造输出路径并保存图片
    file_name = os.path.splitext(os.path.basename(input_path))[0] + '.png'
    output_path = os.path.join(output_folder, file_name)

    # 保存为支持透明度的格式（如 PNG）
    img_resized.save(output_path, format="PNG")
    print(f"图片处理完成: {output_path}")


def process_images_in_folder(input_folder, output_folder, size):
    """
    处理输入文件夹中的所有图片。

    :param input_folder: 输入文件夹路径
    :param output_folder: 输出文件夹路径
    :param size: 指定输出图片的尺寸（宽度=高度）
    """
    if not os.path.exists(input_folder):
        print(f"输入文件夹不存在: {input_folder}")
        return
    
    os.makedirs(output_folder, exist_ok=True)

    images_processed = 0

    for file_name in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file_name)

        # 跳过非图片文件
        if not os.path.isfile(input_path) or not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"跳过非图片文件: {file_name}")
            continue

        process_image(input_path, output_folder, size)
        images_processed += 1

    if images_processed == 0:
        print("输入文件夹中未找到可处理的图片。")
    else:
        print(f"已处理图片总数: {images_processed}")



# 示例调用
if __name__ == "__main__":
    import argparse

    # 命令行参数解析
    parser = argparse.ArgumentParser(description="Resize and pad images to a square size.")
    parser.add_argument("-i", '--input', type=str, help="输入文件夹")
    parser.add_argument("-s", '--size', type=int, help="目标尺寸（宽度=高度）")
    parser.add_argument("-o", '--output', type=str, help="输出文件夹路径")

    args = parser.parse_args()

    # 调用处理函数
    process_images_in_folder(args.input, args.output, args.size)
