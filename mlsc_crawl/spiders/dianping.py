import re

import requests
from scrapy import Selector
from scrapy.http import Request
from scrapy.spiders import CrawlSpider

from mlsc_crawl.items import MlscCrawlItem


class DianpingSpider(CrawlSpider):
    name = 'dianping'

    start_urls = [
        # 'http://www.dianping.com/shopall/2/0'  # 长沙
        # 'http://www.dianping.com/shopall/192/0'  # 株洲
        # 'http://www.dianping.com/shopall/193/0'  # 湘潭
        # 'https://www.dianping.com/shopall/203/0' # 娄底
        # 'https://www.dianping.com/shopall/195/0' # 邵阳
        'http://www.dianping.com/shopall/197/0' # 常德
    ]

    user_agent_flag = True

    xundaili_proxy_flag = True

    font_name_dict = {
        "uniefeb": "1",
        "unie4ff": "2",
        "unif70d": "3",
        "unie6ec": "4",
        "unif404": "5",
        "unie65d": "6",
        "unie284": "7",
        "unif810": "8",
        "unie27b": "9",
        "uniec2d": "0"
    }

    font_code_dict = {}

    css_dict = {}

    svg_dict = {}

    def __init__(self, mode="page"):
        self.mode = mode
        self.error_page = []

    def valid_verify(self, response):
        return False if response.url.find("verify.meituan.com") >= 0 else True

    def parse(self, response):

        if not self.valid_verify(response):
            yield response.request.replace(url=response.request.meta["redirect_urls"][0])
            return

        if self.mode == "page":
            food_urls = response.xpath("//dl[@class='list']")[0].xpath("dd/ul/li/a/@href").extract()
            #
            self.init_font()

            for url in food_urls:
                url = "http:{}".format(url)
                headers = {
                    "Host": "www.dianping.com",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
                    "Referer": response.url
                }
                yield Request(url, headers=headers, callback=self.parse_pages, dont_filter=True)

        elif self.mode == "error":
            with open("error_page") as f:
                error_pages_str = f.read()
            error_page = error_pages_str.split("\n")
            for page in error_page:
                if page:
                    recommend = "-"
                    yield Request(page, callback=lambda response, recommend=recommend: self.parse_shop(response, recommend),
                                  dont_filter=True)

    def parse_page(self, response):
        if not self.valid_verify(response):
            yield response.request.replace(url=response.request.meta["redirect_urls"][0])
            return
        div = response.xpath('//div[@id="shop-all-list"]/ul/li')

        for dd in div:
            shopurl = dd.xpath('div[2]/div[1]/a[1]/@href').extract_first()
            recommend = ",".join(dd.xpath("div/div[@class='recommend']/a/text()").extract())
            yield Request(shopurl, callback=lambda response, recommend=recommend: self.parse_shop(response, recommend),
                          dont_filter=True)

    def parse_shop(self, response, recommend):
        if not self.valid_verify(response):
            yield response.request.replace(url=response.request.meta["redirect_urls"][0])
            return

        num_codes = re.findall('<d class="num">(.*?)</d>', response.text)
        _text = response.text

        for code in num_codes:
            _code = code.replace("&#", "0").replace(";", "")
            _text = _text.replace(code, self.font_name_dict[self.font_code_dict[_code]])

        _text = self.clean_elements(_text)
        s = Selector(text=_text)

        tabs = s.xpath("//div[@class='breadcrumb']/a/text()").extract()

        city = region = categroy = area = ""
        if len(tabs) == 4:
            city, categroy, region, area = tabs
        elif len(tabs) == 3:
            city, categroy, region = tabs
        elif len(tabs) == 2:
            city, region = tabs
        elif len(tabs) == 1:
            categroy = tabs[0]
        else:
            tabs = s.xpath("//div[@class='breadcrumb']/span/text()").extract()
            categroy = tabs[0]

        css = re.search('//s3plus.meituan.net/v1/.*?/svgtextcss/.*?.css', _text)
        address = re.search(r"address: \"(.*?)\"", _text).groups()[0]
        if not address or not css:
            self.logger.error("like %s not address" % response.url)
            self.add_error_page(response)
            return

        data = {
            "url": response.url,
            "shop_name": s.xpath("//h1[@class='shop-name']/text()").extract_first().strip(),
            "address": address,
            "review_count": s.xpath("//*[@id='reviewCount']/text()").extract_first().replace("条评论", "").strip(),
            "city": city,
            "categroy": categroy,
            "region": region,
            "area": area,
            "phone": s.xpath("//p[@class='expand-info tel']/text()").extract()[1].strip(),
            "avg_price": s.xpath("//*[@id='avgPriceTitle']/text()").
                extract_first().replace("人均:", "").replace("元", "").strip(),
            "recommend": recommend
        }

        yield MlscCrawlItem(**data)

    def parse_pages(self, response):
        if not self.valid_verify(response):
            yield response.request.replace(url=response.request.meta["redirect_urls"][0])
            return

        pages = response.xpath('//div[@class="page"]/a/@data-ga-page').extract()

        pg = int(str(pages[-2])) + 1 if pages else 0

        for p in range(1, pg):
            ul = response.url + 'p' + str(p)
            yield Request(ul, callback=self.parse_page, dont_filter=True)

    def init_font(self):
        """
            from fontTools.ttLib import TTFont
            font = TTFont('./xxx.woff')sts
            font.saveXML('.xxx.xml')
        :return:
        """

        with open("dianping.xml") as f:
            line = f.readline()
            while line:
                content = re.findall('code="([^"]*?)" name="([^"]*?)"', line)

                if content:
                    self.font_code_dict[content[0][0]] = content[0][1]
                line = f.readline()

    def convert_svg_by_css(self, text):
        css = re.search('//s3plus.meituan.net/v1/.*?/svgtextcss/.*?.css', text).group()
        if css not in self.css_dict.keys():
            r = requests.get("http:{}".format(css))
            self.css_dict[css] = r.text

        css_text = self.css_dict[css]

        s = Selector(text=text)

        for f in s.xpath("//d"):
            class_ = f.xpath("@class").extract_first()

            svg_url = \
            re.search('d\[class\^\=\"%s\"\]{.*background-image: url\((.*?)\)' % class_[0:2], css_text).groups()[0]
            if svg_url not in self.svg_dict.keys():
                svg_text = requests.get("http:" + svg_url).text
                self.svg_dict[svg_url] = svg_text
            svg_text = self.svg_dict[svg_url]

            s = Selector(text=svg_text)
            svg_data = {}
            for t in s.xpath("//text"):
                x = t.xpath("text()").extract_first()
                y = t.xpath("@y").extract_first()
                svg_data[y] = x

            _temp_svg_y = list(map(int, svg_data.keys()))
            _temp_svg_y.append(int(y))
            _temp_svg_y.sort()
            index = _temp_svg_y.index(int(y))
            if index >= len(_temp_svg_y) - 1:
                index = + 1

            # 通过计算文本的偏移量获取对应的数字，计算公式 文字css x轴 // 字体大小
            x, y = re.search(r'%s{background:-(\d+).0px -(\d+).0px' % class_, css_text).groups()
            font_size = int(re.search('x="(\d{2}) ', svg_text, re.S).groups()[0])
            offset = int(x) // int(font_size)
            num = svg_data[str(_temp_svg_y[index])][offset]
            text = text.replace(f.extract(), num)

        return text

    def clean_elements(self, _text):
        for e in re.findall('<d class="num">.*?</d>', _text):
            _text = _text.replace(e, re.search('<d class="num">(.*?)</d>', e).groups()[0])

        _text = self.convert_svg_by_css(_text)
        return _text

    def add_error_page(self, response):
        self.error_page.append(response.url)
        if self.mode == "page":
            with open("error_page", "a+") as f:
                f.write(response.url + "\n")

