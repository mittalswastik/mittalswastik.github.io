import socket
import threading
import time
import json
import sys
import select

filename = ''
mss = 0
bytesadd = 0
bytesread = 0

counter = -1
send_flag = False
packet = {}
time_data = list()

servers_list = list()


def carry_around_add(a, b):

    c = a + b
    return (c & 0xffff) + (c >> 16)

#calculates checsum in int
def checksum(prev,data):

    # Force data into 16 bit chunks for checksum
    # print("checksum values are")

	if (len(data) % 2) != 0:
		data += "0".encode('utf-8')
	
	s = prev

	for i in range(0, len(data), 2):
		w = data[i] + (data[i+1] << 8)
		s = carry_around_add(s, w)
    
	return s

def rdt_send(send_details):

	global counter
	global bytesread
	# print("here\n")
	# print((send_details['packet']['header']['checksum']).to_bytes(2,'big'))
	clientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	# send_data = json.dumps(send_details['packet']).encode('utf-8')
	# print(send_details['server']['ip'])
	send_data = bytearray(b'')
	# print("checksum\n")
	# print((send_details['packet']['header']['dataid']).to_bytes(2,'big'))
	# print((send_details['packet']['header']['checksum']).to_bytes(2,'big'))
	# print("below are integer checksum and dataid\n")
	# print(send_details['packet']['header']['checksum'])
	# print(send_details['packet']['header']['dataid'])
	sendseqno = (send_details['packet']['header']['seqno']).to_bytes(4,'big')
	# print("below is seqno in bytes\n")
	# print((send_details['packet']['header']['seqno']).to_bytes(4,'big'))
	sendchecksum = (send_details['packet']['header']['checksum']).to_bytes(2,'big')
	senddataid = (send_details['packet']['header']['dataid']).to_bytes(2,'big')
	senddata = (send_details['packet']['data'])
	send_data.extend(sendseqno)
	send_data.extend(sendchecksum)
	send_data.extend(senddataid)
	send_data.extend(senddata)
	# print("data tp send below \n")
	# print(send_data)
	clientSocket.sendto(send_data,(send_details['server']['ip'],send_details['server']['port']))
	# print("data")
	clientSocket.setblocking(0)

	timeout_in_seconds = 0.05

	ready = select.select([clientSocket], [], [], timeout_in_seconds)
	if ready[0]:
	    data = clientSocket.recv(4096)	#creating non blocking socket
	    # data = data.decode('utf-8')
	    # data = json.loads(data)
	    ackno = int.from_bytes(data[0:4],'big')
	    #print("ack number is: ", ackno, "\n")
	    #print("bytesread is:", bytesread, "\n")
	    #if data['ackno'] != send_details['packet']['seqno']:
	    if ackno != send_details['packet']['header']['seqno']+1:
	    	# print("ackno and seqno is", ackno,send_details['packet']['header']['seqno']+bytesread+1,'\n')
	    	#print("Retransmitting because of unordered ack\n")
	    	time.sleep(1)
	    	rdt_send(send_details)
	    else :
	    	#print("Received valid ack\n")
	    	counter -= 1
	    	clientSocket.close()	

	else :
		print("Timeout, sequence no.: ", send_details['packet']['header']['seqno'],"\n")
		rdt_send(send_details) #retrasmit the packet

def utility():
	global filename
	global mss
	global servers_list

	values = sys.argv
	server1 = values[1]
	server2 = values[2]
	server3 = values[3]
	port = int(values[4])
	filename = values[5]
	mss = int(values[6])

	obj = {
		'ip' : server1,
		'port': port
	}

	servers_list.append(obj)

	obj = {
		'ip' : server2,
		'port': port
	}

	servers_list.append(obj)

	obj = {
		'ip' : server3,
		'port': port
	}

	servers_list.append(obj)

if __name__ == "__main__":

	utility()

	check = 0
	seqno = 0
	dataid = 21845	#0101010101010101
	data = b''
	counter = len(servers_list)
	filename = filename.rstrip()

	for i in range(0,1):
		f = open(filename,'rb')
		start = time.time()
		l = f.read(100)
		while(l):

			if not l:
				break

			data += l

			bytesread += len(l)

			if bytesread >= mss:
				check = checksum(check,l)
				csum = ~check & 0xffff
				counter = len(servers_list)
				for x in servers_list:
					send_details = {}
					packet[x['ip']] = {
						'header' : {
							'checksum': csum,
							'seqno': seqno,
							'dataid': dataid
						},

						'data' : data
					}

					send_details = {
						'packet' : packet[x['ip']],
						'server' : x
					}
					start_send = threading.Thread(target=rdt_send, args=(send_details,))
					start_send.daemon = True
					start_send.start()

				while counter!=0:
					b = 2
					#sleep loop

				bytesadd += len(data)
				#print("datasend = :", seqno+bytesread)	
				seqno = seqno+1#+bytesread
				bytesread = 0
				data = b''
				check = 0	

			else :
				check = checksum(check,l)

			prevdata = l
			l = f.read(100)

		print("length of the last segment is", len(prevdata), '\n')
		if len(prevdata) < mss:
			check = checksum(check,l)
			csum = ~check & 0xffff
			counter = len(servers_list)
			for x in servers_list:
				send_details = {}
				packet[x['ip']] = {
					'header' : {
						'checksum': csum,
						'seqno': seqno,
						'dataid': dataid
					},

					'data' : data
				}

				send_details = {
					'packet' : packet[x['ip']],
					'server' : x
				}
				start_send = threading.Thread(target=rdt_send, args=(send_details,))
				start_send.daemon = True
				start_send.start()

			while counter!=0:
				b = 2

		f.close()