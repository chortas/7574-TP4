import socket

NUMBER_SIZE = 8

def number_to_8_bytes(num):
    result = bytearray()
    for i in range(8):
        result.append(num & 255)
        num = num >> 8
    return bytes(result) #para que sea inmutable apartir de aca

def bytes_8_to_number(b):
    res = 0
    for i in range(8):
        try:
            res += b[i] << (i*8)
        except:
            return res
    return res

def send(sock, data):
  try:
    sock.sendall(data)
  except:
    raise RuntimeError("Socket connection failed unexpectedly while sending")

def recv(sock, size):
  data_received = bytearray()
  bytes_received = 0
  while bytes_received < size:
    chunk = sock.recv(size - bytes_received)
    if not chunk:
      raise RuntimeError("Socket connection failed unexpectedly while receiving")
    bytes_received += len(chunk)
    data_received.extend(chunk)
  return data_received

def close(sock):
  try:
    sock.shutdown(socket.SHUT_RDWR)
  except:
    pass
  sock.close()