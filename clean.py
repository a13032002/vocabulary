#!/usr/bin/env python3.2
import sys
from pymongo import MongoClient
from auto_dict import word_filter
HOST = "localhost"


def main(argv):

	client = MongoClient(HOST)
	
	db = client['word']
	words = db.words;

	word_list = words.find()
	for word in word_list:
		seen = set()
		for type_record in word["types"]:
			for meaning in type_record["meanings"]:
				seen.add(meaning)
	
		new_other = []
		update = False
		for m in word["others"]:
			if word_filter(m) and m not in seen:
				new_other.append(m)
			else:
				update = True

		word["others"] = new_other
		words.update({'_id':word["_id"]}, {"$set":{"others": new_other}}, upsert=False)

if __name__ == '__main__':
	sys.exit(main(sys.argv))
		
	

