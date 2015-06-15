from __future__ import with_statement
#Licensed Materials - Property of IBM
#IBM SPSS Products: Statistics General
#(c) Copyright IBM Corp. 2010, 2014
#US Government Users Restricted Rights - Use, duplication or disclosure 
#restricted by GSA ADP Schedule Contract with IBM Corp.
import spss, spssaux

from spssaux import _smartquote
from spssaux import u
import spss, spssaux
from extension import Template, Syntax, processcmd
import locale, os, glob, re, codecs, time, random

__author__ =  'spss, JKP'
__version__=  '1.2.2'

# history
# 15-feb-2010 original version
# 22-feb-2010 added continueonerr, logfilemode, closedata
# 12-mar-2010 generate macro values including surrounding quotes
# 30-mar-2010 add support for generating user-specified macros
# 01-apr-2010 file handle support
# 06-apr-2010 add specific support for searching in files
# 21-apr-2010 add before and after syntax files
# 09-dec-2011 file handle support for logfile

helptext = """SPSSINC PROCESS FILES
FILELIST="input data filespec" or INPUTDATA="directory wildcard spec"
SYNTAX="syntax filespec" [BEFORESYNTAX=filespec] [AFTERSYNTAX=filespec]
SEARCH={NO*|YES}
[OUTPUTDATADIR="directory for data output"]
[VIEWERDIR="directory for Viewer output" or VIEWERFILE="filespec for single Viewer output"]
[LOGFILE="logfile spec"] [LOGFILEMODE={APPEND*|OVERWRITE}
[MACRONAME="root name for macros and file handles"]
[CONTINUEONERROR={YES*|NO}]
[CLOSEDATA={YES*|NO}
[/MACRODEFS PARM1="text" PARM2="text" ... PARM5="text" 
QPARM1="text" QPARM2="text" ... QPARM5="text"]

Example:
SPSSINC PROCESS FILES DIRECTORY="c:/mydata/*.sav"
SYNTAX="c:/myjobs/mysyntax.sps" LOGFILE="c:/myjobs/log.txt" 
VIEWERDIR="c:/myoutput"
/MACRODEFS PARM1="x > 10".

The block of syntax specified in SYNTAX will be executed for each matching file.  
It should include the appropriate command to read the data file or other inputs.
File handles and macros are defined to refer to the input file and various output 
locations.  

The file handles are as follows.
JOB_INPUTFILE: The input file
JOB_DATADIR: The input data directory
JOB_OUTPUTDATADIR: The specified output data directory or <NONE>
JOB_VIEWERDIR: The specified Viewer output directory or <NONE>

For a SAV file you could read the data with the command
GET FILE="JOB_INPUTFILE".
Macros are defined with these same names except starting with "!".  Two
additional macros are defined.
!JOB_DATAFILEROOT: The name of the input data file without its extension
!JOB_DATAFILEEXT: The extension of the input data file

Macro text is quoted.  Here is an example of code that might be used in the
syntax file to export output to the VIEWERDIR in Excel using the data file rootname.

define !out () !quote(!concat(!unquote(!eval(!job_viewerdir)), "/", !unquote(!eval(!job_datafileroot)), ".xls"))
!enddefine.
output export /xls DOCUMENTFILE =!out.

The text !JOB or JOB is replaced by the root name specified in MACRONAME.

BEFORESYNTAX and/or AFTERSYNTAX can specify syntax files to be inserted
before or after any other files are processed.  The before file will have all the file handles
and macros as set for the first input file, and the after file will have these items as set
for the last file processed.

A serious error in BEFORESYNTAX always stops processing.  The
CONTINUEONERROR setting determines whether the AFTERSYNTAX file is
executed if there is an error.

Instead of SYNTAX, SEARCH can be specified to search files according to
parameters passed as !PARM1, !PARM2, and !PARM3.
!PARM1 defines the search condition as a boolean expression as would be
used with SELECT IF
!PARM2 is the id variable. !PARM3 is any other variables to be listed with the results.
Either SYNTAX or SEARCH must be specified but not both.

If CLOSEDATA is YES, the default, all data files are automatically closed 
after each syntax file invocation.

DIRECTORY can specify a directory to process and, optionally, a file pattern.  
For example,
c:/mydata/x*.sav
would process all the sav files in directory c:\mydata whose names start with the letter x.
*.sav is assumed if DIRECTORY does not include a file pattern.

Alternatively, FILELIST specifies processing all of the files listed in the indicated file.  
In order to use a file to specify the files that should be processed, create a file
with one name per line including the path to the file.  The name must be enclosed
in double quotes (").  Anything following on the line is ignored.  
Blank lines and lines starting with # are ignored.

The SPSSINC SPLIT DATASET command can produce a file in the correct format
for FILELIST.

Either DIRECTORY or FILELIST must be specified but not both.

It may be convenient to use this procedure in combination with SPSSINC SPLIT DATASET,
which can break up a dataset according to the values of a splitting variable.

If OUTPUTDATADIR is specified, after the syntax completes for each iteration
the active data file will be written as an .sav file to that directory .
This can be useful when carrying out transformations for a set of files.
You can, of course, leave this field blank and write any data file output you choose.  
The JOB_OUTPUTDATADIR file handle and !JOB_OUTPUTDATADIR macro 
identify the data output location specified in PROCESS FILES.

Viewer output can be saved either in a separate file for each data file or as a single
file for the entire job by specifying either VIEWERDIR or VIEWERFILE
and entering either a directory name or a file specification.  

If VIEWERFILE specifies only a directory, the file will be named VIEWER.SPV.

LOGFILE can specify a file that will contain a log of actions carried out by
this command (not what happens in the invoked syntax), including an entry if
the syntax generates a serious error (level 3 or higher).  LOGFILEMODE
can be APPEND or OVERWRITE.  The file is written in Unicode (utf-8).

If a serious error occurs while executing the syntax file, you can choose whether 
to continue processing with the next data file or to stop processing any further 
files by specifying CONTINUEONERROR= YES or NO.
If possible, the output data and Viewer files will still be written for the data file
that caused the error even if stopping is specified.

MACRODEFS can be used to define macros that can be referenced in
the syntax file that is repeatedly executed.  Each macro name matches the PARMn
or QPARMn parameter with a preceding !.  These macros are defined after the 
macros described above each time a file is processed, so they can refer to the 
stadard macro values.
The definition will be wrapped in quotes and hence be interpreted as a literal
if QPARM is used.  The paramters must always be quoted in the MACRODEFS
subcommand.

If a macro is not defined, it will automatically be defined as empty.

Example:  with this syntax
/MACRODEF PARM1="education >= 12 and education <=16" PARM2="educ age",
the syntax job could contain this code to do frequencies on qualifying data.
SELECT IF !PARM1.
FREQ !PARM2.

This construct could also be used to search for a particular id, say, across files
/MACRODEF PARM1="ID = 12345" PARM2 = "ID"
and, in the syntax file,
SELECT IF !PARM1.
FREQ !PARM2.
But for a literal, say, as a table title, you would use QPARM:
CTABLES ...  /TITLES TITLE=!QPARM1.
with /MACRODEFS QPARM1="The Title".

In these examples, you should use CONTINUEONERROR=YES, since
the SELECT will result in 0 cases in the data if none meet the criteria.

A complete version of a search syntax file is included with this package.

If any of the file or directory specifications to this command use SPSS file handles,
these will be expanded properly in V18 or later, but in earlier versions, they
will not work with directory specifications or where a wildcard expression is
allowed.

/HELP displays this help and does nothing else.
"""

