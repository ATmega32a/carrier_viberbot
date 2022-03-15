from viberbot import Api, BotConfiguration

from properties import auth_token

viber = Api(BotConfiguration(
    name='Оператор Елена',
    # avatar='http://smdtrans.ru/file/2019/06/21/shutterstock_532153933_min_1.jpg',
    avatar='https://pbs.twimg.com/profile_images/2504749497/z0735wcm50uhytsqtgr2_400x400.jpeg',
    auth_token=auth_token
))
