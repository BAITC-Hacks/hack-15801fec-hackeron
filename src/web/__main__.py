import argparse

from .server import run

parser = argparse.ArgumentParser(description="Локальный веб-интерфейс симулятора")
parser.add_argument("--host", default="127.0.0.1", help="адрес для прослушивания")
parser.add_argument("--port", default=8000, type=int, help="порт (по умолчанию: 8000)")
arguments = parser.parse_args()
run(arguments.host, arguments.port)
