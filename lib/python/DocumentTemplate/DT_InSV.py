##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Sequence variables support


$Id: DT_InSV.py,v 1.18 2001/01/16 21:57:19 chrism Exp $'''
__version__='$Revision: 1.18 $'[11:-2]

from string import lower, rfind, split, join
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


    def __len__(self): return 1
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
            l=re.search_group(query_string, (0,))
            if l:
                v=l[1]
                l=l[0]
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
                    if item is mv:
                        item = None
                    if type(item)==type(1):
                        s=item*long(item)
                    else:
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
            start,end,spam=opt(end+1-overlap,0,sz,orphan,sequence)
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
            start,end,spam=opt(0,start-1+overlap,sz,orphan,sequence)
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




def sub(s1, s2, src):
    return join(split(src, s1), s2)

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
            if end < start: end=start
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
