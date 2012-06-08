import sys
import subprocess
import yaml
from subprocess import Popen, PIPE
from xml.dom.minidom import parse, parseString
from collections import namedtuple

# define the param structure
Param = namedtuple('Param', ('parent', 'namespace', 'name', 'type', 'value'))
Node = namedtuple('Node', ('pkg', 'name', 'type'))
Rosparam = namedtuple('Rosparam', ('file', 'command', 'parent'))
Include = namedtuple('Include', ('file'))

# getParams - returns a NodeList of the param nodes
def getParams(launch):
    return launch.getElementsByTagName("param")

# getNodes - returns a NodeList of the node nodes
def getNodes(launch):
    return launch.getElementsByTagName("node")

# getRosparams - returns a NodeList of the rosparam nodes
def getRosparams(launch):
    return launch.getElementsByTagName("rosparam")

# getIncludes - returns a NodeList of the include nodes
def getIncludes(launch):
    return launch.getElementsByTagName("include")

# getGivenAttr - returns the value of the given attribute
# if that attribute exists, otherwise returns ""
# @param attrs the NamedNodeMap of attributes
# @param attrName the name of the attribute we want the value of
def getGivenAttr(attrs, attrName):
    for i in range(attrs.length):
        if attrs.item(i).name == attrName:
            return attrs.item(i).value
    return ""

# buildParamList - given a NodeList of params, this builds
# and returns a list of param struct items
def buildParamList(nodelist):
    paramlist = []
    for i in range(nodelist.length):
        paramlist.append(buildParam(nodelist.item(i)))
    return paramlist

# buildParam - given a param node, this builds a param struct
# and then returns it
def buildParam(node):
    parent = getParamParent(node)
    attrs = node.attributes
    nameAttr = getGivenAttr(attrs, 'name')
    typeAttr = getGivenAttr(attrs, 'type')
    if typeAttr == '':
        typeAttr = 'UNK'
    valueAttr = getGivenAttr(attrs, 'value')
    namespace = getParamNamespace(nameAttr)
    name = getParamName(nameAttr)
    return Param(parent, namespace, name, typeAttr, valueAttr)

# buildNodeList - given a NodeList of nodes, this builds a list
# of ROS nodes and returns that list
def buildNodeList(nodelist):
    nlist = []
    for i in range(nodelist.length):
        nlist.append(buildNode(nodelist.item(i)))
    return nlist

# buildNode - given a node node, this builds a node struct
# and then returns it (made up of pkg, name, type)
def buildNode(node):
    pkg = node.getAttribute('pkg')
    name = node.getAttribute('name')
    type = node.getAttribute('type')
    if type == '':
        type = 'UNK'
    return Node(pkg, name, type)

# getParamParent - given a param node, this determines the parent
# of that param and returns it as a string, this is either a node
# name or just launch (meaning global).
def getParamParent(node):
    parent = node.parentNode
    if parent.nodeName == 'node':
        return parent.getAttribute('name')
    return 'launch'

# getParamNamespace - given a param name as a string, this will
# parse the front end of that string to determine if it is:
# global - '' - 0
# private - '~' - 1
# relative/base - '/' - 2
# it will then return the corresponding int
#def getParamNamespace(name):
#    if name[0] == '~':
#        return 1
#    elif name[0] == '/':
#        return 2
#    else:
#        return 0

# getParamName - the name attribute of the param tag contains both
# the name of the parameter and the namespace of the parameter
def getParamName(name):
    slash = name.rfind('/')
    if slash == -1:
        return name
    return name[slash+1:len(name)]

def getParamNamespace(name):
    slash = name.rfind('/')
    if slash == -1:
        return ''
    return name[0:(slash)]

# printParam - print out the given param
def printParam(param):
    attrs = param.attributes
    nameAttr = getGivenAttr(attrs, 'name');
    typeAttr = getGivenAttr(attrs, 'type');
    valueAttr = getGivenAttr(attrs, 'value');
    print nameAttr, typeAttr, valueAttr

# printParamListCSV - print out the params in CSV form
def printParamListCSV(paramlist):
    for a in paramlist:
        printParamCSV(a)

# printParamCSV - print out the values of the given
# param struct as defined above in CSV form
# parent - the parent of this param
# namespace - the defined namespace
# name - the name of the parameter
# type - the type of the param, if defined
# value - the value that is being assigned
def printParamCSV(param):
    print param.parent + ',' + str(param.namespace) + ',' + param.name + ',' + param.type + ',' + param.value

# printNodeListCSV - print out the nodes in CSV form
def printNodeListCSV(nodelist):
    for a in nodelist:
        printNodeCSV(a)

# printNodeCSV - print out the values of the given
# node struct as defined above in CSV form
# pkg - the package that this node should reside
# name - the name of this node
# type - the type of this node
def printNodeCSV(node):
    print node.pkg + ',' + node.name + ',' + node.type

# printParams - prints out the params in the given nodelist
def printParams(nodelist):
    for i in range(nodelist.length):
        printParam(nodelist.item(i))

# buildRosparamList - given a NodeList of the rosparams,
# build a list of them with the file and the command
def buildRosparamList(nodelist):
    rosparam_list = []
    for i in range(nodelist.length):
        rosparam_list.append(buildRosparam(nodelist.item(i)))
    return rosparam_list

# buildRosparam - given a node that is a rosparam, extract
# the file and the command and return a rosparam tuple
def buildRosparam(node):
    file = node.getAttribute('file')
    command = node.getAttribute('command')
    parent = getParamParent(node)
    return Rosparam(file, command, parent)

# buildIncludeList - given a NodeList of the includes,
# build a list of include structs with the file
def buildIncludeList(nodelist):
    include_list = []
    for i in range(nodelist.length):
        include_list.append(buildInclude(nodelist.item(i)))
    return include_list

