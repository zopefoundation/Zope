"test parses for sql grammar"

test = [
"select a from x where b=c",
"select distinct x.a from x where x.b=c",
"select all a from x where b=c",
"select a from x, y where b=c or x.d=45",
"select a as k from x d, y as m where b=c",
"select 1 as n, a from x where b=c",
"select * from x",
"select a from x where b=c",
"select a from x where not b=c or d=1 and e=5",
"select a from x where a=1 and (x.b=3 or not b=c)",
]