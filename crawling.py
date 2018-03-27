from bs4 import BeautifulSoup
import requests
from util import init_logger,Logger,log_args
import logging
import argparse
import config
from crawler import category_list as CL, employment_list as EL
from os import listdir
from os.path import isfile, join, splitext


def _build_parser():

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--log_level',help=str([value for key, value in logging._levelToName.items()]) +" ( default : INFO )",default=logging._levelToName[logging.INFO])
    parser.add_argument('--data',help="what to crawl"+str(config.CRAWLING_OBJECT_LIST),required=True)
    parser.add_argument('--flush_num',help="[data == category] the crawled data is written when the number of data is more than flush_num,",default=100)
    # parser.add_argument('--url_index',help="[data == job] ex) 1,4 -> 1~4 search url will be read ",default="1,1")
    parser.add_argument('--max_sleep',help="the maximum second of sleep",default=3)

    return parser

# category 폴더 내의 모든 url들 불러옴
def read_url_list():
    file_list = [config.CATEGORY_URL_FILE_PATH + f for f in sorted(listdir(config.CATEGORY_URL_FILE_PATH))]
    url_list = []
    # print(file_list)

    for file in file_list:
        with open(file,"r") as f:
            url_list=url_list+f.readlines()
            # print(len(url_list))
    return file_list,url_list

if __name__=="__main__":

    parser = _build_parser()
    FLAGS = parser.parse_args()
    init_logger(logging._nameToLevel[FLAGS.log_level])
    log_args(FLAGS)

    # Indeed Category URL들을 Crawling
    if FLAGS.data == config.CRAWLING_OBJECT_LIST[0]:
        CL.write_search_url_list(FLAGS.flush_num,FLAGS.max_sleep)

    # data를 Crawling
    elif FLAGS.data == config.CRAWLING_OBJECT_LIST[1]:
        file_list,url_list=read_url_list()
        EL.write_emp_detail(url_list,FLAGS.max_sleep)
        print(file_list)
        print("has been written")

