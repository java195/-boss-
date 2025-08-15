from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth
import time
import random
import os
import json
import traceback

# 初始化配置
chrome_options = Options()
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

service = Service(executable_path=r"C:\Users\42425\Desktop\自动化投递简历\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

# 隐藏自动化痕迹
stealth(
    driver,
    languages=["zh-CN", "zh", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

wait = WebDriverWait(driver, 60)  # 缩短等待时间，避免长时间阻塞
search_text = "北京python实习"
def load_cookies_and_login():
    """加载cookies并登录"""
    print("提示：cookie过段时间会过期，删除boss_cookies.json可重新登录")
    print("强制退出：直接关闭浏览器窗口即可")
    
    if os.path.exists("boss_cookies.json"):
        driver.get("https://www.zhipin.com/")
        with open("boss_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            cookie.pop('domain', None)  # 移除domain限制
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"添加cookie出错: {e}")
        driver.refresh()
        time.sleep(5)
        print("已使用cookie自动登录！")
    else:
        print("未检测到cookie，需要手动登录")
        driver.get("https://www.zhipin.com/web/user/?ka=header-login")
        input("请完成手动登录后按回车继续...")
        with open("boss_cookies.json", "w", encoding="utf-8") as f:
            json.dump(driver.get_cookies(), f)
        print("首次登录，cookie已保存！")

def extract_card_info(card):
    """提取职位卡片信息"""
    boss_font_map = {
        '\ue031': '0', '\ue032': '1', '\ue033': '2', '\ue034': '3',
        '\ue035': '4', '\ue036': '5', '\ue037': '6', '\ue038': '7',
        '\ue039': '8', '\ue03a': '9', '\ue03b': '.'
    }
    
    def restore_boss(salary_str):
        return ''.join(boss_font_map.get(char, char) for char in salary_str)
    
    try:
        job_name = card.find_element(By.XPATH, ".//a[contains(@class,'job-name')]").text.strip()
    except:
        job_name = ""
    
    try:
        salary = card.find_element(By.XPATH, ".//span[contains(@class,'job-salary')]").text.strip()
        salary = restore_boss(salary)
    except:
        salary = ""
    
    try:
        tag_elems = card.find_elements(By.XPATH, ".//ul[contains(@class,'tag-list')]/li")
        tag_list = " | ".join([elem.text.strip() for elem in tag_elems])
    except:
        tag_list = ""
    
    try:
        company = card.find_element(By.XPATH, ".//span[contains(@class,'boss-name')]").text.strip()
    except:
        company = ""
    
    try:
        company_location = card.find_element(By.XPATH, ".//span[contains(@class,'company-location')]").text.strip()
    except:
        company_location = ""
    
    uniq = card.get_attribute("data-jobid") or f"{company}|{job_name}|{salary}"
    
    return {
        "job_name": job_name,
        "salary": salary,
        "tag_list": tag_list,
        "company-location": company_location,
        "company": company,
        "uniq": uniq
    }

def close_popups():
    """关闭可能出现的弹窗"""
    try:
        cancel_btn = driver.find_element(By.XPATH, "//*[contains(@class, 'cancel-btn')]")
        if cancel_btn.is_displayed():
            cancel_btn.click()
            time.sleep(0.5)
    except:
        pass


def safe_click(element, description=""):
    """安全的点击操作"""
    try:
        driver.execute_script("arguments[0].click();", element)
        print(f"已点击: {description}")
        time.sleep(random.uniform(2, 4))
        return True
    except Exception as e:
        print(f"点击失败({description}): {str(e)[:100]}")
        return False

def perform_search(search_text):
    """执行搜索操作"""
    try:
        search_box = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[contains(@placeholder,'搜索职位') or contains(@id,'search')]")))
        search_box.clear()
        
        # 模拟人类输入
        for char in search_text:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.2, 0.5))
        
        search_box.send_keys(Keys.ENTER)
        print(f"已搜索: {search_text}")
        time.sleep(random.uniform(5, 10))  # 等待结果加载
        return True
    except:
        print("搜索失败")
        return False

def main_flow():
    """主流程"""
    # 1. 登录
    load_cookies_and_login()
    
    # 2. 搜索职位
    if not perform_search(search_text):
        return
    
    # 3. 主循环配置
    cards_xpath = "//div[contains(@class,'job-card-wrap')]"
    chat_btn_xpath = "//*[contains(@class, 'op-btn-chat')]"
    processed = set()
    max_greet = 10
    greet_count = 0
    
    while greet_count < max_greet:
        try:
            # 获取当前卡片列表
            try:
                job_cards = wait.until(EC.presence_of_all_elements_located((By.XPATH, cards_xpath)))
                print(f"当前页面卡片数: {len(job_cards)}")
            except:
                try:
                    time.sleep(random.uniform(5,10))
                    job_link = driver.find_element(
                        By.XPATH, 
                        '//div[@class="nav"]//*[contains(@ka, "header-jobs")]'
                    )
                    job_link.click()
                except:
                    print("无职位卡片")
                    continue
                print("获取卡片列表失败")
                driver.get("https://www.zhipin.com/")
                print("准备重新搜索")
                time.sleep(random.uniform(10,20))
                perform_search(search_text)

            
            if not job_cards:
                print("没有找到职位卡片，刷新重试...")
                driver.refresh()
                time.sleep(random.uniform(20, 30))
                continue
            
            # 处理每个卡片
            for idx in range(len(job_cards)):
                try:
                    # 每次重新获取当前卡片，防止stale
                    current_cards = driver.find_elements(By.XPATH, cards_xpath)
                    if idx >= len(current_cards):
                        break
                    
                    card = current_cards[idx]
                    
                    # 提取卡片信息
                    info = extract_card_info(card)
                    if info["uniq"] in processed:
                        continue
                    
                    print(f"\n处理第 {idx+1}/{len(job_cards)} 个职位:" ,info)
                    
                    # 模拟人类操作
                    actions = ActionChains(driver)
                    actions.move_to_element(card).perform()
                    print("鼠标悬停")
                    time.sleep(random.uniform(2, 6))

                    # 滚动页面
                    scroll_y = random.randint(100, 500)
                    driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                    print("随机向下滚动")
                    time.sleep(random.uniform(2, 4))

                    # 确保元素可见
                    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", card)
                    wait.until(EC.element_to_be_clickable(card))
                    print("滚回原始位置")
                    time.sleep(random.uniform(2,4))
                    
                    # 等待详情加载
                    time.sleep(random.uniform(2, 4))
                    
                    # 尝试沟通
                    try:
                        chat_btn = wait.until(EC.element_to_be_clickable((By.XPATH, chat_btn_xpath)))
                        if safe_click(chat_btn, "沟通按钮"):
                            greet_count += 1
                            print(f"沟通成功! (累计: {greet_count}/{max_greet})")
                            
                            # 防反爬休息
                            if greet_count % 3 == 0:
                                rest_time = random.uniform(15, 30)
                                print(f"已沟通3次，休息{rest_time:.1f}秒...")
                                time.sleep(rest_time)
                            else:
                                time.sleep(random.uniform(3, 6))
                            
                            # 关闭可能弹窗
                            close_popups()
                    except Exception as e:
                        print(f"沟通失败: {str(e)[:100]}")
                    
                    # 标记为已处理
                    processed.add(info["uniq"])
                    
                    # 随机浏览详情页
                    if random.random() < 0.4:  # 20%概率浏览详情
                        try:
                            detail_btns = driver.find_elements(By.XPATH, "//a[contains(@href, 'job_detail')]")
                            if detail_btns:
                                safe_click(detail_btns[0], "详情页")
                                time.sleep(random.uniform(3, 6))
                                driver.back()
                                time.sleep(2)
                        except:
                            pass
                    
                    # 返回列表页
                    if "job_detail" in driver.current_url:
                        driver.back()
                        time.sleep(2)
                
                except StaleElementReferenceException:
                    print("元素已过期，重新获取列表...")
                    break
                except Exception as e:
                    print(f"处理卡片时出错: {str(e)[:100]}")
                    continue
            
            # 滚动加载更多
            if greet_count < max_greet:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(3, 6))
        
        except Exception as e:
            print(f"主循环出错: {str(e)[:100]}")
            if "invalid session" in str(e).lower():
                print("会话失效，需要重新登录")
                break
            time.sleep(5)

if __name__ == "__main__":
    try:
        main_flow()
    except Exception as e:
        print(f"程序异常: {str(e)}")
        traceback.print_exc()
    finally:
        input("按回车退出程序...")
        try:
            driver.quit()
        except:
            pass

