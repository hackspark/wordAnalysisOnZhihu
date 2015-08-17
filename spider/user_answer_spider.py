# -*- coding: utf-8 -*- 
import requests, re, time

# 先导数据, 目标用户id, 爬虫账户email和密码, cookie
username = '' #target user id
email = '' #your email account here
password = '' #correpsonding password here
cookie = ''

zhihuUrl = 'http://www.zhihu.com'
answerPageUrl = zhihuUrl + "/people/" + username + "/answers?page="

# 正则表达式部分
pagePattern = re.compile(r'page=\d+">\d+</a>')
answerLinkPattern = re.compile(r'<a class="question_link" href="(.*)">')
approveNumPattern = re.compile(r'<div class="zm-item-vote-info " data-votecount="(\d+)">')
questionPattern = re.compile(r'<title>(.*?)</title>')
answerPattern = re.compile(r'zm-editable-content clearfix">((.|\n)*?)</div>')
possibleTimePattern = re.compile(r'<a class="answer-date-link (.*) href=(.*?)</a>')
timePattern = re.compile(r' ((\d|-|:)*)')
shortLinkPattern = re.compile(r'"(/question/.*?)"')

s = requests.session()

# 模拟浏览器，登陆
login_data = {
    'email': email,
    'password': password
}
s.post(zhihuUrl + '/login/email', login_data)

#更新http Request Headers
httpRequestHeaders = {
	'Connection':'keep-alive',
	'Cookie':cookie,
	'DNT':1,
	'Host':'www.zhihu.com',
	'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/43.0.2357.130 Chrome/43.0.2357.130 Safari/537.36',
	'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}
s.headers.update(httpRequestHeaders)

#获取目标用户 问题回答页
r = s.get(zhihuUrl + '/people/' + username + '/answers')

#获取目标用户 所有回答的链接和赞同数
foundList = pagePattern.findall(r.content)
maxPage = 0
if len(foundList) > 0:
	maxPagePattern = re.compile(r'\d+')
	for item in foundList:
		tmp = maxPagePattern.findall(item)
		if len(tmp)	> 0 and int(tmp[0]) > maxPage:
			maxPage = int(tmp[0])

answerLinks = [] 

#answerLinks 中包含 该回答的短链接， 答案赞同数
f = open(username + '_answerLinks.csv', 'w')

for i in range(0, maxPage):
	#pre 前缀指的是 present 而不是 previous
	preUrl = answerPageUrl + str(i+1)
	preR = s.get(preUrl)
	if preR.status_code == 200:
		answerLink = answerLinkPattern.findall(preR.content)
		approveNum = approveNumPattern.findall(preR.content) # TODO: BUG_如果一个回答是0赞的话，approveNumPattern会匹配不到（应修改正则表达式，或者改用finditer而不是findall（这一项匹配不到时补上0）
		while len(answerLink) - len(approveNum) < 0:
			answerLink.append("error")
		while len(answerLink) - len(approveNum) > 0:
			approveNum.append("0")
		for j in range(0, len(answerLink)):
			f.write(zhihuUrl + answerLink[j] + ',' + approveNum[j] + '\n')
			answerLinks.append(zhihuUrl + answerLink[j])
	else:
		print "[ERROR]", "status_code is", preR.status_code, "when getting answers of page", i
	if i % 100 == 0:
		print "[INFO]", "first", i, "answer links have been gotten."
f.close()

f = open(username + '_answerLinks.csv', 'r')
links = f.readlines()
f.close()

#answerInfos 中包含 该回答的短链接， 答案赞同数， 回答时间
#answerDetails 中包含 该回答的短链接， 答案内容， 问题内容
f = open(username + '_answerInfos.csv', 'w')
fD = open(username + '_answerDetails.dat', 'w')

for i in range(0, len(links)):
    question = "error"
    answer = "error"
    answerTime = "error"
    shortLink = "error"

    preLink = links[i].split(",")[0]
    preR = s.get(preLink)
    preApproveNum = links[i].split(",")[1][:-1]

    if preR.status_code == 200:
        answer = answerPattern.findall(preR.content)
        question = questionPattern.findall(preR.content)
        possibleTimeStr = possibleTimePattern.findall(preR.content)
        question = (question[0][:] if len(question) != 0 else "error") #TODO: 滤掉" - xxx 的回答 - 知乎"
        answer = (answer[0][0][:-3] if len(answer) != 0 else "error")
        # 因为possibleTimePattern会匹配到其他用户回答问题的时间，所以需要筛选（通过判断shortLink是否匹配）
        for strs in possibleTimeStr:
            for item in strs:
                for term in shortLinkPattern.findall(item):
                    if term in preLink:
                        shortLink = term
                        answerTime = timePattern.findall(item)
                        if '-' in answerTime[0][0]:
                            answerTime = answerTime[0][0]
                        else:
                            answerTime = time.strftime('%Y-%m-%d')
                            # 如果是当天的回答，zhihu会显示 时:分，否则会显示 年-月-日
    else:
        print "[ERROR]", "status_code is", preR.status_code, "when getting (index)", i, "answers"
    f.write(str(i) + "," + shortLink + "," + preApproveNum + "," + answerTime + "\n")
    fD.write(str(i) + "]>]>]>" + shortLink + "]>]>]>" + "]>]>]>" + question + "]>]>]>" + answer + "\n")
    print "[INFO]", "Infos and details of first", i+1, "answers have been gotten."

f.close()
fD.close()