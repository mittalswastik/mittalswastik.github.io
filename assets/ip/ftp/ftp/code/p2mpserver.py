from socket import *
import json
import random
import sys

filename = "output"  # input
p = 0.05  # input

# ack_packet= '1010101010101010'
ack_packet = 43690
mss = 15
serverPort = 0

def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)


# calculates checsum in int
def checksum(msg):
    #msg.encode('utf-8')
    # Force data into 16 bit chunks for checksum
    if (len(msg) % 2) != 0:
        msg += "0".encode('utf-8')

    s = 0
    for i in range(0, len(msg), 2):
        w = msg[i] + ((msg[i + 1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff


if __name__ == "__main__":

    values = sys.argv
    serverPort = int(values[1])
    filename = values[2]
    p = float(values[3])
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('0.0.0.0', serverPort))
    #print("The server is ready to receive")
    serverSeqno = 0
    prev_Seqno = 0
    file = open(filename + '.txt', 'wb')
    dataread = 0

    while True:
        message, clientAddress = serverSocket.recvfrom(1024)
        recMessage = message #.decode("utf-8")
        clientSeqnum= int.from_bytes(recMessage[0:4],'big')
        clientChecksum= int.from_bytes(recMessage[4:6],'big')
        clientpacketid= int.from_bytes(recMessage[6:8],'big')
        data=recMessage[8:]

        # print("receive messaged in bytes is", recMessage, '\n')

        # print('Client Seqence Num: ', clientSeqnum, '\n')
        # print('Server Sequence Num: ',serverSeqno, '\n')
        # print('size of data received:', sys.getsizeof(data), '\n')
        # print('Client Checksum: ', clientChecksum, '\n')
        # print('Client dataid: ', clientpacketid, '\n')
        # print('Data is: ', data, '\n')

        prev_checksum = 0
        randomprob = random.random()
        zero = 0

        if (serverSeqno == clientSeqnum):

            if (randomprob > p):  # probability
                serverChecksum = checksum(data)
                previous_checksum = serverChecksum
                # print('Server checksum:', serverChecksum)
                # print('previous checksum:', prev_checksum)
                # print('Client Checksum:', clientChecksum)
                if (clientChecksum == serverChecksum):    # can use carryaround add function to add the checksum
                    # print("client checksum", clientChecksum)

                    # print("server Checksum", serverChecksum)
        
                    # dataread += sys.getsizeof(data)
                    # print('Size of data is', dataread)
                    # serverSeqno =  dataread

                    serverSeqno += 1

                    # =str(serverSeqno).encode('utf-32')
                    # zeros_append=str(zero).encode('utf-16')
                    # ack_packet=str(ack_packet).encode('utf-16')

                    # returnSeqNo = '{0:032b}'.format(serverSeqno)
                    # zeros_append = '{0:016b}'.format(0)
                    # sendAck = returnSeqNo +zeros_append + ack_packet
                    # print('ACK: and address:',sendAck,clientAddress)

                    ackSeqno=serverSeqno.to_bytes(4,'big')
                    zerosappend=(0).to_bytes(2,'big')
                    ack_id=ack_packet.to_bytes(2,'big')
                    ack = bytearray(b'')
                    ack.extend(ackSeqno)
                    ack.extend(zerosappend)
                    ack.extend(ack_id)

                    serverSocket.sendto(ack, clientAddress)
                    file.write(data)
                    # print('Sent ACK with new sequence number')
                    # Seqence number logic??
                    prev_Seqno = serverSeqno
                    # serverSeqno= clientSeqnum+MSS
            else:
                print("Packet Loss, sequence number = ", clientSeqnum, '\n')
        else:
            # print("seqenuce number out of order")
            # sendAck = prev_Seqno +zeros_append + ack_packet
            ackSeqno = prev_Seqno.to_bytes(4, 'big')
            zerosappend = (0).to_bytes(2, 'big')
            ack_id = ack_packet.to_bytes(2, 'big')
            ack = ackSeqno + zerosappend + ack_id
            # print('ACK: ',sendAck)
            serverSocket.sendto(ack, clientAddress)
            #file.write(message.decode('utf-8'))
            #print('Sent ACK with previous sequence number')

    # use prev_Seqno to send back a ack packet

    file.close()
    serverSocket.close()