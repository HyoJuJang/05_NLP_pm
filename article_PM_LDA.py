#!/usr/bin/env python
# coding: utf-8


# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import time
import random
import re
from tqdm import tqdm
# from selenium import webdriver
# from selenium import webdriver
# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver import ActionChains
import pandas as pd
import numpy as np
import time
import requests

import sys
import json
import pickle


# # 네이버 기사 크롤링


def get_news(n_url): 
    news_detail = []
    news_title=[]
    headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'accept' : "*/*",
    'accept-encoding' : 'gzip, deflate, br',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'referer' : n_url
    }
    
    payload = {'as_epq': 'James Clark', 'tbs':'cdr:1,cd_min:01/01/2015,cd_max:01/01/2015', 'tbm':'nws'}
    breq = requests.get(n_url, params=payload, headers=headers) 
    bsoup = BeautifulSoup(breq.content, 'html.parser') 
    try:
        title = bsoup.select('h3#articleTitle')[0].text 
        pdate = bsoup.select('.t11')[0].get_text()[:11] 
        news_detail.append(pdate) 
        _text = bsoup.select('#articleBodyContents')[0].get_text().replace('\n', " ") 
        btext = _text.replace("// flash 오류를 우회하기 위한 함수 추가 function _flash_removeCallback() {}", "")
        news_detail.append(btext.strip()) 
        pcompany = bsoup.select('#footer address')[0].a.get_text() 
        news_detail.append(pcompany) 

        return title, news_detail
    
    except:
        print("양식 다름")
        return [],[]



def get_news_naver(keyw, num_page):
    article_dict={"titles":[], "contents":[],"urls":[], "comments":[]}
    keyw = keyw.replace(' ', '+') 
    for keyword in [keyw]:#,"PM"
        for page in range(num_page):  # 페이지 개수 설정 1~400
            raw = requests.get(f'https://search.naver.com/search.naver?&where=news&query={keyword}&start=' + str(page * 10 + 1)).text
            soup = BeautifulSoup(raw, 'html.parser')
            articles = soup.select('#main_pack > section.sc_new.sp_nnews._prs_nws > div > div.group_news > ul > li')

            for article in tqdm(articles):
                c_tag = article.select_one('div > div.info_group > a:nth-of-type(2)')
                comment_list=[]
                if c_tag!=None:
                    content= c_tag["href"]
                    article_dict["titles"].append(get_news(content)[0])
                    article_dict["contents"].append([get_news(content)[1][1]])
                    article_dict["urls"].append(content)
                    oid = content.split("oid=")[1].split("&")[0] 
                    aid = content.split("aid=")[1] 
                    page = 1
                    headers = {
                        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                        'accept' : "*/*",
                        'accept-encoding' : 'gzip, deflate, br',
                        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        'referer' : content
                    }

                    while True:
                        c_url = "https://apis.naver.com/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId=default_society&pool=cbox5&_callback=jQuery1707138182064460843_1523512042464&lang=ko&country=&objectId=news" + oid + "%2C" + aid + "&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=" + str(page) + "&refresh=false&sort=FAVORITE"
                        # 파싱
                        r = requests.get(c_url, headers=headers)
                        cont = BeautifulSoup(r.content, "html.parser")
                        total_comm = str(cont).split('comment":')[1].split(",")[0]
                        match = re.findall('"contents":([^\*]*),"userIdNo"', str(cont))
                        # 댓글을 리스트에 중첩
                        comment_list.append(match)
                        
                        time.sleep(random.uniform(0.1,0.2))
                        if int(total_comm) <= ((page) * 20):
                            break
                        else:
                            page += 1
                    article_dict["comments"].append(comment_list)
    return article_dict



#naver_dict = get_news_naver('전동 킥보드', 1)


# # 다음 기사 크롤링