def Run(args):
    """Execute the SPSSINC PROCESS FILES extension command"""
    
    ##debugging
    #try:
        #import wingdbstub
        #if wingdbstub.debugger != None:
            #import time
            #wingdbstub.debugger.StopDebug()
            #time.sleep(2)
            #wingdbstub.debugger.StartDebug()
    #except:
        #pass

    args = args[args.keys()[0]]

    oobj = Syntax([
        Template("FILELIST", subc="",  ktype="literal", var="filelist"),
        Template("INPUTDATA", subc="", ktype="literal", var="inputdata"),
        Template("SYNTAX", subc="", ktype="literal", var="syntax"),
        Template("BEFORESYNTAX", subc="", ktype="literal", var="beforesyntax"),
        Template("AFTERSYNTAX", subc="", ktype="literal", var="aftersyntax"),
        Template("SEARCH", subc="", ktype="bool", var="search"),
        Template("OUTPUTDATADIR", subc="", ktype="literal", var="outputdatadir"),
        Template("VIEWERDIR", subc="", ktype="literal", var="viewerdir"),
        Template("VIEWERFILE", subc="", ktype="literal", var="viewerfile"),
        Template("LOGFILE", subc="", ktype="literal", var="logfile"),
        Template("LOGFILEMODE", subc="" , ktype="str", var="logfilemode", vallist=['append','overwrite']),
        Template("MACRONAME", subc="", ktype="literal", var="macroname"),
        Template("CONTINUEONERROR", subc="", ktype="bool", var="continueonerror"),
        Template("CLOSEDATA", subc="", ktype="bool", var="closedata"),
        Template("PARM1", subc="MACRODEFS", ktype="literal", var="parm1"),
        Template("PARM2", subc="MACRODEFS", ktype="literal", var="parm2"),
        Template("PARM3", subc="MACRODEFS", ktype="literal", var="parm3"),
        Template("PARM4", subc="MACRODEFS", ktype="literal", var="parm4"),
        Template("PARM5", subc="MACRODEFS", ktype="literal", var="parm5"),
        Template("QPARM1", subc="MACRODEFS", ktype="literal", var="qparm1"),
        Template("QPARM2", subc="MACRODEFS", ktype="literal", var="qparm2"),
        Template("QPARM3", subc="MACRODEFS", ktype="literal", var="qparm3"),
        Template("QPARM4", subc="MACRODEFS", ktype="literal", var="qparm4"),
        Template("QPARM5", subc="MACRODEFS", ktype="literal", var="qparm5"),
        Template("ITEMS", subc="MACRODEFS", ktype="str", var="ignore"),
        Template("HELP", subc="", ktype="bool")])
    
    
    #enable localization
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg
    # A HELP subcommand overrides all else
    if args.has_key("HELP"):
        #print helptext
        helper()
    else:
        processcmd(oobj, args, applySyntaxToFiles)

