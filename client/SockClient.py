import socket
import struct


class SockClient:
    """
    Client for communicating over sockets
    Uses the following packet format:
    | PACKET SIZE (32-bit unsigned integer, Little-Endian) | PAYLOAD |
    """
    def __init__(self, host: str, port: int):
        sock = socket.socket()
        self.addr = (host, port)
        self.sock = sock

    def connect(self) -> None:
        self.sock.connect(self.addr)

    def send(self, msg: str) -> None:
        encoded_msg = msg.encode()
        size = len(encoded_msg)
        packet = struct.pack(f"<I{size}s", size, encoded_msg)
        self.sock.send(packet)

    def recv(self) -> str:
        header, _ancdata, _flags, _addr = self.sock.recvmsg(4)
        remaining_size, = struct.unpack("<I", header)
        msg = b""
        while remaining_size > 0:
            recvd, _ancdata, _flags, _addr = self.sock.recvmsg(remaining_size)
            remaining_size -= len(recvd)
            msg += recvd
        return msg.decode()


if __name__ == "__main__":
    client = SockClient("127.0.0.1", 1234)
    client.connect()
    print(client.recv())
