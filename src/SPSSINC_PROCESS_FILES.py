
#Licensed Materials - Property of IBM
#IBM SPSS Products: Statistics General
#(c) Copyright IBM Corp. 2010, 2020
#US Government Users Restricted Rights - Use, duplication or disclosure 
#restricted by GSA ADP Schedule Contract with IBM Corp.
import spss, spssaux

from spssaux import _smartquote
from spssaux import u
import spss, spssaux
from extension import Template, Syntax, processcmd
import locale, os, glob, re, codecs, time, random

__author__ =  'spss, JKP'
__version__=  '1.3.0'

# history
# 15-feb-2010 original version
# 22-feb-2010 added continueonerr, logfilemode, closedata
# 12-mar-2010 generate macro values including surrounding quotes
# 30-mar-2010 add support for generating user-specified macros
# 01-apr-2010 file handle support
# 06-apr-2010 add specific support for searching in files
# 21-apr-2010 add before and after syntax files
# 09-dec-2011 file handle support for logfile
# 02-feb-2023 major rework for simplification

helptext = """SPSSINC PROCESS FILES"""

def Run(args):
    """Execute the SPSSINC PROCESS FILES extension command"""
        
    # debugging
            # makes debug apply only to the current thread
    #try:
        #import wingdbstub
        #import threading
        #wingdbstub.Ensure()
        #wingdbstub.debugger.SetDebugThreads({threading.get_ident(): 1})
    #except:
        #pass

    args = args[list(args.keys())[0]]

    oobj = Syntax([
        Template("FILELIST", subc="",  ktype="literal", var="filelist"),
        Template("INPUTDATA", subc="", ktype="literal", var="inputdata"),
        Template("SYNTAX", subc="", ktype="literal", var="syntax"),
        Template("BEFORESYNTAX", subc="", ktype="literal", var="beforesyntax"),
        Template("AFTERSYNTAX", subc="", ktype="literal", var="aftersyntax"),
        Template("SEARCH", subc="", ktype="bool", var="search"),
        Template("OUTPUTDATADIR", subc="", ktype="literal", var="outputdatadir"),
        Template("OUTPUTDATATYPE", subc="", ktype="str", var="outputdatatype",
            vallist=["sav", "zsav", "xls", "csv"]),
        Template("OUTPUTVIEWERDIR", subc="", ktype="literal", var="outputviewerdir"),
        Template("OUTPUTVIEWERTYPE", subc="", ktype="str", var="outputviewertype",
            vallist= ["spv", "xls", "xlsx", "pdf", "html", "ppt", "txt", "doc"]), 
        Template("LOGFILE", subc="", ktype="literal", var="logfile"),
        Template("LOGFILEMODE", subc="" , ktype="str", var="logfilemode",
            vallist=['append','overwrite']),
        Template("MACRONAME", subc="", ktype="literal", var="macroname"),
        Template("CONTINUEONERROR", subc="", ktype="bool", var="continueonerror"),
        Template("CLOSEDATA", subc="", ktype="bool", var="closedata"),
        Template("CLOSEVIEWER", subc="", ktype="bool", var="closeviewer"),
        
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
    if "HELP" in args:
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
        print(("Help file not found:" + helpspec))
try:    #override
    from extension import helper
except:
    pass
def applySyntaxToFiles(syntax=None, search=False, inputdata=None, filelist=None,
    outputdatadir=None, outputdatatype="sav", 
    outputviewerdir=None, outputviewertype="spv",
    logfile=None,  logfilemode="append", macroname="!JOB", 
    continueonerror=True, closedata=True, closeviewer=True, 
    parm1=None, parm2=None, parm3=None, parm4=None, parm5=None,
    qparm1=None, qparm2=None, qparm3=None, qparm4=None, qparm5=None, ignore=None,
    beforesyntax=None, aftersyntax=None):
    """Apply a syntax file to each file matching inputspec or item in filelist,
    and optionally write output and data files."""
    
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

    #if viewerfile == "":   # The CDB can't handle an empty field with a keyword assignment
        #viewerfile = None
    myenc = locale.getlocale()[1]  # get current encoding in case conversions needed
    cwd = spssaux.getShow("DIRECTORY")
    global unicodeit   #hate to do this
    def unicodeit(value):
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return value
        if not isinstance(value, str):
            return  str(value, myenc)
        else:
            return value
    
    if (not (inputdata is None) ^ (filelist is None)):
        raise ValueError(_("Either FILELIST or INPUTDATA must be specified but not both"))
    #if viewerdir and viewerfile:
        #raise ValueError(_("Cannot specify both VIEWERDIR and VIEWEROUTFILE"))
    if not ((syntax is not None) ^ search):
        raise ValueError(_("Must specify either a syntax file or searching but not both"))
    
    fhandles = Handles()
    
    if outputviewerdir:
        outputviewerdir = fhandles.resolve(outputviewerdir)
    outputviewerdir = unescape(outputviewerdir)
    outputviewerdir = tiltslash(fixloc(outputviewerdir, cwd, isdir=True))
    ###viewerfile = tiltslash(unescape(viewerfile))
    
    ###if viewerfile and os.path.isdir(viewerfile):
    #if viewerfile is not None and os.path.isdir(viewerfile):
        #raise ValueError(_("Viewer file is only a directory.  A file specification is required to use this option."))
    ###viewerfile = fixloc(viewerfile, cwd) + "VIEWER.SPV"
        
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
        logfile = unicodeit(logfile + "LOG.TXT")

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
                ###spss.SetMacroValue(macroname + "_DATADIR", quotewrap(outputdatadir)) # no trailing separator.  Can be blank
                spss.SetMacroValue(macroname + "_INPUTFILE", quotewrap(input)) # full input file spec
                spss.SetMacroValue(macroname + "_OUTPUTDATADIR", (quotewrap(outputdatadir  or "<NONE>")))                
                spss.SetMacroValue(macroname + "_OUTPUTVIEWERDIR", (quotewrap(outputviewerdir or "<NONE>")))
            except (UnicodeEncodeError, UnicodeDecodeError):
                # do not translate this message
                if not warned:
                    print(_("""This version of IBM SPSS Statistics does not support 
extended characters in macro definitions.  Some macros will not be defined."""))
                    warned = True
                    
            spss.Submit(filehandlesyn % (macroname[1:] + "_INPUTFILE", input))
            spss.Submit(filehandlesyn % (macroname[1:] + "_DATADIR", datadir))
            # output data directory if specified
            spss.Submit(filehandlesyn % (macroname[1:] + "_OUTPUTDATADIR", outputdatadir or "<NONE>"))
            # directory for Viewer output if specified
            spss.Submit(filehandlesyn % (macroname[1:] + "_VIEWERDIR",  (outputviewerdir or "<NONE>")))
            
            # create output and export file handles and macros 
            # ignoring any / or \ at the end of the directory name as input
            # The SAVE TRANSLATE command treats file handles incorrectly and tacks on a file type
            # extension, so the extension is omitted in the file handle unless it is sav
            if outputdatadir:  # specification for output data file to be written by user INSERT file
                outputdatadir = re.sub(r"[\\/]$", "", outputdatadir)
                spec = outputdatadir + "/"+ nameparts[0] + "." + outputdatatype  # output data filespec per iteration
                if outputdatatype not in ["sav", "zsav"]:
                    specnoext = outputdatadir + "/"+ nameparts[0]  # output data filespec per iteration, no extension
                else:
                    specnoext = spec
                spss.Submit(filehandlesyn % (macroname[1:] + "_OUTPUTDATA", specnoext))
                spss.SetMacroValue(macroname + "_OUTPUTDATA", spec)
            spss.SetMacroValue(macroname + "_OUTPUTDATATYPE", outputdatatype)
            
            if outputviewerdir:  # specification for output export file to be written by user code
                outputviewerdir = re.sub(r"[\\/]$", "", outputviewerdir)
                spec = outputviewerdir + "/" + nameparts[0] + "." + outputviewertype
                spss.Submit(filehandlesyn % (macroname[1:] + "_OUTPUTVIEWER", spec))
                spss.Submit(filehandlesyn % (macroname[1:] + "_OUTPUTVIEWERDIR", outputviewerdir))
                spss.SetMacroValue(macroname + "_OUTPUTVIEWERDIR", outputviewerdir + "/" +
                    nameparts[0] + "." + outputviewertype)
            spss.SetMacroValue(macroname + "_OUTPUTVIEWERTYPE", outputviewertype)
            
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

            #if outputviewerdir:
                #outputname = outputviewerdir + datafileroot + ".spv"
                #log.write(_("Writing %s") % outputname)
                #try:
                    #spss.Submit('OUTPUT SAVE OUTFILE="%s".' % outputname) # save designated window
                #except:
                    #log.write(_("Error writing Viewer file"))
                    #return    ### debug
                #spss.Submit("OUTPUT CLOSE *.")
                #ncoutputname = os.path.normcase(outputname)
                #if ncoutputname in outviewerset:
                    #log.write(_("Warning: Output file overwritten: %s") % ncoutputname)
                #outviewerset.add(ncoutputname)
            if closedata:
                spss.Submit("""DATASET CLOSE ALL.
            NEW FILE.""")
            if closeviewer:
                spss.Submit("""OUTPUT CLOSE NAME=*""")
            if failed and not continueonerror:
                break
        if aftersyntax and (continueonerror or not failed) and not beforefailed:
            try:
                log.write(_("Inserting aftersyntax file: %s.") % aftersyntax)
                spss.Submit("""INSERT FILE="%s".""" % aftersyntax)
            except:
                log.write(_("Serious error processing AFTER file: %s.") % aftersyntax)
        #if viewerfile:
            #log.write(_("Writing %s") % viewerfile)
            #spss.Submit('OUTPUT SAVE NAME=* OUTFILE="%s".' % viewerfile)
    
def quotewrap(item, qchar='"'):
    """wrap item in quotes using SPSS quote within quote rule and return it.
    
    item is a stringlike object"""
    
    return qchar + item.replace(qchar, qchar+qchar) + qchar

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
    {"\t": r"\t", "\n":r"\n", "\r": r"\r", "\'":r"\'", "\a":r"\a","\b":r"\b", "\f":r"\f","\\N":r"\N", "\v":r"\v"}

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