def daum_search(keyword, num_page):
    keyword = keyword.replace(' ', '+') 
    url = 'https://search.daum.net/search?w=news&DA=PGD&spacing=0'
    daum_url_list = []
    for page in range(1, 1+num_page):
        req_params = {
            'q': keyword, # 검색어(키워드)를 쿼리 스트링에 파라미터로 추가
            'p': page # 검색 페이지 번호를 쿼리 스트링에 파라미터로 추가
        }
        response = requests.get(url, params=req_params)
        html = response.text.strip()

        soup = BeautifulSoup(html, 'html5lib')
        li_list = soup.find_all('div',{'class' : 'wrap_cont'})
        nb_list = [li.find('a',{'class':'f_nb'}) for li in li_list if not li.find('a',{'class':'f_nb'}) == None]
        daum_url_list.append([url.get('href') for url in nb_list])
        #time.sleep(random.uniform(2,4)) 
    return daum_url_list



def get_news_daum(keyword, num_page):
    url_list = sum(daum_search(keyword, num_page),[])
    news_detail = {"titles":[], "contents":[],"urls":[], "comments":[]}
    comment_list = []
    #news_class = []
    for d_url in tqdm(url_list):
        headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'accept' : "*/*",
        'accept-encoding' : 'gzip, deflate, br',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        payload = {'as_epq': 'James Clark', 'tbs':'cdr:1,cd_min:01/01/2015,cd_max:01/01/2015', 'tbm':'nws'}
        try:
            breq = requests.get(d_url, params=payload, headers=headers) 
            bsoup = BeautifulSoup(breq.text)
            news_class = bsoup.find('span',{'class' : 'ir_wa'}).get_text()
            if news_class == '뉴스':
                news_title = bsoup.select_one('h3.tit_view').get_text()
                news_title.replace('<h3 class="tit_view" data-translation="true">', "") 
                news_title.replace('</h3>','')
                news_title.replace('[영상]','')
                news_contents = ''
                news_comments = []

                for p in bsoup.select('div#harmonyContainer p'):
                    news_contents += p.get_text()

                #access_token_id 반환
                org = d_url
                article_id = org.split("/")[-1]
                req = requests.get(org)
                soup = BeautifulSoup(req.content)
                data_client_id = soup.find('div',{'class':'alex-area'}).get('data-client-id')

                # authorization 값 반환
                headers['referer'] = org
                token_url = "https://alex.daum.net/oauth/token?grant_type=alex_credentials&client_id={}".format(data_client_id)
                req = requests.get(token_url, headers=headers)
                access_token = json.loads(req.content)['access_token']
                authorization = 'Bearer '+access_token

                # article - comment 연결 짓는 key값 반환
                headers['authorization'] = authorization
                post_url = """https://comment.daum.net/apis/v1/ui/single/main/@{}""".format(article_id)
                req = requests.get(post_url, headers = headers)
                soup = BeautifulSoup(req.content,'html.parser')
                post_id = json.loads(soup.text)['post']['id']

                count = len(comment_list)
                offset = 0

                while True:
                    request_url = "https://comment.daum.net/apis/v1/posts/{}/comments?parentId=0&offset={}&limit=100&sort="
                    "RECOMMEND&isInitial=false&hasNext=true".format(post_id, offset)

                    req = requests.get(request_url, headers=headers)
                    soup = BeautifulSoup(req.content,'html.parser')
                    temp_json_list = json.loads(soup.text)
                    for temp_json in temp_json_list:
                        temp_json['org_url'] = org
                        try:
                            news_comments.append(temp_json['content'])
                        except:
                            news_comments.append([])
                    comment_list.extend(temp_json_list)
                    if len(temp_json_list) < 100:
                        break
                    else:
                        offset += 100
                        time.sleep(1)

                news_detail['titles'].append(news_title)
                news_detail['contents'].append([news_contents])
                news_detail['urls'].append(d_url)
                news_detail['comments'].append(news_comments)

                time.sleep(random.uniform(2,4)) 
        except:
            pass
    return news_detail


#daum_dict = get_news_daum('전동 킥보드', 1)


# ### 네이버, 다음 기사 크롤링(max(네이버)=400, max(다음)=80)


naver_dict = get_news_naver('전동 킥보드', 400)
daum_dict=get_news_daum('전동 킥보드', 80)




# # 크롤링 된 결과 확인 및 저장

naver_dict['contents']
daum_dict['contents']

path = 'C:/Users/commend/Dropbox/2021_2/intern/nlp/'

