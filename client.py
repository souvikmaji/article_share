import os
import pickle
import random
import socket
from _thread import *


# get file and save
def p2p_get_request(filename, peer_host, peer_upload_port):
    s = socket.socket()
    s.connect((peer_host, int(peer_upload_port)))
    data = p2p_request_message(filename, host)
    s.send(bytes(data, 'utf-8'))
    data_rec = pickle.loads(s.recv(1024 * 100))
    print("Data_rec", str(data_rec))
    status = data_rec[0].split()[0]
    if status == "200":
        current_path = os.getcwd()
        filename = current_path + "/" + filename
        my_data = data_rec[1]
        with open(filename, 'wb') as file:
            file.write(my_data)
        with open(filename, 'rb') as file:
            text = file.read()
            print(text)
    else:
        print("Data recieve failed")
    s.close()


# display p2p response message
def p2p_response_message(filename):
    current_path = os.getcwd()
    # filename = current_path + '/' + filename
    if os.path.exists(filename):
        status = "200"
        phrase = "OK"
        txt = open(filename, "rb")
        data = txt.read()
        content_length = os.path.getsize(filename)
        message = [status + " " + phrase + "\n" + "Content-Length: " + str(content_length) + "\n", data]
    else:
        status = "404"
        phrase = "Not Found"
        message = status + " " + phrase + "\n"
    return message


# send rfcs to peers
def send_file(conn, filename):
    txt = open(filename, "rb")
    data = txt.read(1024)
    while data:
        conn.send(data)
        data = txt.read(1024)
    s.close()


def recv_file(conn, filename):
    txt = open(filename, "wb")
    data = conn.recv(1024)
    while data:
        txt.write(data)
        data = conn.recv(1024)
    txt.close()


# display p2p request message
def p2p_request_message(file_name, host):
    message = "GET FILE: " + str(file_name) + " Host: " + str(host) + "\n"
    return message


# display p2s request message for ADD method
def p2s_add_message(host, port, title):  # for ADD
    message = "ADD\nHost: " + str(host) + "\n" + "Port: " + str(port) + "\n" \
                                                                        "Title: " + str(title) + "\n"
    return [message, host, port, title]


# display p2s request message for LOOKUP method
def p2s_lookup_message(host, port, title, get_or_lookup):  # LOOKUP method
    message = "LOOKUP\n" + \
              "Host: " + str(host) + "\n" \
                                     "Port: " + str(port) + "\n" \
                                                            "Title: " + str(title) + "\n"
    return [title, get_or_lookup]


# display p2s request message for LIST methods
def p2s_list_request(host, port):
    message = "LIST ALL\n" \
              "Host: " + str(host) + "\n" \
                                     "Port: " + str(port) + "\n"
    return message


# get the list of the local rfcs
def get_local_rfcs():
    rfcs_path = os.getcwd()
    rfc_files = [num for num in os.listdir(rfcs_path) if os.path.isfile(os.path.join(rfcs_path, num))]
    return rfc_files


# pass peer's hostname, port number and local file names in client
def peer_information():
    keys = ["Title"]
    rfcs_title = get_local_rfcs()
    rfcs_title = []
    for title in rfcs_title:
        entry = [title]
        dict_list_of_files.insert(0, dict(zip(keys, entry)))
    return [upload_port_num, dict_list_of_files]


upload_port_num = 65000 + random.randint(1, 500)  # upload port: 65000~65500
dict_list_of_files = []  # list of dictionaries of RFC numbers and Titles.
s = socket.socket()
host = "127.0.0.1"
port = 7734
s.connect((host, port))
data = pickle.dumps(peer_information())  # send all the peer information to server
s.send(data)
data = s.recv(1024)
print(data.decode('utf-8'))


def print_combined_list(dictionary_list, keys):
    for item in dictionary_list:
        print(' '.join([item[key] for key in keys]))


def get_user_input():
    # if key press, then close:
    user_input = input("> Enter ADD, LIST, LOOKUP, GET, or EXIT:  ")
    if user_input == "EXIT":
        data = pickle.dumps("EXIT")
        s.send(data)
        s.close()  # Close the socket when done

    elif user_input == "ADD":
        user_input_filename = input("> Enter filename: ")
        data = pickle.dumps(p2s_add_message(host, upload_port_num, user_input_filename))
        s.send(data)
        server_data = s.recv(1024)
        print(server_data.decode('utf-8'))
        get_user_input()

    elif user_input == "LIST":
        data = pickle.dumps(p2s_list_request(host, port))
        s.send(data)
        new_data = pickle.loads(s.recv(1024))
        print_combined_list(new_data[0], new_data[1])

        get_user_input()
    elif user_input == "GET":
        user_input_filename = input("> Enter the filename: ")
        data = pickle.dumps(p2s_lookup_message(host, port, user_input_filename, "0"))
        s.send(data)
        server_data = pickle.loads(s.recv(1024))
        if not server_data[0]:
            print(server_data[1])
        else:
            p2p_get_request(str(user_input_filename), server_data[0]["Hostname"], server_data[0]["Port Number"])
        get_user_input()
    elif user_input == "LOOKUP":
        user_input_filename = input("> Enter filename: ")
        data = pickle.dumps(p2s_lookup_message(host, port, user_input_filename, "1"))
        s.send(data)
        server_data = pickle.loads(s.recv(1024))
        print(server_data[1], end="")
        keys = ['Title', 'Hostname', 'Port Number']
        print_combined_list(server_data[0], keys)
        get_user_input()
    else:
        get_user_input()


def p2p_listen_thread(str, i):
    upload_socket = socket.socket()
    host = "127.0.0.1"
    upload_socket.bind((host, upload_port_num))
    upload_socket.listen(5)
    while True:
        c, addr = upload_socket.accept()
        data_p2p_undecoded = c.recv(1024)
        data_p2p = data_p2p_undecoded.decode('utf-8')
        index1st = data_p2p.index(':')
        index2nd = data_p2p.index('H')
        filename = data_p2p[index1st + 2: index2nd - 1]  # get the filename
        print('Got connection from ', addr, " for file: ", filename)
        c.send(pickle.dumps(p2p_response_message(filename)))

        c.close()


# Start listen thread for file transfer
start_new_thread(p2p_listen_thread, ("hello", 1))
get_user_input()
