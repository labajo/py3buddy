#  Program to that uses py3buddy using Mqtt Events


import sys
import os
import argparse
import configparser
import py3buddy
import paho.mqtt.client as mqtt
import time

def main(argv):
    parser = argparse.ArgumentParser()

    # options for the commandline
    parser.add_argument("-c", "--config", action="store", dest="cfg",
                        help="path to configuration file", metavar="FILE")
    args = parser.parse_args()

    # first some sanity checks for the configuration file
    if args.cfg is None:
        parser.error("Configuration file missing")

    if not os.path.exists(args.cfg):
        parser.error("Configuration file does not exist")

    # then parse the configuration file
    config = configparser.ConfigParser()

    configfile = open(args.cfg, 'r')

    try:
        config.readfp(configfile)
    except Exception:
        print("Cannot read configuration file", file=sys.stderr)
        sys.exit(1)

    buddy_config = {}
    mqtt_server = 'localhost'
    mqtt_topic = 'ibuddy/events'
    for section in config.sections():
        if section == 'ibuddy':
            try:
                productid = int(config.get(section, 'productid'))
                buddy_config['productid'] = productid
            except:
                pass

            buddy_config['reset_position'] = False
            try:
                reset_position_val = config.get(section, 'reset_position')
                if reset_position_val == 'yes':
                    buddy_config['reset_position'] = True
            except:
                pass
        if section == 'mqtt':
            try:
                mqtt_server = config.get(section, 'mqtt_server')
                mqtt_topic = config.get(section, 'mqtt_topic')
            except:
                pass

    print("mqtt server: " + mqtt_server)
    client = mqtt.Client()

    # initialize an iBuddy and check if a device was found and is accessible
    client.ibuddy = py3buddy.iBuddy(buddy_config)

    if client.ibuddy.dev is None:
        print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
        sys.exit(1)

    print("\npy3buddy is listening\n")

    def on_connect(cli, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        cli.subscribe(mqtt_topic)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(cli, userdata, msg):
        if cli.ibuddy.dev is None:
            cli.ibuddy = py3buddy.iBuddy(buddy_config)
            if cli.ibuddy.dev is None:
                print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
                sys.exit(1)
        if msg.topic == mqtt_topic:
            print(msg.topic + " " + str(msg.payload))
            print("Executing: ", msg.payload.decode('ascii'))
            cli.ibuddy.executecommand(msg.payload.decode('ascii'))
            cli.ibuddy.reset()
            time.sleep(7)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_server, 1883, 60)
    client.loop_forever()


if __name__ == "__main__":
    main(sys.argv)
