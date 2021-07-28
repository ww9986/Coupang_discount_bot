import re
import requests
import time
import pymysql

from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert


def search(str1, str2):
    name = str1
    keyword = str2

    if keyword.find('아이패드') > -1:
        if keyword.find('인치') > -1:
            keyword = re.sub('인치', '형', keyword)

    name = name.lower()

    if keyword.find('아이폰') == -1:
        keyword = keyword.split(' ')

        for a in keyword:
            index = name.find(a)
            if index == -1 or (name[index + len(a)] != ' ' and name[index + len(a)] != ','):
                return False
            name = name[:index] + name[index + len(a):]

    else:
        if name.find(keyword) == -1:
            return False

    return True


def crawling(keyword):
    base_url = 'https://www.coupang.com'  # 쿠팡 주소

    # User-Agent header설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    }
    url = 'https://www.coupang.com/np/search?rocketAll=true&q={}&brand=&offerCondition=&filter=&availableDeliveryFilter=&filterType=rocket%2Ccoupang_global&isPriceRange=false&priceRange=&minPrice=&maxPrice=&page={}&trcid=&traid=&filterSetByUser=true&channel=auto&backgroundColor=&component=&rating=0&sorter=scoreDesc&listSize=36'.format(
        keyword, 1)
    index_resp = requests.get(url, headers=headers)
    index_html_src = index_resp.text
    index_soup = BeautifulSoup(index_html_src, 'lxml')
    index = index_soup.select_one(
        '#searchOptionForm > div.search-wrapper > div.search-content.search-content-with-feedback > div.search-pagination > a.btn-last.disabled')
    if index:
        index = int(index)
    else:
        index = int(index_soup.select_one(
            '#searchOptionForm > div.search-wrapper > div.search-content.search-content-with-feedback > div.search-pagination > span.btn-page > a:nth-child(3)').text)
    print(index)

    for i in range(1, index + 1):
        print(i)

        url = 'https://www.coupang.com/np/search?rocketAll=true&q={}&brand=&offerCondition=&filter=&availableDeliveryFilter=&filterType=rocket%2Ccoupang_global&isPriceRange=false&priceRange=&minPrice=&maxPrice=&page={}&trcid=&traid=&filterSetByUser=true&channel=auto&backgroundColor=&component=&rating=0&sorter=scoreDesc&listSize=36'.format(
            keyword, i)

        i += 1

        # Beautiful 객체 생성
        external_resp = requests.get(url, headers=headers)
        if external_resp.status_code == 200:
            external_html_src = external_resp.text
            external_soup = BeautifulSoup(external_html_src, 'lxml')

            product_list = external_soup.find_all('li', attrs={'class': re.compile('^search-product')})  # 제품 목록 가져오기
            product_detail = {}

            for product in product_list:
                if product.find('span', attrs={'class': 'ad-badge-text'}) or product.find('div',
                                                                                          attrs={
                                                                                              'class': 'out-of-stock'}):
                    continue

                product_detail['name'] = product.find('div', attrs={'class': 'name'}).text  # 제품명

                check = search(product_detail['name'], keyword)
                if not check:
                    continue

                product_detail['link'] = base_url + product.find('a', attrs={'class': 'search-product-link'})[
                    'href']  # 제품링크 가져오기

                # 제품 링크를 바탕으로 제품의 상세 정보 (제목, 가격 및 할인율) 가져오기 위한 Beautiful 객체 생성
                resp = requests.get(product_detail['link'], headers=headers)
                html_src = resp.text
                soup = BeautifulSoup(html_src, 'lxml')

                product_detail['origin_price'] = int(
                    ''.join(re.sub('원', '', soup.find('span', attrs={'class': 'origin-price'}).text).split(
                        ',')))  # 원래 가격 (할인 전)
                product_detail['discount_rate'] = soup.find('span', attrs={'class': 'discount-rate'}).text  # 할인율
                product_detail['discount_rate'] = re.sub('\n', '', product_detail['discount_rate'])
                product_detail['discount_rate'] = re.sub(' ', '', product_detail['discount_rate'])

                if product_detail['discount_rate'].find('%') == 0:
                    product_detail['discount_rate'] = '0%'

                # 할인율이 존재한다면
                if product_detail['discount_rate'] != '0%':
                    try:
                        product_detail['discount_price'] = int(''.join(re.sub('원', '', soup.select_one(
                            '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-price-container > div.prod-price > div > div.prod-sale-price.wow-coupon-discount > span.total-price > strong').text).split(
                            ',')))  # 할인 가격
                    except AttributeError:
                        product_detail['discount_price'] = int(''.join(re.sub('원', '', soup.select_one(
                            '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-price-container > div.prod-price > div > div.prod-sale-price.prod-major-price > span.total-price').text).split(
                            ',')))

                try:
                    wow_price = soup.select_one(
                        '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-price-container > div.prod-price > div > div.prod-coupon-price.prod-major-price > span.total-price > strong')
                    wow_price = int(''.join(re.sub('원', '', wow_price.text).split(
                        ',')))  # 할인 가격 + 와우 혜택 가격
                    product_detail['wow_price'] = wow_price
                except:
                    pass

                if soup.select_one(
                        '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-ccid-detail-container > div > div.ccid-detail-tit > a'):
                    # 카드 할인 정보를 가져오기 위한 selenium 설정
                    chrome_options = Options()
                    chrome_options.add_argument(
                        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36')  # 카트 할인 관련 팝업을 띄우기 위한 버튼 클릭

                    # 브라우저 실행 및 제품 상세 페이지 접속
                    chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  # 크롬드라이버 버전 확인

                    try:
                        browser = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=chrome_options)
                    except:
                        chromedriver_autoinstaller.install(True)
                        browser = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options=chrome_options)

                    browser.implicitly_wait(10)
                    browser.get(product_detail['link'])
                    browser.delete_all_cookies()

                    time.sleep(
                        2)  # time sleep을 안주거나 너무 빨리하면(나는 2초로 했음) 웹창 띄우는 시간과 alert를 처리하는 시간 및 사진 저장하는 시간 순서가 안맞아서 에러남

                    # alert 처리하기 - 별도 화면 참고바람
                    try:  # try 아래를 시도해보고 안되면 except로 감
                        result = browser.switch_to_alert()

                        # alert 창 확인
                        result.accept()

                        # alert 창 끄기
                        # result.dismiss()
                        time.sleep(2)  # 여기도 time sleep 필요하고, 내가 2초로 한 이유는 더 빠르게 하면 타이밍이 안맞아서 에러남

                    except:
                        "There is no alert."

                    browser.find_element_by_css_selector(
                        '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-ccid-detail-container > div > div.ccid-detail-tit > a').click()

                    browser.find_element_by_css_selector(
                        '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-ccid-detail-container > div > div.ccid-detail-tit > a').click()
                    card_link = browser.find_element_by_css_selector('#creditCardBenefitContent > iframe')
                    browser.switch_to_frame(card_link)

                    uniqueness = browser.find_elements_by_css_selector(
                        'tbody > tr:nth-child(1) > td > p > span:nth-child(2)')  # 와우 회원 전용 여부
                    try:
                        product_detail['uniqueness'] = uniqueness.text  # 텍스트 가져오기
                    except AttributeError:
                        pass

                    # 카드 할인 금액 가져오기
                    card = browser.find_element_by_css_selector('tbody > tr:nth-child(1) > td > p').text
                    percent = re.findall('\d+', card)
                    money = re.findall('\d+', card[card.find('최'): card.find(',')])

                    percent = int(percent[0]) * 0.01
                    money = int(money[0]) * 10000
                    card_discount = None

                    if product_detail.get('wow_price'):  # 와우 혜택가가 존재한다면
                        card_discount = money if product_detail['wow_price'] * percent >= money else percent

                        if card_discount == percent:
                            total_price = int(round(round(
                                int(product_detail['wow_price']) * (
                                        1 - percent)) / 10) * 10)  # 최종 할인가 구하기 (와우 할인가 - (와우 할인가 * 카드 할인율))
                        else:
                            total_price = int(product_detail['wow_price']) - money  # 최종 할인가 구하기 (와우 할인가 - 카드 할인가)

                        product_detail['total_price'] = total_price

                    else:
                        card_discount = money if product_detail['discount_price'] * percent >= money else percent

                        if product_detail.get('discount_price'):  # 기본 할인이 존재한다면
                            if card_discount == percent:
                                total_price = int(round(round(int(product_detail['discount_price']) * (
                                        1 - percent)) / 10) * 10)  # 최종 할인가 구하기 (일반 할인가 - (일반 할인가 * 카드 할인율))
                            else:
                                total_price = int(
                                    product_detail['discount_price']) - money  # 최종 할인가 구하기 (일반 할인가 - 카드 할인가)

                                product_detail['total_price'] = total_price

                        else:
                            card_discount = money if product_detail['origin_price'] * percent >= money else percent

                            if card_discount == percent:
                                total_price = int(round(round(int(product_detail['origin_price']) * (
                                        1 - percent)) / 10) * 10)  # 최종 할인가 구하기 (기본 가격 - (기본 가격 * 카드 할인율))
                            else:
                                total_price = int(product_detail['origin_price']) - money  # 최종 할인가 구하기 (기본 가격 - 카드 할인가)

                                product_detail['origin_price'] = total_price

                    if card_discount == percent:
                        product_detail['card_discount'] = str(int(percent / 0.01)) + '%'
                    else:
                        product_detail['card_discount'] = str(format(money, ',')) + '원'

                    product_detail['total_discount'] = round(
                        (int(product_detail['origin_price']) - int(product_detail['total_price'])) / int(
                            product_detail['origin_price']) / 0.01)  # 최종 할인율 구하기 {(원래 가격 - 최종 가격) / 원래 가격} / 0.01

                    table = browser.find_element_by_css_selector(
                        '#react-root > div > div.ccid-benefit-old__benefit-list > table > tbody')
                    companies = table.find_elements_by_tag_name('img')
                    logos = []

                    for company in companies:
                        logos.append(company.get_attribute('alt'))
                    product_detail['card_company'] = logos

                    browser.quit()

                else:
                    if product_detail['discount_rate'] != '0%':
                        pass
                    # if int(re.sub('%', '', product_detail['discount_rate'])) <= 20:
                    # continue
                    else:
                        continue

                stock = soup.select_one(
                    '#contents > div.prod-atf > div > div.prod-buy.new-oos-style.not-loyalty-member.eligible-address.without-subscribe-buy-type.DISPLAY_0 > div.prod-price-container > div.prod-price > div > div.aos-label')
                if stock:
                    product_detail['Out of stock'] = stock

                print('제품명: ' + product_detail.get('name'))
                print('제품 링크: ' + product_detail.get('link'))
                print('제품 정가 (할인전 가격): ' + str(format(product_detail.get('origin_price'), ',')) + '원')
                if product_detail.get('discount_rate'):
                    print('제품 할인율: ' + product_detail['discount_rate'])
                    print('할인 가격: ' + str(format(product_detail['discount_price'], ',')) + '원')
                if product_detail.get('wow_price'):
                    print('와우 혜택가: ' + str(format(product_detail['wow_price'], ',')) + '원')
                if product_detail.get('card_discount'):
                    print('카드 할인시 와우회원 여부: ' + product_detail.get('uniqueness', '필요 없음'))
                    print('대상 카드사: ' + str(product_detail['card_company']))
                    print('카드 할인율: ' + product_detail['card_discount'])
                    print('최종 할인율: ' + str(product_detail['total_discount']) + '%')
                    print('최종 가격: ' + str(format(product_detail['total_price'], ',')) + '원')
                if product_detail.get('Out of stock'):
                    print(product_detail['Out of stock'])
                print('-' * 100)


'''
   keyword = input('알림을 받고자 하는 제품의 이름을 입력하세요.\n'
                   '그램과 같은 제품은 반드시 연도를 앞에 적어주세요. ex) 2021 그램 16\n'
                   '만약 앞에 제조사를 붙이고 싶다면 풀네임을 적어주세요. ex) 삼성 -> 삼성전자, LG -> LG전자\n'
                   '제품을 특정하지, 검색된 상품 전체를 대상으로 정보를 불러옵니다.\n'
                   '휴대폰의 경우 뒤에 자급제를 붙여주세요. ex) 아이폰 12 자급제\n'
                   '대소문자는 상관하지 않습니다.\n'
                   '>>> ')  # 검색하고자 하는 제품 입력받기
   '''
keyword = '아이폰 12 자급제'
