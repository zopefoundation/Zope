##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
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
      of the 'in' tag is used as follows::

         <!--#in sequence-->some markup<!--#/in-->

      A more complete case is used as follows::

        <!--#in sequence sort=age-->
          <!--#var sequence-number-->) <!--#var age-->
        <!--#/in-->

    Attributes

      sort -- Define the sort order for sequence items.  If an item in
      the sequence does not define 

      Within an 'in' block, variables are substituted from the
      elements of the iteration.  The elements may be either
      instance or mapping objects.  In addition, the variables:

         'sequence-item' -- The element.

         'sequence-var-nnn' -- The value of a specific named attribute
           of the item, where 'nnn' is the name.  For example, to get
           an items 'title' attribute, use 'sequence-var-title'.  This
           construct is most useful in an 'if' tag to test whether an
           attribute is present, because the attribute lookup will be
           extended to the full document template namespace.

         'sequence-key' -- The key associated with the element in an
           items list. See below.

         'sequence-index' -- The index, starting from 0, of the
           element within the sequence.

         'sequence-number' -- The index, starting from 1, of the
           element within the sequence.

         'sequence-letter' -- The index, starting from 'a', of the
           element within the sequence.

         'sequence-Letter' -- The index, starting from 'A', of the
           element within the sequence.

         'sequence-roman' -- The index, starting from 'i', of the
           element within the sequence.

         'sequence-Roman' -- The index, starting from 'I', of the
           element within the sequence.

         'sequence-start' -- A variable that is true if the element
           being displayed is the first of the displayed elements,
           and false otherwise.

         'sequence-end' -- A variable that is true if the element
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

          'start'   -- The number of the first element to be shown,
                       where elements are numbered from 1.

          'end'     -- The number of the last element to be shown,
                       where elements are numbered from 1.

          'size'    -- The desired number of elements to be shown at
                       once.

          'orphan'  -- The desired minimum number of objects to be
                       displayed.  The default value for this
                       parameter is 3.

          'overlap' -- The desired overlap between batches. The
                       default is no overlap.     

      Typically, only 'start' and 'size' will be specified.

      When batch insertion is used, several additional variables are
      defined for use within the sequence insertion text:

          'sequence-query' -- The original query string given in a get
             request with the form variable named in the 'start'
             attribute removed.  This is extremely useful when
             building URLs to fetch another batch.

             To see how this is used, consider the following example::

                 <!--#in search_results size=20 start=batch_start-->

                    ... display rows

                    <!--#if sequence-end--> <!--#if next-sequence-->
                      <a href="<!--#var URL-->/<!--#var sequence-query
                          -->&batch_start=<!--#var
                          next-sequence-start-number-->">
                      (Next <!--#var next-sequence-size--> results)
                      </a>
                    <!--#/if--> <!--#/if-->

                 <!--#/in-->

             If the original URL is: 'foo/bar?x=1&y=2', then the
             rendered text (after row data are displated) will be::

                      <a href="foo/bar?x=1&y=2&batch_start=20">
                      (Next 20 results)
                      </a>

             If the original URL is: 'foo/bar?batch_start=10&x=1&y=2',
             then the rendered text (after row data are displated)
             will be::

                      <a href="foo/bar?x=1&y=2&batch_start=30">
                      (Next 20 results)
                      </a>

          'sequence-step-start-index' -- The index, starting from 0,
             of the start of the current batch.

          'sequence-step-end-index' -- The index, starting from 0, of
             the end of the current batch.

          'sequence-step-size' -- The batch size used.

          'previous-sequence' -- This variable will be true when the
             first element is displayed and when the first element
             displayed is not the first element in the sequence.

          'previous-sequence-start-index' -- The index, starting from
             0, of the start of the batch previous to the current
             batch.

          'previous-sequence-end-index' -- The index, starting from
             0, of the end of the batch previous to the current
             batch.

          'previous-sequence-size' -- The size of the batch previous to
             the current batch.

          'previous-batches' -- A sequence of mapping objects
             containing information about all of the batches prior
             to the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-size -- The size of the batch.

          'next-sequence' -- This variable will be true when the last
             element is displayed and when the last element
             displayed is not the last element in the sequence.

          'next-sequence-start-index' -- The index, starting from
             0, of the start of the batch after the current
             batch.

          'next-sequence-end-index' -- The index, starting from
             0, of the end of the batch after the current
             batch.

          'next-sequence-size' -- The size of the batch after
             the current batch.

          'next-batches' -- A sequence of mapping objects
             containing information about all of the batches after
             the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-size -- The size of the batch.

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

    'else' continuation tag within in

      An 'else' tag may be used as a continuation tag in the 'in' tag.
      The source after the 'else' tag is inserted if:

        - The sequence given to the 'in' tag is of zero length, or

        - The 'previous' attribute was used and their are no
          previous batches, or

        - The 'next' attribute was used and their are no
          next batches, or

''' #'

__rcs_id__='$Id: DT_In.py,v 1.30 1998/09/14 22:03:32 jim Exp $'
__version__='$Revision: 1.30 $'[11:-2]

from DT_Util import ParseError, parse_params, name_param, str
from DT_Util import render_blocks, InstanceDict
from string import find, atoi, join
import ts_regex
from DT_InSV import sequence_variables, opt
TupleType=type(())

class InFactory:
    blockContinuations=('else',)
    name='in'

    def __call__(self, blocks):
        i=InClass(blocks)
        if i.batch: return i.renderwb
        else: return i.renderwob

In=InFactory()

class InClass:
    elses=None
    expr=sort=batch=mapping=None
    start_name_re=None
    
    def __init__(self, blocks):
        tname, args, section = blocks[0]
        args=parse_params(args, name='', start='1',end='-1',size='10',
                          orphan='3',overlap='1',mapping=1,
                          skip_unauthorized=1,
                          previous=1, next=1, expr='', sort='')
        self.args=args
        has_key=args.has_key

        if has_key('sort'): self.sort=args['sort']
        if has_key('mapping'): self.mapping=args['mapping']
        for n in 'start', 'size', 'end':
            if has_key(n): self.batch=1

        for n in 'orphan','overlap','previous','next':
            if has_key(n) and not self.batch:
                raise ParseError, (
                    """
                    The %s attribute was used but neither of the
                    <code>start</code>, <code>end</code>, or <code>size</code>
                    attributes were used.
                    """ % n, 'in')

        if has_key('start'):
            v=args['start']
            if type(v)==type(''):
                try: atoi(v)
                except:
                    self.start_name_re=ts_regex.compile(
                        '&+'+
                        join(map(lambda c: "[%s]" % c, v),'')+
                        '=[0-9]+&+')
                    
        name,expr=name_param(args,'in',1)
        if expr is not None: expr=expr.eval
        self.__name__, self.expr = name, expr
        self.section=section.blocks
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
            self.elses=section.blocks
            

    def renderwb(self, md):
        expr=self.expr
        name=self.__name__
        if expr is None:
            sequence=md[name]
            cache={ name: sequence }
        else:
            sequence=expr(md)
            cache=None

        if not sequence:
            if self.elses: return render_blocks(self.elses, md)
            return ''

        section=self.section
        params=self.args
        
        mapping=self.mapping

        if self.sort is not None: sequence=self.sort_sequence(sequence)

        next=previous=0
        try: start=int_param(params,md,'start',0)
        except: start=1
        end=int_param(params,md,'end',0)
        size=int_param(params,md,'size',0)
        overlap=int_param(params,md,'overlap',0)
        orphan=int_param(params,md,'orphan','3')
        start,end,sz=opt(start,end,size,orphan,sequence)
        if params.has_key('next'): next=1
        if params.has_key('previous'): previous=1

        last=end-1
        first=start-1

        try: query_string=md['QUERY_STRING']
        except: query_string=''

        vars=sequence_variables(sequence,'?'+query_string,self.start_name_re)
        kw=vars.data
        kw['mapping']=mapping
        kw['sequence-step-size']=sz
        kw['sequence-step-overlap']=overlap
        kw['sequence-step-start']=start
        kw['sequence-step-end']=end
        kw['sequence-step-start-index']=start-1
        kw['sequence-step-end-index']=end-1
        kw['sequence-step-orphan']=orphan

        push=md._push
        pop=md._pop
        render=render_blocks

        if cache: push(cache)
        push(vars)
        try:
            if previous:
                if first > 0:
                    pstart,pend,psize=opt(None,first+overlap,
                                          sz,orphan,sequence)
                    kw['previous-sequence']=1
                    kw['previous-sequence-start-index']=pstart-1
                    kw['previous-sequence-end-index']=pend-1
                    kw['previous-sequence-size']=pend+1-pstart
                    result=render(section,md)

                elif self.elses: result=render(self.elses, md)
                else: result=''
            elif next:
                try:
                    # The following line is a sneaky way to test whether
                    # there are more items, without actually
                    # computing a length:
                    sequence[end]
                    pstart,pend,psize=opt(end+1-overlap,None,
                                          sz,orphan,sequence)
                    kw['next-sequence']=1
                    kw['next-sequence-start-index']=pstart-1
                    kw['next-sequence-end-index']=pend-1
                    kw['next-sequence-size']=pend+1-pstart
                    result=render(section,md)
                except:
                    if self.elses: result=render(self.elses, md)
                    else: result=''
            else:
                result = []
                append=result.append
                validate=md.validate
                for index in range(first,end):
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
                                # The following line is a sneaky way to
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
        
                    if index==last: kw['sequence-end']=1

                    client=sequence[index]

                    if validate is not None:
                        try: vv=validate(sequence,sequence,index,client,md)
                        except: vv=0
                        if not vv:
                            if (params.has_key('skip_unauthorized') and
                                params['skip_unauthorized']):
                                if index==first: kw['sequence-start']=0
                                continue
                            raise ValidationError, index

                    kw['sequence-index']=index
                    if type(client)==TupleType and len(client)==2:
                        client=client[1]

                    if mapping: push(client)
                    else: push(InstanceDict(client, md))

                    try: append(render(section, md))
                    finally: pop(1)

                    if index==first: kw['sequence-start']=0


                result=join(result, '')

        finally:
            if cache: pop()
            pop()

        return result

    def renderwob(self, md):
        expr=self.expr
        name=self.__name__
        if expr is None:
            sequence=md[name]
            cache={ name: sequence }
        else:
            sequence=expr(md)
            cache=None

        if not sequence:
            if self.elses: return render_blocks(self.elses, md)
            return ''

        section=self.section
        
        mapping=self.mapping

        if self.sort is not None: sequence=self.sort_sequence(sequence)

        vars=sequence_variables(sequence)
        kw=vars.data
        kw['mapping']=mapping

        l=len(sequence)
        last=l-1

        push=md._push
        pop=md._pop
        render=render_blocks

        if cache: push(cache)
        push(vars)
        try:
                result = []
                append=result.append
                validate=md.validate
                for index in range(l):
                    if index==last: kw['sequence-end']=1
                    client=sequence[index]

                    if validate is not None:
                        try: vv=validate(sequence,sequence,index,client,md)
                        except: vv=0
                        if not vv:
                            if (self.args.has_key('skip_unauthorized') and
                                self.args['skip_unauthorized']):
                                if index==1: kw['sequence-start']=0
                                continue
                            raise ValidationError, index

                    kw['sequence-index']=index
                    if type(client)==TupleType and len(client)==2:
                        client=client[1]

                    if mapping: push(client)
                    else: push(InstanceDict(client, md))

                    try: append(render(section, md))
                    finally: pop()
                    if index==0: kw['sequence-start']=0

                result=join(result, '')

        finally:
            if cache: pop()
            pop()

        return result

    def sort_sequence(self, sequence):

        sort=self.sort
        mapping=self.mapping
        isort=not sort
        k=None
        s=[]
        for client in sequence:
            if type(client)==TupleType and len(client)==2:
                if isort: k=client[0]
                v=client[1]
            else:
                if isort: k=client
                v=client

            if sort:
                if mapping: k=v[sort]
                else: k=getattr(v, sort)
                if not basic_type(k):           
                    try: k=k()
                    except: pass

            s.append((k,client))

        s.sort()

        sequence=[]
        for k, client in s: sequence.append(client)

        return sequence


basic_type={type(''): 1, type(0): 1, type(0.0): 1, type(()): 1, type([]): 1
            }.has_key

def int_param(params,md,name,default=0, st=type('')):
    try: v=params[name]
    except: v=default
    if v:
        try: v=atoi(v)
        except:
            v=md[v]
            if type(v) is st: v=atoi(v)
    return v
