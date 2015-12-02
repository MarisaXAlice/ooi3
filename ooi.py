"""OOI3: Online Objects Integration version 3.0"""

import argparse
import asyncio
import os

import jinja2
from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from base import config
from handlers.frontend import FrontEndHandler
from handlers.service import ServiceHandler

parser = argparse.ArgumentParser(description='Online Objects Integration version 3.0')
parser.add_argument('-H', '--host', default='127.0.0.1',
                    help='The host of OOI server')
parser.add_argument('-p', '--port', type=int, default=9999,
                    help='The port of OOI server')

base_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    """OOI运行主函数。

    :return: none
    """

    # 解析命令行参数
    args = parser.parse_args()
    host = args.host
    port = args.port

    # 初始化事件循环
    loop = asyncio.get_event_loop()

    # 初始化请求处理器
    frontend = FrontEndHandler()
    service = ServiceHandler()

    # 定义会话中间件
    middlewares = [session_middleware(EncryptedCookieStorage(config.secret_key)), ]

    # 初始化应用
    app = web.Application(middlewares=middlewares, loop=loop)

    # 定义Jinja2模板位置
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(base_dir, 'templates')))

    # 给应用添加路由
    app.router.add_route('GET', '/', frontend.form)
    app.router.add_route('POST', '/', frontend.login)
    app.router.add_route('GET', '/kancolle', frontend.normal)
    app.router.add_route('POST', '/service/osapi', service.get_osapi)
    app.router.add_route('POST', '/service/flash', service.get_flash)
    app.router.add_static('/static', os.path.join(base_dir, 'static'))
    app_handlers = app.make_handler()

    # 启动OOI服务器
    server = loop.run_until_complete(loop.create_server(app_handlers, host, port))
    print('OOI serving on http://%s:%d' % server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app_handlers.finish_connections(1.0))
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()

if __name__ == '__main__':
    main()