def helper():
    """open html help in default browser window
    
    The location is computed from the current module name"""
    
    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + \
         "markdown.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print("Help file not found:" + helpspec)
try:    #override
    from extension import helper
except:
    pass
def applySyntaxToFiles(syntax=None, search=False, inputdata=None, filelist=None,  outputdatadir=None, 
    viewerdir=None, viewerfile=None, logfile=None, macroname="!JOB", 
    continueonerror=True, closedata=True, logfilemode="append", 
    parm1=None, parm2=None, parm3=None, parm4=None, parm5=None,
    qparm1=None, qparm2=None, qparm3=None, qparm4=None, qparm5=None, ignore=None,
    beforesyntax=None, aftersyntax=None):
    """Apply a syntax file to each file matching inputspec or item in filelist, and optionally write output and data files.
    
    inputdata is a wildcard directory specification of data files to process.  E.,g., "c:/mydata/*.sav"
    filelist is a list of files in the format produced by SPSSINC SPLIT FILES
    Exactly one of these must be given.
    syntax is a filespec for a syntax file to execute via the INSERT command
    search indicates file searching
    If outputdatadir is not None, each input file will be written to the specified data directory after processing.
    
    If viewerdir is not None, the designated Viewer window will be written to that directory and closed
    after processing each input file.  It will have the input data file name but with an spv extension.
    If viewerfile, alternatively, is specified, all the output remaining in the active Viewer will be written 
    to that single file at the end of the entire job.
    If logfile is not None, a log of file progress will be written as a plain text file.  If it is a directory,
    the log will be written to LOG.TXT in that directory
    If errors occur on INSERT, continueonerror determines whether processing continues.
    If closedata, all data files are automatically closed after each iteration.
    beforesyntax and aftersyntax can name syntax files to be run before and after
    other files are processed.
    """
    
    #* !PARM1 defines the search condition.
    #* !PARM2 is the id variable. !PARM3 is any other variables to be listed.
    searchsyntax = r"""get file="JOB_INPUTFILE".
%(dsn)s
oms /select all except=texts /exceptif subtypes="Report"
/destination viewer=no.
TEMPORARY.
select if !PARM1.
SUMMARIZE  /TABLE !PARM2
  /FORMAT=LIST  NOCASENUM LIMIT=100
  /TITLE='Matched Cases'  /CELLS=NONE.
omsend."""

    myenc = locale.getlocale()[1]  # get current encoding in case conversions needed
    cwd = spssaux.getShow("DIRECTORY")
    global unicodeit   #hate to do this
    def unicodeit(value):
        if isinstance(value, (int, float)):
            return unicode(value)
        if value is None:
            return value
        if not isinstance(value, unicode):
            return  unicode(value, myenc)
        else:
            return value
    
    if (not (inputdata is None) ^ (filelist is None)):
        raise ValueError(_("Either FILELIST or INPUTDATA must be specified but not both"))
    if viewerdir and viewerfile:
        raise ValueError(_("Cannot specify both VIEWERDIR and VIEWEROUTFILE"))
    if not ((syntax is not None) ^ search):
        raise ValueError(_("Must specify either a syntax file or searching but not both"))
    
    fhandles = Handles()
    
    if viewerdir:
        viewerdir = fhandles.resolve(viewerdir)
    viewerdir = unescape(viewerdir)
    viewerdir = tiltslash(fixloc(viewerdir, cwd, isdir=True))
    viewerfile = tiltslash(unescape(viewerfile))
    
    if viewerfile and os.path.isdir(viewerfile):
        viewerfile = fixloc(viewerfile, cwd) + "VIEWER.SPV"
        
    if logfile:
        logfile = fhandles.resolve(logfile)
        
    if not macroname.startswith("!"):
        raise ValueError(_("MACRONAME must start with !"))
    
    if outputdatadir:
        outputdatadir = fhandles.resolve(outputdatadir)
    outputdatadir = tiltslash(unescape(outputdatadir))
    if outputdatadir and  (outputdatadir.endswith("/") or outputdatadir.endswith("\\")):
        outputdatadir = outputdatadir[:-1]    # no separator ending
        
  # expand any file handle if V18 or later.  xml parameter type can't be InputFile because of wildcards
    if inputdata:
        inputdata = Handles().resolve(inputdata)
    inputdata = tiltslash(unescape(inputdata))
    inputdata = fixloc(inputdata, cwd, isdir=False)
    if inputdata and os.path.isdir(inputdata):
        inputdata = inputdata + "*.sav"
        
    logfile = tiltslash(unescape(logfile))
    if logfile and os.path.isdir(logfile):
        logfile = fixloc(logfile, cwd)
        logfile = unicodeit(logfile + u"LOG.TXT")

    inputsource = unicodeit(inputdata or filelist)
    outnameset = set()
    outviewerset = set()
    warned = False
    failed = False
    with Writelog(logfile, logfilemode) as log:
        if syntax:
            log.write(_("START: apply %(syntax)s to %(inputsource)s") % locals())
        else:
            log.write(_("START: searching in %(inputsource)s") % locals())            
        if inputdata:
            source = glob.iglob
        else:
            source = getfilelist
            
        first = True
        beforefailed = False
        
        for input in source(inputsource):
            input = unicodeit(input)
            input = input.replace("\\", "/")
            if not os.path.isfile(input):
                log.write(_("Skipping %s: not a file") % input)
                continue
            # create macro and file handle definitions
            # For the file name ".sav", make the root "" - different from splitext behavior
            nameparts = os.path.splitext(os.path.basename(input))
            if nameparts[1] == "" and nameparts[0].lower() == ".sav":
                datafileroot = ""
                datafileext = ".sav"
            else:
                datafileroot = nameparts[0]
                datafileext = nameparts[1]
                
            filehandlesyn = 'FILE HANDLE %s /NAME="%s".'
            datadir = os.path.dirname(input)  # input data directory
            try:
                spss.SetMacroValue(macroname + "_DATAFILEROOT", quotewrap(datafileroot))  # just the root name
                spss.SetMacroValue(macroname + "_DATAFILEEXT", quotewrap(datafileext)) # just the extension
                spss.SetMacroValue(macroname + "_DATADIR", quotewrap(datadir)) # no trailing separator.  Can be blank
                spss.SetMacroValue(macroname + "_INPUTFILE", quotewrap(input)) # full input file spec
                spss.SetMacroValue(macroname + "_OUTPUTDATADIR", (quotewrap(outputdatadir  or "<NONE>")))                
                spss.SetMacroValue(macroname + "_VIEWERDIR", (quotewrap(viewerdir or "<NONE>")))
            except (UnicodeEncodeError, UnicodeDecodeError):
                # do not translate this message
                if not warned:
                    print _("""This version of IBM SPSS Statistics does not support 
extended characters in macro definitions.  Some macros will not be defined.""")
                    warned = True
                    
            spss.Submit(filehandlesyn % (macroname[1:] + "_INPUTFILE", input))
            spss.Submit(filehandlesyn % (macroname[1:] + "_DATADIR", datadir))
            # output data directory if specified
            spss.Submit(filehandlesyn % (macroname[1:] + "_OUTPUTDATADIR", outputdatadir or "<NONE>"))
            # directory for Viewer output if specified
            spss.Submit(filehandlesyn % (macroname[1:] + "_VIEWERDIR",  (viewerdir or "<NONE>")))
            
            for i, parmdef in enumerate(zip([parm1, parm2, parm3, parm4, parm5],
                [qparm1, qparm2, qparm3, qparm4, qparm5])):
                pdef = parmdef[0]
                qdef = parmdef[1]
                if qdef is None:
                    qdef = ""
                spss.SetMacroValue("!QPARM" + str(i+1), quotewrap(qdef))
                if pdef is None:
                    pdef = ""
                spss.SetMacroValue("!PARM" + str(i+1), pdef)

            # user must include the file read using the macro or file handle in the INSERTed syntax.  E.g.,
            # GET FILE=JOB_INPUTFILE.
            
            try:
                if first and beforesyntax:
                    first = False
                    try:
                        log.write(_("Inserting beforesyntax file: %s.") % beforesyntax)
                        spss.Submit("""INSERT FILE = "%s". """ % beforesyntax)
                    except:
                        log.write(_("Serious error processing BEFORE file: %s.  Stopping") % beforesyntax)
                        beforefailed = True
                        break
                if syntax:
                    log.write(_("Defining: %(input)s and INSERTing %(syntax)s") % locals())
                    spss.Submit("""INSERT FILE= "%s".""" % syntax)
                else:
                    if closedata:
                        dsn = ""
                    else:
                        dsn = "DATASET NAME S" + str(random.random()) + "."
                    spss.Submit(searchsyntax % locals())
            except:
                log.write(_("Serious error processing: %s.  %s") % (input, continueonerror and _("Continuing") or _("Stopping")))
                failed = True
            if outputdatadir:
                outname = outputdatadir + os.sep + datafileroot + ".sav"
                log.write(_("Writing %s") % outname)
                try:
                    spss.Submit('SAVE OUTFILE="%s".' % outname)
                except:
                    log.write(_("Error writing data file"))
                ncoutname = os.path.normpath(outname)
                if ncoutname in outnameset:
                    log.write(_("Warning: file overwritten: %s") % ncoutname)
                outnameset.add(ncoutname)

            if viewerdir:
                outputname = viewerdir + datafileroot + ".spv"
                log.write(_("Writing %s") % outputname)
                try:
                    spss.Submit('OUTPUT SAVE OUTFILE="%s".' % outputname) # save designated window
                except:
                    log.write(_("Error writing Viewer file"))
                    return    ### debug
                spss.Submit("OUTPUT CLOSE *.")
                ncoutputname = os.path.normcase(outputname)
                if ncoutputname in outviewerset:
                    log.write(_("Warning: Output file overwritten: %s") % ncoutputname)
                outviewerset.add(ncoutputname)
            if closedata:
                spss.Submit("""DATASET CLOSE ALL.
            NEW FILE.""")
            if failed and not continueonerror:
                break
        if aftersyntax and (continueonerror or not failed) and not beforefailed:
            try:
                log.write(_("Inserting aftersyntax file: %s.") % aftersyntax)
                spss.Submit("""INSERT FILE="%s".""" % aftersyntax)
            except:
                log.write(_("Serious error processing AFTER file: %s.") % aftersyntax)
        if viewerfile:
            log.write(_("Writing %s") % viewerfile)
            spss.Submit('OUTPUT SAVE NAME=* OUTFILE="%s".' % viewerfile)
    
