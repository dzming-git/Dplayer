# -*- coding: utf-8 -*-
"""
NodeManager Flask集成示例

这个文件展示如何将NodeManager集成到Flask应用。
"""

from flask import Flask, jsonify
from src.common.libweb import NodeManager, FlaskAdapter, register_all_routes


def create_app():
    """
    创建集成了NodeManager的Flask应用

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    # 创建NodeManager并注册所有路由
    node_manager = NodeManager()
    register_all_routes(node_manager)

    # 创建Flask适配器并注册到Flask
    adapter = FlaskAdapter(node_manager)
    adapter.register_to_flask(app)

    return app


# 传统Flask路由仍然可以正常工作
def create_dual_app():
    """
    创建双轨模式的Flask应用（NodeManager + 传统路由）

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    # 1. NodeManager路由
    node_manager = NodeManager()
    register_all_routes(node_manager)

    # 创建通用处理器处理所有NodeManager路由
    adapter = FlaskAdapter(node_manager)

    # 2. 传统Flask路由（仍然有效）
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Dplayer API',
            'mode': 'dual',
            'node_routes': len(node_manager.get_registered_routes()),
            'endpoints': {
                'api': '/api/*',
                'health': '/health',
                'status': '/api/status'
            }
        })

    @app.route('/traditional')
    def traditional():
        return jsonify({
            'message': 'This is a traditional Flask route',
            'node_manager_routes': len(node_manager.get_registered_routes())
        })

    # 注册NodeManager的通用处理器
    # 注意：需要为每个路由单独注册，这里简化处理
    routes = node_manager.get_registered_routes()
    for route in routes:
        path = route['path']
        methods = [route['method']]
        handler = adapter.create_request_handler()
        app.add_url_rule(path, view_func=handler, methods=methods)

    return app


if __name__ == '__main__':
    # 示例运行
    app = create_dual_app()
    print("Starting Flask app with NodeManager...")
    print("Routes registered:", len(app.url_map._rules))
    app.run(host='0.0.0.0', port=5000, debug=True)
