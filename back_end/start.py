"""
服务启动脚本
提供便捷的启动方式和参数配置
"""
import argparse
import uvicorn
from config import settings


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Salotto Demo API 服务器")
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.HOST,
        help=f"服务器主机地址 (默认: {settings.HOST})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"服务器端口 (默认: {settings.PORT})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.DEBUG,
        help="启用热重载 (开发模式)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数量 (默认: 1)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="日志级别 (默认: info)"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    print("=" * 60)
    print("🚀 启动 Salotto Demo API 服务器")
    print("=" * 60)
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📚 API 文档: http://{args.host}:{args.port}/docs")
    print(f"📖 ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"🔧 热重载: {'启用' if args.reload else '禁用'}")
    print(f"👷 工作进程: {args.workers}")
    print(f"📝 日志级别: {args.log_level}")
    print("=" * 60)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # reload 模式只能单进程
        log_level=args.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()