def quotewrap(item):
    """wrap item in double quotes and return it.
    
    item is a stringlike object"""
    
    return '"' + item + '"'

class Writelog(object):
    """Manage a log file"""
    def __init__(self, logfile, mode):
        """logfile is the file name
        mode is "overwrite" or "append" """
        self.logfile = logfile
        if self. logfile:
            fmode = mode == "overwrite" and "wb" or "ab"
            self.file = codecs.open(logfile, fmode, encoding="utf_8_sig")
            
    def __enter__(self):
        return self
    
    def write(self, text):
        if self.logfile:
            self.file.write(time.asctime() + ": " + text + os.linesep)
            
    def close(self):
        if self.logfile:
            self.file.write(time.asctime() + _(": CLOSING LOG") + os.linesep)
            self.file.close()
            
    def __exit__(self, type, value, tb):
        """cleanup for use with with statement"""
        self.close()
        return False
        
def tiltslash(astr):
    "stamp out any backslashes in a string or None object"
    
    if astr is None:
        return None
    else:
        return astr.replace("\\", "/")
    
def getfilelist(filelist):
    """Return files to process as contents from filelist
    
    Lines in filelist are expected to start with a double-quoted file name.
    The remainder of the line is ignored.
    Lines starting with # in column 1 are ignred.
    
    filelist is expected to be encoded in utf-8 and to start with a BOM."""
    
    with codecs.open(filelist, encoding="utf_8_sig") as f:
        for line in f:
            if re.match(r"[ \t]*(#|$)", line):  # ignore blank and comment lines
                continue
            line = unicodeit(line)
            mo = re.search(r'".*?"', line)
            if mo is None:
                raise ValueError(_("Bad format in filelist file: %s") % line)
            yield mo.group()[1:-1]  # get the file name - expecting       
 
