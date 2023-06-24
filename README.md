# Reproduce LIMA

a smol effort to reproduce Meta's Less is More for Aligment (LIMA)

Hypothesis: Tiny finetuning dataset size only worked well because of significant overlap with the pretraining dataset.

## Data

After manual analysis of the published dataset and cross referencing with stack exchange and r/WritingPrompts, it's clear most of the selected prompts fall outside of the top 1% in upvoted reddit submissions and stack exchange questions. My best guess is Meta used random sampling with a very small filter to filter out submissions/questions with tiny scores. Then, manually reviewed and selected their prompts.

The LIMA paper reads like they just take the highest upvoted questions/submissions that look useful, but I guess this isn't too surprising that they go down to scores in the single digits because that's where the diversity is.

## Training

todo

## Evaluation

todo

## Instructions

Need 128GB ram for downloading/unzipping the dataset

For stackexchange, run `python3 stackexchange.py` (takes 40m on my 128GB 48CPU cloud VM *after* the downloads finish)
This will apply automatic quality filters and get the top 1,000 QA pairs from each exchange.
It will also tell you how many examples from each stack exchange community should be included in the final dataset.
From here on, you'll need to manually filter to build your dataset

Manual filtering rules (done "manually" by gpt3.5)
* Question is self contained in the title. (not implemented)
* Answer should not be written in first person
* Answer should not reference other answers

You should end up with 400 QA pairs from stack exchange. This takes me about 2 hours.

Then i run the script `python3 compare.py stackexchange` which tells me there's 20% overlap with my dataset versus the version that the LIMA team published.

Pushshift (reddit data source for LIMA) is no longer online. Their data is hosted by [the eye](https://the-eye.eu/redarcs/).