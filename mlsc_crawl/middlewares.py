# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import base64


class XundailiProxyDownloaderMiddleware(object):
    proxy_user = "HY5TS0OK2V433V2D"
    proxy_pass = "AD1ACE274D67C1A7"

    def process_request(self, request, spider):
        if hasattr(spider, "xundaili_proxy_flag") and spider.xundaili_proxy_flag:
            request.meta["proxy"] = "http://http-dyn.abuyun.com:9020"
            user_pass = "%s:%s" % (self.proxy_user, self.proxy_pass)
            proxy_auth = "Basic " + base64.b64encode(user_pass.encode("utf8")).decode("utf8")
            request.headers["Proxy-Authorization"] = proxy_auth


from random_useragent.random_useragent import Randomize


class UserAgentDownloaderMiddleware(object):
    """
        User-Agent 自动切换插件
    """

    def __init__(self):
        self.r_agent = Randomize()

    def process_request(self, request, spider):
        if hasattr(spider, "user_agent_flag") and spider.user_agent_flag and not request.meta.get("dont_user_agent",
                                                                                                  False):
            request.headers["User-Agent"] = self.r_agent.random_agent('desktop', 'windows')
