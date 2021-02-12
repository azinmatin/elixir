import ConfigParser
import os
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--c', help='config file')
    args = parser.parse_args()
    configFilePath = args.c
    # print configFilePath, configFilePath[0]

    configParser = ConfigParser.RawConfigParser()
    configParser.read(configFilePath)
    folder = configParser.get('shared', 'folder')
    dataset = configParser.get('shared', 'd')
    res_path = 'YOUR PATH' + folder
    if not os.path.exists(res_path):
        os.makedirs(res_path)
        print 'directory created:', res_path
    with open(res_path+'config.txt', 'w') as f_out:
        with open(configFilePath, 'r') as f_in:
            f_out.write(f_in.read())