def fixsep(item, cwd):
    "ensure item ends with directory separator and make into absolute path"
    if item is None:
        return item
    if not os.path.abspath(item):
        item = cwd + os.sep + item
    if not (item.endswith("/") or item.endswith("\\")):
        item = item + os.sep
    return item

def fixloc(item, cwd, isdir=False):
    """return item aligned with SPSS process and add trailing separator if appropriate
    
    item is a filespec possibly including a file wildcard
    cwd is the SPSS process current working directory
    If isdir, item is known to be a directory (or None)"""
    
    if item is None:
        return item
    if isdir or os.path.isdir(item):
        dname = item
        bname = ""
    else:
        dname, bname = os.path.dirname(item), os.path.basename(item)
    if not os.path.isabs(dname):
        parts = os.path.splitdrive(item)
        if not parts[0] == "":
            raise ValueError(_("Relative paths cannot be specified with a drive letter: %s") % item)
        #dname = os.path.join(cwd, parts[1])
        dname = cwd + "/" + parts[1]   # problems with \ in macro definition
        if not os.path.exists(dname):
            raise ValueError(_("Directory or file does not exist: %s") % dname)
    return dname + "/" + bname

escapemapping = \
    {"\t": r"\t", "\n":r"\n", "\r": r"\r", "\'":r"\'", "\a":r"\a","\b":r"\b", "\f":r"\f","\N":r"\N", "\v":r"\v"}

def unescape(item):
    "Undo any escape sequences due to the UP"
    
    if item is None:
        return item
    return "".join([escapemapping.get(ch, ch) for ch in item])

class Handles(object):
    """Version-guarded file handle resolver"""
    def __init__(self):
        try:
            self.fh = spssaux.FileHandles()
        except:
            self.fh = None


    def resolve(self, filespec):
        "Ordinary handle resolver but guarded.  Returns expanded filespec if possible"
        
        if self.fh:
            return self.fh.resolve(filespec)
        else:
            return filespec