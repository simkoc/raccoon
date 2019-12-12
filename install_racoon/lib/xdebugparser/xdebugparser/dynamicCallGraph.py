from py2neo.ogm import GraphObject, Property, RelatedTo
from uuid import uuid4
import sys
sys.setrecursionlimit(10000)


class BasicNode(GraphObject):
    """ Any node in a deep model DB must extend this class
    """

    __primarykey__ = "uuid"

    uuid = Property()

    projname = Property()
    xdebugid = Property()
    dm_type = Property()

    def __init__(self, projname, xid, dm_type=None):
        self.projname = projname
        self.dm_type = dm_type
        self.xdebugid = xid
        self.uuid = str(uuid4())


class DynamicTreeRoot(BasicNode):
    filename = Property()
    requesturl = Property()
    callNr = Property()

    calls = RelatedTo(["DynamicFunctionCall"])

    def __init__(self, requesturl, projname, xid):
        super(DynamicTreeRoot, self).__init__(projname, xid)
        self.requesturl = requesturl
        self.callNr = 0

    def add_call(self, callNode):
        # multiple calls from tree root are possible (destructors!)
        self.calls.add(callNode, {"callnr": self.callNr})
        self.callNr = self.callNr + 1


class DynamicFunctionName(BasicNode):
    functionName = Property()
    sourceFile = Property()

    def __init__(self, functionName, sourceFile, projname, xid):
        super(DynamicFunctionName, self).__init__(projname, xid)
        self.functionName = functionName
        self.sourceFile = sourceFile

    def __str__(self):
        return self.functionName


def octal_print(s):
    # this is evil black string magic but it fixes the
    # octal encoding issue - it ain't stupid if it works
    charlist = list()
    for character in s:
        try:
            character.decode('ascii')
            charlist.append(character)
        except:
            charlist.append('\\'+oct(ord(character))[1:])
    return ''.join(charlist)


class DynamicFunctionCall(BasicNode):
    parameters = Property()
    returnvalue = Property()
    callNr = Property()
    functionname = Property()

    calls = RelatedTo(["DynamicFunctionCall"])
    isfunction = RelatedTo(["DynamicFunctionName"])
    returns = RelatedTo(["DynamicReturnValue"])
    calledwith = RelatedTo(["DynamicParameter"])

    def __init__(self, parameters, isfunction, projname, functionname, xid):
        super(DynamicFunctionCall, self).__init__(projname, xid)
        self.callNr = 0
        self.functionname = functionname
        encoded_params = list()
        counter = 0
        for param in parameters:
            try:
                val = param.decode('ascii')
            except:
                val = octal_print(param)
            parameter = DynamicParameter(val, projname, xid, counter)
            self.calledwith.add(parameter)
            encoded_params.append(val)
            counter = counter + 1

        self.parameters = ",".join(encoded_params)
        self.isfunction.add(isfunction)

    def add_call(self, callNode):
        self.calls.add(callNode, {"callnr": self.callNr})
        self.callNr = self.callNr + 1

    def update_return_value(self, record):
        val = ""
        try:
            val = record._return_value.decode('ascii', 'strict')
        except:
            val = octal_print(record._return_value)
        self.returnvalue = val
        self.returns.add(DynamicReturnValue(val, self.projname, self.xdebugid))

    def __str__(self):
        return "{} called with {}".format(self.functionname, self.parameters)


class DynamicParameter(BasicNode):

    name = Property()
    content = Property()
    childnum = Property()

    def __init__(self, parameter, projname, xid, childnum):
        super(DynamicParameter, self).__init__(projname, xid)
        split = parameter.split("=")
        if len(split) == 2:
            self.name = split[0]
            self.content = split[1]
        else:
            self.name = "unknown"
            self.content = split[0]


class DynamicReturnValue(BasicNode):

    content = Property()

    def __init__(self, content, projname, xid):
        super(DynamicReturnValue, self).__init__(projname, xid)
        if (content is None) or (content == ""):
            self.content = "NULL"
        else:
            self.content = content


def push_function_call(callingNode, targetRecord,
                       functionDictionary, projname,
                       xdebugid):
    targetFunctionNode = None
    if targetRecord._function_name not in functionDictionary:
        targetFunctionNode = DynamicFunctionName(targetRecord._function_name,
                                                 targetRecord._filename,
                                                 projname, xdebugid)
        functionDictionary[targetRecord._function_name] = targetFunctionNode
    else:
        targetFunctionNode = functionDictionary[targetRecord._function_name]

    newCallingNode = DynamicFunctionCall(targetRecord._parameters,
                                         targetFunctionNode, projname,
                                         targetRecord._function_name,
                                         xdebugid)

    callingNode.add_call(newCallingNode)

    return newCallingNode


def generate_dynamic_call_graph(xtrace, projname, xdebugid, graph):
    root = DynamicTreeRoot(xtrace._requesturl, projname, xdebugid)
    callStack = [root]
    nodes = [callStack[-1]]
    functionDictionary = {}
    lastExit = None
    current_call_node = callStack[-1]
    depth = 0
    for record in xtrace._trace_content:
        try:
            if record._type == "ENTRY":
                depth = depth + 1
                current_call_node = push_function_call(current_call_node, record,
                                                       functionDictionary, projname,
                                                       xdebugid)
                callStack.append(current_call_node)
                nodes.append(current_call_node)
            if record._type == "EXIT":
                depth = depth - 1
                lastExit = callStack.pop()
                current_call_node = callStack[-1]
            if record._type == "RETURN":
                lastExit.update_return_value(record)
        except:
            print "encountered exception {} in record {}".format(sys.exc_info()[0], record)
            raise

    if len(callStack) != 1:
        raise Exception("at the end of parsing the call stack is of size {} - must be 1".format(len(callStack)))
    nodeCount = len(nodes)
    print "the dyn call graph has %s nodes" % (nodeCount,)
    graph.push(root)
    # for node in reversed(nodes):
    #    if counter % 100:
    #        print "inserted nodes {}/{}".format(counter, nodeCount)
    #    graph.push(node)
