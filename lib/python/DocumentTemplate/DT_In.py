
'''Sequence insertion

       A sequence may be inserted using an 'in' command.  The 'in'
       command specifies the name of a sequence object and text to
       be inserted for each element in the sequence.  

       The EPFS syntax for the in command is::

          %(in name)[
               text
          %(in name)]

       The HTML syntax for the in command is::

          <!--#in name-->
               text 
          <!--#/in name-->

      See the example below that shows how 'if', 'else', and 'in' commands
      may be combined to display a possibly empty list of objects.

      The text included within an 'in' command will be refered to
      as an 'in' block.

    Synopsis

      If the variable 'sequence' exists as a sequence, a simple case
      of the 'in' tag is used as follows:

        '<!--#in sequence-->some markup<!--#/in-->'

      A more complete case is used as follows:

        '<!--#in sequence sort=age-->'
	'  <!--#var sequence-number-->) <!--#var age-->'
	'<!--#/in-->'

    Attributes

      sort -- Define the sort order for sequence items.  If an item in
      the sequence does not define 

      Within an 'in' block, variables are substituted from the
      elements of the iteration.  The elements may be either
      instance or mapping objects.  In addition, the variables:

         sequence-item -- The element.

         sequence-index -- The index, starting from 0, of the
           element within the sequence.

         sequence-number -- The index, starting from 1, of the
           element within the sequence.

         sequence-letter -- The index, starting from 'a', of the
           element within the sequence.

         sequence-Letter -- The index, starting from 'A', of the
           element within the sequence.

         sequence-roman -- The index, starting from 'i', of the
           element within the sequence.

         sequence-Roman -- The index, starting from 'I', of the
           element within the sequence.

         sequence-start -- A variable that is true if the element
           being displayed is the first of the displayed elements,
           and false otherwise.

         sequence-end -- A variable that is true if the element
           being displayed is the last of the displayed elements,
           and false otherwise.

      are defined for each element.

      Normally, 'in' blocks are used to iterate over sequences of
      instances.  If the optional parameter 'mapping' is specified
      after the sequence name, then the elements of the sequence
      will be treated as mapping objects.

      An 'in' command may be used to iterate over a sequence of
      dictionary items.  If the elements of the iteration are
      two-element tuples, then then the template code given in the
      'in' block will be applied to the second element of each
      tuple and may use a variable, 'sequence-key' to access the
      first element in each tuple.

    Batch sequence insertion

      When displaying a large number of objects, it is sometimes
      desireable to display just a sub-sequence of the data.
      An 'in' command may have optional parameters,
      as in::

          <!--#in values start=start_var size=7-->

      The parameter values may be either integer literals or
      variable names.

      Up to five parameters may be set:

          start   -- The number of the first element to be shown,
                     where elements are numbered from 1.

          end     -- The number of the last element to be shown,
                     where elements are numbered from 1.

          size    -- The desired number of elements to be shown at
                     once.

          orphan  -- The desired minimum number of objects to be
                     displayed.  The default value for this
                     parameter is 3.

          overlap -- The desired overlap between batches. The
                     default is no overlap.     

      Typically, only 'start' and 'size' will be specified.

      When batch insertion is used, several additional variables are
      defined for use within the sequence insertion text:

          sequence-step-size -- The batch size used.

          previous-sequence -- This variable will be true when the
             first element is displayed and when the first element
             displayed is not the first element in the sequence.

          previous-sequence-start-index -- The index, starting from
             0, of the start of the batch previous to the current
             batch.

          previous-sequence-end-index -- The index, starting from
             0, of the end of the batch previous to the current
             batch.

          previous-sequence-size -- The size of the batch previous to
             the current batch.

          previous-batches -- A sequence of mapping objects
             containing information about all of the batches prior
             to the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-end-index -- The size of the batch.

          next-sequence -- This variable will be true when the last
             element is displayed and when the last element
             displayed is not the last element in the sequence.

          next-sequence-start-index -- The index, starting from
             0, of the start of the batch after the current
             batch.

          next-sequence-end-index -- The index, starting from
             0, of the end of the batch after the current
             batch.

          next-sequence-size -- The size of the batch after
             the current batch.

          next-batches -- A sequence of mapping objects
             containing information about all of the batches after
             the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-end-index -- The size of the batch.

      For each of the variables listed above with names ending in
      "-index", there are variables with names ending in "-number",
      "-roman", "-Roman", "-letter", and "-Letter" that are indexed
      from 1, "i", "I", "a", and "A", respectively.  In addition,
      for every one of these variables there are variables with
      names ending in "-var-xxx", where "xxx" is an element
      attribute name or key.

    Summary statistics

      When performing sequence insertion, special variables may be
      used to obtain summary statistics.  To obtain a summary
      statistic for a variable, use the variable name:
      'statistic-name', where 'statistic' is a statistic name and
      'name' is the name of a data variable.

      Currently supported statistic names are:

	total -- The total of numeric values.

	count -- The total number of non-missing values.

	min -- The minimum of non-missing values.

	max -- The maximum of non-missing values.

	median -- The median of non-missing values.

	mean -- The mean of numeric values values.

	variance -- The variance of numeric values computed with a
	  degrees of freedom qeual to the count - 1.

	variance-n -- The variance of numeric values computed with a
	  degrees of freedom qeual to the count.

	standard-deviation -- The standard deviation of numeric values
	  computed with a degrees of freedom qeual to the count - 1.

	standard-deviation-n -- The standard deviation of numeric
	  values computed with a degrees of freedom qeual to the count.

      Missing values are either 'None' or the attribute 'Value'
      of the module 'Missing', if present.
''' #'

