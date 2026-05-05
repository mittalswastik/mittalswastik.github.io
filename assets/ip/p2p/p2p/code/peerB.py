import socket
import threading
import time
import json

server = -1
flag = False
status = False
cookie = -1
rfc_list = {}
active_peerlist = list()

"""
	'hostname':
	'port_number':
"""

peer_details = {
	'ip' : "10.12.140.138",
	'port': 7003
}

rs_server = {
	'ip' : "10.12.140.245",
	'port' : 65423
}
# Funtions To Handle Communication With Peer

def sendRfcList(param,payload):
	#create a message type
	message = {
		'message_type' : "GetRfcList",
		'message_payload' : rfc_list
	}

	data_send = json.dumps(message).encode('utf-8')
	param['socket'].sendall(data_send)


def sendRfc(param,payload):
	global flag
	filename = str(payload['title'])
	f = open(filename,'rb')
	l = f.read(1024)
	while (l):
		param['socket'].send(l)
		#print('Sent ',repr(l))
		l = f.read(1024)
		if not l:
			break

	#print("End of sever")		
	f.close()
	flag = True
	#send the whole text file

def peerServerRecieve(param):
	data = param['socket'].recv(20000)
	data_receive = data.decode('utf-8')
	data_receive = json.loads(data_receive)

	if data_receive['message_type'] == "GetRfc":
		sendRfc(param,data_receive['message_payload'])
	elif data_receive['message_type'] == "GetRfcList":
		sendRfcList(param,data_receive['message_payload'])

	param['socket'].close()		


def peerServerAccept(param):
	global status
	global server
	while status: # till the time peer is alive
		newsocket, addr = server.accept()
		details = {
			'socket': newsocket,
			'addr': addr
		}
		peer_server = threading.Thread(target=peerServerRecieve, args=(details,))
		peer_server.daemon = True
		peer_server.start()

	server.close()	

def peerServer():
	print("Peer server Initiated")
	global server
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	server.bind((peer_details['ip'],peer_details['port']))
	server.listen(50)

def replyToGetRfc(socket,param):
	#store the rfc to local directory. Add the rfc as current peer rfc as well
	with open(str(param['rfc']['title']), 'wb') as f:
		while True:
			#print('receiving data...')
			#print('start')
			data = socket.recv(1024)
			#print('data=%s', (data))
			if  len(data) < 1024:
				f.write(data)
				break	
			# write data to a file
			f.write(data)	
			
	# on retrieving the rfc add the rfc to the host rfc index
	if peer_details['ip'] in rfc_list.keys():
		rfc_list[peer_details['ip']].append(param['rfc'])
	else :
		data = list()
		data.append(param['rfc'])
		rfc_list[peer_details['ip']] = data

	f.close()	

def replyToRfcList(param):
	for x in param:	# x is the key itself so no need of x.keys()[0]
		#print param[x]
		if x in rfc_list.keys():	# this handles the case where a hostname may not be in the rfc list of the peer
			for y in param[x]:
		 		if y not in rfc_list[x]:
		 			rfc_list[x].append(y)	# to avoid dupicate entries of rfc within single host

		else:
			rfc_list[x] = param[x] # if no entry for host present put the whole list in the rfc index

def connectToPeer(param):
	#print("Connection To Other Peer Initiated")
	#print(param)

	data_to_send = {
		'message_type' : param['message_type'],
		'message_payload' : param['message_payload']['rfc']
	}

	print("Connection To Peer Established To" + data_to_send['message_type'])
	print("sent message looks like")
	print(data_to_send)

	#print(param)

	data_to_send = json.dumps(data_to_send).encode('utf-8')
	#print(data_to_send)
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#print(param['message_payload']['connection_details']['port_number'])
	client.connect((param['message_payload']['connection_details']['hostname'],param['message_payload']['connection_details']['port_number']))
	client.sendall(data_to_send)
	if param['message_type'] == "GetRfc":
		print("Receiving the rfc data, Will not print this")
		replyToGetRfc(client,param['message_payload'])

	else :
		message = client.recv(20000)	# data received is much mode than just 4096 bytes
		message.decode('utf-8')
		message = json.loads(message)
		print("Received From Peer" + message[message_type])
		print("Received message looks like")
		print(message)
		replyToRfcList(message['message_payload'])
			
	# if receive -1 no data received
	client.close()

