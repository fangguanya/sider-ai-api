"""An API library for sider.ai, providing alternative access to ChatGPT, Gemini, Claude, and other models. \
国内访问ChatGPT、Gemini、Claude的替代解决方案，访问sider.ai的API请求库。
For the documentation, see github.com/qfcy/sider-ai-api.
"""
import sys,os,json,traceback,gzip,bz2,zlib,shutil,time
import requests
from warnings import warn
try:import brotli # 处理brotli压缩格式
except ImportError:brotli=None

__version__="1.0.0"

DOMAIN="api2.sider.ai"
ORIGIN="chrome-extension://dhoenijjpgpeimemopealfcbiecgceod"

DEFAULT_TOKEN_FILE="_token.json"
COOKIE_TEMPLATE='token=Bearer%20{token}; '
'refresh_token=discard; '
'userinfo-avatar=https://chitchat-avatar.s3.amazonaws.com/default-avatar-14.png; '
'userinfo-name=User; userinfo-type=phone; '

HEADER={ # 从浏览器的开发工具复制获得
 'Accept': '*/*',
 'Accept-Encoding': 'gzip, deflate, br, zstd',
 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7,en-GB;q=0.6,ja;q=0.5',
 'Cache-Control': 'no-cache',
 'Origin': ORIGIN,
 'Pragma': 'no-cache',
 'Sec-Fetch-Dest': 'empty',
 'Sec-Fetch-Mode': 'cors',
 'Sec-Fetch-Site': 'none',
 'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
 'sec-ch-ua-mobile': '?0',
 'sec-ch-ua-platform': '"Windows"',
 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 '
               'Edg/130.0.0.0'
}

MODELS=["sider", # Sider Fusion
    "gpt-4o-mini",
    "claude-3-haiku",
    "claude-3.5-haiku",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "llama-3", # llama 3.1 70B
    "llama-3.3-70b",
    "deepseek-chat" # deepseek-v3
]
ADVANCED_MODELS=["gpt-4o",
"claude-3.5-sonnet",
"gemini-1.5-pro",
"llama-3.1-405b",
"o1-mini",
"o1", # o1
"deepseek-reasoner" # deepseek-r1
]
def normpath(path):
    # 重写os.path.normpath。规范化Windows路径，如去除两端的双引号等
    path=os.path.normpath(path).strip('"')
    if path.endswith(':'): # 如果路径是盘符，如 C:
        path += '\\'
    return path

def parse_cookie(cookie):
    cookie_dict = {}
    pairs = cookie.split(';')

    for pair in pairs:
        # 去除前后空格
        pair = pair.strip()
        if '=' in pair:
            # 按等号分割键和值
            key, value = pair.split('=', 1)  # 只分割一次
            cookie_dict[key.strip()] = value.strip()  # 去除空格并存入字典

    return cookie_dict
#def handle_verify(url, content, cookie):
#    # 备用函数，用于处理cloudflare的验证（暂时不用到）
#    from selenium import webdriver # 懒加载selenium库
#    from selenium.webdriver.edge.service import Service
#    service = Service(executable_path=shutil.which("msedgedriver"))
#    driver = webdriver.Edge(service=service)
#    driver.get(url)  # 访问一个需要的 URL
#    time.sleep(2)
#    for k,v in parse_cookie(cookie).items():
#        driver.add_cookie({"name":k,"value":v})
#    driver.execute_script("""document.open();
#document.write(arguments[0]); document.close();""", content)
#    cookie_str=cookie # 默认
#    try:
#        while driver.window_handles:
#            if "sider.ai" in driver.current_url and \
#                "404 page not found" in driver.page_source:
#                print("Getting cookies")
#                cookie_str=""
#                for cookie in driver.get_cookies():
#                    if not cookie["domain"]==DOMAIN:continue
#                    cookie_str+="%s:%s;"%(cookie["name"],cookie["value"])
#            if "sider.ai" in driver.current_url: # 如果用户登录了sider
#                print("Getting cookies from Sider")
#                new_cookie_str=""
#                for cookie in driver.get_cookies():
#                    if not cookie["domain"]==DOMAIN:continue
#                    new_cookie_str+="%s:%s;"%(cookie["name"],cookie["value"])
#            time.sleep(1)
#        driver.quit()
#        if "token=Bearer" in new_cookie_str:
#            cookie_str=new_cookie_str
#    except BaseException:
#        traceback.print_exc()
#    #print("New cookie:",cookie_str)
#    return cookie_str  # 退出循环

def upload_image(filename,header):
    url="https://api1.sider.ai/api/v1/imagechat/upload"
    header = header.copy()
    #header["content-type"] = "multipart/form-data"
    #header["accept-encoding"] = "gzip, deflate"
    with open(filename, 'rb') as img:
        files = {'file': ("ocr.jpg",img,'application/octet-stream')}  # file 应与API要求的字段名一致
        response = requests.post(url, headers=header, files=files)
        if response.status_code!=200:
            raise Exception({"error": response.status_code, "message": response.text[:1024]})
    coding=response.headers.get('Content-Encoding')
    if not response.content.startswith(b"{") and coding is not None:
        decompress=None
        if coding == 'deflate':
            decompress=zlib.decompress
        elif coding == 'gzip':decompress=gzip.decompress
        elif coding == 'bzip2':decompress=bz2.decompress
        elif brotli is not None and coding == 'br':
            decompress=brotli.decompress
        data=decompress(response.content)
    else:
        data=response.content
    return json.loads(data.decode("utf-8"))