__rcs_id__='$Id: DT_In.py,v 1.10 1997/11/11 18:38:03 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.10 $'[11:-2]

from DT_Util import *
from string import find, atoi, join
import regex
from regsub import gsub

class In:
    blockContinuations=('else',)
    name='in'
    elses=None
    expr=None
    start_name_re=None
    
    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='', start='1',end='-1',size='10',
			  orphan='3',overlap='1',mapping=1,
			  previous=1, next=1, expr='', sort='')
	self.args=args
	if args.has_key('start'):
	    v=args['start']
	    if type(v)==type(''):
		try: atoi(v)
		except:
		    self.start_name_re=regex.compile(
			'[?&]'+
			join(map(lambda c: "[%s]" % c, v),'')+
			'=[0-9]+\(&\|$\)')
		    
	name,expr=name_param(args,'in',1)
	self.__name__, expr = name, expr
	self.section=section
	if len(blocks) > 1:
	    if len(blocks) != 2: raise ParseError, (
		'too many else blocks', 'in')
	    tname, args, section = blocks[1]
	    args=parse_params(args, name='')
	    if args:
		ename=name_param(args)
		if ename != name:
		    raise ParseError, (
			'name in else does not match in', 'in')
	    self.elses=section
	    

    def render(self, md):
	expr=self.expr
	if expr is None: sequence=md[self.__name__]
	else: sequence=expr.eval(md)

	if not sequence:
	    if self.elses: return self.elses(None, md)
	    return ''

	section=self.section
	params=self.args
	nbatchparams=len(params)-1

	if params.has_key('mapping'):
	    mapping=1
	    nbatchparams=nbatchparams-1
	else:
	    mapping=0

	if params.has_key('sort'):
	    sort=params['sort']
	    nbatchparams=nbatchparams-1
	    s=[]
	    for client in sequence:
		if type(client)==TupleType and len(client)==2: v=client[1]
		else: v=client
		if mapping: v=v[sort]
		else: v=getattr(v, sort)
		try: v=v()
		except: pass
		s.append((v,client))
	    s.sort()
	    sequence=[]
	    for v, client in s: sequence.append(client)

	next=previous=0
	if nbatchparams:
	    try: start=int_param(params,md,'start',0)
	    except: start=1
	    end=int_param(params,md,'end',0)
	    size=int_param(params,md,'size',0)
	    overlap=int_param(params,md,'overlap',0)
	    orphan=int_param(params,md,'orphan','3')
	    start,end,sz=opt(start,end,size,orphan,sequence)
	    if params.has_key('next'): next=1
	    if params.has_key('previous'): previous=1
	else:
	    start=1
	    end=len(sequence)

	last=end-1
	first=start-1

	try: query_string=md['QUERY_STRING']
	except: query_string=''

	vars=sequence_variables(sequence,'?'+query_string,self.start_name_re)
	kw=vars.data
	# kw['sequence-length']=l
	kw['mapping']=mapping
	if nbatchparams:
	    kw['sequence-step-size']=sz
	    kw['sequence-step-overlap']=overlap
	    kw['sequence-step-start']=start
	    kw['sequence-step-end']=end
	    kw['sequence-step-orphan']=orphan
	try:
	    md.push(vars)
	    if previous:
		if first > 0:
		    pstart,pend,psize=opt(None,first+overlap,
					  sz,orphan,sequence)
		    kw['previous-sequence']=1
		    kw['previous-sequence-start-index']=pstart-1
		    kw['previous-sequence-end-index']=pend-1
		    kw['previous-sequence-size']=pend+1-pstart
		    result=section(None,md)
		else: result=''
	    elif next:
		try:
		    # The following line is a neaky way to test whether
		    # there are more items, without actually
		    # computing a length:
		    sequence[end]
		    pstart,pend,psize=opt(end+1-overlap,None,
					  sz,orphan,sequence)
		    kw['next-sequence']=1
		    kw['next-sequence-start-index']=pstart-1
		    kw['next-sequence-end-index']=pend-1
		    kw['next-sequence-size']=pend+1-pstart
		    result=section(None,md)
		except: result=''
	    else:
		result = []
		for index in range(first,end):
		    if nbatchparams:
			if index==first and index > 0:
			    pstart,pend,psize=opt(None,index+overlap,
						  sz,orphan,sequence)
			    kw['previous-sequence']=1
			    kw['previous-sequence-start-index']=pstart-1
			    kw['previous-sequence-end-index']=pend-1
			    kw['previous-sequence-size']=pend+1-pstart
			else:
			    kw['previous-sequence']=0
			    if index==last:
				try:
				    # The following line is a neaky way to
				    # test whether there are more items,
				    # without actually computing a length:
				    sequence[end]
				    pstart,pend,psize=opt(end+1-overlap,None,
							  sz,orphan,sequence)
				    kw['previous-sequence']=0
				    kw['next-sequence']=1
				    kw['next-sequence-start-index']=pstart-1
				    kw['next-sequence-end-index']=pend-1
				    kw['next-sequence-size']=pend+1-pstart
				except: pass
    	
		    if index==first: kw['sequence-start']=1
		    else: kw['sequence-start']=0
		    if index==last: kw['sequence-end']=1
		    else: kw['sequence-end']=0
		    client=sequence[index]
		    kw['sequence-index']=index
		    if type(client)==TupleType and len(client)==2:
			client=client[1]
		    if mapping:
			client=mapping_wrapper(client)
		    result.append(section(client,md))
		result=join(result, '')
	finally:
	    md.pop(1)

	return result

    __call__=render