# # 저장
# with open(path+'naver_dict.pickle', 'wb') as f:
#     pickle.dump(naver_dict, f, pickle.HIGHEST_PROTOCOL)

# with open(path+'daum_dict.pickle', 'wb') as f:
#     pickle.dump(daum_dict, f, pickle.HIGHEST_PROTOCOL)

# 읽기
with open(path+'data/naver_dict.pickle', 'rb') as f:
    naver_dict = pickle.load(f)
    
with open(path+'data/daum_dict.pickle', 'rb') as f:
    daum_dict = pickle.load(f)

    
len(naver_dict['titles'])
len(daum_dict['titles'])


# # 네이버 U 다음

naver_idx = [naver_dict['titles'].index(x) for x in naver_dict['titles'] if type(x) == str]
naver_headlines = [naver_dict['titles'][idx] for idx in naver_idx]

interaction = set(daum_dict['titles']) & set(naver_headlines)
daum_inter_idx = [daum_dict['titles'].index(inter) for inter in interaction]

daum_contents = [daum_dict['contents'][i] for i in range(len(daum_dict['contents'])) if i not in daum_inter_idx]

naver_contents = [naver_dict['contents'][idx] for idx in naver_idx]
naver_contents = [x for x in naver_contents if len(x) == 3]
naver_contents = [x[1] for x in naver_contents]

for cont in daum_contents:
    naver_contents.append(cont)

all_contents = naver_contents

len(all_contents)


# # 자연어 전처리