class Session:
    def __init__(self,token=None,context_id="",cookie=None):
        if token is None:
            with open(DEFAULT_TOKEN_FILE,encoding="utf-8") as f:
                config=json.load(f)
                token=config["token"]
                cookie=config.get("cookie")
        self.context_id=context_id
        self.total=self.remain=None # 总/剩下调用次数
        self.header=HEADER.copy()
        self.header['authorization']=f'Bearer {token}'
        if cookie is None:cookie=COOKIE_TEMPLATE.format(token=token)
        self.header['Cookie']=cookie
    def get_text(self,url,header,payload):
        # 一个生成器，获取输出结果
        response = requests.post(url, headers=header, json=payload, stream=True)
        if response.status_code == 200:
            for line_raw in response.iter_lines():
                if not line_raw.strip():continue
                try:
                    # 解析每一行的数据
                    line = line_raw.decode("utf-8")
                    if not line.startswith("data:"):continue

                    response = line[5:]  # 去掉前缀 "data:"
                    if not response:continue # 确保数据非空
                    if response=="[DONE]":break
                    data = json.loads(response)
                    if data["msg"].strip():
                        yield "<Message: %s Code: %d>" % (data["msg"],data["code"])
                    if data["data"] is not None and "text" in data["data"]:
                        self.context_id=data["data"].get("cid","") or self.context_id # 对话上下文
                        self.total=data["data"].get("total",None) or self.total # or:在返回None时保留之前的self.total
                        self.remain=data["data"].get("remain",None) or self.remain
                        yield data["data"]["text"] # 输出消息
                except Exception as err:
                    warn(f"Error processing stream: {err} Raw: {line_raw}")
        else:
            raise Exception({"error": response.status_code, "message": response.text})
    def chat(self,prompt,model="gpt-4o-mini"):
        # 一个生成器，使用提示词调用AI，返回结果
        url = "https://api2.sider.ai/api/v2/completion/text"
        header = self.header.copy()
        header["content-type"] = 'application/json'
        payload = {
            "prompt": prompt,
            "stream": True,
            "app_name": "ChitChat_Edge_Ext",
            "app_version": "4.23.1",
            "tz_name": "Asia/Shanghai",
            "cid": self.context_id, # 对话上下文id，如果为空则开始新对话
            "model": model,
            "search": False,
            "auto_search": False,
            "filter_search_history": False,
            "from": "chat",
            "group_id": "default",
            "chat_models": [],
            "files": [],
            "prompt_template": {
                "key": "artifacts", # 在artifact的新窗口中显示结果
                "attributes": {"lang": "original"}
            },
            "tools": {"auto": ["data_analysis"]}, # 还可以加入"search"或者"text_to_image"
            "extra_info": {
                "origin_url": ORIGIN+"/standalone.html",
                "origin_title": "Sider"
            }
        }
        return self.get_text(url,header,payload)
    def ocr(self,filename,model="gemini-2.0-flash"):
        # 一个生成器，调用OCR并返回结果
        data = upload_image(filename,self.header)
        img_id = data["data"]["id"]
        url="https://api2.sider.ai/api/v2/completion/text"
        payload = {
            "prompt": "ocr",
            "stream": True,
            "app_name": "ChitChat_Edge_Ext",
            "app_version": "4.23.1",
            "tz_name": "Asia/Shanghai",
            "cid": self.context_id,
            "model": model,
            "from": "ocr",
            "image_id": img_id,
            "ocr_option": {
                "force_ocr": True,
                "use_azure": False
            },
            "tools": {},
            "extra_info": {
                "origin_url": ORIGIN+"/standalone.html",
                "origin_title": "Sider"
            }
        }
        return self.get_text(url,self.header,payload)

def test_chat(session):
    while True:
        try:
            if session.remain is not None:
                msg=f"输入提示词 ({session.remain}/{session.total}): "
            else:msg="输入提示词: "
            prompt=input(msg)
            if prompt.strip():
                for result in session.chat(prompt, "gpt-4o-mini"):
                    print(result,end="")
                print()
        except Exception:
            traceback.print_exc()

def test_ocr(session):
    while True:
        try:
            filename=normpath(input("拖曳文件到本窗口（或输入文件路径），再按Enter: ").strip())
            if filename.strip():
                for result in session.ocr(filename):
                    print(result,end="")
                print()
        except Exception:
            traceback.print_exc()

if __name__=="__main__":
    token_file=sys.argv[1] if len(sys.argv)>=2 else DEFAULT_TOKEN_FILE
    with open(token_file,encoding="utf-8") as f:
        config=json.load(f)
        token=config["token"]
        cookie=config.get("cookie")
    session=Session(token=token,cookie=cookie)
    test_chat(session)