import os, sys
from pathlib import Path
import damei as dm
import json
from ....version import __appname__
import time


logger = dm.getLogger('user_manager')

class PremisionLevel:
    NONE = 0
    PUBLIC = 1
    FREE = 1
    USER = 2  # 登录
    PLUS = 3  # 付费用户
    ADMIN = 4  # 管理员


class UserManager(object):

    def __init__(self, use_sso_auth=False) -> None:
        self._users_file = f'{Path.home()}/.{__appname__}/users.json'
        self._users_cookie_file = f'{Path.home()}/.{__appname__}/users_cookie.json'
        self._users = self.read_users_from_file()
        self._cookies = self.read_cookies_from_file()
        self._sso_auth = None  # 初始化为None，只有在使用sso_auth时才会初始化
        self.use_sso_auth = use_sso_auth

    @property
    def sso_auth(self):
        if self._sso_auth is None:
            from ...utils.sso_oauth import SSOAuth
            self._sso_auth = SSOAuth()
        return self._sso_auth

    def read_users_from_file(self):
        if not os.path.exists(self._users_file):
            os.makedirs(os.path.dirname(self._users_file), exist_ok=True)
            empty_dict = dict()
            self.save_users_to_file(empty_dict)
            return empty_dict
        else:
            with open(self._users_file, 'r') as f:
                return json.load(f)
            
    def read_cookies_from_file(self):
        file_path = self._users_cookie_file
        if not os.path.exists(file_path):   
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            empty_dict = dict()
            self.save_file(file_path, empty_dict)
            return empty_dict
        else:
            with open(file_path, 'r') as f:
                return json.load(f)
            
    def save_users_to_file(self, users):
        with open(self._users_file, 'w') as f:
            json.dump(users, f, indent=4)
            
    def save_file(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    @property
    def users(self):
        return self._users
    
    @property
    def cookies(self):
        return self._cookies
    
    def get_user_data(self, user):
        """
        与get_user_info的区别是，get_user_data不包含密码，并会补充一些信息，用于前端显示
        样例：
        {
        "username": "public",
        "phone": "13112345678",
        "phone_verified": True,
        "email": "zhangsan@example.com",
        "user_type": "free",
        "usage": 5,
        "limit": 10,
        "group": None,
        "group_admin": False,
        "group_members": None,
        }
        """
        user_info = self.users.get(user, {})
        # user_info.pop('password', None)

        # print('user_info', user_info)
        user_data = dict()
        user_data['username'] = user
        user_data['phone'] = user_info.get('phone', None)
        user_data['phone_verified'] = user_info.get('phone_verified', False)
        user_data['email'] = user_info.get('email', None)
        user_data['user_type'] = user_info.get('user_type', 'free')
        user_data['user_type'] = 'admin' if user_info.get('is_admin', False) else user_data['user_type']
        user_data['usage'] = user_info.get('usage', 0)
        user_data['limit'] = user_info.get('limit', 10)
        default_group = 'ihep' if user_info.get('auth_type', 'local') == 'sso' else ''
        user_data['group'] = user_info.get('group', default_group)
        user_data['group'] = user_data['group'] if isinstance(user_data['group'], str) else ', '.join(user_data['group'])
        user_data['own_group'] = user_info.get('own_group', None)
        if user_data['own_group'] is not None:
            user_data['group'] = user_data['own_group'] + '(own), ' + user_data['group']
        user_data['group_members'] = user_info.get('group_members', None)
        return user_data
    
    def get_user_info(self, user):
        return self.users[user]
    
    def add_user(self, user, password=None, **kwargs):
        one_user = dict()
        one_user['password'] = password
        one_user['auth_type'] = kwargs.get('auth_type', 'local')
        one_user.update(kwargs)
        self._users[user] = one_user
        # TODO: 保存到文件中
        self.save_users_to_file(self._users)

    def remove_user(self, user):
        del self._users[user]

    def verify_user(self, user, password, **kwargs):
        # logger.info(f'Try local auth. all users: {self._users}')
        use_sso_auth = kwargs.get('use_sso_auth', self.use_sso_auth)

        if user in self._users.keys():
            auth_type = self._users[user].get('auth_type', 'local')
            is_ok = self._users[user]['password'] == password
            if is_ok:
                return True, ''
            else:
                pass
                # return False, '密码错误'
                # if auth_type == 'sso' and use_sso_auth:
                #     return self.sso_verify_user(user, password, **kwargs)
        else:
            pass

        logger.info(f'Local auth failed, try sso auth.')
        if use_sso_auth:
            ok, msg = self.sso_verify_user(user, password, **kwargs)
            if ok:
                return True, ''
            else:
                return False, f'本地和统一认证用户均失败，请尝试注册。msg: {msg}'
        return False, '本地用户不存在'

    def sso_verify_user(self, user, password, **kwargs):
        ok, msg = self.sso_auth.verify_user(user, password)
        logger.debug(f'SSO auth result: {ok}, {msg}')
        if ok:
            # logger.info(f'{user} ssoauth verify user success!')
            # 在本地保存用户信息，下次直接使用本地验证
            if not self.is_exist(user):
                self.add_user(user, password, auth_type='sso')
            return True, ''
        else:
            # logger.info(f'{user} ssoauth verify user failed!')
            return False, msg
    
    def is_exist(self, user):
        return user in self._users.keys()
    
    def is_admin(self, user):
        if user not in self._users.keys():
            return False
        return self._users[user].get('is_admin', False)
    
    def is_plus(self, user):
        if user not in self._users.keys():
            return False
        if self.is_admin(user):  # admin一定是plus
            return True
        return self._users[user].get('is_plus', False)
    
    def is_sso_user(self, user):
        if user not in self._users.keys():
            return False
        return self._users[user].get('auth_type', 'local') == 'sso'

    def has_own_api_key(self, user):
        if user not in self._users.keys():
            return False
        return self._cookies[user].get('api_key', False)

    def get_cookie(self, user):
        return self._cookies.get(user, None)
    
    def write_cookie(self, user, **kwargs):
        if user not in self._users.keys():
            raise Exception(f'User {user} not exist!')
        if user not in self._cookies.keys():
            self._cookies[user] = dict()
        self._cookies[user].update(kwargs)
        logger.debug(f'Write cookie for user {user}: {self._cookies[user]}')
        self.save_file(self._users_cookie_file, self._cookies)

    def save_history(self, user, convo_id, one_entry):
        # logger.debug(f'Save history for user {user}: {one_entry}')
        if user not in self._users.keys():
            pass
        if user not in self._cookies.keys():
            self._cookies[user] = dict()
        if 'history_convos' not in self._cookies[user].keys():
            # print('history_convos not in cookies')
            self._cookies[user]['history_convos'] = dict()
        if convo_id not in self._cookies[user]['history_convos'].keys():
            # print('convo_id not in cookies')
            self._cookies[user]['history_convos'][convo_id] = list()
        # self._cookies[user]['history'].append(one_entry)
        # print(self._cookies[user]['history_convos'][convo_id])

        one_entry['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self._cookies[user]['history_convos'][convo_id].append(one_entry)
        self.save_file(self._users_cookie_file, self._cookies)

    def get_permission_level(self, user):
        if user not in self._users.keys():  # 未登录
            return 0
        elif user == 'public':  # public
            return 1
        else:
            if self.is_admin(user):  # admin
                return 4
            elif self.is_plus(user):  # plus
                return 3
            # elif self.is_sso_user(user):  # sso
                # """SSO用户视为plus用户"""
                # return 3
            elif self.has_own_api_key(user):  # 有自己的api key
                return 3
            else:
                return 2  # 登录
            
    def user_level(self, user):
        return self.get_permission_level(user)
    
    def user_level_str(self, user):
        level = self.get_permission_level(user)
        if level == 0:
            return '未登录'
        elif level == 1:
            return '公共'
        elif level == 2:
            return '登录'
        elif level == 3:
            return 'plus'
        elif level == 4:
            return '管理员'
        else:
            raise Exception(f'Unknown user level: {level}')
        

    def get_rate_limited(self, username):
        if username == None or username == 'public':
            a = 2
            msg = f'公共用户访问速率限制1条/秒，当前负载{a}条/秒，等等再试或请登录绑定独占Bot。'
            return True, msg
        else:
            return False, ''

        
        
        
