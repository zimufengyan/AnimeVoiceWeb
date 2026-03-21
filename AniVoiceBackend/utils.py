import random
import os
import re
import logging
import trace
import requests
import sys
import httpx

rates = {'S': 0.02, 'A': 0.08, 'B': 0.4, 'C': 0.4, 'D': 0.1}  


class ColorFilter(logging.Filter):
    """清除ANSI颜色代码的过滤器"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def filter(self, record):
        if record.msg:
            record.msg = self.ansi_escape.sub('', str(record.msg))
        if record.args:
            record.args = tuple(
                self.ansi_escape.sub('', str(arg))
                if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def configure_root_logger(
        level=logging.INFO,
        file_path=None,
        max_size=10,  # 0表示不轮转
        backup_count=0
):
    """
    配置根日志记录器，支持同时输出到控制台和文件

    :param level: 日志级别，默认INFO
    :param file_path: 日志文件路径（可选），默认不输出到文件
    :param max_size: 日志文件最大大小，单位MB
    :param backup_count:
    """

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(message)s'
    )

    # 创建处理器列表
    handlers = []

    # 控制台处理器（始终启用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # 文件处理器（可选）
    if file_path:
        # 自动创建日志目录
        log_dir = os.path.dirname(file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        if max_size > 0 and backup_count > 0:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                filename=file_path,
                maxBytes=max_size * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ColorFilter())  # 添加颜色过滤器
        handlers.append(file_handler)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清理旧处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加新处理器
    for handler in handlers:
        root_logger.addHandler(handler)



def execute_request(
        url: str, param: dict = None, method="GET"
):
    """
    requests 请求处理函数
    """
    response = None
    try:
        if method == 'GET':
            response = requests.get(
                url,
                params=param
            )
        else:
            response = requests.post(
                url, 
                json=param
            )
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP Error: {http_err}")
        return False, response
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request Error: {req_err}")
        return False, response
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return False, response
    else:
        logging.info(f"Successfully sent to {url}!")
        return True, response
    

async def async_execute_request(
        url: str, param: dict = None, method="GET"
):
    """
    异步 HTTP 请求处理函数
    """
    response = None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            if method == 'GET':
                response = await client.get(
                    url,
                    params=param
                )
            else:
                response = await client.post(
                    url,
                    json=param
                )
            response.raise_for_status()
    except httpx.HTTPStatusError as http_err:
        logging.error(f"HTTP Error: {http_err}")
        return False, response
    except httpx.RequestError as req_err:
        logging.error(f"Request Error: {req_err}")
        return False, response
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return False, response
    else:
        logging.info(f"Successfully sent to {url}!")
        return True, response


def generate_rate():
    keys = list(rates.keys())  
    weights = list(rates.values()) 
    selected_rate = random.choices(keys, weights=weights)[0] 
    return selected_rate

def get_random_image(directory):
    # 从dir中所有图片中随机抽取一张图片返回该图片的绝对路径
     # 获取指定目录下所有文件  
    all_files = os.listdir(directory)  
    
    # 筛选出图片文件，假设支持的格式为 .jpg, .jpeg, .png, .svg  
    image_extensions = ('.jpg', '.jpeg', '.png', 'svg')  
    image_files = [f for f in all_files if f.lower().endswith(image_extensions)]  
    
    if not image_files:  
        return None  
    
    selected_image = random.choice(image_files)  
    return os.path.abspath(os.path.join(directory, selected_image))


def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None
