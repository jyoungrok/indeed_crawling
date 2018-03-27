from bs4 import BeautifulSoup
import requests
from util import init_logger, Logger, log_args
import logging
import argparse
import xml.etree.ElementTree as ET
import config
import time
import random
import pickle as pkl



def _build_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--log_level',
                        help=str([value for key, value in logging._levelToName.items()]) + " ( default : INFO )",
                        default=logging._levelToName[logging.INFO])
    # parser.add_argument('--job_type', help=str([value for value in JOB_TYPE_LIST]), required=True)

    return parser


def _indent(elem, level=1):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


'''
    h2 tag + class = jobtitle
'''


def _get_html(url):
    _html = ""
    resp = requests.get(url)
    if resp.status_code == 200:
        _html = resp.text
    return _html


'''
    각 페이지에서 채용 공고의 Key들을 불러옴
'''


def get_emp_key(url,index):
    # 해당 페이지에 "다음" 글씨가 있는지 여부
    # next_page_exist=True

    req_url = url +"&start=" + str(index * 50)
    Logger.debug("get_emp_key request URL = " + url)
    html = _get_html(url)

    soup = BeautifulSoup(html, 'html.parser')

    job_key_list = []


    # a_tag 중 채용공고에 대한 Tag를 찾는 방식
    # -> 일반 채용공고 뿐만 아니라 유료 광고도 불러옴 (일반 채용 공고 10개 + 유료 광고 6개)
    for a_tag in soup.find_all("a", {"data-tn-element": "jobTitle"}):
        split_id = a_tag.parent["id"].split("_")

        id_type = split_id[0]
        emp_id = split_id[1]

        job_key_list.append(emp_id)

    return job_key_list


'''
    API를 이용하여 job key 가져오기
'''


def get_emp_key_from_api(location, index):
    # api는 최대 25개 까지 1번에 읽기 가능...
    url = config.INDEED_API_SEARCH_URL + "&l=" + location + "&start=" + str(index * 25)

'''
    채용 공고 내용 불러오기 

    # Return
        xml : 채용 공고 내용을 xml 형태로 구성

'''


def get_job_detail(key):
    job_dict = {}
    req_url = config.INDEED_JOB_SEARCH_URL + key
    html = _get_html(req_url)
    soup = BeautifulSoup(html, 'html.parser')

    # job header 내용 Parsing
    job_header = soup.find("div", {"data-tn-component": "jobHeader"})
    Logger.debug("request URL =" + req_url)
    # print(job_header)

    job_title = job_header.find("b", {"class": "jobtitle"}).contents[0].get_text()
    company = job_header.find("span", {"class": "company"}).get_text()
    location = job_header.find("span", {"class": "location"}).get_text()
    cmp_description = ""


    soup.find("span", {"class": "company"})
    # company description이 없는 페이지도 있음
    try:
        cmp_description = soup.find("div", {"class": "cmp_description"}).get_text()
    except AttributeError:
        Logger.debug("cmp_description does not exists")

    job_summary = soup.find("span", {"id": "job_summary"}).get_text()

    Logger.debug("jobtitle = " + job_title)
    Logger.debug("company = " + company)
    Logger.debug("location = " + location)
    Logger.debug("cmp_description = " + cmp_description)
    Logger.debug("job_summary = " + job_summary)

    xml = ET.Element("root")
    ET.SubElement(xml, "job_key").text = key
    ET.SubElement(xml, "jobtitle").text = job_title
    ET.SubElement(xml, "company").text = company
    ET.SubElement(xml, "location").text = location
    ET.SubElement(xml, "cmp_description").text = cmp_description
    ET.SubElement(xml, "job_summary").text = job_summary

    Logger.debug(ET.tostring(xml, encoding="utf=8"))
    _indent(xml)

    return xml


def _write_xml(xml, file_path):
    ET.ElementTree(xml).write(file_path, encoding="UTF-8")


# 0.1~sec초 간격으로 randomly sleep
def rand_sleep(sec):
    sleep_len = random.uniform(0.1, sec)
    Logger.debug("sleep " + str(sleep_len) + "sec")
    time.sleep(sleep_len)

