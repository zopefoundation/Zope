The MIMETools Product

 The MIMETools product is alpha quality software.  It may not work as
 documented or at all.  If you encounter bugs in MIMETools, please
 report your problem to support@digicool.com or discuss it on the Zope 
 mailing list, zope@zope.org.

 Currently, the MIMETools product's only function is to provide the
 <!--#mime--> DTML tag.

 The <!--#mime--> tag is used to construct MIME containers.  The
 syntax of the <!--#mime--> tag is:


 <!--#mime [type=x, disposition=y, encode=z]-->

  Contents of first part

 <!--#boundary [type=x, disposition=y, encode=z]--> 

  Contents of second part
   
 <!--#boundary [type=x, disposition=y, encode=z]--> 

  Contents of nth part

 <!--#/mime-->


 The area of data between tags, called a block, is encoded into
 whatever is specified with the 'encode' tag attribute for that block.
 If no encoding is specified, 'base64' is defaulted.  Valid encoding
 options include 'base64', 'quoted-printable', 'uuencode',
 'x-uuencode', 'uue' and 'x-uue'.  If the 'encode' attribute is set to
 '7bit' no encoding is done on the block and the data is assumed to be
 in a valid MIME format.

 If the 'disposition' attribute is not specified for a certain block,
 then the 'Content-Disposition:' MIME header is not included in that
 block's MIME part.

 The entire MIME container, from the opening mime tag to the closing,
 has it's 'Content-Type:' MIME header set to 'multipart/mixed'.

 For example, the following DTML:

  <!--#mime encode=7bit type=text/plain-->
  This is the first part.
  <!--#boundary encode=base64 type=text/plain-->
  This is the second.
  <!--#/mime-->

 Is rendered to the following text:

  Content-Type: multipart/mixed;
      boundary="216.164.72.30.501.1550.923070182.795.22531"


  --216.164.72.30.501.1550.923070182.795.22531
  Content-Type: text/plain
  Content-Transfer-Encoding: 7bit

  This is the first part.

  --216.164.72.30.501.1550.923070182.795.22531
  Content-Type: text/plain
  Content-Transfer-Encoding: base64

  VGhpcyBpcyB0aGUgc2Vjb25kLgo=

  --216.164.72.30.501.1550.923070182.795.22531--


 The #mime tag is particulary handy in conjunction with the #sendmail
 tag.  This allows Zope to send attachments along with email.  Here is 
 an example:

  Create a DTML method called 'input' with the following code:

    <!--#var standard_html_header-->
    <form method=post action="send" ENCTYPE="multipart/form-data">
    <input type=file name="afile"><br>
    Send to:<input type=textbox name="who"><br>
    <input type=submit value="Send">
    </form>
    <!--#var standard_html_footer-->


  Create another DTML Method called 'send' with the following code:

    <!--#var standard_html_header-->
    <!--#sendmail smtphost=localhost -->
    From: michel@digicool.com
    To: <!--#var who-->
    <!--#mime type=text/plain encode=7bit-->

    Hi <!--#var who-->, someone sent you this attachment.

    <!--#boundary type=application/octet-stream disposition=attachment 
    encode=base64--><!--#var "afile.read()"--><!--#/mime-->

    <!--#/sendmail-->

    Mail with attachment was sent.
    <!--#var standard_html_footer-->


  Notice that there is no blank line between the 'To:' header and the
  starting #mime tag.  If a blank line is inserted between them then
  the message will not be interpreted as multipart by the recieving mailreader.

  Also notice that there is no newline between the #boundary tag and
  the #var tag, or the end of the #var tag and the closing #mime tag.
  This is important, if you break the tags up with newlines then they
  will be encoded and included in the MIME part, which is probably not
  what you're after.

  As per the MIME spec, #mime tags may be nested within #mime tags arbitrarily.








