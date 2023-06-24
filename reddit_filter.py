import sys
import jsonlines
r = jsonlines.open(sys.argv[1])
print("Getting the score of the 500th most highest rated submission")
# takes < 1m for r/WritingPrompts submissions on my cloud VM
score_threshold = sorted((l['score'] for l in r), reverse=True)[500]
print("Found score threshold:", score_threshold)

# get about 500 of the highest rated submissions
r = jsonlines.open(sys.argv[1]) # need to reset file read
x = sorted((({'id': l['id'], 'title': l['title'], 'selftext': l['selftext'], 'score': l['score']}) for l in r if l['score'] > score_threshold), key=lambda item: item['score'], reverse=True)
print(x)
with jsonlines.open('out.jsonl', mode='w') as w:
    w.write_all(x)

print("Top 500 ish posts written to out.jsonl and you must now manually review them")