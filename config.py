
# Google Place API Key
API_KEY = 'AIzaSyBaSvZ_yenf5MnlTzkl9evqX9vutccF2qc'

# Valid server ids
SERVERS = ['Goloman', 'Hands', 'Holiday', 'Welsh', 'Wilkes']

'''
Communication Protocol:
Goloman talks with Hands, Holiday and Wilkes.
Hands talks with Wilkes.
Holiday talks with Welsh and Wilkes.
'''
COMMUNICATION_PROTOCOL = {'Goloman': ['Hands', 'Holiday', 'Wilkes'],
        'Hands': ['Goloman', 'Wilkes'],
        'Holiday': ['Goloman', 'Welsh', 'Wilkes'],
        'Welsh': ['Holiday'],
        'Wilkes': ['Goloman', 'Hands', 'Holiday']}

# IP address
IP = '127.0.0.1'

# Port mappings
PORTS = {'Goloman': 11429,
         'Hands': 11430,
         'Holiday': 11431,
         'Welsh': 11432,
         'Wilkes': 11433}