'''
    url_list에 해당하는 
    채용 공고를 읽어와서 xml로 씀
'''
def write_emp_detail(url_list,max_sleep):

    crawling_data_num = 0
    start_time = time.time()

    # job detail을 불러와 xml파일로 쓴 job key들
    key_dict = {}

    # 요청시 실패한 key list 저장
    failed_key_list = []
    url_index=0
    # URL 당 최대 1000개의 job detail적음
    for url in url_list:
        Logger.info(str(url_index+1) + "/"+str(len(url_list))+" job list request URL = "+url.replace("\n",""))
        url_index+=1
        job_key_list=[]


        # 채용 공고 목록 페이지에서 job key들을 받아옴
        # 50개씩 최대 20번 불러옴
        try:
            req_url = config.INDEED_URL+url+"&limit=50"
            prev_key_list=[]
            for index in range(20):
                cur_key_list = get_emp_key(req_url,index)
                # 페이지 index가 넘어간 경우 계속 똑같은 list를 반복하므로 이 경우 더 이상 job key를 받아오지 않음
                if prev_key_list==cur_key_list:
                    break
                else:
                    prev_key_list=cur_key_list
                job_key_list=job_key_list+cur_key_list
                rand_sleep(max_sleep)
        except:
            continue

        Logger.info("job key list length = "+str(len(job_key_list)))

        not_exist_cnt = 0

        # job key들의 채용 공고 detail 받아옴
        for key in job_key_list:
            # 해당 key에 대해서 아직 Crwaling 안한 경우
            # Crawling 수행하고 xml 파일 적음
            if not key in key_dict:
                key_dict[key] = True
                try:
                    xml = get_job_detail(key)
                except:
                    Logger.warn(key + " parsing failed")
                    failed_key_list.append(key)
                    rand_sleep(max_sleep)
                    continue

                file_path = config.JOB_DETAIL_FILE_PATH + key + ".xml"
                _write_xml(xml, file_path)
                Logger.debug(file_path+" is written")
                not_exist_cnt += 1
                crawling_data_num += 1
                rand_sleep(max_sleep)
            else:
                Logger.debug("key " + key + " already exist")

        # url
        Logger.info("total data num =" + str(crawling_data_num) + " added data num =" + str(
                            not_exist_cnt) + " elapsed time = " + str(time.time() - start_time)+"\n")

        # 현재까지 가져온 모든 key들을 pkl로 저장
        key_dict_path = "key_dict.pkl"
        # 적은 job key의 dictionary를 pickle 파일로 저장
        with open(key_dict_path, "wb") as f:
            pkl.dump(key_dict, f)

        Logger.info(key_dict_path + "has been written")



                        # if not_exist_cnt==0:
                        #     Logger.info("threre are not any employment not written")
                        #     break



# if __name__ == "__main__":
#
#     parser = _build_parser()
#     FLAGS = parser.parse_args()
#     init_logger(logging._nameToLevel[FLAGS.log_level])
#     log_args(FLAGS)
#
#     job_type = FLAGS.job_type
#
#     key_dict = {}
#
#     # 요청시 실패한 key list 저장
#     failed_key_list = []
#
#     index = 0
#     crawling_data_num = 0
#
#     start_time = time.time()
#
#     while True:
#
#         Logger.info(str(index) + "th job list request")
#         job_key_list = get_emp_key(job_type, 25)
#         # job_key_list = get_emp_key(job_type,index)
#
#         rand_sleep(MAX_SLEEP_SEC)
#         index += 1
#
#         not_exist_cnt = 0
#         for key in job_key_list:
#             # 해당 key에 대해서 아직 Crwaling 안한 경우
#             # Crawling 수행
#             if not key in key_dict:
#                 key_dict[key] = True
#                 try:
#                     xml = get_job_detail(key)
#                 except:
#                     Logger.warn(key + " parsing failed")
#                     failed_key_list.append(key)
#                     rand_sleep(MAX_SLEEP_SEC)
#                     continue
#
#                 file_path = XML_FILE_PATH + key + ".xml"
#                 _write_xml(xml, file_path)
#                 not_exist_cnt += 1
#                 crawling_data_num += 1
#                 rand_sleep(MAX_SLEEP_SEC)
#
#         Logger.info("total data num =" + str(crawling_data_num) + " added data num =" + str(
#             not_exist_cnt) + " elapsed time = " + str(time.time() - start_time))
#
#         # if not_exist_cnt==0:
#         #     Logger.info("threre are not any employment not written")
#         #     break
#
#     # 실패한 Key들 적음
#     with open("failed_key_list.txt", "w") as f:
#         f.write("\n".join(failed_key_list))
#
#

        # html = _get_html(INDEED_QUERY_URL)
        # soup = BeautifulSoup(html, 'html.parser')
        # result = soup.find_all("h2")
        # result = soup.h2['job']
        # # print(soup)
        # print(result)

