from socket import *
import time
import threading
import datetime
import json


# fuctions to be done ovr the list
peer_count = 1
peer_list = {}

rs_server = {
    'ip' :  "10.12.140.245",
    'port' : 65423
}

def registerPeer(param,message):
    global peer_count
    if (message['cookie_number'] == -1):
        peer_count = peer_count + 1
        new_peer = {
            'cookie_number' : peer_count,
            'hostname' : message['hostname'],
            'active_flag' : 1,
            'time_to_live' : 7200,
            'port_number' : message['port'],
            'peer_active_count' : 1,
            'latest_peer_active' : str(datetime)
        }

        # new_list.insert(peer_dict)
        peer_list[peer_count] = new_peer
        reply_message = {
            'message_type' : "Register",
            'message_payload' : {
                'cookie_number' : peer_count
            }
        }

        reply_message = json.dumps(reply_message).encode('utf-8')
        param['socket'].sendall(reply_message)

    else:
        peer_list[message['cookie_number']]['active_flag'] = 1
        peer_list[message['cookie_number']]['peer_active_count'] = peer_list[message['cookie_number']]['peer_active_count'] + 1
        
        reply_message = {
            'message_type' :"Register",
            'message_payload' : {
                'cookie_number' : peer_count
            }
        }

        reply_message = json.dumps(reply_message).encode('utf-8')
        param['socket'].sendall(reply_message)


def leave(param,message):
    peer_list[message['cookie_number']]['active_flag'] = 0
    reply_message = {
        'message_type':"Leave", 
        'message_payload':"succsessfully left"
    }
    reply_message = json.dumps(reply_message).encode('utf-8')
    param['socket'].send(reply_message)


def keepalive(param,message):
    cookie = message['cookie_number']
    item = peer_list[cookie]
    item['time_to_live'] = 7200
    resp_message_ka = {'message_type':"keepalive",'message_payload':"reset of timer done"}
    resp_message_ka = json.dumps(resp_message_ka)
    param['socket'].send(resp_message_ka.encode('utf-8'))


def pquery(param,message):
    response = list()
    temp = {}

    for i in peer_list:
        if (peer_list[i]["active_flag"] == 1):
            temp['hostname'] = peer_list[i]['hostname']
            temp['port_number'] = peer_list[i]['port_number']
            response.append(temp)
            temp = {}
    
    reply_message = {
        'message_type': "PQuery",
        'message_payload': response
    }
    
    reply_message = json.dumps(reply_message).encode('utf-8')
    param['socket'].send(reply_message)


def decrement():
    for x in peer_list:
        if peer_list[x]['time_to_live'] == 0:
            peer_list[x]['active_flag'] = 0
        else:
            peer_list[x]['time_to_live'] = peer_list[x]['time_to_live']-1

# timer which periodically after every 1 second, decreases the time to live of the peer by 1

def timer(params):
    while True:
        time.sleep(1)
        decrement()


def recievePeerRequest(param):
    receive_buffer = b''
    receive_buffer = param['socket'].recv(1024).decode('utf-8')
    message = json.loads(receive_buffer)
    print("Message Received From Peer")
    print(message)
    if (message['message_type'] == "Register"):
        registerPeer(param,message['message_payload'])
    elif (message['message_type'] == "Leave"):
        leave(param,message['message_payload'])
    elif (message['message_type'] == "PQuery"):
        pquery(param,message['message_payload'])
    elif (message['message_type'] == "KeepAlive"):
        keepalive(param,message['message_payload'])

    param['socket'].close()


if __name__ == "__main__":

    with open("rs.json",'r') as myfile:
        data = myfile.read()

    obj = json.loads(data)

    rs_server = obj[0]['rs_server']

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((rs_server['ip'], rs_server['port']))
    serverSocket.listen(50)
    print("Registeration Server Started")

    periodic_timer = threading.Thread(target=timer, args=(1,))  # 1 is just a random parameter here
    periodic_timer.daemon = True
    periodic_timer.start()

    while True:
        
        connectionSocket, addr = serverSocket.accept()
        connection_details = {
            'socket': connectionSocket,
            'addr': addr
        }

        rs_server = threading.Thread(target=recievePeerRequest, args=(connection_details,))
        rs_server.daemon = True  # using this thread starts running in the background
        rs_server.start()