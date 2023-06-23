# compares the official lima dataset with ours to see how much overlap their is
import jsonlines
file = jsonlines.open("../official_lima_train.jsonl")
official = []
for i in file:
  if i['source'] == 'stackexchange':
    question = i['conversations'][0]
    answer = i['conversations'][1]
    official.append(question)
  
other = jsonlines.open("dataset.jsonl")
mine = []
for i in other:
  question = i['title']
  mine.append(question)

print(len(official))

from Levenshtein import ratio
print(ratio("".join(official), "".join(mine)))