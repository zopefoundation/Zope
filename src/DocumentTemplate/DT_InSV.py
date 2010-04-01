##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Sequence variables support


$Id$'''
__version__='$Revision: 1.22 $'[11:-2]

from math import sqrt
import re

try:
    import Missing
    mv=Missing.Value
except: mv=None

TupleType = tuple

class sequence_variables:

    alt_prefix = None

    def __init__(self,items=None,query_string='',start_name_re=None,
                 alt_prefix=''):

        self.items=items
        self.query_string=query_string
        self.start_name_re=start_name_re
        if alt_prefix:
            self.alt_prefix = alt_prefix + '_'

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

    def roman(self,index): return self.Roman(index).lower()

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

        roman = roman.replace('DCCCC', 'CM')
        roman = roman.replace('CCCC', 'CD')
        roman = roman.replace('LXXXX', 'XC')
        roman = roman.replace('XXXX', 'XL')
        roman = roman.replace('VIIII', 'IX')
        roman = roman.replace('IIII', 'IV')

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
        l=self['sequence-length']=len(self.items)
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
            reg=self.start_name_re

            if type(reg)==type(re.compile(r"")):
                mo = reg.search(query_string)
                if mo is not None:
                    v = mo.group(0)
                    l = mo.start(0)
                    query_string=(query_string[:l]+ query_string[l+len(v)-1:])

            else:
                l=reg.search_group(query_string, (0,))
                if l:
                    v=l[1]
                    l=l[0]
                    query_string=(query_string[:l]+ query_string[l+len(v)-1:])

            query_string='?'+query_string[1:]
        else: query_string='?'
        self['sequence-query']=query_string

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
                else:
                    try: item=getattr(item,name)
                    except:
                        if name != 'item':
                            raise
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

    def __setitem__(self, key, value):
        self.data[key] = value
        if self.alt_prefix:
            if key.startswith('sequence-'): key = key[9:]
            self.data[self.alt_prefix + key] = value

    def __getitem__(self,key,
                    special_prefixes=special_prefixes,
                    special_prefix=special_prefixes.has_key
                    ):
        data=self.data
        if data.has_key(key): return data[key]

        l=key.rfind('-')
        if l < 0:
            alt_prefix = self.alt_prefix
            if not (alt_prefix and key.startswith(alt_prefix)):
                raise KeyError, key

            suffix = key[len(alt_prefix):].replace('_', '-')
            if '-' in suffix:
                try: return self[suffix]
                except KeyError: pass
            prefix = 'sequence'
            key = 'sequence-' + suffix
        else:
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
