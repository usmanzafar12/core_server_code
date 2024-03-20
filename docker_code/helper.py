import socket
import threading
import time
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from pathlib import Path
import sys
import os
from datetime import datetime
import pandas as pd

def decodethis(data):
    record = int(data[18:20], 16)
    timestamp = int(data[20:36], 16)
    lon = int(data[38:46], 16)
    lat = int(data[46:54], 16)
    alt = int(data[54:58], 16)
    sats = int(data[62:64], 16) #maybe
    print("Record: " + str(record) + "\nTimestamp: " + str(timestamp) + "\nLat,Lon: " + str(lat) + ", " + str(lon) + "\nAltitude: " + str(alt) + "\nSats: " +  str(sats) )
    return "0000" + str(record).zfill(4)


def decode_gps_data(name, data):
    timestamp = int(data[20:36], 16)
    lon = int(data[38:46], 16)
    lat = int(data[46:54], 16)
    info = name + " " + '"Timestamp":' + str(timestamp) + ','+'"Lat":' + str(lat) + ','+'"Long":' + str(lon)
    return(info)


def calc_data_count(str_val):
    str_val = str_val.hex()
    count = int(str_val[18:20],16)
    byte_count = count.to_bytes(4, byteorder = 'big')
    return byte_count


def total_length(str_val):
    str_val = str_val.hex()
    #print(str_val)
    return int(str_val[8:16],16) + 13


def calculate_bytes(str_val):
    str_val = str_val.hex()
    return int(len(str_val)/2)


def detect_key_press():
    global condition
    condition = False

def get_codec(str_val):
    str_val = str_val.hex()
    codec = str_val[16:18]
    #byte_count = count.to_bytes(4, byteorder = 'big')
    return codec.upper()


class SocketHandler(threading.Thread):
    
    def __init__(self, conn, addr, write_api, lock, allowed):
        super(SocketHandler, self).__init__()
        self.conn = conn 
        self.addr = addr
        self.write_api = write_api
        self.daemon = True
        self.lock = lock
        self.imei = ""
        self.allowed = allowed
     
    def handshake(self):
        pass
    
    def run(self):
        self.handle_client(self.conn, self.addr)   
        
    def handle_client(self, conn, addr):
        global condition
        condition = True
        while condition:
            avl_data = ''
            pkt_size = 0
            data = self.conn.recv(4096)
            print("handling client")
            #print(data)
            if (data.hex()[:4] == '000f'):
                logging.info(f"the length of handshake message is {len(data)}")
                self.conn.send(bytes().fromhex('01'))
                self.imei = data[2:].decode() 
                self.name = self.imei
                print("this is the imei ",self.imei)
                #print(self.allowed)
                if self.imei not in self.allowed:
                    self.conn.send(bytes().fromhex('00'))
                    return self.conn.close()
                else:
                    print("Im here")
                    self.conn.send(bytes().fromhex('01'))
                    self.imei = data[2:].decode() 
                    self.name = self.imei
                print("this is the imei number 2 ",self.imei)
            elif len(data) < 45:
                return self.conn.close()
            else:
                data_count = calc_data_count(data)
                codec_version = get_codec(data)
                print(codec_version)
                if codec_version == '8E':
                    self.conn.send(data_count)   
                    pkt_len = total_length(data)
                    logging.info("Codec 8 extended found")
                    logging.info(f"length of packet {pkt_len}")
                    #data
                    #logging.info(data.hex())
                else:
                    logging.info("Codec 8  found")
                    self.conn.send(data_count)   
                    pkt_len = total_length(data)
                    logging.info(f"length of packet {pkt_len}")
                    #data
                    #logging.info(data.hex())
                if data:
                    flag = self.write_db(data.hex(), codec_version)
#                return self.conn.close()

    
    def write_db(self, data, codec='08'):
        #print("helllo")
        if codec == '08':
            org = "qeeri"
            bucket = "codec8"
            line = "gps_data" + f",imei={self.imei}" + f" raw_data=\"{data}\"" + f"{time.time_ns()}" 
            logging.info(line)
        elif codec == '8E':
            org = "qeeri"
            bucket = "codec8x"
            line = "gps_data" + f",imei={self.imei}" + f" raw_data=\"{data}\"" + f"{time.time_ns()}" 
            logging.info(line)
        else:
            org = "qeeri"
            bucket = "gps"
            line = "gps_data" + f",imei={self.imei}" + f" raw_data=\"{data}\"" + f"{time.time_ns()}" 
            logging.info(line)
            
        #print(line)
        with self.lock:
            try:
                logging.info(f"Lock acquired by{self.imei}")
                self.write_api.write(bucket, org, line, batch=1)
                flag = True
            except:
                flag = False
        logging.info(f"Lock released by{self.imei}")
        return flag