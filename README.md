**The English documentation is placed below the Chinese version.**  

`sider_ai_api`是一个调用[sider.ai](sider.ai)的Python API库，提供了在不能访问ChatGPT等国外AI平台的情况下，调用ChatGPT、Gemini、Claude、llama，乃至o1等国外大模型的完整解决方案。  

## 安装

打开终端，并输入`pip install sider-ai-api`即可。  

## 用法
### `Session` 类

`Session` 类用于与 Sider API 交互，提供聊天和 OCR 功能，同时管理 API 的身份验证、请求头和会话状态。

#### 构造函数:

```python
def __init__(self,token=None,context_id="",cookie=None):
```

- **参数**:
  - `token` (str): 可选，身份验证令牌，如`"eyJhbGciOiJIUzI..."`，注意**不需要**加`Bearer `这个开头。如果为None，则自动读取`DEFAULT_TOKEN_FILE` (默认是`_token.json`) 中的token和cookie。
  - `context_id` (str): 可选，对话上下文的 ID，如`"C0M.......EB"`，空字符串表示开始新对话。默认为空字符串。
  - `cookie` (str): 可选，身份验证所需的 cookie 字符串，如`"key1=value1;key2=value2"`。如果不提供，默认使用`COOKIE_TEMPLATE`常量中的模板。

#### 主要方法:

##### `chat(prompt, model="gpt-4o-mini")`

用提示词与 AI 对话，返回一个字符串生成器，包含AI的响应结果。

- **参数**:
  - `prompt` (str): 用户提示词。
  - `model` (str): 使用的 AI 模型，默认为 `"gpt-4o-mini"`。

- **返回**: 一个字符串生成器，逐步返回 AI 的响应，可以使用`"".join()`拼接。

##### `ocr(filename, model="gemini-2.0-flash")`

对图像文件执行 OCR 识别，返回结果的字符串生成器。

- **参数**:
  - `filename` (str): 图像文件的路径。
  - `model` (str): 使用的 OCR 模型，默认为 `"gemini-2.0-flash"`。完整的模型列表可以在`MODELS`和`ADVANCED_MODELS`常量中找到。

- **返回**: 一个字符串生成器，逐步返回 AI 的响应。

#### 属性:

- `context_id`: 对话上下文id，如果为`""`则表示开始新对话。对话上下文会由服务器端保存。  
- `total`: API的总调用次数，为整数或者None。  
- `remain`: API的剩余调用次数，为整数或者None。  

## 示例代码

```python
from sider_ai_api import Session

# 首先设置token和cookie变量
session = Session(token=token, cookie=cookie)
print("".join(session.chat("Hello, ChatGPT!", "gpt-4o-mini")))
print("".join(session.chat("Hello, Claude!", "claude-3.5-haiku")))
print("".join(session.chat("Hello, Gemini!", "gemini-2.0-flash")))
print("".join(session.chat("Hello, DeepSeek!", "deepseek-chat")))  # DeepSeek-v3
print("".join(session.chat("Hello, o1!", "o1")))
print("".join(session.ocr("path/to/image.jpg"))) # OCR
print(f"还剩{session.remain}/{session.total}次API调用。")
```

## 关于token和cookie

`Session`类是必须提供token的。token可以在浏览器的设置或者开发者工具中查看。对于Edge，cookie和token可以在[edge://settings/cookies/detail?site=sider.ai](edge://settings/cookies/detail?site=sider.ai)中查看。  
如果只有token而没有额外的cookie信息，如`CloudFront-Signature`等，也一样能调用聊天功能，但是在OCR识别的上传图片这一步，会提示需要Cloudflare验证的错误消息，因此建议包含完整的cookie。  

---

`sider_ai_api` is a Python API library for interacting with [sider.ai](sider.ai). It provides a complete solution for accessing large language models such as ChatGPT, Gemini, Claude, Llama, and even o1, in scenarios where direct access to foreign AI platforms like ChatGPT is unavailable.

## Installation

Just open the terminal and enter `pip install sider-ai-api`.  

## Usage
### `Session` Class

The `Session` class is used to interact with the Sider API. It provides chat and OCR functionalities while managing API authentication, request headers, and session states.

#### Constructor:

```python
def __init__(self, token=None, context_id="", cookie=None):
```

- **Parameters**:
  - `token` (str): Optional. The authentication token, e.g., `"eyJhbGciOiJIUzI..."`. Note that **you don't need** to prepend `Bearer ` to the token. If set to None, it will automatically read the token and cookie from `DEFAULT_TOKEN_FILE` (default is `_token.json`).
  - `context_id` (str): Optional. The ID of the conversation context, such as `"C0M.......EB"`. An empty string indicates starting a new conversation. Defaults to an empty string.
  - `cookie` (str): Optional. The cookie string required for authentication, e.g., `"key1=value1;key2=value2"`. If not provided, the default `COOKIE_TEMPLATE` constant will be used.

#### Main methods:

##### `chat(prompt, model="gpt-4o-mini")`

Interact with the AI using a prompt. Returns a string generator containing the AI's response.

- **Parameters**:
  - `prompt` (str): The user prompt.
  - `model` (str): The AI model to use. Defaults to `"gpt-4o-mini"`. A complete list of models can be found in the `MODELS` and `ADVANCED_MODELS` constants.

- **Returns**: A string generator that progressively yields the AI's response. You can use `"".join()` to concatenate the output.

##### `ocr(filename, model="gemini-2.0-flash")`

Perform OCR (Optical Character Recognition) on an image file. Returns a string generator containing the recognition result.

- **Parameters**:
  - `filename` (str): The path to the image file.
  - `model` (str): The OCR model to use. Defaults to `"gemini-2.0-flash"`.

- **Returns**: A string generator that progressively yields the OCR result.

#### Attributes:

- `context_id`: The conversation context ID. If it is `""`, it indicates starting a new conversation. The conversation context is stored on the server side.  
- `total`: The total number of API calls available, as an integer or `None`.  
- `remain`: The remaining number of API calls, as an integer or `None`.  

## Example Code

```python
from sider_ai_api import Session

# Firstly, set the token and cookie variables
session = Session(token=token, cookie=cookie)
print("".join(session.chat("Hello, ChatGPT!", "gpt-4o-mini")))
print("".join(session.chat("Hello, Claude!", "claude-3.5-haiku")))
print("".join(session.chat("Hello, Gemini!", "gemini-2.0-flash")))
print("".join(session.chat("Hello, DeepSeek!", "deepseek-chat")))  # DeepSeek-v3
print("".join(session.chat("Hello, o1!", "o1")))
print("".join(session.ocr("path/to/image.jpg")))  # OCR
print(f"Remaining {session.remain}/{session.total} API calls.")
```

## About Token and Cookie

The `Session` class requires a token that can be found in your browser settings or developer tools. For Edge, you can view the cookie and token at [edge://settings/cookies/detail?site=sider.ai](edge://settings/cookies/detail?site=sider.ai).  
If you only have the token and not additional cookie information (e.g., `CloudFront-Signature`), you can still use the chat functionality. However, for OCR image uploads, you may encounter an error requiring Cloudflare verification. Therefore, it is recommended to include the full cookie.  