# Spring 2018 CS131 Project - Proxy herd with asyncio
Name: Vishaal Agartha, UID: 804603234

### Constants
To see constants (servers, port mappings, etc.) look at `config.py`

### Running the servers
Execute the shell script:
```
./run.sh
```
Or, run a server individually
```
python3 server.py <server_name>
```

### Testing
Once the servers are launched run the test script:
```
python3 test_client.py
```
Currently, there are 11 messages stored in a list that will be sent one at a time to the server on port 11431 (Holiday).

Only messages 1, 2 and 10, 11 are valid right now. 

You can add/remove messages if you like.

Press Ctrl+C to stop the client and close the connection

### Logger
All logging output are stored in the `./logs` folder. Each server has a specific log specified by its id.
