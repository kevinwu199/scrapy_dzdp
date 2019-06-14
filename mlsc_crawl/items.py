# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MlscCrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    shop_name = scrapy.Field()
    address = scrapy.Field()
    review_count = scrapy.Field()
    city = scrapy.Field()
    categroy = scrapy.Field()
    region = scrapy.Field()
    area = scrapy.Field()
    phone = scrapy.Field()
    avg_price = scrapy.Field()
    recommend = scrapy.Field()

