import requests
import os
import platform
import time
from datetime import datetime, timedelta
import random
from Crypto.Cipher import AES  
import hashlib
import base64
import json
import smtplib  
from email.mime.text import MIMEText  
from email.header import Header  

class Encryptor:  
    """  
    模仿encrypt.js 和 decrypt.js  
    """  
    def __init__(self):  
        # 生成密钥
        key_str = "26a45a0edce6f0bc31d30028e9959e1b"  
        self.key = key_str.encode('utf-8')  

        # 初始化向量 (IV) 的生成
        iv_hex = hashlib.sha256(self.key).hexdigest()[:32]   # 对 key_str 本身进行 sha256 哈希，取前16字节(128位)作为IV  
        self.iv = bytes.fromhex(iv_hex)  

    def _pkcs7_pad(self, data):  
        """手动实现PKCS#7填充，模仿pad函数"""  
        block_size = AES.block_size  # 16 bytes  
        padding_len = block_size - (len(data) % block_size)  
        padding = bytes([padding_len] * padding_len)  
        return data + padding  

    def _pkcs7_unpad(self, data):  
        """手动实现PKCS#7去填充， 模仿unpad函数"""  
        padding_len = data[-1]  
        return data[:-padding_len]  

    def encrypt(self, plain_data: dict) -> str:  
        """  
        加密数据字典。  
        1. 将字典转为 JSON 字符串。  
        2. PKCS#7 填充。  
        3. AES-256-CBC 加密。  
        4. Base64 编码。  
        """  
        try:  
            plain_text = json.dumps(plain_data, separators=(',', ':')).encode('utf-8')

            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            
            padded_data = self._pkcs7_pad(plain_text)
            encrypted_bytes = cipher.encrypt(padded_data)
            
            first_pass_b64_bytes = base64.b64encode(encrypted_bytes)
            first_pass_b64_string = first_pass_b64_bytes.decode('utf-8')

            first_pass_b64_string_no_padding = first_pass_b64_string.rstrip('=')

            string_to_encode_as_bytes = first_pass_b64_string_no_padding.encode('utf-8')
            second_pass_b64_bytes = base64.b64encode(string_to_encode_as_bytes)
            
            final_encrypted_string = second_pass_b64_bytes.decode('utf-8')
            
            return final_encrypted_string
        except Exception as e:  
            print(f"加密失败: {e}")  
            return None  

    def decrypt(self, encrypted_final_str: str) -> dict:
        """
        解密一个与目标JS代码加密逻辑一致的字符串。
        """
        try:
            first_pass_decoded_bytes = base64.b64decode(encrypted_final_str)
            first_pass_decoded_string = first_pass_decoded_bytes.decode('utf-8')

            padding_needed = len(first_pass_decoded_string) % 4
            if padding_needed:
                padded_string = first_pass_decoded_string + '=' * (4 - padding_needed)
            else:
                padded_string = first_pass_decoded_string
            
            encrypted_original_bytes = base64.b64decode(padded_string)

            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            
            decrypted_padded_bytes = cipher.decrypt(encrypted_original_bytes)
            decrypted_bytes = self._pkcs7_unpad(decrypted_padded_bytes)
            
            decrypted_json = decrypted_bytes.decode('utf-8')
            return json.loads(decrypted_json)
        
        except (ValueError, TypeError, base64.binascii.Error) as e:
            print(f"解密失败：输入数据格式或填充不正确。错误: {e}")
            return None
        except Exception as e:
            print(f"解密过程中发生未知错误: {e}")
            return None

# 创建一个实例
encryptor = Encryptor()  

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')  # Windows
    else:
        os.system('clear')  # Linux/Mac

