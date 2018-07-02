import asyncio, aiohttp, os, logging, sys, functools, datetime, time, json, re, config

class PropagationProtocol(asyncio.Protocol):
  def __init__(self, message, recipient): 
    self.message = message
    self.recipient = recipient

  def connection_made(self, transport):
    self.transport = transport
    self.transport.write(self.message.encode())

  def connection_lost(self, transport):
    self.transport.close() 

class ServerClientProtocol(asyncio.Protocol):
  client_locations = {}
  def __init__(self, name):
    self.name = name

  def connection_made(self, transport):
    peername = transport.get_extra_info('peername')
    logger.info('Connection from {}'.format(peername))
    self.peername = peername
    self.transport = transport

  def data_received(self, data):
    all_messages = data.decode()
    logger.info('Data received: {!r}'.format(all_messages))
    all_messages = all_messages.replace('\r\n', '\n')
    all_messages_lst = all_messages.split('\n')[:-1]
    for message in all_messages_lst:
      message_lst = message.split(' ')
      if message_lst[0]=='IAMAT':
        self.handle_IAMAT(message_lst)
      elif message_lst[0]=='WHATSAT':
        self.handle_WHATSAT(message_lst)
      elif message_lst[0]=='AT':
        self.handle_AT(message_lst)
      else:
        error_message = '? ' + message
        self.transport.write(error_message.encode())
        logger.info('Sent error response: ' + error_message) 

  # Handle IAMAT Request from client
  # Ex: IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997
  def handle_IAMAT(self, message_lst):
    message = ' '.join(message_lst)
    if len(message_lst)!=4 or not self.check_IAMAT(message_lst):
      error_message = '? ' + message
      self.transport.write(error_message.encode())
      logger.info('Sent error response: ' + error_message) 
      return

    client = message_lst[1]
    time_difference = time.time() - float(message_lst[3])
    if time_difference>0:
        time_difference='+'+str(time_difference)[0:11]
    else:
        time_difference='-'+str(time_difference)[0:11]
    client_location = 'AT ' + self.name + ' ' + time_difference + ' ' + ' '.join(message_lst[1:])
    AT_message = 'AT ' + self.name + ' ' + time_difference + ' ' + ' '.join(message_lst[1:]) + ' ' + self.name + '\n'

    ServerClientProtocol.client_locations[client] = client_location
    logger.info('Updated {} location'.format(client))
    self.transport.write(AT_message.encode())
    self.flood(AT_message)

  def check_IAMAT(self, message_lst):
    lat, lon = self.parse_lat_lon(message_lst[2])
    # Parse timestamp
    time_str = message_lst[3]
    # Validate lat, long, timestamp
    try:
      lat = float(lat)
      lon = float(lon)
      time = float(time_str)
      datetime.datetime.utcfromtimestamp(time)
      if lat>90 or lat<-90 or lon>180 or lon<-180: 
        return False
    except ValueError:
      return False
    return True

  def parse_lat_lon(self, lat_lon_str):
    # Parse latitude, longitude
    lat = lat_lon_str[0]
    lon = ''
    tmp = lat_lon_str[1:]
    if '+' in tmp:
      tmp2 = tmp.split('+')
      lat+=tmp2[0]
      lon='+' + tmp2[1]
    elif '-' in tmp:
      tmp2 = tmp.split('-')
      lat+=tmp2[0]
      lon='-' + tmp2[1]
    return (lat, lon)
    

  # Handle WHATSAT request from client
  # Ex: WHATSAT kiwi.cs.ucla.edu 10 5
  def handle_WHATSAT(self, message_lst):
    message = ' '.join(message_lst)
    if len(message_lst)!=4 or not self.check_WHATSAT(message_lst):
      error_message = '? ' + message
      self.transport.write(error_message.encode())
      logger.info('Sent error response: ' + error_message) 
      return

    try:
      client = message_lst[1]
      client_location = ServerClientProtocol.client_locations[client]
      (lat, lon) = self.parse_lat_lon(client_location.split(' ')[4])
      lat_lon_str = lat + ',' + lon 
      radius_str = str(1000*int(message_lst[2])) 
    except KeyError:
      error_message = '? ' + message
      self.transport.write(error_message.encode())
      logger.info('Error: unknown location for client ' + message_lst[1] + ' sent error response: ' + error_message) 
      return
    future = loop.create_task(self.fetch_places(lat_lon_str, radius_str))
    future.add_done_callback(functools.partial(self.handle_places_resp, message_lst=message_lst))

  def check_WHATSAT(self, message_lst):
    try:
      radius = float(message_lst[2])
      n_items = int(message_lst[3])
      if radius<0 or radius>50:
        return False
      elif n_items<0 or n_items>20:
        return False
    except ValueError:
      return False
    return True

  async def fetch_places(self, lat_lon_str, radius_str):
    # use aiohttp to fetch from Google Places API
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=' + lat_lon_str + '&radius=' + radius_str + '&&key=' + config.API_KEY
    async with aiohttp.ClientSession(loop=loop) as session:
      async with session.get(url) as resp:
        return await resp.text()

  def handle_places_resp(self, future, message_lst):
    logger.info('Received location information')

    client = message_lst[1]
    n_items = int(message_lst[3])

    resp_text = future.result().rstrip()
    # Remove trailing newlines
    resp_text = resp_text.rstrip()
    # Replace double or more newlines with one
    resp_text = re.sub(r'\n+', '\n',resp_text)

    resp_dict = json.loads(resp_text)
    results = resp_dict['results']
    restricted_results = results[:n_items]
    restricted_resp = resp_dict.copy()
    restricted_resp['results'] = restricted_results

    AT_message = ServerClientProtocol.client_locations[client] + '\n' + json.dumps(restricted_resp, indent=2) + '\n\n'

    self.transport.write(AT_message.encode())
    logger.info('Sent location information to {}'.format(client))
    
  # Handle AT message
  # Ex: AT Goloman +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997 <received servers>
  def handle_AT(self, message_lst):
    client = message_lst[3]
    location_str = message_lst[4]
    new_timestamp_str = message_lst[5]
    new_timestamp = float(new_timestamp_str)

    new_client_location = ' '.join(message_lst[:6])
    try:
        # only update if current timestamp < new timestamp
        client_location = ServerClientProtocol.client_locations[client]
        curr_timestamp = float(client_location.split(' ')[5]) 
        if new_timestamp>curr_timestamp:
            ServerClientProtocol.client_locations[client] = new_client_location
    except KeyError:
        ServerClientProtocol.client_locations[client] = new_client_location

    AT_message = ' '.join(message_lst) + ' ' + self.name + '\n'
    self.flood(AT_message)

  def flood(self, message):
    # Check if neighboring server has already received
    already_received = message.replace('\n', '').split(' ')[5:]
    for recipient in config.COMMUNICATION_PROTOCOL[self.name]:
      if recipient not in already_received:
        logger.info('Sent to {}: {!r}'.format(recipient, message))
        propagation_coro = loop.create_connection(lambda: PropagationProtocol(message, recipient), config.IP, config.PORTS[recipient])
        loop.create_task(propagation_coro)

  def connection_lost(self, exc):
    logger.info('Closed connection')
    self.transport.close() 

