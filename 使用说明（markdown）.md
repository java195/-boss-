# Boss直聘自动化投递脚本使用说明

## 一、准备工作

### 1. **Python 依赖安装**

请确保已安装 Python 3.7 及以上版本。

打开命令行窗口，运行下列命令安装依赖：

```bash
pip install selenium selenium-stealth
```

```bash
pip install selenium
```

```bash
pip install requests
```

也忽略上方的所有指令 直接运行下面一行指令
```bash
pip install -r requirements.txt
```

### 2. **Chrome 版本与驱动配置**

- 请确保你的 Chrome 浏览器版本与 chromedriver 匹配。  
  推荐下载安装最新 Chrome，并在 [chromedriver 官网](https://chromedriver.chromium.org/downloads) 下载对应版本。

- 将 `chromedriver.exe` 放到适当目录，并在主脚本 `Service(executable_path=...)` 处填写绝对路径。例如：

```python
service = Service(executable_path=r"C:\Users\你的用户名\Desktop\自动化投递简历\chromedriver.exe")
```

### 3. **脚本、依赖文件存放**

- 本脚本建议与 `chromedriver.exe`、`boss_cookies.json`（首次自动生成）放在同一目录，避免路径问题。

---

## 二、首次使用流程

1. **运行脚本**
    - 打开命令行窗口，进入本脚本所在目录。
    - 输入命令：
      ```bash
      python boss.py
      ```
    - 如果 cookie 文件不存在，程序会自动要求你手动登录一次 Boss 直聘（扫码、输入手机号等均支持），并在成功后回车。

2. **自动保存 cookie**
    - 登录成功后脚本会自动保存 cookie 到本目录下 `boss_cookies.json`，之后再启动脚本**无需重复登录**（除非 cookie 过期）。

---

## 三、后续自动登录

- 之后再次运行脚本，会自动利用 cookie 登录 Boss直聘，无需人工干预。
- 如果长时间不用、cookie失效/被风控拒绝，再按照首次注册流程重新手动登录一遍即可，脚本会自动更新 cookie。

---

## 四、脚本参数及自定义

- **岗位搜索（默认北京 python 实习）**
    - 可直接在源码第70行
      ```python
      job = "北京python实习"
      ```
      修改为你需要投递的岗位关键字，如：
      ```python
      job = "Java开发工程师"
      ```

- **沟通最大次数限制：**
    ```python
    max_greet = 10
    ```
    若需每次最大投递数量增减，请修改此参数（如 20）。

- **沟通/行为伪装，自动刷新等全部已内置，无需手动调整。**

---

## 五、常见问题与解决

- **cookie 过期/风控异常：**
    - 删除脚本目录下的 `boss_cookies.json`，重新运行脚本，按提示手动登录即可。

- **浏览器与 chromedriver 兼容问题：**
    - 报错如“chrome version mismatch”请重新下载对应版本 chromedriver。

- **退出方法：**
    - 直接关闭主窗口即可强制退出。
    - 正常投递工作结束后会提示 `按回车退出...`，直接按回车关闭浏览器和脚本。

---

## 六、必备文件一览

- boss.py   （主脚本，可自由命名）
- chromedriver.exe  （放在你指定的目录）
- boss_cookies.json （首次登录自动生成）

---

## 七、进阶说明

- 本脚本已集成 selenium-stealth，能有效降低 Boss直聘对自动化脚本的风控。
- 所有沟通行为都做了伪装，模拟真实用户操作，减少风控风险。
- 默认投递岗位、沟通数量均可自主调整——找到源码相关参数直接修改即可。
- 后续支持多岗位/多城市/多账号扩展，如需要请联系开发者或自行按此模板拓展。

---

## 八、常用命令速查

```bash
# 安装依赖
pip install selenium selenium-stealth

# 运行脚本
python boss.py

# cookie异常/需重新登录
del boss_cookies.json  # 或直接用文件管理器删掉
python boss.py         # 按提示重新登录
```



