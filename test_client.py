import asyncio

class TestClientProtocol(asyncio.Protocol):
    def __init__(self, message, loop):
        self.messages = messages
        self.loop = loop

    def connection_made(self, transport):
        for message in self.messages:
            transport.write(message.encode())
            print('Data sent: {!r}'.format(message))

    def data_received(self, data):
        print('Data received: {!r}'.format(data.decode()))

    def connection_lost(self, exc):
        print('Stop the event loop')
        self.loop.stop()

loop = asyncio.get_event_loop()
m1 = 'IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997\n'
m2 = 'WHATSAT kiwi.cs.ucla.edu 10 5\r\n'
m3 = 'kiwi.cs.ucla.edu 10 5\n'
m4 = 'IAMAT kiwi.cs. .edu 10 5\r\n'
m5 = 'IAMAT kiwi.cs.ucla.edu +34.068930+-118.445127 1520023934.918963997\r\n'
m6 = 'IAMAT kiwi.cs.ucla.edu +34.068930,118.445127 -12312.918963997\n'
m7 = 'WHATSAT kiwi.cs.ucla.edu -10 5\n'
m8 = 'WHATSAT kiwi.cs.ucla.edu 10 -5.2\n'
m9 = 'WHATSAT new_client.edu 10 1\n'
m10 = 'IAMAT new_client.edu +34.068930-118.445127 1520023934.918963997\n'
m11 = 'WHATSAT new_client.edu 10 1\n'

messages = [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11]

coro1 = loop.create_connection(lambda: TestClientProtocol(messages, loop),
                              '127.0.0.1', 11431)
loop.run_until_complete(
  coro1
)
loop.run_forever()
loop.close()
