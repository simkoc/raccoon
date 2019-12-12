"""
Author: Simon Koch <s9sikoch@stud.uni-saarland.de>
Thus file contains the code to parse xdebug trace files
with trace_format = 1.
It also provides the means to extract all fopen calls
of the given trace and returns all parameters to those calls
as well as returning mysql queries after preparation.
"""
import re
import hashlib
import dateutil.parser as dp


def integerp(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def remove_non_state_changing_queries(query_list):
    return [query for query in query_list if
            not re.search('SHOW', query[0]) and
            not re.search('show', query[0]) and
            not re.search('SELECT', query[0]) and
            not re.search('select', query[0])]


def clean_query(query):
    # print "before: {}".format(query)
    query = re.sub(" [ ]+",
                   " ",
                   re.sub(r'\n|\t|\\',
                          " ",
                          re.sub(r'\\t|\\n|\\|\n',
                                 " ",
                                 re.sub(r"\\'",
                                        "'",
                                        query))))
    query = query.strip()
    # print "reg: {}".format(query)
    # study of the query reveals that there
    # tends to be a leading ' and a closing '_ which is unwanted
    # this is in case the query ends on ' due to > = 'stuff'< but if leading than unlikely
    if query[0] == "'": # there is no reason for leading '
        query = query[1:]

    # print "mid: {}".format(query)
        
    amount = query.count("'") 
    if query[-1] == "'" and amount % 2 == 1: # there is tail ' and the amount is uneven
        query = query[:-1]
        
    # print "after: {}".format(query)
        
    return query.strip()


def position(item, elemlist, start=-1,
             test=lambda lhs, rhs: lhs == rhs):
    ret = []
    if start == -1:
        ret = [i for i, x in enumerate(elemlist) if test(x, item)]
    else:
        ret = [i for i, x in enumerate(elemlist[start + 1:]) if test(x, item)]
    assert(len(ret) >= 1)
    return ret[0]


def extract_argument(execute_parameter):
    return re.sub("[ 0-9]+ =>", execute_parameter, "")


def parse_array_content(array_content):
    ret = []
    for content in re.split(",", array_content):  # TODO:this can badly break if , is a contained value
        if re.search("=>", content):  # TODO:this can badly break if => is contained value
            ret.append(re.split("=>", content)[1])
        else:
            ret.append(content)
    return ret


def array_to_parameterlist(execute_parameter_array):
    # print execute_parameter_array
    if execute_parameter_array:
        array_content_bracketed = re.sub("array ",
                                         "",
                                         execute_parameter_array).rstrip()
        # print "'{}'".format(array_content_bracketed)
        return parse_array_content(array_content_bracketed[1:-1])
    else:
        return None


def find_nth_occurence(nth, item, elemlist, start=-1,
                       test=lambda lhs, rhs: lhs == rhs):
    if nth == 0:
        if start == -1:
            return None
        else:
            start
    else:
        pos = position(item, elemlist, start=(start + 1))
        return find_nth_occurence(nth - 1, item, elemlist,
                                  start=pos, test=test)


def inject_and_replace_nth(nth, inject_array, array):
    return array[0:nth] + inject_array + array[nth+1:]


def remove_first_and_last_char(string):
    return string[1:-1]


def replace_qmark_with_string(nth, string, query):
    # print "stuff", nth, string, query
    if find_nth_occurence(nth, '?', query):
        return inject_and_replace_nth(find_nth_occurence(nth, '?', query),
                                      string,
                                      query)
    else:
        ValueError("Replacing #{} ? with {} in query {} failed".format(nth, string, query))


def pdo_bind_values(prep_string, prepare_statements):
    prepare_statements.reverse()
    # print prep_string
    # print prepare_statements
    for item in prepare_statements:
        if integerp(item._parameters[0]):
            prep_string = replace_qmark_with_string(int(item._parameters[0]),
                                                    item._parameters[1],
                                                    prep_string)
        else:
            # apparently both :ID and ID are valid subs -.-
            replace_id = remove_first_and_last_char(item._parameters[0])
            replace_id = "{}".format(replace_id) if replace_id[0] == ":" else ":{}".format(replace_id)
            # print replace_id
            prep_string = re.sub(replace_id,
                                 item._parameters[1],
                                 prep_string)
    return prep_string


def pdo_function_calls_to_query_string(records):
    # print(records)
    assert(records[0]._function_name == "PDO->prepare")
    # print "working on {}".format(records)
    if not records[-1]._function_name == "PDOStatement->execute":
        print "[WARN] last given record NOT PDOStatement->execute"

    prep_string = records[0]._parameters[0]
    # print prep_string
    prep_string = pdo_bind_values(prep_string, records[1:-1])
    # print prep_string
    if len(records[-1]._parameters) > 0:
        # print "{}".format(array_to_parameterlist(records[-1]._parameters[0]))
        for item in array_to_parameterlist(records[-1]._parameters[0]):
            # print "in {} replace with {}".format(prep_string, item)
            prep_string = re.sub("\\?",
                                 item,
                                 prep_string,
                                 count=1)
            # print "result: {}".format(prep_string)
    # print "resulted in {}".format(prep_string)
    return prep_string


class FunctionNGram:

    def __init__(self, function_list):
        self._function_list = function_list

    def __hash__(self):
        return int(hashlib.sha224(
            str("".join(self._function_list))).hexdigest(),
                16)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return "".join(self._function_list)


class Record:
    _type = "BASIC"
    _level = None
    _function_nr = None

    def __init__(self, level, function_nr):
        self._level = level
        self._function_nr = function_nr


class EntryRecord(Record):
    _time_index = None
    _memory_usage = None
    _function_name = None
    _user_defined_p = None
    _name_of_ir_file = None
    _filename = None
    _line_number = None
    _parameters = None

    def __init__(self, level, function_nr, always, time_index, memory_usage,
                 function_name, user_defined_p, name_of_ir_file,
                 filename, line_number, param_count, parameters):
        # super(self.__class__, self, level, function_nr).__init__()
        self._type = "ENTRY"
        self._level = level
        self._function_nr = function_nr
        self._time_index = time_index
        self._memory_usage = memory_usage
        self._function_name = function_name
        self._user_defined_p = user_defined_p
        self._name_of_ir_file = name_of_ir_file
        self._filename = filename
        self._line_number = line_number
        self._parameters = parameters

    def __str__(self):
        return "{}//{}//{}//{}//{}//{}//{}//{}".format(self._time_index,
                                                       self._memory_usage,
                                                       self._function_name,
                                                       self._user_defined_p,
                                                       self._name_of_ir_file,
                                                       self._filename,
                                                       self._line_number,
                                                       self._parameters)

    def __repr__(self):
        return self.__str__()


class ExitRecord(Record):
    _time_index = None
    _memory_usage = None

    def __init__(self, level, function_nr, time_index, memory_usage):
        # super(self.__class__, self, level, function_nr).__init__()
        self._type = "EXIT"
        self._level = level
        self._function_nr = function_nr
        self._time_index = time_index
        self._memory_usage = memory_usage


class ReturnRecord(Record):
    _return_value = None

    def __init__(self, level, function_nr, return_value):
        # super(self.__class__, self, level, function_nr)
        self._type = "RETURN"
        self._level = level
        self._function_nr = function_nr
        self._return_value = return_value

    def __str__(self):
        return "[RET values:{}]".format(self._return_value)


class XdebugTrace:
    _trace_content = []
    _debug = False
    _time = None
    _requesturl = None

    def __init__(self, xdebug_stream, requesturl="", debug=False):
        self._trace_content = []
        self._debug = debug
        self._requesturl = requesturl
        self.parse_xdebug_stream(xdebug_stream)

    def parse_time(self, time_line):
        sr = re.search("\\[.+\\]", time_line)
        if sr is not None:
            res = sr.group(0)
            res = res[1:-1]
            return dp.parse(res)
        else:
            return dp.parse("0001-01-01 00:00:00")

    def parse_xdebug_stream(self, xdebug_stream):
        xdebug_stream.readline()  # the first three
        xdebug_stream.readline()  # lines are really
        self._time = self.parse_time(xdebug_stream.readline())  # no needed

        count = 0
        for line in xdebug_stream:
            count += 1
            last = self.parse_xdebug_line(line)
            if last:
                self._trace_content.append(last)
            else:
                break
        if self._debug:
            print "parsed {} xdebug dump lines and extracted {} entries".format(count,
                                                                                len(self._trace_content))

    def parse_xdebug_line(self, line):
        if line is None:
            return None
        eline = re.split(r'\t', line)
        try:
            catch_bad_format = eline[2]  # check if line exists
        except:
            return None  # this catches broken lines within the xdebug REALLY EVIL THO

        try:
            if eline[0] == "" and eline[1] == "" and eline[2] == "":
                return None
            elif eline[2] == "0":
                return EntryRecord(eline[0], eline[1], eline[2], eline[3],
                                   eline[4], eline[5], eline[6], eline[7],
                                   eline[8], eline[9], eline[10], eline[11:])
            elif eline[2] == "1":
                return ExitRecord(eline[0], eline[1], eline[2], eline[3])
            elif eline[2] == "R":
                return ReturnRecord(eline[0], eline[1], eline[5])
            else:
                raise ValueError("There ain't no such thing as {} as the always part in '{}'".format(eline[2], line))
        except IndexError:
            print "line '{}' resulted in IndexError".format(eline)
            raise

    def get_changed_file_paths(self):
        return [entry for entry in self._trace_content
                if entry.__class__ == "EntryRecord" and
                entry._function_name == "fopen"]

    def get_all_pdo_calls(self):
        return [entry for entry in self._trace_content
                if isinstance(entry, EntryRecord) and
                (entry._function_name == "PDO->prepare" or
                 entry._function_name == "PDOStatement->bindValue" or
                 entry._function_name == "PDOStatement->execute")]

    def get_pdo_prepared_queries(self):
        pdo_records = self.get_all_pdo_calls()
        queries = []
        query_times = []

        def get_preparation_set(start_record, remaining_traces):
            # print start_record
            if remaining_traces:
                # print remaining_traces[0]
                if "PDOStatement->bindValue" in remaining_traces[0]._function_name:
                    li, remaining = get_preparation_set(start_record, remaining_traces[1:])
                    if li is None:
                        raise ValueError("list of PDO must not be empty")
                    return [remaining_traces[0]] + li, remaining
                elif "PDOStatement->execute" in remaining_traces[0]._function_name:
                    return [remaining_traces[0]], remaining_traces[1:]
                else:
                    raise ValueError(
                        "unexpected trace element {}\n in context of start_record {}".format(
                            remaining_traces[0], start_record))
            else:
                return [start_record]

        def get_next_pdo_start(remaining_traces):
            if remaining_traces:
                if "PDO->prepare" in remaining_traces[0]._function_name:
                    return remaining_traces[0], remaining_traces[1:]
                else:
                    pass  # this looks quite fishy in the original lisp but the code works oO
            else:
                return None

        while pdo_records:
            start_record, remaining_records = get_next_pdo_start(pdo_records)
            records, remaining_records = get_preparation_set(start_record, remaining_records)
            query = pdo_function_calls_to_query_string([start_record] + records)
            if query is not None:
                queries.append(query)
                query_times.append(records[-1]._time_index)
            pdo_records = remaining_records

        return queries, query_times

    def get_regular_sql_queries(self):
        buf = [record for record in self._trace_content if
               record._type == "ENTRY" and
               (record._function_name == "mysqli->query" or
                record._function_name == "PDO->query" or
                record._function_name == "PDO->exec" or
                record._function_name == "mysql_query")]

        ret = []
        query_times = []

        for elem in buf:
            # print elem
            ret.append(clean_query(elem._parameters[0]))
            query_times.append(elem._time_index)

        return ret, query_times

    def get_mysqli_queries(self):
        buf = [record for record in self._trace_content if
               isinstance(record, EntryRecord) and
               record._function_name == "mysqli_query"]

        ret = []
        query_times = []
        for elem in buf:
            ret.append(elem._parameters[1])
            query_times.append(elem._time_index)

        return ret, query_times

    def get_sql_queries(self, keep_all_queries=False, logger=None):
        queries, query_times = self.get_mysqli_queries()
        bqueries, bquery_times = self.get_pdo_prepared_queries()
        queries += bqueries
        query_times += bquery_times
        bqueries, bquery_times = self.get_regular_sql_queries()
        queries += bqueries
        query_times += bquery_times

        buff = [[clean_query(query), time] for query, time in
                zip(queries, query_times)]
        queries = [elem[0] for elem in buff]
        query_times = [elem[1] for elem in buff]
        if logger is not None:
            logger.debug("I contain {} queries".format(len(queries)))
        if keep_all_queries:
            return queries, query_times
        else:
            buff = remove_non_state_changing_queries(buff)
            queries = [elem[0] for elem in buff]
            query_times = [elem[1] for elem in buff]
            return queries, query_times

    def get_all_referenced_source_files(self, logger=None):
        require_includes = [record for record in self._trace_content if
                            record._type == "ENTRY" and
                            (record._function_name == "require_once" or
                             record._function_name == "require" or
                             record._function_name == "include_once" or
                             record._function_name == "include")]
        table = {}
        for entry in require_includes:
            table[entry._name_of_ir_file] = True

        ret = []
        for key in table:
            ret.append(key)

        return sorted(ret)

    def get_all_used_source_files(self, logg=None):
        entry_records = [record for record in self._trace_content if
                         record._type == "ENTRY"]
        table = {}
        for entry in entry_records:
            table[entry._filename] = True

        ret = []
        for key in table:
            ret.append(key)

        return sorted(ret)

    def get_start_timestamp(self):
        return self._time

    def generate_flat_function_n_gram(self, n):
        entry_records = [record for record in self._trace_content if
                         record._type == "ENTRY"]

        buffer = []
        n_grams = []
        for entry in entry_records:
            buffer.append(entry._function_name)
            if len(buffer) == n:
                n_grams.append(FunctionNGram(buffer))
                buffer = []

        return n_grams

    def compare_ngram_fingerprints(self, other_xdebug, n=3):
        self_ngram = self.generate_flat_function_n_gram(n)
        other_ngram = other_xdebug.generate_flat_function_n_gram(n)
        a = set(self_ngram)
        b = set(other_ngram)
        diff = [item for item in a if item not in b]
        return 1 - float(len(diff))/len(a)
