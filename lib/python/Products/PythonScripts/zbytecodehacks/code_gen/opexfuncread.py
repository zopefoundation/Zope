import os,string

file=open(os.path.join(os.path.dirname(__file__ ),'op_execute_methods'),'r')

lines=string.split(file.read(),'\n')[1:]

exec_funcs={}

n=len(lines)

for i in range(n):
    if (not lines[i]) or lines[i][0]==' ':
        continue
    j=i
    body=[]
    while j<n:
        if lines[j][0]==' ':
            while lines[j] and lines[j][0]==' ':
                body.append(lines[j])
                j=j+1
            break
        j=j+1
    body='    '+string.join(body,'\n    ')
    exec_funcs[lines[i][:-1]]=body
    
