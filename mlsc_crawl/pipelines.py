# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy.exporters import CsvItemExporter


class DianPingPipeline(object):

    def open_spider(self, spider):
        self.file = open("enrolldata.csv", "wb")
        self.exporter = CsvItemExporter(self.file,
                                        fields_to_export=["url", "shop_name", "address", "review_count", "city",
                                                          "categroy", "region", "area", "phone", "avg_price",
                                                          "recommend"])
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

        if spider.mode == "error" and spider.error_page:
            with open("error_page_after", "a+") as f:
                for url in spider.error_page:
                    f.write(url+ "\n")