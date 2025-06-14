import pandas as pd
import re

def markdown_to_df(markdown_table):
    table = markdown_table.strip().split('\n')

    output = []

    for i in table:
        line = i.strip().split('|')
        k = []
        for j in line:
            j = j.strip()
            if j:
                k.append(j)
        output.append(k)
    
    print(output)

markdown_to_df('''|Название       |Вес, г|Ккал|Б, г|Ж, г|У, г|
|---------------|------|----|----|----|----|
|Жареное мясо  |175   |280 |20.0|22.5|3.0 |
|Каша           |175   |110 |3.5 |1.5 |22.0|
|Белый хлеб     |75    |270 |8.0 |3.5 |52.5|
|ИТОГО          |425   |660 |31.5|27.5|77.5|''')