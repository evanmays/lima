# Reproduce LIMA

Weekend effort to reproduce Meta's Less is More for Aligment (LIMA)

Hypothesis: Tiny finetuning dataset size only worked well because of significant overlap with the pretraining dataset.

I cheat by using their already published paper author prompts.

Half finished, accepting PRs

- [ ] Stack Exchange (STEM)
- [ ] Stack Exchange (Other)
- [ ] wikiHow
- [ ] Pushshift r/WritingPrompts
- [ ] Natural Instructions
- [ ] Paper Authors (Group A)

## Instructions

Need 128GB ram for downloading/unzipping the dataset

For stackexchange, run `python3 stackexchange.py` (takes 5m on my 128GB 48CPU cloud VM *after* the downloads finish)
This will apply automatic quality filters and get the top 1,000 QA pairs from each exchange.
It will also tell you how many examples from each stack exchange community should be included in the final dataset.
From here on, you'll need to manually filter to build your dataset

Manual filtering rules
* Question is self contained in the title.
* Answer should not be written in first person
* Answer should not reference other answers

You should end up with 400 QA pairs from stack exchange. This takes me about 2 hours.

Then i run the script `python3 compare.py stackexchange` which tells me there's 80% overlap with my dataset versus the version that the LIMA team published.