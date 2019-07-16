# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import re
import sys
import time

import requests

from lxml import html


class User(object):

    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.username = kwargs["username"]
        self.full_name = ""
        self.is_private = False
        self.is_verified = False
        self.follows = []
        self.contents = []
        self.end_cursor = ""
        self.profile_pic_url = ""
        # self.followed = 0
        # self.following = 0

    def __repr__(self):
        return "User %s<%s>" % (self.id, self.username)

    def add(self, user):
        self.follows.append(user)
        print(user)


class InstagramAPI(object):

    def __init__(self, **kwargs):
        self.fan = kwargs["fan"]
        self.brand = kwargs["brand"]
        self.endpoint = "https://www.instagram.com"
        self.queryid = ""
        self.session = requests.Session()
        headers = {
            'authority': 'www.instagram.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': 'sessionid=IGSC72e744b84b15e3d827892e5e57a5cf63734d1a097800c81d98842ee6b6464a12%3A0H9LhlbAWEZtD0RrmM2cbV8XAUHve2nn%3A%7B%22_auth_user_id%22%3A7109575542%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%227109575542%3Aef6Ytycxq4CfqCYFILGAN9rA8R4Sk1dA%3A622e2c3b39690056440d62e136422d40f0a70481c9ea652c2d6c181314df44b2%22%2C%22last_refreshed%22%3A1537714456.3288357258%7D',
        }
        self.session.headers.update(headers)

    def run(self):
        fan_url = "%s/%s/" % (self.endpoint, self.fan)
        brand_url = "%s/%s/" % (self.endpoint, self.brand)
        r = self.session.get(fan_url)
        if r.status_code != 200:
            return {"status": None, "message": "Bad Response for Fan User."}
        self.queryid = self.find_following_query_id(r)
        if self.queryid is None:
            return {"status": None, "message": "Invalid Fan Query Hash."}
        fan_user = self.get_profile(r)
        if fan_user is None:
            return {"status": None, "message": "Cookies/Response Error at Fan processing."}

        if fan_user.is_private is True:
            print("private fan profile")
            r = self.session.get(brand_url)
            if r.status_code != 200:
                return {"status": None, "message": "Bad Response for Brand User."}
            self.queryid = self.find_followed_query_id(r)
            # print (self.queryid)
            if self.queryid is None:
                return {"status": None, "message": "Invalid Brand Query Hash."}
            brand_user = self.get_profile(r)
            if brand_user is None:
                return {"status": None, "message": "Cookies/Response Error at Brand processing."}
            if brand_user.is_private is True:
                return {"status": None, "message": "Fan & Brand profiles are private"}
            return self.is_followed(brand_user)

        return self.is_following(fan_user)

    def is_following(self, user):
        params = {
            'query_hash': self.queryid,
            'variables': '{"id":"%s","first":50}' % (user.id)
        }
        while True:
            r = self.session.get(
                'https://www.instagram.com/graphql/query/', params=params)
            edges = r.json()
            if edges["status"] == "fail":
                return {"status": False, "message": edges["message"]}

            for edge in edges["data"]["user"]["edge_follow"]["edges"]:
                u = User(id=edge["node"]["id"],
                         username=edge["node"]["username"])
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]

                user.add(u)
                if self.brand == u.username:
                    return {"status": True, "message": "Success"}

            has_next_page = edges["data"]["user"][
                "edge_follow"]["page_info"]["has_next_page"]
            if has_next_page:
                end_cursor = edges["data"]["user"][
                    "edge_follow"]["page_info"]["end_cursor"]
                params = {
                    'query_hash': self.queryid,
                    'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, end_cursor)
                }
            else:
                break
            time.sleep(2)
        return {"status": False, "message": "No following."}

    def is_followed(self, user):
        params = {
            'query_hash': self.queryid,
            'variables': '{"id":"%s","first":50}' % (user.id)
        }
        while True:
            r = self.session.get(
                'https://www.instagram.com/graphql/query/', params=params)
            edges = r.json()
            if edges["status"] == "fail":
                return {"status": False, "message": edges["message"]}

            for edge in edges["data"]["user"]["edge_followed_by"]["edges"]:
                u = User(id=edge["node"]["id"],
                         username=edge["node"]["username"])
                u.full_name = edge["node"]["full_name"]
                u.is_verified = edge["node"]["is_verified"]
                user.add(u)
                if self.fan == u.username:
                    return {"status": True, "message": "Success"}

            has_next_page = edges["data"]["user"][
                "edge_followed_by"]["page_info"]["has_next_page"]
            if has_next_page:
                end_cursor = edges["data"]["user"][
                    "edge_followed_by"]["page_info"]["end_cursor"]
                params = {
                    'query_hash': self.queryid,
                    'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, end_cursor)
                }
            else:
                break
            time.sleep(3)

        return {"status": False, "message": "No following."}

    def find_followed_query_id(self, r):
        js_url = re.search(
            "/static/bundles/base/Consumer.js/(.*?).js", r.text, re.S | re.M)

        if js_url:
            js_link = "%s%s" % (self.endpoint, js_url.group(0))
            res = self.session.get(js_link)
            query_filter = re.search(
                "\)\,u=\"(.*?)\"\,s=", res.text, re.S | re.M)
            if query_filter:
                qid = query_filter.group(1)
                return qid
            else:
                return None
        else:
            return None

    def find_following_query_id(self, r):
        js_url = re.search(
            "/static/bundles/base/Consumer.js/(.*?).js", r.text, re.S | re.M)
        if js_url:
            js_link = "%s%s" % (self.endpoint, js_url.group(0))
            res = self.session.get(js_link)
            query_filter = re.search(
                ",l=\"(.*?)\"\,s=1;", res.text, re.S | re.M)
            if query_filter:
                qid = query_filter.group(1)
                return qid
            else:
                return None
        else:
            return None

    def get_profile(self, r):
        sharedData = self.parse_shared_data(r.text)
        if sharedData == {}:
            return None

        t = html.fromstring(r.text)
        userid = sharedData["entry_data"][
            "ProfilePage"][0]["graphql"]["user"]["id"]
        username = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["username"]
        full_name = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["full_name"]
        is_verified = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["is_verified"]
        is_private = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["is_private"]
        # following = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_follow"]["count"]
        # followed = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_followed_by"]["count"]

        user = User(id=userid, username=username)
        user.full_name = full_name
        user.is_private = is_private
        user.is_verified = is_private
        # user.followed = followed
        # user.following = following

        return user

    def parse_shared_data(self, html_string):
        res = re.search("\>window\.\_sharedData = (.*?)\;\<",
                        html_string, re.S | re.M | re.I)
        if res:
            return json.loads(res.group(1))
        else:
            return {}


