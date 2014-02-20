#!/usr/bin/env python3.2
from pyquery import PyQuery as pq
from lxml import etree
import urllib
import sys
from pymongo import MongoClient
import time
HOST = "localhost"

def print_if_stored(word, host, tag):
	client = MongoClient(host)
	
	db = client['word']
	words = db.words;
	record = words.find_one({'name':word, 'tag':tag})
	if record is None: return False
	print (word, record['kk'], '(from db@%s, tag = %s, time:%s)' % (host, record["tag"], record["time"]))
	for t in record["types"]:
		print (t["name"]);
		for idx, (meaning, sample) in enumerate(zip(t["meanings"], t["samples"])):
			print ("\t%d. %s" % (idx + 1, meaning))
			if len(sample) > 0: print("\t\t%s" % (sample))
	
	print("---------Other Explanations----------")
	for i, meaning in enumerate(record['others']):
		print("\t%d. %s" %(i+1, meaning))
	
	return True;

def insert_to_db(word, host, record):
	client = MongoClient(host)
	
	db = client['word']
	words = db.words;
	words.insert(record)

def word_filter(string):
	if "【英】" in string :return False
	if "formal -【正式】" in string :return False
	for c in string:
		if 0x4e00 <= ord(c) and ord(c) <= 0x9fff:
			return True
	
	return False

def main(argv):
	if len(argv) != 1 + 2:
		print ("Usage : %s tag word " % (argv[0]), file = sys.stderr)
		return -1
		
	tag = argv[1]
	if print_if_stored(argv[2], HOST, tag):
		return 0


	yahoo_url = "http://tw.dictionary.yahoo.com/dictionary?p=%s" % (urllib.parse.quote(argv[2]))
	req = urllib.request.Request(yahoo_url)
	req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
	req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36')
	req.add_header('Accept-Encoding', 'html')
	req.add_header('Accept-Language','en-US,en;q=0.8,zh-TW;q=0.6')
	req.add_header('Referer', 'http://tw.dictionary.yahoo.com/')
	html = urllib.request.urlopen(req).read().decode('utf8')

	d = pq(html)
	types = d(".type-item");
	if types.size() <= 0:
		print("Word not found!", file=sys.stderr)
		return -1

	word = d.find('div.summary h2').eq(0).text()
	others = d.find('div.disambiguate-wrapper').find('div.summary')
	kk = d.find('dd').eq(0).text()
	print (word, kk, ('(save to db@%s, tag=%s)') % (HOST, tag))
	
	record = {'name' : word, 'types' : [], 'kk':kk, 'others': [], 'tag':tag, 'time':time.strftime('%Y/%m/%d %H:%M:%S')}
	

	seen = set()
	for i in range(types.size()):
		type_name = types.eq(i).find('div.type').text()
		print (type_name)
		type_record = {'name':type_name}
		meanings = []
		samples = []
		ols = types.eq(i).find('li.exp-item')
		for j in range(ols.size()):
			meaning = ols.eq(j).find('.exp').text()
			print ("\t%d. %s" % (j + 1, meaning))
			if ols.eq(j).find('.sample').size() > 0 :
					sample = ols.eq(j).find('.sample').text().replace("\n", "")
					sample = ' '.join([x for x in sample.split(' ') if len(x) > 0])
					print ("\t\t%s" % (sample))
			else:
				sample = ""
			seen.add(meaning)
			meanings.append(meaning)
			samples.append(sample)
			

		type_record['meanings'] = meanings
		type_record['samples'] = samples
	
		record['types'].append(type_record)

	print("---------Other Explanations----------")
	for i in range(others.size()):
		w = others.eq(i).find('h2').text()
		if w != word:continue
		meaning = others.eq(i).find('p.explanation').text()
		if not word_filter(meaning) or meaning in seen: continue
		print ("\t%d. %s" % (i + 1, meaning))
		record["others"].append(meaning)
		seen.add(meaning)
	
	insert_to_db(word, HOST, record)


if __name__ == '__main__':
	sys.exit(main(sys.argv))