def refine(contents): 
    pure = re.sub('\[.*?\]', '', str(contents))   
    pure = re.sub('\【.*?\】', '', pure)
    pure = re.sub('\(.*?\)', '', pure)
    #pure = re.sub('[-=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·▲■]▷', '', pure)
    #pure = re.sub(".+(?=기자)"," ", pure)
    pure = re.sub("[가-힣]+\s+기자"," ", pure)
    
    pure = re.sub('기자', "", pure)
    pure = re.sub('이메일', "", pure)
    pure = re.sub('검색', "", pure)
    pure = re.sub('전화', "", pure)

    pure = re.sub(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",'',pure)
    
    pure = re.sub('[a-zA-Z0-9]',' ',pure).strip()
    p = re.compile("\W+|\d+")
    content = p.sub(" ", pure)
    
    return str(content)

all_contents_refined = [refine(cont) for cont in all_contents]

# with open(path + 'all_contents_refined', 'wb') as f:
#     pickle.dump(all_contents_refined, f)


#######################################################################
#######################################################################
#######################################################################

# pickle로 저장해 둠
path = 'C:/Users/commend/Dropbox/2021_2/intern/nlp/'
with open(path + 'all_contents_refined', 'rb') as f:
    all_contents_refined = pickle.load(f)

## stopwords & press

with open(path + 'press.txt', "r", encoding='UTF-8') as file:
    strings = file.readlines()
    
press_ = [strg.split(',')[1:] for strg in strings]

press = [prs[1:] for prs in press_[0]]
press.append('아시아일보')
press.append('뉴시스')
press.append('엠빅뉴스')
press.append('아이뉴스')
press.append('데일리안')

none_dic = pd.read_csv(path+'none_dic.csv', header = None, encoding = "cp949")
none = none_dic[0].tolist()

# ## tokenization & bigram

from konlpy.tag import Komoran

# bigram 생성에 필요한 library
from gensim.models import Phrases
from gensim.models.phrases import Phraser

# vectorize & lda에 필요한 library
from gensim import corpora
from gensim.models.ldamodel import LdaModel

# gensim의 ldamodel에 최적화된 라이브러리
import pyLDAvis
import pyLDAvis.gensim_models as gensimvis  

komo = Komoran()

def text_preprocessing(text,tokenizer):
    
    tokens = []
    stopwords = none 
    
    #txt = re.sub('[^가-힣a-z]', ' ', text) # 영어와 한글만 가져옴
    #token = tokenizer.morphs(text) # 모든 형태소 처리(morphs) ,명사만 뽑기(nouns)
    token = tokenizer.nouns(text) # 모든 형태소 처리(morphs) ,명사만 뽑기(nouns)
    
    token = [t for t in token if t not in stopwords] # 불용어 필터
    token = [t for t in token if t not in press if len(t) > 1]
    tokens.append(' '.join(token))
    
    return tokens

# all_contents_nouns = []
# for cont, idx in zip(all_contents_refined, range(len(all_contents_refined))):
#     try:
#         all_contents_nouns.append(text_preprocessing(cont, komo))
#     except:
#         pass
#         print(idx)


all_contents_nouns = []
for cont, idx in zip(all_contents_refined, range(len(all_contents_refined))):
    try:
        all_contents_nouns.append([x.split(' ') for x 
         in text_preprocessing(cont, komo)][0])
    except:
        pass
        print(idx)

        
all_contents_nouns
len(all_contents_nouns)

all_contents_nouns_org = all_contents_nouns.copy()

# bigrams/trigrams를 더한다. (20번이 넘게 나타나는 것들만)
bigram = Phrases(all_contents_nouns, min_count=20)
for idx in range(len(all_contents_nouns)):
    for token in bigram[all_contents_nouns[idx]]:
        if '_' in token:
            # 토큰이 bigram이면 document에 추가한다.
            all_contents_nouns[idx].append(token)
            
dictionary = corpora.Dictionary(all_contents_nouns) 
# rare & common tokens 지우기
# 너무 자주 나오거나 너무 안나오는 단어들 지우기
max_freq = 0.6
min_wordcount = 2
dictionary.filter_extremes(no_below=min_wordcount, no_above=max_freq)
 
_ = dictionary[0]  # dictionary.id2token를 시작

all_contents_nouns

corpus = [dictionary.doc2bow(doc) for doc in all_contents_nouns]

print('Number of unique tokens: %d' % len(dictionary))
print('Number of documents: %d' % len(corpus))
corpus

## hyperparameter tuning

from tqdm import tqdm

# num_topics_l = list(range(3,11))
# chunksize_l = [100, 1000, 2000]
# passes_l = [10, 20, 30, 40]
# iterations_l = [100, 400, 500, 1000]
# random_state_l = [2021, 2022, 12, 30, 0]

num_topics_l = list(range(3,11))
chunksize_l = [2000]
passes_l = [20, 30, 40]
iterations_l = [500]
random_state_l = [2022]
#random_state_l = [2021, 2022, 12, 30, 0]

model_list = []
                                                        
for random_state in random_state_l:                    
    for chunksize in tqdm(chunksize_l):
        for passes in passes_l:
            for iterations in iterations_l:
                for num_topics in num_topics_l:
                    model = LdaModel(corpus = corpus, id2word = dictionary, chunksize = chunksize,
                                           alpha ="auto", eta="auto",
                                           iterations = iterations, num_topics = num_topics,
                                           passes = passes, random_state=random_state)
                    top_topics = model.top_topics(corpus)
                    tc = sum([t[1] for t in top_topics])
                    hyper = [num_topics, passes]
                    model_list.append((model, tc, hyper))
                    print('done')

                    
# with open(path + 'model_list_1231', 'wb') as f:
#     pickle.dump(model_list, f)

# grid search 결과 저장해 둠
with open(path + 'model_list_1231', 'rb') as f:
    result_list = pickle.load(f)
        
len(result_list)

model_list = [list(x) for x in result_list]
model_perplexity = [x[0].log_perplexity(corpus) for x in model_list]

results = pd.DataFrame(data={'condition_ntopic':[x[2][0] for x in model_list],'condition_passes':[x[2][1] for x in model_list],'coherence':[x[1] for x in model_list], 'perplexity':model_perplexity})

results.sort_values(by='coherence', ascending=False)
results.sort_values(by='perplexity')

## best model 시각화

model, tc = max([tuple(mod[:2]) for mod in model_list], key=lambda x: x[1])
print('Topic coherence: %.3e' %tc)
print('\nPerplexity: ', model.log_perplexity(corpus))

# Save model.
model.save(path + '/model.atmodel')
# Load model.
model_saved = LdaModel.load(path + '/model.atmodel')
model.show_topic(0)

model.print_topics(num_words=10) 

vis = gensimvis.prepare(model, corpus, dictionary)
pyLDAvis.display(vis)