def int_param(params,md,name,default=0):
    try: v=params[name]
    except: v=default
    if v:
	try: v=atoi(v)
	except:
	    v=md[v]
	    if type(v)==types.StringType:
		v=atoi(v)
    return v

def opt(start,end,size,orphan,sequence):
    if size < 1:
	if start > 0 and end > 0 and end >= start:
	    size=end+1-start
	else: size=7
    if start > 0:

	try: sequence[start-1]
	except: start=len(sequence)
	# if start > l: start=l

	if end > 0:
	    if end > start: end=start
	else:
	    end=start+size-1
	    try: sequence[end+orphan]
	    except: end=len(sequence)
	    # if l - end < orphan: end=l
    elif end > 0:
	try: sequence[end-1]
	except: end=len(sequence)
	# if end > l: end=l
	start=end+1-size
	if start - 1 < orphan: start=1
    else:
	start=1
	end=start+size-1
	try: sequence[end+orphan]
	except: end=len(sequence)
	# if l - end < orphan: end=l
    return start,end,size

class mapping_wrapper:
    def __init__(self,mapping):
	self.mapping=mapping

    def __getattr__(self,name):
	return self.mapping[name]

class sequence_variables:

    def __init__(self,items=None,query_string='',start_name_re=None):
	
	self.items=items
	self.query_string=query_string
	self.start_name_re=start_name_re

	self.data={
	    'previous-sequence': 0,
	    'next-sequence': 0,
	    }

    def number(self,index): return index+1
    def letter(self,index): return chr(ord('a')+index)
    def Letter(self,index): return chr(ord('A')+index)
    def key(self,index):    return self.items[index][0]
    def item(self,index, tt=type(())):
	i=self.items[index]
	if type(i) is tt and len(i)==2: return i[1]
	return i

    def roman(self,index): return lower(self.Roman(index))

    def Roman(self,num):
	# Force number to be an integer value
	num = int(num)+1

	# Initialize roman as an empty string
        roman = ''

	while num >= 1000:
		num = num - 1000
                roman = '%sM' % roman

	while num >= 500:
		num = num - 500
                roman = '%sD' % roman

	while num >= 100:
		num = num - 100
	        roman = '%sC' % roman

	while num >= 50:
		num = num - 50
                roman = '%sL' % roman

	while num >= 10:
		num = num - 10
	        roman = '%sX' % roman                 

	while num >= 5:
		num = num - 5
	        roman = '%sV' % roman

	while num < 5 and num >= 1:
		num = num - 1
	        roman = '%sI' % roman

	# Replaces special cases in Roman Numerals
	roman = sub('DCCCC', 'CM', roman)
	roman = sub('CCCC', 'CD', roman)
	roman = sub('LXXXX', 'XC', roman)
	roman = sub('XXXX', 'XL', roman)
	roman = sub('VIIII', 'IX', roman)
	roman = sub('IIII', 'IV', roman)

	return roman


    def value(self,index,name):
	data=self.data
	item=self.items[index]
	if type(item)==TupleType and len(item)==2:
	    item=item[1]
	if data['mapping']: return item[name]
	return getattr(item,name)

    def first(self,name):
	data=self.data
	if data['sequence-start']: return 1
	index=data['sequence-index']
	return self.value(index,name) != self.value(index-1,name)

    def last(self,name):
	data=self.data
	if data['sequence-end']: return 1
	index=data['sequence-index']
	return self.value(index,name) != self.value(index+1,name)

    statistic_names=(
	'total', 'count', 'min', 'max', 'median', 'mean',
	'variance', 'variance-n','standard-deviation', 'standard-deviation-n',
	)

    def statistics(self,name):
	try:
	    import Missing
	    mv=Missing.Value
	except: mv=None
	items=self.items
	data=self.data
	mapping=data['mapping']
	count=sum=sumsq=0
	min=max=None
	scount=smin=smax=None
	values=[]
	svalues=[]
	for item in items:
	    try:
		if mapping: item=item[name]
		else: item=getattr(item,name)
		try:
		    s=item*item
		    sum=sum+item
		    sumsq=sumsq+s
		    values.append(item)
		    if min is None:
			min=max=item
		    else:
			if item < min: min=item
			if item > max: max=item
		except:
		    if item is not None and item is not mv:
			if smin is None: smin=smax=item
			else:
			    if item < smin: smin=item
			    if item > smax: smax=item
			svalues.append(item)
	    except: pass

	# Initialize all stats to empty strings:
	for stat in self.statistic_names: data['%s-%s' % (stat,name)]=''

	count=len(values)
	try: # Numeric statistics
	    n=float(count)
	    mean=sum/n
	    sumsq=sumsq/n - mean*mean
	    data['mean-%s' % name]=mean
	    data['total-%s' % name]=sum
	    data['variance-n-%s' % name]=sumsq
	    data['standard-deviation-n-%s' % name]=math.sqrt(sumsq)
	    if count > 1:
		sumsq=sumsq*n/(n-1)
		data['variance-%s' % name]=sumsq
		data['standard-deviation-%s' % name]=math.sqrt(sumsq)	    
	    else:
		data['variance-%s' % name]=''
		data['standard-deviation-%s' % name]=''
	except:
	    if min is None: min,max,values=smin,smax,svalues
	    else:
		if smin < min: min=smin
		if smax > max: max=smax
		values=values+svalues
	    count=len(values)

	data['count-%s' % name]=count
	# data['_values']=values
	if min is not None:
	    data['min-%s' % name]=min
	    data['max-%s' % name]=max
	    values.sort()
	    if count==1:
		data['median-%s' % name]=min
	    else:
		n=count+1
		if n/2*2==n: data['median-%s' % name]=values[n/2-1]
		else:
		    n=n/2
		    try: data['median-%s' % name]=(values[n]+values[n-1])/2
		    except:
			try: data['median-%s' % name]=(
			    "between %s and %s" % (values[n],values[n-1]))
			except: pass
	

    def __getitem__(self,key):
	data=self.data
	try: return data[key]
	except:
	    if key=='previous-batches':
		return self.previous_batches()
	    if key=='next-batches':
		return self.next_batches()
	    l=rfind(key,'-')
	    suffix=key[l+1:]
	    prefix=key[:l]
	    try: return getattr(self,suffix)(data[prefix+'-index'])
	    except:
		if prefix[-4:]=='-var':
		    prefix=prefix[:-4]
		    try: return self.value(data[prefix+'-index'],suffix)
		    except: pass
		elif prefix in self.statistic_names:
		    self.statistics(suffix)
		    return data[key]
		elif prefix=='first': return self.first(suffix)
		elif prefix=='last': return self.last(suffix)
		elif key=='sequence-length':
		    data[key]=l=len(self.items)
		    return l
		elif key=='sequence-query' and self.start_name_re is not None:
		    query_string=self.query_string
		    re=self.start_name_re
		    l=re.search(query_string)
		    if l >= 0:
			v=re.group(0)
			if v[:1]=='?' or v[-1:]=='&': b=l+1
			else: b=l
			query_string=query_string[:b]+query_string[l+len(v):]
		    data[key]=query_string
		    return query_string
		    
		raise KeyError, key

    def next_batches(self):
	data=self.data
	sequence=self.items
	try:
	    if not data['next-sequence']: return ()
	    sz=data['sequence-step-size']
	    start=data['sequence-step-start']
	    end=data['sequence-step-end']
	    l=len(sequence)
	    orphan=data['sequence-step-orphan']
	    overlap=data['sequence-step-overlap']
	except: AttributeError, 'next-batches'
	r=[]
	while end < l:
	    start,end,spam=opt(end+1-overlap,None,sz,orphan,sequence)
	    v=sequence_variables(self.items,
				 self.query_string,self.start_name_re)
	    d=v.data
	    d['batch-start-index']=start-1
	    d['batch-end-index']=end-1
	    d['batch-size']=end+1-start
	    d['mapping']=data['mapping']
	    r.append(v)
	data['next-batches']=r
	return r

    def previous_batches(self):
	data=self.data
	sequence=self.items
	try:
	    if not data['previous-sequence']: return ()
	    sz=data['sequence-step-size']
	    start=data['sequence-step-start']
	    end=data['sequence-step-end']
	    l=len(sequence)
	    orphan=data['sequence-step-orphan']
	    overlap=data['sequence-step-overlap']
	except: AttributeError, 'previous-batches'
	r=[]
	while start > 1:
	    start,end,spam=opt(None,start-1+overlap,sz,orphan,sequence)
	    v=sequence_variables(self.items,
				 self.query_string,self.start_name_re)
	    d=v.data
	    d['batch-start-index']=start-1
	    d['batch-end-index']=end-1
	    d['batch-size']=end+1-start
	    d['mapping']=data['mapping']
	    r.append(v)
	r.reverse()
	data['previous-batches']=r
	return r

############################################################################
# $Log: DT_In.py,v $
# Revision 1.10  1997/11/11 18:38:03  jim
# Made sequence-items work when iterating over mapping items.
#
# Revision 1.9  1997/11/07 17:08:33  jim
# Changed so exception is raised if a sequence cannot be gotten during
# rendering.
#
# Revision 1.8  1997/10/28 16:33:49  paul
# Small change to docstring.
#
# Revision 1.7  1997/10/05 19:50:58  jim
# Made sort work with methods.
#
# Revision 1.6  1997/10/05 19:41:59  jim
# Added sort option.
#
# Revision 1.5  1997/09/25 20:58:24  jim
# Added sequence-query to *vastly* simplify browse by batch!
#
# Revision 1.4  1997/09/25 18:56:38  jim
# fixed problem in reporting errors
#
# Revision 1.3  1997/09/22 14:42:50  jim
# added expr
#
# Revision 1.2  1997/09/02 19:04:24  jim
# Got rid of ^Ms
#
# Revision 1.1  1997/08/27 18:55:42  jim
# initial
#
#