# buildInclude - given a node that is an Include, extract
# the file and create an Include struct to be returned
def buildInclude(node):
    file = node.getAttribute('file')
    return Include(file)

# readInRosparamFile - given the file of a rosparam tuple,
# access and read in the file for more parameter info
def readInLaunchFile(filename):
    currDom = parse(filename)
    # do stuff with the dom then

# resolvePath - given a rosparam or include path, it will
# use ROS to resolve it and then it will return the version
# of the path that is full and resolved
def resolvePath(rospath):
    p = Popen("rospack find " + rospath, stdout=PIPE, shell=True)
    return p.stdout.readline().rstrip()

# getResolvedFilename - given the file attribute of a rosparam node
# that is for loading, this will resolve the absolute path if
# necessary and then return the full path for the yaml file.
# e.g. $(find beginner_tutorial)/src/stuff.yaml
def getResolvedFilename(fileAttr):
    filename = ""
    if fileAttr.startswith('$(find'):
        i1 = fileAttr.find(' ')+1
        i2 = fileAttr.find(')')
	#filename = fileAttr[i1:i2]
	filename = resolvePath(fileAttr[i1:i2]) + fileAttr[(i2+1):len(fileAttr)]
    else:
        filename = fileAttr
    return filename

# loadYamlFiles - given a list of rosparam structs, for each one
# that is a load, get the full path with getYamlFilename and then
# load in the file and start reading from it.
def loadYamlFiles(rosparamlist):
    paramlist = []
    for rp in rosparamlist:
        if rp.command != 'load':
            continue
        filename = getResolvedFilename(rp.file)
        stream = file(filename, 'r')
        datamap = yaml.load(stream)
	for tup in datamap:
            #print tup[0] + ' -- ' + tup[1]
            #print tup + ' -- ' + str(datamap[tup])
            paramlist.append(Param(rp.parent, '', tup, 'UNK', str(datamap[tup])))
    return paramlist

# loadIncludeFiles - given a list of Include structs, each one
# should be another launch file which can then be subsequently
# parsed, so pull it out, create a dom for it and then run the
# extraction process on it
def loadIncludeFiles(includelist):
    paramlist = []
    for include in includelist:
        filename = getResolvedFilename(include.file)
        paramlist.extend(parseLaunch(filename))
    return paramlist

# parseLaunch - this is the master function that will take an
# initial launch file name as input and will extract all the
# params and nodes, then it will extract the includes and rosparams
# and open up those to pull out their params and nodes and so forth
def parseLaunch(filename):
    currDom = parse(filename)
    params = []
    paramlist = getParams(currDom)
    nodelist = getNodes(currDom)
    rosparamlist = getRosparams(currDom)
    includelist = getRosparams(currDom)

# There are two things that we need to get from the launch files:
# 1. We want a list of all the params, so we need a getAllParams
# 2. We want a list of all the nodes, so we need a getAllNodes
def getAllParams(filename):
    # first, we get the params from this main file
    dom = parse(filename)
    params = []
    paramlist = getParams(dom)
    params.extend(buildParamList(paramlist))

    # then we get all the params from YAML files from rosparams
    rosparamlist = buildRosparamList(getRosparams(dom))
    if len(rosparamlist) > 0:
        params.extend(loadYamlFiles(rosparamlist))

    # then we print out all the params collected so far
    printParamListCSV(params)

    # finally, we recursively call getAllParams on any includes
    # this will ensure that any YAML files and includes then also
    # get called
    includelist = getIncludes(dom)
    for include in buildIncludeList(includelist):
        getAllParams(getResolvedFilename(include.file))

# paramsToDB - 

# getExtendedParamSchema - this function is going to work similarly
# to the getAllParams function, except that it will print out the
# parameter information as a CSV using the extended schema:
# := id,runID,timestamp,transType,source,name,value,default,type,setFrom,nodeNS,paramNS,succ,msg
# := --,-----,---------,------set,----lf,name,value,-------,type,-----lf,------,paramNS,----,---
def getExtendedParamSchema(filename):
    # first, we get the aprams form this main file
    dom = parse(filename)
    params = []
    paramlist = getParams(dom)
    params.extend(buildParamList(paramlist))

    # then we get all the params from the YAML files form rosparams
    rosparamlist = buildRosparamList(getRosparams(dom))
    if len(rosparamlist) > 0:
        params.extend(loadYamlFiles(rosparamlist))

    # then we print out all the params in extended form
    printExtendedParamListCSV(params)

    # finally, we do recursive call to any includes
    includelist = getIncludes(dom)
    for include in buildIncludeList(includelist):
        getExtendedParamSchema(getResolvedFilename(include.file))

# printExtendedParamListCSV - this is going to take the given list of
# param structs and call printExtendedParamCSV on each.
def printExtendedParamListCSV(paramlist):
    for param in paramlist:
        printExtendedParamCSV(param)

# printExtendedParamCSV - this is going to take the given param struct
# and then print it out based on the extended schema.
def printExtendedParamCSV(param):
    print ",,,set,lf," + param.name + "," + param.value + ",," + param.type + "," + param.parent + ",," + param.namespace + ",,"

def getAllNodes(filename):
    # first, we get the nodes for this main file
    dom = parse(filename)
    nodes = []
    nodelist = getNodes(dom)
    nodes.extend(buildNodeList(nodelist))
    
    # then we print all the nodes collected so far
    printNodeListCSV(nodes)
    
    # finally, we recursively call getAllNodes on any includes
    includelist = getIncludes(dom)
    for include in buildIncludeList(includelist):
        getAllNodes(getResolvedFilename(include.file))
