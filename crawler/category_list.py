'''
    Indeed의 Category list를 크롤링
'''
import requests
from bs4 import BeautifulSoup
import time
from random import *
from util import init_logger,Logger,log_args
import config

INDEED_URL="https://kr.indeed.com"
INDEED_CATEGORY_URL = "https://kr.indeed.com/browsejobs"

# def _build_parser():
#
#     parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
#     parser.add_argument('--log_level',help=str([value for key, value in logging._levelToName.items()]) +" ( default : INFO )",default=logging._levelToName[logging.INFO])
#     return parser


def _get_html(url):
   _html = ""
   resp = requests.get(url)
   if resp.status_code == 200:
      _html = resp.text
   return _html

# 첫 browse 페이지에서 category 별 링크 찾음
def _get_browse_tag(url):

    # 다음 세부분류 category로의 링크들
    browse_url_list=[]
    # 특정 Category로 채용 공고를 찾는 링크들
    search_url_list=[]

    soup = BeautifulSoup(_get_html(url), 'html.parser')
    main_content=soup.find("table",{"id":"main_content"})
    if main_content == None:
        main_content=soup.find("table",{"id":"browsejobs_main_content"})

    for a_tag in main_content.find_all("a"):
        # print(a_tag)
        if "browsejobs" in a_tag["href"]:
            browse_url_list.append(a_tag["href"])
            Logger.debug("browsejobs = "+a_tag.text)
        else:
            search_url_list.append(a_tag["href"])
            Logger.debug("search = "+a_tag.text)

    return browse_url_list, search_url_list

'''
    category 별 Search URL 불러옴
    # Parameter
        flush_num : flush_num 이상으로 Search_url이 쌓였을 때 마다 pkl 파일 생성
'''
def write_search_url_list(flush_num,max_sleep):
    browse_url_list, _=_get_browse_tag(INDEED_CATEGORY_URL)

    file_index=0
    search_url_list=[]

    Logger.info("browse url list length = " + str(len(browse_url_list)) + " search url list length = " + str(
        len(search_url_list)))

    # browse_url 없을 때 까지 search url 계속 추가하면서 찾음
    while len(browse_url_list)!=0:

        Logger.debug("checking browse url = "+browse_url_list[0])
        new_br_list,new_search_list=_get_browse_tag(INDEED_URL+browse_url_list[0])
        browse_url_list=browse_url_list+new_br_list
        search_url_list=search_url_list+new_search_list
        del browse_url_list[0]
        # return search_url_list
        Logger.info("browse url list length = "+str(len(browse_url_list))+" search url list length = "+str(len(search_url_list)))
        time.sleep(uniform(0.1, max_sleep))

        if len(search_url_list)>=flush_num:
            file_path =config.CATEGORY_URL_FILE_PATH+"search_url_list_"+str(file_index)+".txt"
            # with open(pkl_name,"wb") as f:
            #         pkl.dump(search_url_list,f)

            with open(file_path, "w") as f:
                f.write("\n".join(search_url_list))

            Logger.info("searurl "+str(len(search_url_list))+" is written to "+file_path+"\n")

            search_url_list=[]
            file_index+=1
