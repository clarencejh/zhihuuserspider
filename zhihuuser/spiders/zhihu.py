# -*- coding: utf-8 -*-
import json

from scrapy import Spider, Request

from zhihuuser.items import ZhihuuserItem


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_url_token = 'excited-vczh'
    offset = 0
    limit = 20

    # 用户详情信息 json
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    # 用户粉丝列表url
    follow_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    follow_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    # 用户关注列表url
    followee_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}'
    followee_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'

    def start_requests(self):
        yield Request(self.user_url.format(user=self.start_url_token, include=self.user_query),
                      callback=self.parse_user)
        yield Request(
            self.followee_url.format(user=self.start_url_token, include=self.followee_query, offset=self.offset,
                                     limit=self.limit), callback=self.parse_followee)
        yield Request(self.follow_url.format(user=self.start_url_token, include=self.follow_query,          offset=self.offset, limit=self.limit), callback=self.parse_follow)

    def parse_user(self, response):
        results = json.loads(response.text)
        item = ZhihuuserItem()
        for field in item.fields:
            if field in results.keys():
                item[field] = results.get(field)
        yield item

        yield Request(
            self.followee_url.format(user=results.get('url_token'), include=self.followee_query, offset=self.offset,
                                     limit=self.limit), callback=self.parse_followee)
        yield Request(
            self.follow_url.format(user=results.get('url_token'), include=self.follow_query, offset=self.offset,
                                   limit=self.limit), callback=self.parse_follow)

    # 粉丝列表
    def parse_follow(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              callback=self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_url = results.get('paging').get('next')
            yield Request(next_url, callback=self.parse_follow)

    def parse_followee(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              callback=self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_url = results.get('paging').get('next')
            yield Request(next_url, callback=self.parse_followee)
