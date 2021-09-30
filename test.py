from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
options = webdriver.ChromeOptions()
options.add_argument('log-level=3')
options.add_argument("--window-size=800,800")
browser = webdriver.Chrome(chrome_options=options)


url =""

browser.get(url)
soup = BeautifulSoup(browser.page_source, "lxml")
search = soup.find_all('li',{'class':'b_algo'})
for s in search:
    print("====================")
    print(s.get_text(" "))


res_infocard = ""
infocard = soup.find_all('li',{'class':'b_ans'}) 

for i in infocard:
    print(i.get_text(" "))

compurl = soup.find_all('a',{'class':'ibs_2btns'})
for x in compurl:
    x = x['href']
    if "maps/" not in x:
        print(x)




browser.quit()
