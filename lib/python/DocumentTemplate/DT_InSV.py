#!/bin/env python
############################################################################## 
#
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
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
############################################################################## 
__doc__='''Sequence variables support


$Id: DT_InSV.py,v 1.4 1998/05/08 14:54:40 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

from string import lower, upper, rfind
from math import sqrt
TupleType=type(())
try:
    import Missing
    mv=Missing.Value
except: mv=None


class sequence_variables:

    def __init__(self,items=None,query_string='',start_name_re=None):
	
	self.items=items
	self.query_string=query_string
	self.start_name_re=start_name_re

	self.data=data={
	    'previous-sequence': 0,
	    'next-sequence': 0,
	    'sequence-start': 1,
	    'sequence-end': 0,
	    }


    def number(self,index): return index+1
    def even(self,index): return index%2 == 0
    def odd(self,index): return index%2
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

    def first(self,name,key=''):
	data=self.data
	if data['sequence-start']: return 1
	index=data['sequence-index']
	return self.value(index,name) != self.value(index-1,name)

    def last(self,name,key=''):
	data=self.data
	if data['sequence-end']: return 1
	index=data['sequence-index']
	return self.value(index,name) != self.value(index+1,name)

    def length(self, ignored):
	l=self.data['sequence-length']=len(self.items)
	return l

    def query(self, *ignored):
	if self.start_name_re is None: raise KeyError, 'sequence-query'
        query_string=self.query_string
        while query_string and query_string[:1] in '?&':
            query_string=query_string[1:]
        while query_string[-1:] == '&':
            query_string=query_string[:-1]
        if query_string:
            query_string='&%s&' % query_string                  
            re=self.start_name_re
            l=re.search(query_string)
            if l >= 0:
                v=re.group(0)
                query_string=(query_string[:l]+
                              query_string[l+len(v)-1:])
            query_string='?'+query_string[1:]
        else: query_string='?'
        self.data['sequence-query']=query_string
        return query_string
	

    statistic_names=(
	'total', 'count', 'min', 'max', 'median', 'mean',
	'variance', 'variance-n','standard-deviation', 'standard-deviation-n',
	)

    def statistics(self,name,key):
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
	    data['standard-deviation-n-%s' % name]=sqrt(sumsq)
	    if count > 1:
		sumsq=sumsq*n/(n-1)
		data['variance-%s' % name]=sumsq
		data['standard-deviation-%s' % name]=sqrt(sumsq)	    
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

	return data[key]

    def next_batches(self, suffix='batches',key=''):
	if suffix != 'batches': raise KeyError, key
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

    def previous_batches(self, suffix='batches',key=''):
	if suffix != 'batches': raise KeyError, key
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


    special_prefixes={
	'first': first,
	'last': last,
	'previous': previous_batches,
	'next': next_batches,
	# These two are for backward compatability with a missfeature:
	'sequence-index': lambda self, suffix, key: self['sequence-'+suffix],
	'sequence-index-is': lambda self, suffix, key: self['sequence-'+suffix],
	}
    for n in statistic_names: special_prefixes[n]=statistics

    def __getitem__(self,key,
		    special_prefixes=special_prefixes,
                    special_prefix=special_prefixes.has_key
                    ):
        data=self.data
        if data.has_key(key): return data[key]

        l=rfind(key,'-')
	if l < 0: raise KeyError, key

        suffix=key[l+1:]
        prefix=key[:l]

        if hasattr(self, suffix):
	    try: v=data[prefix+'-index']
	    except: pass
	    else: return getattr(self,suffix)(v)

	if special_prefix(prefix):
	    return special_prefixes[prefix](self, suffix, key)

        if prefix[-4:]=='-var':
            prefix=prefix[:-4]
            try: return self.value(data[prefix+'-index'],suffix)
            except: pass

        if key=='sequence-query': return self.query()
            
        raise KeyError, key


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
	    try: sequence[end+orphan-1]
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
	try: sequence[end+orphan-1]
	except: end=len(sequence)
	# if l - end < orphan: end=l
    return start,end,size

############################################################################## 
#
# $Log: DT_InSV.py,v $
# Revision 1.4  1998/05/08 14:54:40  jim
# Fixed bug in handling of sequence-query.
#
# Revision 1.3  1998/04/20 15:16:56  jim
# Fixed bug in backward support for sequence-index-even etc.
#
# Revision 1.2  1998/04/03 19:28:41  jim
# Fixed statistics bug.
#
# Revision 1.1  1998/04/02 17:37:36  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
#