# Handle all exceptions
def exception_handler(loop, context):
  if 'exception' in context: 
    if isinstance(context['exception'], ConnectionRefusedError):
      logger.info('Error: neighboring server down')
    else:
      logger.info('Error: ' + str(context['exception']))
  else:
      logger.info('Error: ' + str(context))

if __name__ == '__main__':
  if len(sys.argv)!=2:
    print('Usage: python3 server.py <server_name>')
    exit(1)
  server_name = sys.argv[1]
  if server_name not in config.SERVERS:
    print('Error: invalid server name')
    exit(1)
  port = config.PORTS[server_name]

  # Setup logging 
  if not os.path.exists('./logs'):
    os.mkdir('./logs')
  logger = logging.getLogger(server_name)
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler('./logs/' + server_name + '.log')
  fh.setLevel(logging.DEBUG)
  # create formatter and add it to the handlers
  formatter = logging.Formatter('%(message)s')
  fh.setFormatter(formatter)
  # add the handlers to the logger
  logger.addHandler(fh)
  # Create server
  loop = asyncio.get_event_loop()
  loop.set_exception_handler(exception_handler)
  coro = loop.create_server(lambda: ServerClientProtocol(server_name), config.IP, port)
  server = loop.run_until_complete(coro)

  # Serve requests until Ctrl+C is pressed
  logger.info(server_name + ' serving on {}'.format(server.sockets[0].getsockname()))
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    pass

  # Close the server
  server.close()
  loop.run_until_complete(server.wait_closed())
  loop.close()