# Funtions To Handle Communication With Registration Server

def replyToRegister(message):
	global cookie
	cookie = message['cookie_number']

def replyToLeave(message):
	global status
	status = False
	print("Message from server " + message)

def replyToPquery(message):
	global active_peerlist
	#print(message)
	active_peerlist = message

def connectToRS(param):
	global cookie 

	print("Connection To Registration Server Initiated")
	print("Sending message below")
	print(param)
	data_to_send = json.dumps(param).encode('utf-8')
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect((rs_server['ip'],rs_server['port']))
	client.sendall(data_to_send)
	if param['message_type'] != "KeepAlive":
		message = client.recv(4096).decode('utf-8')
		message = json.loads(message)
		print("Message received for" + message['message_type'])
		print(message)
		if message['message_type'] == "Register":
	   		replyToRegister(message['message_payload'])
	   	elif message['message_type']=="Leave":
	   		replyToLeave(message['message_payload'])
	   	elif message['message_type']=="PQuery":
	   		replyToPquery(message['message_payload'])

	elif param['message_type'] == "KeepAlive":
		print("keep alive request sent")   		

	client.close()



def decrementTtlFromRfc(param):
	global status

	while status:
		for x in rfc_list.keys():
			if x != peer_details['ip']:
				for y in rfc_list[x]:
					y['ttl'] = y['ttl']-1

					if y['ttl'] <= 0:
						print("ttl value experired, resetting it to 7200")
						y['ttl'] = 7200

		time.sleep(5)	



def sendPeriodicAliveMsg(param):
	global status
	global cookie

	message = {
		'message_type' : "KeepAlive",
		'message_payload' : {
			'cookie_number' : cookie
		}
	}

	while status:
		connectToRS(message)
		time.sleep(5)

# Peer Program Loader

if __name__ == "__main__":
	

	with open("peerB.json",'r') as myfile:
		data = myfile.read()

	obj = json.loads(data)
	
	rs_server = obj[0]['rs_server']
	peer_details = obj[0]['peer_details']

	rfcstart = 1
	rfcs = list()
	for x in range(0,2):
		rfcs.append({
			'rfc_number' : rfcstart,
			'title': "rfc"+str(rfcstart)+".txt",
			'hostname' : peer_details['ip'],
			'ttl': 7200
		})

		rfcstart = rfcstart + 1

	# end specific to peer 0

	rfc_list[peer_details['ip']] = rfcs	

	peerServer()
	#will add 60 rfc

	global cookie
	global flag
	global status

	message = {
		'message_type': "Register",
		'message_payload': {
			'hostname': peer_details['ip'],
			'port': peer_details['port'],
			'cookie_number': cookie
		}
	}

	connectToRS(message)

	if cookie != -1:
		status = True

	if status:
		keep_alive_thread = threading.Thread(target=sendPeriodicAliveMsg, args=(1,))
		keep_alive_thread.daemon = True
		keep_alive_thread.start()
		decrement_rfc_ttl = threading.Thread(target=decrementTtlFromRfc, args=(1,))
		decrement_rfc_ttl.daemon = True
		decrement_rfc_ttl.start()
		start_server = threading.Thread(target=peerServerAccept, args=(1,))
		start_server.daemon = True
		start_server.start()

	while flag == False :
		a = 1
		#do nothing

	message = {
		'message_type' : "Leave",
		'message_payload' : {
			'cookie_number' : cookie
		}
	}

	connectToRS(message)

	print("done")

	#start_server.join()

	time.sleep(2)