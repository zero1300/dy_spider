import requests
import os
import json
import time
import webview
from urllib.parse import urlparse
from loguru import logger

class Douyin(object):
    def __init__(self, target: str, limit: int = 0, v_web_id: id = ''):
        self.http = requests.Session()
        self.http.headers.clear()
        self.http.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 Edg/110.0.1587.46'
        })
        self.limit = limit
        self.verify_web_id = v_web_id
        self.url = self.url2redirect(target.strip())
        # 判断链接类型（user/video/challenge/music），取目标ID
        *_, self.type, self.id = urlparse(self.url).path.strip('/').split('/')
        self.down_path = os.path.join('.', '下载')
        if not os.path.exists(self.down_path): os.makedirs(self.down_path)
        self.has_more = True
        self.videosInfo = []  # 采集的信息列表
        self.videosDL = []  # 采集的下载列表
        self.over_num = 0

        # 初始化函数
        if not self.test_cookie():
            self.get_verify()
        self.get_target_info()
    
    def get_target_info(self):
        dic = {'user': ('sec_uid', 'nickname'), 'challenge': ('ch_id', 'cha_name'), 'music': ('music_id', 'title')}
        url = f'https://www.douyin.com/web/api/v2/user/info/?{dic["user"][0]}={self.id}'
        res = self.http.get(url)
        if res.content:
            res = res.json()
        else:
            self.quit("目标解析失败,程序退出")
        try:
            res = self.http.get(url).json()
            for key, value in res.items():
                if key.endswith('_info'):
                    self.info = value
                    self.down_path = os.path.join(self.down_path,
                                                  self.str2path(f'{self.type}_{value[dic[self.type][1]]}_{self.id}'))
                    break
        except:
            self.quit("目标解析失败,程序退出")

    @staticmethod
    def str2path(str: str):
        """
        把字符串转为Windows合法文件名
        """
        # 非法字符
        lst = ['\r', '\n', '\\', '/', ':', '*', '?', '"', '<', '>', '|', ' ']
        # 非法字符处理方式1
        for key in lst:
            str = str.replace(key, '_')
        # 非法字符处理方式2
        # str = str.translate(None, ''.join(lst))
        # 文件名+路径长度最大255，汉字*2，取80
        if len(str) > 80:
            str = str[:80]
        return str.strip()

    def quit(self, str):
        logger.error(str)
        exit()

    def url2redirect(self, url):
        """
        取302跳转地址
        短连接转长链接
        """
        r = self.http.head(url, allow_redirects=False)
        return r.headers.get('Location', url)

    def test_cookie(self, v_web_id=''):
        if self.verify_web_id:
            pass
        elif v_web_id:
            self.verify_web_id = v_web_id
        elif os.path.exists('./verify'):
            with open('./verify', 'r', encoding='utf-8') as f:
                self.verify_web_id = f.read()
        else:
            return False

        self.http.headers.update({'Cookie': 's_v_web_id=' + self.verify_web_id})
        res = self.http.get('https://www.douyin.com/web/api/v2/aweme/post/').content  # 检测cookie是否有效
        if res:  # 有返回结果，证明cookie未过期，直接销毁窗口，进入主程序
            logger.success(f'验证成功：{self.verify_web_id}')
            with open('./verify', 'w', encoding='utf-8') as f:
                f.write(self.verify_web_id)
            return True
        else:
            return False

    def get_verify(self):
        """
        手动过验证码
        """
        import ctypes
        user32 = ctypes.windll.user32
        w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        side = 1080 * 255 // h  # 窗口大小自适应系统缩放
        # if self.type == 'video':  # 单作品网页不显示验证码，但此cookie接口没数据，所以要用主页链接取验证码
        #     url = 'https://www.douyin.com/share/user/MS4wLjABAAAA-Hb-4F9Y2cX_D0VZapSrRQ71BarAcaE1AUDI5gkZBEY'  # 指定一处验证码可以通用
        # else:
        #     url = self.url
        # 单作品及私密账号页面不显示验证码，所以要指定主页链接取验证码
        url = 'https://www.douyin.com/share/user/MS4wLjABAAAA-Hb-4F9Y2cX_D0VZapSrRQ71BarAcaE1AUDI5gkZBEY'  # 指定一处验证码可以通用
        self.window = webview.create_window(
            # hidden=True,# 4.0.2 bug已修复，但是使用会闪黑框，效果还不如现在，没必要改了
            minimized=True,  # 最小化
            frameless=True,  # 无边框
            width=side,
            height=side,  # 1080p：无框高255；125%：无框高315，框高40
            title='请手动过验证码',
            url=url  # 每次使用目标URL获取验证码，会出现两个域名，短期可能需要两次验证
        )

        webview.start(
            func=self.__webview_start,
            private_mode=False,
            user_agent=
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 Edg/110.0.1587.46'
            # 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        )
    
    def __webview_start(self):
        logger.info('验证码加载中...')
        self.window.hide()
        self.verify_web_id = ''
        while not self.verify_web_id:
            for c in self.window.get_cookies():
                if c.get('s_v_web_id'):
                    self.verify_web_id = c.get('s_v_web_id').value
                    break
            time.sleep(0.5)
        if self.test_cookie():
            self.window.destroy()  # 销毁验证码窗口
            return
        self.window.show()  # 显示验证码窗口
        time.sleep(0.5)
        self.window.restore()  # 显示验证码窗口，从最小化恢复
        for i in range(60 * 2):
            if self.test_cookie():
                self.window.destroy()  # 销毁验证码窗口
                return
            else:
                if i % 2 == 0: logger.info(f'请在 {60-i//2}秒 之内通过验证')
                time.sleep(0.5)
        self.window.destroy()  # 销毁验证码窗口
        self.quit('验证失败，程序退出。')

    def test_cookie(self, v_web_id=''):
        """
        测试cookie有效性
        """
        if self.verify_web_id:
            pass
        elif v_web_id:
            self.verify_web_id = v_web_id
        elif os.path.exists('./verify'):
            with open('./verify', 'r', encoding='utf-8') as f:
                self.verify_web_id = f.read()
        else:
            return False

        self.http.headers.update({'Cookie': 's_v_web_id=' + self.verify_web_id})
        res = self.http.get('https://www.douyin.com/web/api/v2/aweme/post/').content  # 检测cookie是否有效
        if res:  # 有返回结果，证明cookie未过期，直接销毁窗口，进入主程序
            logger.success(f'验证成功：{self.verify_web_id}')
            with open('./verify', 'w', encoding='utf-8') as f:
                f.write(self.verify_web_id)
            return True
        else:
            return False

    def download(self):
        filename = f'{self.down_path}.txt'
        if os.path.exists(filename):
            command = f"aria2c.exe -c --console-log-level warn -d {self.down_path} -i {filename}"
            os.system(command)  # system有输出，阻塞
        

    def __append_videos(self, aweme_list):
        """
        数据入库
        """
        for item in aweme_list:
            if self.limit and len(self.videosDL) - self.over_num - self.limit >= 0:
                # 如果给出了限制采集数目，直接退出循环
                # self.videosL = self.videosL[:self.limit + self.over_num]  # 超出的删除
                logger.info(f'已达到限制数量：{len(self.videosDL)-self.over_num}')
                break

            # ===== 收集视频信息 =====
            id = item['aweme_id']
            images = item.get('images')
            vid = item['video'].get('vid')
            desc = self.str2path(item['desc'])
            info = item.get('statistics', {'aweme_id': id})
            info.pop('play_count', '')  # 播放量只返回0，不保存
            info['desc'] = desc
            info['cover'] = item['video']['origin_cover']['url_list'][0]
            if item.get('music'):
                info['music_title'] = self.str2path(item['music']['title'])
                info['music_play_url'] = item['music']['play_url']['url_list'][0]
            hashtags = item.get('text_extra')
            if hashtags:
                info['hashtags'] = [{
                    'hashtag_id': hashtag['hashtag_id'],
                    'hashtag_name': hashtag['hashtag_name']
                } for hashtag in hashtags]
            if vid:  # 视频
                filename = f'{id}_{desc}.mp4'
                down_path = self.down_path
                download_addr = item['video'].get('download_addr')
                if download_addr:
                    download_addr = download_addr['url_list'][0].replace('ratio=540p', 'ratio=1080p').replace(
                        'ratio=720p', 'ratio=1080p').replace('watermark=1', 'watermark=0')  # 去水印+高清
                else:
                    download_addr = item['video']['play_addr']['url_list'][0].replace('/playwm/', '/play/')  # 高清
                self.videosDL.append(f'{download_addr}\n\tdir={down_path}\n\tout={filename}\n')  # 用于下载
                info['download_addr'] = download_addr
                self.videosInfo.append(info)  # 用于保存信息
            elif images:  # 图集作品
                download_addrs = []
                for index, image in enumerate(images):
                    down_path = os.path.join(self.down_path, f'{id}_{desc}')
                    download_addr = image['url_list'][-1]  # 最后一个是jpeg格式，其他的是heic格式
                    filename = urlparse(download_addr).path  # 以防格式变化，直接从网址提取后缀
                    suffix = filename[filename.rindex('.'):]
                    filename = f'{id}_{index + 1}{suffix}'
                    self.videosDL.append(f'{download_addr}\n\tdir={down_path}\n\tout={filename}\n')  # 用于下载
                    download_addrs.append(download_addr)
                info['download_addr'] = download_addrs
                self.videosInfo.append(info)  # 用于保存信息
                self.over_num += len(images) - 1
            else:  # 作品列表中有图集
                i_list = self.parse(id)
                if i_list and i_list[0].get('images'):
                    self.__append_videos(i_list)
                else:
                    logger.error('图集作品解析出错')

        logger.info(f'采集中，已采集到{len(self.videosDL)-self.over_num}条结果')

    # 生成 Aria 下载文件
    def crawl(self):
        cursor = 0
        retry = 0
        max_retry = 10
        dic = {
            'user': ('max_cursor', 'sec_uid', 'aweme/post'),
            'like': ('max_cursor', 'sec_uid', 'aweme/like'),
            'challenge': ('cursor', 'ch_id', 'challenge/aweme'),
            'music': ('cursor', 'music_id', 'music/list/aweme')
        }
        url = f'https://www.douyin.com/web/api/v2/{dic["user"][2]}/'

        while self.has_more:
            params = {dic["user"][1]: self.id, "count": "20", dic["user"][0]: cursor}
            res = self.http.get(url, params=params).json()
            cursor = res.get(dic[self.type][0])
            self.has_more = res.get('has_more')
            aweme_list = res.get('aweme_list')
            if aweme_list:
                self.__append_videos(aweme_list)
            if self.videosDL:
                logger.success(f'采集完成，共采集到{len(self.videosDL)-self.over_num}条结果')
                with open(f'{self.down_path}.txt', 'w', encoding='utf-8') as f:  # 保存为Aria下载文件
                    f.writelines(self.videosDL)

        
        
# lemit:下载视频数量
# d = Douyin("https://www.douyin.com/user/MS4wLjABAAAA_PdqQHLg_zwyoE8Cpd-tfSUKE6Ia6i9kvvp97xDY3KM?vid=7096062416236088589", limit=5)
# 获取文件下载地址
# d.crawl()
# 开始下载
# a.download()