class Content(object):

    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.user = kwargs["user"]
        self.images = kwargs["images"]
        self.created_time = kwargs["created_time"]
        self.caption = kwargs["caption"]
        self.likes = kwargs["likes"]
        self.comments = kwargs["comments"]
        self.link = kwargs["link"]
        self.type = kwargs["type"]
        self.video_url = None
    
    def __repr__(self):
        return "Content %s %s %s" % (self.id)


class InContentAPI(object):

    def __init__(self, **kwargs):
        self.brand = kwargs["brand"]
        self.last_post_id = kwargs["last_post_id"]
        self.endpoint = "https://www.instagram.com"
        self.queryid = ""
        self.is_last_post_id = False
        self.session = requests.Session()
        headers = {
            'authority': 'www.instagram.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': 'sessionid=IGSC72e744b84b15e3d827892e5e57a5cf63734d1a097800c81d98842ee6b6464a12%3A0H9LhlbAWEZtD0RrmM2cbV8XAUHve2nn%3A%7B%22_auth_user_id%22%3A7109575542%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22_auth_user_hash%22%3A%22%22%2C%22_platform%22%3A4%2C%22_token_ver%22%3A2%2C%22_token%22%3A%227109575542%3Aef6Ytycxq4CfqCYFILGAN9rA8R4Sk1dA%3A622e2c3b39690056440d62e136422d40f0a70481c9ea652c2d6c181314df44b2%22%2C%22last_refreshed%22%3A1537714456.3288357258%7D'
        }
        self.session.headers.update(headers)

    def run(self):
        brand_url = "%s/%s/" % (self.endpoint, self.brand)
        r = self.session.get(brand_url)
        if r.status_code != 200:
            return {"status": None, "message": "Bad Response for Brand User."}
        self.queryid = self.find_post_query_id(r)
        if self.queryid is None:
            return {"status": None, "message": "Invalid Brand Query Hash."}
        brand_user = self.get_profile(r)
        if brand_user is None:
            return {"status": None, "message": "Cookies/Response Error at Brand processing."}
        if brand_user.is_private is True:
            return {"status": None, "message": "Brand profiles are private"}
        return self.get_contents(brand_user)

    def get_contents(self, user):
        if self.is_last_post_id == True:
            return self.get_json(user.contents)
        params = {
            'query_hash': self.queryid,
            'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, user.end_cursor)
        }
        while True:
            r = self.session.get(
                'https://www.instagram.com/graphql/query/', params=params)
            edges = r.json()
            if edges["status"] == "fail":
                return {"status": False, "message": edges["message"]}

            for node in edges["data"]["user"]["edge_owner_to_timeline_media"]["edges"]:
                if len(node["node"]["edge_media_to_caption"]["edges"]) != 0:
                    caption = node["node"]["edge_media_to_caption"][
                        "edges"][0]["node"]["text"]
                else:
                    caption = ""
                content = Content(
                    id="%s_%s" % (node["node"]["id"], user.id),
                    user={
                        "id": user.id,
                        "full_name": user.full_name,
                        "username": user.username,
                        "profile_picture": user.profile_pic_url
                    },
                    created_time=node["node"]["taken_at_timestamp"],
                    caption={
                        "id": node["node"]["id"],
                        "text": caption
                    },
                    likes={
                        "count": node["node"]["edge_media_preview_like"]["count"]
                    },
                    comments={
                        "count": node["node"]["edge_media_to_comment"]["count"]
                    },
                    type=("video", "image")[node["node"]["is_video"] == False],
                    link="https://www.instagram.com/p/%s/" % (
                        node["node"]["shortcode"]),
                    images={
                        "thumbnail": {
                            "width": node["node"]["thumbnail_resources"][0]["config_width"],
                            "height": node["node"]["thumbnail_resources"][0]["config_height"],
                            "url": node["node"]["thumbnail_resources"][0]["src"]
                        },
                        "low_resolution": {
                            "width": node["node"]["thumbnail_resources"][2]["config_width"],
                            "height": node["node"]["thumbnail_resources"][2]["config_height"],
                            "url": node["node"]["thumbnail_resources"][2]["src"]
                        },
                        "standard_resolution": {
                            "width": node["node"]["thumbnail_resources"][4]["config_width"],
                            "height": node["node"]["thumbnail_resources"][4]["config_height"],
                            "url": node["node"]["thumbnail_resources"][4]["src"]
                        }
                    }
                )
                if node["node"]["is_video"] is True:
                    if "video_url" in node["node"]:
                        video_url = node["node"]["video_url"]
                    else:
                        video_url = None
                    content.video_url = video_url

                print(len(user.contents), content)
                user.contents.append(content)
                if len(user.contents) >= 100 or content.id == self.last_post_id:
                    return self.get_json(user.contents[:100])

            has_next_page = edges["data"]["user"][
                "edge_owner_to_timeline_media"]["page_info"]["has_next_page"]
            if has_next_page:
                end_cursor = edges["data"]["user"][
                    "edge_owner_to_timeline_media"]["page_info"]["end_cursor"]
                params = {
                    'query_hash': self.queryid,
                    'variables': '{"id":"%s","first":25,"after":"%s"}' % (user.id, end_cursor)
                }
            else:
                break
            time.sleep(2)
        return self.get_json(user.contents)

    def get_json(self, cnts):
        ret_cnts = []
        for cnt in cnts:
            ret_cnts.append({
                'id': cnt.id,
                'user': cnt.user,
                'created_time': cnt.created_time,
                'caption': cnt.caption,
                'likes': cnt.likes,
                'comments': cnt.comments,
                'type': cnt.type,
                'link': cnt.link,
                'images': cnt.images,
                'video_url': cnt.video_url
            })

        return ret_cnts

    def find_post_query_id(self, r):
        js_url = re.search(
            "/static/bundles/base/ProfilePageContainer.js/(.*?)\.js", r.text, re.S | re.M)
        if js_url:
            js_link = "%s%s" % (self.endpoint, js_url.group(0))
            res = self.session.get(js_link)
            query_filter = re.search(
                "r\.pagination\}\,queryId\:\"(.*?)\"\,", res.text, re.S | re.M)

            if query_filter:
                qid1 = query_filter.group(1)
                return qid1
            else:
                return None
        else:
            return None

    def get_profile(self, r):
        sharedData = self.parse_shared_data(r.text)
        if sharedData == {}:
            return None

        t = html.fromstring(r.text)
        userid = sharedData["entry_data"][
            "ProfilePage"][0]["graphql"]["user"]["id"]
        username = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["username"]
        full_name = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["full_name"]
        is_verified = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["is_verified"]
        is_private = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["is_private"]
        profile_pic_url = sharedData["entry_data"]["ProfilePage"][
            0]["graphql"]["user"]["profile_pic_url"]
        # following = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]
        # followed = sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_followed_by"]["count"]

        user = User(id=userid, username=username)
        user.full_name = full_name
        user.is_private = is_private
        user.is_verified = is_private
        user.profile_pic_url = profile_pic_url

        if sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["page_info"]["has_next_page"] == True:
            user.end_cursor = sharedData["entry_data"]["ProfilePage"][0]["graphql"][
                "user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]

        for node in sharedData["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]:
            if len(node["node"]["edge_media_to_caption"]["edges"]) != 0:
                caption = node["node"]["edge_media_to_caption"][
                    "edges"][0]["node"]["text"]
            else:
                caption = ""
            content = Content(
                id="%s_%s" % (node["node"]["id"], userid),
                user={
                    "id": userid,
                    "full_name": full_name,
                    "username": username,
                    "profile_picture": profile_pic_url
                },
                created_time=node["node"]["taken_at_timestamp"],
                caption={
                    "id": node["node"]["id"],
                    "text": caption
                },
                likes={
                    "count": node["node"]["edge_media_preview_like"]["count"]
                },
                comments={
                    "count": node["node"]["edge_media_to_comment"]["count"]
                },
                type=("video", "image")[node["node"]["is_video"] == False],
                link="https://www.instagram.com/p/%s/" % (
                    node["node"]["shortcode"]),
                images={
                    "thumbnail": {
                        "width": node["node"]["thumbnail_resources"][0]["config_width"],
                        "height": node["node"]["thumbnail_resources"][0]["config_height"],
                        "url": node["node"]["thumbnail_resources"][0]["src"]
                    },
                    "low_resolution": {
                        "width": node["node"]["thumbnail_resources"][2]["config_width"],
                        "height": node["node"]["thumbnail_resources"][2]["config_height"],
                        "url": node["node"]["thumbnail_resources"][2]["src"]
                    },
                    "standard_resolution": {
                        "width": node["node"]["thumbnail_resources"][4]["config_width"],
                        "height": node["node"]["thumbnail_resources"][4]["config_height"],
                        "url": node["node"]["thumbnail_resources"][4]["src"]
                    }
                }
            )
            if node["node"]["is_video"] is True:
                if "video_url" in node["node"]:
                    video_url = node["node"]["video_url"]
                else:
                    video_url = None
                content.video_url = video_url
            
            
            if content.id == self.last_post_id:
                self.is_last_post_id == True
                break
            user.contents.append(content)
        return user

    def parse_shared_data(self, html_string):
        res = re.search("\>window\.\_sharedData = (.*?)\;\<",
                        html_string, re.S | re.M | re.I)
        if res:
            return json.loads(res.group(1))
        else:
            return {}


def contents(brand, last_post_id):
    api = InContentAPI(brand=brand, last_post_id=last_post_id)
    result = api.run()
    return result


def main(fan, brand):
    # fan = sys.argv[1]
    # brand = sys.argv[2]
    api = InstagramAPI(fan=fan, brand=brand)
    result = api.run()
    # print (result)
    return result


# if __name__ == '__main__':
#     fan = sys.argv[1]
#     brand = sys.argv[2]
#     main(fan, brand)
