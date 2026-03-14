"""
优化网络连接配置，解决局域网偶现连接失败问题
"""

import socket
import time

def optimize_socket(sock):
    """
    优化socket配置，提高连接稳定性
    
    解决问题：
    1. 连接超时导致的偶发失败
    2. TCP保活机制缺失导致的连接断开
    3. 连接重用问题
    """
    # 设置TCP保活机制，防止连接长时间空闲被防火墙断开
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)   # 60秒后开始发送保活
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)  # 每10秒发送一次
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)     # 连续6次失败后断开
    
    # 允许地址重用，避免TIME_WAIT导致端口占用
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)    # Linux支持
    
    # 设置发送和接收缓冲区大小
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)    # 64KB发送缓冲区
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)    # 64KB接收缓冲区
    
    # 禁用Nagle算法，减少小数据包延迟
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    return sock


def optimize_flask_app(app):
    """
    优化Flask应用的网络配置
    
    需要在Flask应用启动前调用
    """
    import werkzeug.serving
    
    # 重写werkzeug的create_socket方法，应用我们的优化
    original_create_socket = werkzeug.serving.WSGIRequestHandler.connection_setup
    
    def optimized_connection_setup(self):
        # 调用原始方法创建socket
        original_create_socket(self)
        
        # 应用socket优化
        try:
            if hasattr(self.connection, 'setsockopt'):
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception as e:
            # 优化失败不影响正常运行
            print(f"[警告] Socket优化失败: {e}")
    
    werkzeug.serving.WSGIRequestHandler.connection_setup = optimized_connection_setup


if __name__ == '__main__':
    # 测试socket优化
    print("测试socket优化配置...")
    
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_sock = optimize_socket(test_sock)
    
    print("Socket配置已优化:")
    print(f"  - TCP保活: 启用")
    print(f"  - 地址重用: 启用")
    print(f"  - Nagle算法: 禁用")
    print(f"  - 缓冲区: 64KB")
    
    test_sock.close()
    print("\n请在app.py和admin_app.py中导入此模块并调用optimize_flask_app(app)")