def login(username, password):  
    url = "https://xuanwu.nobeliumbiz.com/api/user/login"  
    # url = "https://xuanwu.nobeliumbiz.com/login"  
    headers = {  
        "Host": "xuanwu.nobeliumbiz.com",   
        "Accept": "application/json",  
        "Content-Type": "application/json", "X-Hospital": "xuanwu",  
        "Authorization": "Bearer", "Charset": "utf-8",  
        "Referer": "https://servicewechat.com/wxe0d6a3f51d535e25/21/page-frame.html",  
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/604.1 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d33) NetType/4G Language/zh",  
        "Accept-Encoding": "gzip, deflate, br"  
    }  

    # 准备要加密的数据  
    plain_data = { "num": username, "password": password }  
    # 使用加密器加密数据  
    encrypted_payload = encryptor.encrypt(plain_data) 
 
    print("===========================")
    print("1. 加密结果:", encrypted_payload)
    # 调试信息 - 字节长度
    print("3. 加密结果长度:", len(encrypted_payload), "字符")
    print("===========================")

    # 构建最终要发送的请求体  
    request_data = {"encryptedData": encrypted_payload}  

    try:  
        response = requests.post(url, headers=headers, json=request_data)  
        if response.status_code == 200:  
            # 服务器返回的数据也需要解密  
            server_encrypted_data = response.json().get("encryptedData")  
            decrypted_data = encryptor.decrypt(server_encrypted_data)  

            if decrypted_data and decrypted_data.get("code") == 0:  
                access_token = decrypted_data["data"]["access_token"]  
                year_id = decrypted_data["data"]["user"]["year_id"]  
                print(f"登录成功，信息已存储\ntoken: {access_token}\nyear_id: {year_id}")  
                with open("logininfo.txt", "w", encoding="utf-8") as f:  
                    f.write(f"{access_token}\n{year_id}\n{username}\n{password}")  
            else:  
                message = decrypted_data.get("message", "未知错误")  
                print(f"登录失败，错误信息：{message}")  
        else:  
            print(f"请求失败，状态码: {response.status_code}")  
    except requests.exceptions.RequestException as e:  
        print(f"Request failed: {e}")  

def get_attendence_info(lng, lat, location):  
    if not os.path.exists("logininfo.txt"):  
        print("请先登录获取token")  
        return None  

    with open("logininfo.txt", "r", encoding="utf-8") as f:  
        content = [line.strip() for line in f.readlines()]  
    
    if len(content) < 4:  
        print("logininfo.txt 文件不完整，请重新登录。")  
        return None  

    access_token, year_id, username, password = content  
    
    url = "https://xuanwu.nobeliumbiz.com/api/student/check_in/list"  
    plain_params = { "lng": str(lng), "lat": str(lat), "teaching_year_id": year_id }  
    encrypted_payload = encryptor.encrypt(plain_params)  
    
    # 加密后的数据作为 URL 查询参数  
    params = {"encryptedData": encrypted_payload}  

    headers = {  
        # "Host": "wx-api.nobeliumbiz.com", # 修正  
        "Accept": "application/json",   
        "Content-Type": "application/json",  
        "X-Hospital": "xuanwu", 
        "Authorization": "Bearer " + access_token,  
        "Charset": "utf-8", "Referer": "https://servicewechat.com/wxe0d6a3f51d535e25/21/page-frame.html",  
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/604.1 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d33) NetType/4G Language/zh",  
        "Accept-Encoding": "gzip, deflate, br"  
    }  

    try:  
        response = requests.get(url, headers=headers, params=params)  
        if response.status_code == 200:  
            server_encrypted_data = response.json().get("encryptedData")  
            decrypted_data = encryptor.decrypt(server_encrypted_data)  

            if decrypted_data and decrypted_data.get("code") == 0:  
                for item in decrypted_data.get("data", {}).get("list", []):  
                    if location in item.get("attendance_config_name", ""):  
                        print("当前属于：" + item["attendance_config_name"])  
                        return item["attendance_config_id"]  
                print("未找到包含'宣武'的签到项")  
                return None  
            
            message = decrypted_data.get("message", "")  
            print(f"获取签到信息失败: {message}")   
            if "请先登录" in message:  
                print("Token 已失效，尝试重新登录以更新 Token")  
                login(username, password)   
                print("再次尝试获取签到信息")  
                return get_attendence_info(lng, lat)   
            return None   
        else:  
            print(f"请求失败，状态码: {response.status_code}")  
            return None  
    except requests.exceptions.RequestException as e:  
        print(f"Request failed: {e}")  
        return None  

def check_in(lng, lat, attendance_id):  
    if not os.path.exists("logininfo.txt"):  
        print("请先登录获取token\n")  
        return  

    with open("logininfo.txt", "r", encoding="utf-8") as f:  
        content = f.readlines()  
    
    access_token = content[0].strip()  
    year_id = content[1].strip()  
    
    url = "https://xuanwu.nobeliumbiz.com/api/student/check_in"  
    headers = {  
        # "Host": "wx-api.nobeliumbiz.com", # 修正  
        "accept": "application/json",   
        "x-hospital": "xuanwu",  
        "authorization": "Bearer " + access_token,   
        "content-type": "application/json",  
        "charset": "utf-8",   
        "referer": "https://servicewechat.com/wxe0d6a3f51d535e25/21/page-frame.html",  
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/604.1 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.61(0x18003d33) NetType/4G Language/zh",  
        "accept-encoding": "gzip, deflate, br"  
    }  

    plain_data = {  
        "lng": str(lng), "lat": str(lat),  
        "attendance_config_id": attendance_id,  
        "teaching_year_id": year_id  
    }  
    encrypted_payload = encryptor.encrypt(plain_data)  
    request_data = {"encryptedData": encrypted_payload}  

    try:  
        response = requests.post(url, json=request_data, headers=headers)  
        if response.status_code == 200:  
            server_encrypted_data = response.json().get("encryptedData")  
            decrypted_data = encryptor.decrypt(server_encrypted_data)  

            if decrypted_data and decrypted_data.get("code") == 0:  
                print("打卡成功")  
            else:  
                message = decrypted_data.get("message", "未知错误")  
                print(f"打卡失败，错误信息：{message}")  
        else:  
            print(f"请求失败，状态码: {response.status_code}")  
    except requests.exceptions.RequestException as e:  
        print(f"Request failed: {e}")  

