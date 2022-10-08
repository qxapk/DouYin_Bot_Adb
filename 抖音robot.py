#https://blog.csdn.net/weixin_42253753/article/details/122732070
#https://openapi.baidu.com/oauth/2.0/authorize?client_id=zQxXl54X488ktlGR1z3yK544jNIDqnVL&redirect_uri=oob&response_type=code&scope=netdisk
#https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&code=bae1a3b2cae415567475a19e921c71cb&client_id=zQxXl54X488ktlGR1z3yK544jNIDqnVL&client_secret=gSFqyb3DKf5zVx40mXMGPK0wzWG2bjya&redirect_uri=oob
import json, os, re,hashlib, requests,urllib.parse,sqlite3,time,urllib.request
from urllib.parse import urlencode
from tld import get_tld

class BaiDuWangPan():
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.app_name = '短视频收藏夹'
        self.app_key = ''  # Appkey
        self.secret_key = ''  # Secretkey
        self.precreate_api = 'https://pan.baidu.com/rest/2.0/xpan/file?'  # 预上传
        self.upload_api = 'https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?'  # 分片上传
        self.create_api = 'https://pan.baidu.com/rest/2.0/xpan/file?'  # 创建文件
        self.query_file_url = 'http://pan.baidu.com/rest/2.0/xpan/multimedia?'  # 查询文件信息
        self.get_token_url = 'https://openapi.baidu.com/oauth/2.0/token?'  # 获取token

    def get_refresh_token(self):
        """
        使用Refresh Token刷新以获得新的Access Token
        :param refresh_token: 必须参数，用于刷新Access Token用的Refresh Token。注意一个Refresh Token只能被用来刷新一次；
        :return:
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.app_key,
            "client_secret": self.secret_key
        }
        response = requests.post(self.get_token_url, data)
        res_data = json.loads(response.text)
        return {
            "error": res_data.get("error", None),
            "error_description": res_data.get("error_description", ''),
            "access_token": res_data.get("access_token", ''),
            "refresh_token": res_data.get("refresh_token", ''),
            "session_key": res_data.get("session_key", ''),
            "session_secret": res_data.get("session_secret", ''),
        }

    def precreate(self, file_path):
        """
        预上传
        请求参数rtype=0时，如果云端存在同名文件，此次调用会失败。
        云端文件重命名策略：假设云端已有文件为test.txt，新的名称为test(1).txt1, 当发现已有目录 /dir 时, 新创建的目录命名为：/dir(1) 。
        content-md5和slice-md5都不为空时，接口会判断云端是否已存在相同文件，如果存在，返回的return_type=2，代表直接上传成功，无需请求后面的分片上传和创建文件接口。
        :param file_path: 文件路径
        :return:
        更多黑科技，关注公众号：小千哥
        """
        hou = file_path.split('.')[-1]#文件后缀
        wj_name = file_path.split('/')[-1]
        remote_path = '/'+ self.app_name + '/'+hou+'/' + wj_name
        #print('hou:', hou, 'wj_name：', wj_name,'remote_path:',remote_path)
        size = os.path.getsize(file_path)
        block_list = []
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024 * 1024 * 4)
                if not data:
                    break
                file_md5 = hashlib.md5(data).hexdigest()
                block_list.append(file_md5)
        params = {
            'method': 'precreate',
            'access_token': self.access_token,
        }
        data = {
            'path': remote_path,
            'size': size,
            'isdir': 0,
            'autoinit': 1,
            'block_list': json.dumps(block_list)
        }
        api = self.precreate_api + urlencode(params)
        response = requests.post(api, data=data)
        res_data = json.loads(response.content)
        errno = res_data.get('errno', 0)
        if errno:
            raise
        return res_data.get('uploadid', ''), remote_path, size, block_list

    def upload(self, remote_path, uploadid, partseq, file_data):
        """
        分片上传
        普通用户单个分片大小固定为4MB（文件大小如果小于4MB，无需切片，直接上传即可），单文件总大小上限为4G。
        普通会员用户单个分片大小上限为16MB，单文件总大小上限为10G。
        超级会员用户单个分片大小上限为32MB，单文件总大小上限为20G。
        :param remote_path: 上传后使用的文件绝对路径
        :param uploadid: precreate接口下发的uploadid
        :param partseq: 文件分片的位置序号，从0开始，参考precreate接口返回的block_list
        :param file_data: 上传的文件内容
        :return:
        """
        data = {}
        files = [
            ('file', file_data)
        ]
        params = {
            'method': 'upload',
            'access_token': self.access_token,
            'path': remote_path,
            'type': 'tmpfile',
            'uploadid': uploadid,
            'partseq': partseq
        }
        api = self.upload_api + urlencode(params)
        response = requests.post(api, data=data, files=files)
        res_data = json.loads(response.content)
        errno = res_data.get('errno', 0)
        if errno:
            raise
        md5 = res_data.get('md5', '')
        return md5

    def create(self, remote_path, size, block_list, uploadid):
        """
        创建文件
        :param remote_path: 上传后使用的文件绝对路径
        :param size: 文件大小B
        :param block_list: 文件各分片MD5的json串，MD5对应superfile2返回的md5，且要按照序号顺序排列
        :param uploadid: uploadid
        :return:
        """
        params = {
            'method': 'create',
            'access_token': self.access_token,
        }
        api = self.create_api + urlencode(params)
        data = {
            'path': remote_path,
            'size': size,
            'isdir': 0,
            'uploadid': uploadid,
            'block_list': json.dumps(block_list)
        }
        response = requests.post(api, data=data)
        res_data = json.loads(response.content)
        errno = res_data.get('errno', 0)
        if errno:
            raise
        else:
            fs_id = res_data.get("fs_id", '')
            md5 = res_data.get("md5", '')
            server_filename = res_data.get("server_filename", '')
            category = res_data.get("category", 0)
            path = res_data.get("path", '')
            ctime = res_data.get("ctime", '')
            isdir = res_data.get("isdir", '')
            return fs_id, md5, server_filename, category, path, isdir

    def finall_update_file(self, file_path):
        #print("finall_update_file_file_path：",file_path)
        uploadid, remote_path, size, block_list = self.precreate(file_path)
        _block_list = []
        with open(file_path, 'rb') as f:
            i = 0
            while True:
                data = f.read(1024 * 1024 * 4)
                if not data:
                    break
                md5 = self.upload(remote_path, uploadid, i, data)
                _block_list.append(md5)
                i += 1
        fs_id, md5, server_filename, category, path, isdir = self.create(remote_path, size, _block_list, uploadid)

    def download_file(self, fs_id):
        """
        查询文件并下载
        先查询文件是否存在，若存在则返回文件下载地址(dlink)
        下载文件需要在下载地址拼上access_token
        :param fs_id: 文件id数组，数组中元素是uint64类型，数组大小上限是：100
        :return:
        """
        dlink = ''
        params = {
            "method": "filemetas",
            "access_token": self.access_token,
            "fsids": json.dumps([int(fs_id)]),
            "dlink": 1
        }
        api_url = self.query_file_url + urlencode(params)
        response = requests.get(api_url)
        res_data = json.loads(response.text)
        errmsg = res_data.get("errmsg", None)
        if errmsg == 'succ':
            res_list = res_data.get("list", [])
            if res_list:
                dlink = res_list[0].get('dlink', '')
            if dlink:
                return dlink + '&' + 'access_token={}'.format(self.access_token)
        else:
            raise

def download(url, filename):
    #更多黑科技，关注公众号：小千哥
    #print("Dow：",url,filename)
    try:
        urllib.request.urlretrieve(url, filename)
    except Exception as e:
        print('下载文件失败：',url,filename,e)
        download(url, filename)
def get(url):
    #更多黑科技，关注公众号：小千哥
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36 Core/1.77.85.400 QQBrowser/10.9.4610.400'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.content.decode()
    except requests.exceptions.Timeout:
        for i in range(1, 10):
            print('请求超时，第%s次重复请求' % i)
            response = requests.get(url, headers=headers,timeout=5)
            if response.status_code == 200:
                return response.content.decode()
    return -1  # 当所有请求都失败，返回  -1  ，此时有极大的可能是网络问题或IP被封。
def get_cdx(url):#重定向
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36 Core/1.77.85.400 QQBrowser/10.9.4610.400'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.url
    except requests.exceptions.Timeout:
        for i in range(1, 10):
            print('请求超时，第%s次重复请求' % i)
            response = requests.get(url, headers=headers,timeout=5)
            if response.status_code == 200:
                return response.url
    return -1  # 当所有请求都失败，返回  -1  ，此时有极大的可能是网络问题或IP被封。
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
def go_adb():
    # adb -s emulator-5670 kill-server  删除多余设备
    a = os.popen("adb devices").read()
    if a.find('127.0.0.1:5555') == -1:  #不存在
        b = os.popen("adb connect 127.0.0.1:5555").read()
        if a.find('127.0.0.1:5555') != -1:  # 存在
            os.popen("adb shell chmod 777 /data/data").read()
def qu_chu_url():
    go_adb()
    #更多黑科技，关注公众号：小千哥
    adb_a = os.popen(r"adb pull /data/data/my.maya.android/databases/78320872371_im.db-wal C:\Users\aabb\Desktop\duo_shan").read()
    adb_b = os.popen(r"adb pull /data/data/my.maya.android/databases/78320872371_im.db-shm C:\Users\aabb\Desktop\duo_shan").read()
    adb_c = os.popen(r"adb pull /data/data/my.maya.android/databases/78320872371_im.db C:\Users\aabb\Desktop\duo_shan").read()
    #print('a'+adb_a,'b'+adb_b,adb_c)

    conn = sqlite3.connect(r'C:\Users\aabb\Desktop\duo_shan\78320872371_im.db')  # 打开数据库
    conn.row_factory = dict_factory
    cour = conn.cursor()  # 创建游标
    cour.execute(r"SELECT * FROM `msg` where `conversation_id`='7149059490183168552'")
    output = cour.fetchall()
    for s, ku in enumerate(output):
        article = str(json.dumps(ku, ensure_ascii=False))
        f = open('dy_dow.txt', 'r', encoding='utf-8')
        text = str(f.readlines())
        f.close
        un = sqlite3.connect(r"C:\Users\aabb\Desktop\duo_shan\user_duo_shan.db")  # 打开数据库
        un.row_factory = dict_factory
        unc = un.cursor()
        unc.execute(r'SELECT * FROM `duo_shan` where `sender`="' + str(ku["sender"]) + '"')
        user_cha = unc.fetchall()  # 查
        if text.find(str(ku["msg_server_id"])) == -1:  # 新出现的消息


            #更多黑科技，关注公众号：小千哥
            qw = json.loads(ku['content'])
            if('text' in qw):
                ds_text = qw['text']
                print('有txt')
                if ds_text.find('昵称：') != -1 and ds_text.find('授权：') != -1:
                    print('txt符合')
                    b = ds_text.split('：')
                    name = b[1].split('，')[0]
                    url = 'https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&code='+b[2]+'&client_id=zQxXl54X488ktlGR1z3yK544jNIDqnVL&client_secret=gSFqyb3DKf5zVx40mXMGPK0wzWG2bjya&redirect_uri=oob'
                    print(url)
                    fan = get(url)
                    print(fan)
                    if str(fan).find('refresh_token') != -1 and str(fan).find('access_token') != -1:
                        fan_j = json.loads(fan)
                        refresh_token = fan_j['refresh_token']
                        access_token = fan_j['access_token']
                        print(refresh_token,access_token)


                        un2 = sqlite3.connect(r"C:\Users\aabb\Desktop\duo_shan\user_duo_shan.db")  # 打开数据库
                        un2.row_factory = dict_factory
                        unc2 = un2.cursor()
                        unc2.execute(r'SELECT * FROM `duo_shan` where `sender`="' + str(ku["sender"]) + '"')
                        user_cha = unc2.fetchall()  # 查
                        if (len(user_cha) == 0):#没有就创建
                            unc2.execute(r'INSERT INTO `duo_shan`(`sender`,`name`,`refresh_token`,`access_token`) VALUES ("'+str(ku["sender"])+'","'+ name +'","'+refresh_token+'","'+access_token+'")')
                        else:#有就编辑
                            unc2.execute(r'update `duo_shan` set `sender`="'+str(ku["sender"])+'",`name`="'+name+'",`refresh_token`="'+refresh_token+'",`access_token`="'+access_token+'" where `sender`="'+str(ku["sender"])+'"')
                        un2.commit()  # 提交数据-同步到数据库文件-增删改查，除了查询以外有需要进行提交
                        unc2.close()  # 关闭游标
                        un2.close()  # 关闭连接
                        print('有')




            if article.find('content_title') != -1 and article.find('itemId') != -1 and article.find('url_list') != -1:
                if (len(user_cha) != 0):
                    #print(user_cha[0])
                    #print(ku["msg_server_id"], ku["content"])
                    text = json.loads(ku["content"])
                    content_name = text['content_name']#作者名
                    content_name = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', "",content_name)  # 过滤字符
                    content_name = re.sub(u'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]+', "",content_name)  # 过滤表情
                    content_name = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "",content_name)  # 过滤字符
                    content_title = text['content_title']  # 标题
                    content_title = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', "",content_title)#过滤字符
                    content_title = re.sub(u'[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF]+', "", content_title)#过滤表情
                    content_title = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", content_title)#过滤字符
                    content_title = content_name + 'zn_nz' + content_title  # 标题
                    content_title = content_title.replace('\n', '').replace('\r', '')
                    cover_url = text['cover_url']['url_list'][0]#封面图
                    itemId = text['itemId']#视频id

                    refresh_token = user_cha[0]['refresh_token']
                    access_token = user_cha[0]['access_token']

                    jie_xi(itemId,content_title,cover_url,refresh_token,access_token)

            with open('dy_dow.txt', 'a', encoding='utf-8') as f:
                f.write(str(ku["msg_server_id"]) + ',')
        unc.close()  # 关闭游标
        un.close()  # 关闭连接

def jie_dy(item):
    fan = get('https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids='+item)
    fan_j = json.loads(fan)
    url = fan_j['item_list'][0]['video']['play_addr']['url_list'][0]
    url = re.compile(r'/playwm/').sub(r'/play/', url)  # 替换文本
    return url
def jie_xi(itemId,content_title,cover_url,refresh_token,access_token):
    print('进入jie_xi')
    #更多黑科技，关注公众号：小千哥
    c_url = jie_dy(itemId)
    #print('重定向之前的：',c_url,itemId)
    if c_url.count('http') == 2:#是图文就忽略！
        return ''

    c_url = get_cdx(c_url)#获取重定向之后的
    video_lu_mp4 = r'C:/Users/aabb/Desktop/video/' + content_title + '.mp4'
    video_lu_jpg = r'C:/Users/aabb/Desktop/video/' + content_title + '.jpg'
    print("开始下载：",video_lu_mp4,c_url)
    download(c_url, video_lu_mp4)
    download(cover_url, video_lu_jpg)

    # 百度网盘__上传
    b = BaiDuWangPan()
    b.access_token = access_token
    b.refresh_token = refresh_token

    print('百度云初始化完毕！')
    b.finall_update_file(video_lu_mp4)  # 上传
    b.finall_update_file(video_lu_jpg)  # 上传
    #print('成功：'+video_lu_mp4)

    os.remove(video_lu_mp4)# 删除单个文件
    os.remove(video_lu_jpg)# 删除单个文件




if __name__ == '__main__':
    while True:
        #授权，在抖音群，回复：
        #昵称：小千哥，授权：ea58b3d279fc5bad09ad3e294b3260fd
        # 将模拟器App系统目录文件虹吸到电脑，利用电脑的python读取
        qu_chu_url()
        #更多黑科技，关注公众号：小千哥
        time.sleep(3)

