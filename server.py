#!/usr/bin/python

import pickle
import socket
from _thread import *

s = socket.socket()
host = "127.0.0.1"
port = 7734
s.bind((host, port))
s.listen(5)

peer_list = []  # Global list of dictionaries for peers
file_list = []  # Global list of dictionaries for files
combined_list = []


def response_message(status):
    if status == "200":
        phrase = "OK"
    elif status == "404":
        phrase = "Not Found"
    elif status == "400":
        phrase = "Bad Request"
    message = status + " " + phrase + "\n"
    return message


# P2S response message from the server
def p2s_lookup_response(filename):
    response = search_combined_dict(filename)
    if not response:
        status = "404"
        phrase = "Not Found"
        message = status + " " + phrase + "\n"
        return response, message
    else:
        status = "200"
        phrase = "OK"
        message = status + " " + phrase + "\n"
        return response, message


def p2s_lookup_response2(filename):
    response = search_combined_dict2(filename)
    if len(response) == 0:
        status = "404"
        phrase = "Not Found"
        message = status + " " + phrase + "\n"
        return response, message
    else:
        status = "200"
        phrase = "OK"
        message = status + " " + phrase + "\n"
        return response, message


def p2s_add_response(conn, hostname, port, filename):
    response = "200 OK\n" + filename + " " + str(hostname) + " " + str(port)
    conn.send(bytes(response, 'utf-8'))


def search_combined_dict(filename):
    for d in combined_list:
        if d['Title'] == filename:
            return d

    return False


def search_combined_dict2(filename):
    my_list = []
    for d in combined_list:
        if d['Title'] == filename:
            my_list.append(d)

    return my_list


def p2s_list_response(conn):
    message = response_message("200")
    conn.send(bytes(message, 'utf-8'))


# Takes a list and appends a dictionary of hostname and port number
def create_peer_list(dictionary_list, hostname, port):
    keys = ['Hostname', 'Port Number']

    entry = [hostname, str(port)]
    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list, keys


# Creates file_list
def create_file_list(dictionary_list, dict_list_of_files, hostname):
    keys = ['Title', 'Hostname']

    for file in dict_list_of_files:
        filename = file['Title']
        entry = [filename, hostname]
        dictionary_list.insert(0, dict(zip(keys, entry)))

    return dictionary_list, keys


def create_combined_list(dictionary_list, dict_list_of_files, hostname, upload_port):
    keys = ['Title', 'Hostname', 'Port Number']

    for file in dict_list_of_files:
        filename = file['Title']
        entry = [filename, hostname, str(upload_port)]
        dictionary_list.insert(0, dict(zip(keys, entry)))

    return dictionary_list, keys


# Inserts new Dictionary item to file_list when client makes an ADD request
def append_to_file_list(dictionary_list, filename, hostname):
    keys = ['Title', 'Hostname']
    entry = [filename, hostname]

    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list


def append_to_combined_list(dictionary_list, filename, hostname, port):
    keys = ['Title', 'Hostname', 'Port Number']
    entry = [filename, hostname, str(port)]

    dictionary_list.insert(0, dict(zip(keys, entry)))
    return dictionary_list


# Prints the list of dictionary items
def print_dictionary(dictionary_list, keys):
    for item in dictionary_list:
        print(' '.join([item[key] for key in keys]))


# Deletes the entries associated with the hostname
def delete_peers_dictionary(dict_list_of_peers, hostname):
    dict_list_of_peers[:] = [d for d in dict_list_of_peers if d.get('Hostname') != hostname]
    return dict_list_of_peers


# Deletes the entries associated with the hostname
def delete_rfcs_dictionary(dict_list_of_files, hostname):
    dict_list_of_files[:] = [d for d in dict_list_of_files if d.get('Hostname') != hostname]
    return dict_list_of_files


def delete_combined_dictionary(combined_dict, hostname):
    combined_dict[:] = [d for d in combined_dict if d.get('Hostname') != hostname]
    return combined_dict


def return_dict():
    keys = ['Title', 'Hostname', 'Port Number']
    return combined_list, keys


# Create a thread for each client. This prevents the server from blocking communication with multiple clients
def client_thread(conn, addr):
    global peer_list, file_list, combined_list
    conn.send(bytes('Thank you for connecting', 'utf-8'))
    print('Got connection from ', addr)
    data = pickle.loads(conn.recv(1024))  # receive the[upload_port_num,rfc_num, rfcs_title]
    my_port = data[0]
    print("upload pot_no: ", my_port)
    # Generate the peer list and RFC list
    peer_list, peer_keys = create_peer_list(peer_list, addr[0], data[0])  # change addr[1] to data[0]
    file_list, file_keys = create_file_list(file_list, data[1], addr[0])
    combined_list, combined_keys = create_combined_list(combined_list, data[1], addr[0], data[0])

    while True:
        data = pickle.loads(conn.recv(1024))  # receive the[upload_port_num, rfcs_num, rfcs_title]
        if data == "EXIT":
            break
        if type(data) == str:
            # LIST
            # p2s_list_response(conn)
            new_data = pickle.dumps(return_dict())
            conn.send(new_data)
        else:
            # ADD
            print(data)
            if data[0][0] == "A":
                p2s_add_response(conn, data[1], data[2], data[3])  # Put server response message here
                file_list = append_to_file_list(file_list, data[3], addr[0])
                combined_list = append_to_combined_list(combined_list, data[3], addr[0], my_port)
                print_dictionary(file_list, file_keys)
            if data[1] == "0":
                # GET
                new_data = pickle.dumps(p2s_lookup_response(data[0]))
                conn.send(new_data)
            elif data[1] == "1":
                # LOOKUP
                print(p2s_lookup_response2(data[0]))
                new_data = pickle.dumps(p2s_lookup_response2(data[0]))
                conn.send(new_data)

    # Remove the client's info from the dictionaries
    peer_list = delete_peers_dictionary(peer_list, addr[0])
    file_list = delete_rfcs_dictionary(file_list, addr[0])
    combined_list = delete_combined_dictionary(combined_list, addr[0])
    conn.close()


while True:
    c, addr = s.accept()  # Establish connection with client.
    start_new_thread(client_thread, (c, addr))
s.close()
