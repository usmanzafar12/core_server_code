from helper import *

        
def start():
    
    global condition 
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    lock = threading.Lock()
    port = os.environ['PORT']
    
    try:
        token = os.environ["INFLUXDB_TOKEN"]
    except Exception as e:
        logging.info("NO TOKEN PRESENT")

    condition = True
    workers = []
    influx_ip = socket.gethostbyname("influx")
    print("this is the influx_ip", influx_ip)
    client = InfluxDBClient(url=f"http://{influx_ip}:8086", token=token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    #logging.info(os.environ["INFLUXDB_CONNECTION"])
    logging.info(os.environ["INFLUXDB_TOKEN"])
    logging.info(os.environ["PORT"])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', int(port)))
    s.settimeout(30)
    s.listen()
    df = pd.read_csv('devices2.csv')
    df['str'] = df['imei'].apply(lambda x: str(x))
    allowed = set(df['str'].values)
    #thread = threading.Thread(target=detect_key_press)
    #thread.start()
    print("the allowed values are", allowed)
    logging.info(" Server is listening ...")
    
    while condition:
        try:

            logging.info(datetime.now())
            conn, addr = s.accept()
            handler = SocketHandler(conn, addr, write_api, lock, allowed)
            workers.append(handler)
            handler.start()
            logging.info(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
        except Exception as e:
            logging.info(f"Exception Caught: {e}, Continuing")
    logging.info("Aborting threads gracefully....")
    
    for worker in workers:
        worker.join()
    return "Connection Closed"


if __name__ == "__main__":
    start()
