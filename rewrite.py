import re

with open("docs/documentation.tex", "r", encoding="utf-8") as f:
    text = f.read()

# Tone and Style Replacements
replacements = [
    (r"This section explores the data pipeline", r"The data pipeline architecture"),
    (r"This section explores", r"This section details"),
    (r"delve into", r"analyze"),
    (r"delves into", r"analyzes"),
    (r"a testament to", r"demonstrating"),
    (r"seamlessly", r""),
    (r"seamless", r""),
    (r"pivotal", r"critical"),
    (r"landscape", r"environment"),
    (r"In conclusion,", r""),
    (r"robust", r"fault-tolerant"),
    (r"elevate", r"improve"),
    (r"leveraging", r"using"),
    (r"state-of-the-art", r"modern"),
    (r"trustworthiness", r"interpretability"),
    
    # Meta-commentary removal
    (r"As we can see from the figure above,", r""),
    (r"The following table summarizes", r"Table \ref{...} details"),
    (r"This chapter will discuss", r""),
    (r"Let\'s examine", r"Examining"),
]

for old, new in replacements:
    text = re.sub(old, new, text, flags=re.IGNORECASE)

with open("docs/documentation.tex", "w", encoding="utf-8") as f:
    f.write(text)
