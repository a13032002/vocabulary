#!/usr/bin/env python3
HOST = "localhost"
import sys
from pymongo import MongoClient
from time import strptime, mktime
from pyquery import PyQuery as pq

def filter(record, time_begin, time_end):
	TIME_FORMAT = "%Y/%m/%d %H:%M:%S"
	insert_time = mktime(strptime(record['time'], TIME_FORMAT))
	
	if time_begin is not None:
		if mktime(strptime(time_begin, TIME_FORMAT)) > insert_time:
			return False
	
	if time_end is not None:
		if mktime(strptime(time_end, TIME_FORMAT)) < insert_time:
			return False
	
	return True

		

def get_words(host, tag = None, time_begin = None, time_end = None):
	client = MongoClient(host)
	
	db = client['word']
	words = db.words;

	word_list = words.find() if tag is None else words.find({'tag':tag})
	word_list = [word for word in word_list if filter(word, time_begin, time_end)]

	return word_list

def generate_html(word_list, output_file, title="Word List"):
	style = "td, tr {border:solid 1px black;}\ntable {border-collapse:collapse;}"
	html = pq("<html><head><meta charset=\"UTF-8\"><title>%s</title><style>%s</style></head><body></body></html>" % (title, style))
	body = html.find("body")
	table = pq("<table>")
	for idx, word in enumerate(word_list):
		type_count = len(word["types"]) + (1 if len(word["others"]) != 0 else 0)
		row = pq("<tr>")
		column = pq("<td>").attr('rowspan', str(type_count + 1)).html("%d. %s<br>%s" % (idx + 1, word["name"], word["kk"]))
		row.append(column).appendTo(table)
		for type_record in word["types"]:
			row = pq("<tr>")
			pq("<td>").html(type_record["name"]).appendTo(row)
			pq("<td>").html(';'.join(type_record["meanings"])).appendTo(row)
			row.appendTo(table)

		if len(word["others"]) > 0:
			row = pq("<tr>")
			pq("<td>").appendTo(row)
			pq("<td>").html(';'.join(word["others"])).appendTo(row)
			row.appendTo(table)
	
	table.appendTo(body)


	with open(output_file, 'w') as f:
		print("<html>", file=f)
		print(html.html(), file=f)
		print("</html>", file=f)
	

def main(argv):
	if len(argv) < 1 + 1:
		print("Usage : %s output_file [tag] [time_begin] [time_end]" % (argv[0],), file = sys.stderr)
		return -1

	tag = None
	output_file = argv[1]
	time_begin = None
	time_end = None

	if len(argv) > 1 + 1:
			tag = argv[2] if argv[2] != "None" else None
	if len(argv) > 1 + 2:
		time_begin = argv[3] if argv[3] != "None" else None
	if len(argv) > 1 + 3:
		time_end = argv[4] if argv[4] != "None" else None

	word_list = get_words(HOST, tag, time_begin, time_end)
	
	generate_html(word_list, output_file)

if __name__ == '__main__':
	sys.exit(main(sys.argv))