def run_background(lng, lat, location):
    """修改了之前有问题的默认签到时间，并且让签到时间在默认时间附近随机浮动，以免过于规整，而被发现"""

    schedule_file = "schedule.txt"
    if not os.path.exists(schedule_file):
        print("未找到schedule.txt，将生成默认时间表文件。请自行修改并重新运行定时程序\n格式为每行一个时间，使用24h制 (HH:MM)")
        with open(schedule_file, "w", encoding="utf-8") as f:
            f.write("07:45\n11:45\n13:15\n17:15\n17:45\n23:45")
        return

    with open(schedule_file, "r", encoding="utf-8") as f:
        target_times = [line.strip() for line in f if line.strip()]

    scheduled_jobs = {}
    today = datetime.now().date()

    def reschedule_jobs():
        nonlocal today
        today = datetime.now().date()
        scheduled_jobs.clear()
        with open("logininfo.txt", "r", encoding="utf-8") as f:  
            content = [line.strip() for line in f.readlines()]
            j, i, username, password = content 
            login(username, password)
        print(f"\n新的一天 ({today}), 重新登陆，重新生成随机签到时间...")
        for t_str in target_times:
            try:
                base_time = datetime.strptime(t_str, "%H:%M").time()
                base_datetime = datetime.combine(today, base_time)
                random_offset = random.uniform(-600, 600)  # 正负10min
                scheduled_time = base_datetime + timedelta(seconds=random_offset)
                scheduled_jobs[t_str] = {"time": scheduled_time, "executed": False}
                print(f"  - 原定时间 {t_str}, 今日随机签到时间: {scheduled_time.strftime('%H:%M:%S')}")
            except ValueError:
                print(f"警告: schedule.txt 中的 '{t_str}' 不是有效的 HH:MM 格式，已忽略。")

    reschedule_jobs()
    print("\n检测到schedule.txt，正在运行定时程序。请勿关闭窗口...")

    while True:
        if datetime.now().date() > today:
            reschedule_jobs()

        now = datetime.now()
        for t_str, job_info in scheduled_jobs.items():
            if not job_info["executed"] and now >= job_info["time"]:
                print(f"\n到达预定时间 {job_info['time'].strftime('%H:%M:%S')} (原定 {t_str})，开始执行签到...")
                attendance_id = get_attendence_info(lng, lat, location)
                if (attendance_id != 0):
                    check_in(lng, lat, attendance_id)
                else:
                    print("未能获取到包含宣武医院签到信息，签到流程中止。")
                job_info["executed"] = True
        
        time.sleep(30) # 每30秒检查一次

if (__name__ == "__main__"):
    basic_info = {"宣武": ["116.36239963107639", "39.891154513888885"],
                "儿童医院":["116.35457", "39.91253"]}

    location = input("请输入签到位置（1.宣武/2.儿童医院）：")
    if (location == "1"):
        location = "宣武"
    elif (location == "2"):
        location = "儿童医院"
    else:
        print("请输入正确数字！")
        exit()
    lng, lat = basic_info[location]

    while True: 
        operation = input("1.登录\n2.执行手动签到\n3.定时程序\n0.退出\n请输入数字选择操作并回车: ")  
        if (operation == "1"):  
            user = input("输入用户id：")  
            passwd = input("输入用户密码：")  
            login(user, passwd)  
        elif (operation == "2"):  
            print("开始执行手动签到流程...")   
            attendance_id = get_attendence_info(lng, lat, location)  
            if (attendance_id != 0):  
                check_in(lng, lat, attendance_id)
                pass
            else:  
                print("未能获取到包含宣武医院签到信息，签到流程中止。") 
        elif (operation == "3"): 
            try: 
                run_background(lng, lat, location)  
            except Exception as e:
                # 捕获签到过程中可能出现的其他异常  
                error_msg = f"签到过程中发生未知错误: {e}"  
                print(error_msg)  
        elif (operation == "0"):  
            break  
        else:
            print("请输入正确数字！")
        
        input("回车以继续...")
        clear_screen()